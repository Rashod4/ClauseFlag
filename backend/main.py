import os
import uuid
import json
import sqlite3
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Since this is an MVP local dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'clauseflag.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript("""
      CREATE TABLE IF NOT EXISTS analyses (
        id TEXT PRIMARY KEY,
        url TEXT,
        raw_text TEXT,
        status TEXT,
        clause_count INTEGER,
        risk_summary TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        completed_at DATETIME
      );

      CREATE TABLE IF NOT EXISTS clauses (
        id TEXT PRIMARY KEY,
        analysis_id TEXT,
        position INTEGER,
        text TEXT,
        risk TEXT,
        confidence REAL,
        anomaly_score REAL,
        category TEXT,
        explanation TEXT,
        FOREIGN KEY(analysis_id) REFERENCES analyses(id)
      );
    """)
    conn.commit()
    conn.close()

init_db()

MIN_TEXT_LENGTH = 50
MAX_TEXT_LENGTH = 100_000


class AnalyzeRequest(BaseModel):
    url: Optional[str] = None
    text: Optional[str] = None

class ClauseResponse(BaseModel):
    id: str
    text: str
    risk: str
    confidence: float
    anomaly_score: float
    category: str
    explanation: str

class AnalysisSummaryResponse(BaseModel):
    id: str
    status: str
    clause_count: int
    risk_summary: dict

def split_into_sentences(text: str) -> List[str]:
    import re
    # Simple regex-based sentence splitter
    sentences = re.split(r'(?<=[.!?]) +', text)
    return [s.strip() for s in sentences if len(s.strip()) > 5]

def process_analysis_job(analysis_id: str, text: str):
    import sqlite3
    from classifier import get_classifier
    from anomaly import get_anomaly_detector
    from explainer import get_explainer

    try:
        sentences = split_into_sentences(text)
        
        classifier = get_classifier()
        anomaly_detector = get_anomaly_detector()
        explainer = get_explainer()

        risk_summary = {"safe": 0, "watch": 0, "danger": 0}
        clauses_data = []

        for i, sentence in enumerate(sentences):
            # 1. Zero-shot Classification (risk & confidence)
            class_res = classifier.classify(sentence)
            risk = class_res["risk"]
            confidence = class_res["confidence"]

            # 2. Anomaly Scoring against known corpus
            anomaly_score = anomaly_detector.compute_anomaly_score(sentence)

            # 3. Rule-based explanation and categorization
            exp_res = explainer.generate_explanation(sentence, risk)

            if risk in risk_summary:
                risk_summary[risk] += 1
            else:
                risk_summary["watch"] += 1

            clauses_data.append({
                "id": str(uuid.uuid4()),
                "analysis_id": analysis_id,
                "position": i,
                "text": sentence,
                "risk": risk,
                "confidence": confidence,
                "anomaly_score": anomaly_score,
                "category": exp_res["category"],
                "explanation": exp_res["explanation"]
            })

        # Save to DB
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        for c_data in clauses_data:
            c.execute("""
                INSERT INTO clauses (id, analysis_id, position, text, risk, confidence, anomaly_score, category, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (c_data["id"], c_data["analysis_id"], c_data["position"], c_data["text"], c_data["risk"], c_data["confidence"], c_data["anomaly_score"], c_data["category"], c_data["explanation"]))
        
        c.execute("""
            UPDATE analyses 
            SET status = 'complete', clause_count = ?, risk_summary = ?, completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (len(sentences), json.dumps(risk_summary), analysis_id))
        
        conn.commit()
        conn.close()

    except Exception as e:
        import traceback
        traceback.print_exc()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE analyses SET status = 'failed' WHERE id = ?", (analysis_id,))
        conn.commit()
        conn.close()

def _find_cached_analysis(url: str) -> Optional[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    row = c.execute("""
        SELECT id, status FROM analyses
        WHERE url = ? AND status = 'complete'
          AND created_at > datetime('now', '-24 hours')
        ORDER BY created_at DESC LIMIT 1
    """, (url,)).fetchone()
    conn.close()
    if row:
        return {"id": row["id"], "status": row["status"]}
    return None


def _validate_text_length(text: str) -> None:
    if len(text) < MIN_TEXT_LENGTH:
        raise HTTPException(status_code=400, detail="Text too short to analyze")
    if len(text) > MAX_TEXT_LENGTH:
        raise HTTPException(status_code=400, detail="Text exceeds maximum length")


@app.post("/api/analyze")
async def create_analysis(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    from scraper import scrape_url

    text = request.text
    url = request.url

    if not url and not text:
        raise HTTPException(
            status_code=422,
            detail="Either 'url' or 'text' must be provided",
        )

    if url and not text:
        cached = _find_cached_analysis(url)
        if cached:
            return cached
        try:
            text = scrape_url(url)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    _validate_text_length(text)

    analysis_id = str(uuid.uuid4())

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO analyses (id, url, raw_text, status, clause_count, risk_summary)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (analysis_id, url, text, 'processing', 0, json.dumps({"safe": 0, "watch": 0, "danger": 0})))
    conn.commit()
    conn.close()

    background_tasks.add_task(process_analysis_job, analysis_id, text)

    return {"id": analysis_id, "status": "processing"}

@app.get("/api/analyses/{analysis_id}")
async def get_analysis(analysis_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    row = c.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Analysis not found")
        
    return {
        "id": row["id"],
        "url": row["url"],
        "status": row["status"],
        "clause_count": row["clause_count"],
        "risk_summary": json.loads(row["risk_summary"]),
        "created_at": row["created_at"],
        "completed_at": row["completed_at"],
    }

@app.get("/api/analyses/{analysis_id}/clauses")
async def get_clauses(analysis_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Check if analysis is complete
    status = c.execute("SELECT status FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
    if not status:
        conn.close()
        raise HTTPException(status_code=404, detail="Analysis not found")
        
    if status["status"] != "complete":
        conn.close()
        # If it's processing, just return empty list as a signal to keep waiting
        return {"clauses": []}
    
    rows = c.execute("SELECT * FROM clauses WHERE analysis_id = ? ORDER BY position ASC", (analysis_id,)).fetchall()
    conn.close()

    clauses = [dict(row) for row in rows]
    return {"clauses": clauses}
