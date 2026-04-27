import os
import uuid
import json
import sqlite3
from datetime import datetime, timedelta

import bcrypt
import jwt

from fastapi import Depends, FastAPI, BackgroundTasks, Header, HTTPException
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

      CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS history (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        url TEXT,
        analysis_result TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
      );

      CREATE INDEX IF NOT EXISTS idx_analyses_url_status ON analyses(url, status);
      CREATE INDEX IF NOT EXISTS idx_clauses_analysis_id ON clauses(analysis_id);
    """)
    conn.commit()
    conn.close()

init_db()


def _migrate_old_explanations():
    """Re-generate explanations for clauses still stored as plain strings."""
    from explainer import get_explainer

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT id, text, risk, explanation FROM clauses").fetchall()
    explainer = get_explainer()

    migrated = 0
    for row in rows:
        raw = row["explanation"] or ""
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict) and "summary" in parsed:
                continue
        except (json.JSONDecodeError, TypeError):
            pass

        exp_res = explainer.generate_explanation(row["text"], row["risk"])
        conn.execute(
            "UPDATE clauses SET explanation = ?, category = ? WHERE id = ?",
            (json.dumps(exp_res["explanation"]), exp_res["category"], row["id"]),
        )
        migrated += 1

    if migrated:
        conn.commit()
    conn.close()


_migrate_old_explanations()

# ── Auth configuration ──────────────────────────────────────────────

JWT_SECRET = os.environ.get("CLAUSEFLAG_JWT_SECRET", "dev-secret-change-in-production!")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


def get_optional_user_id(
    authorization: Optional[str] = Header(default=None),
) -> Optional[str]:
    """Return the user_id from Bearer token, or None if absent/invalid."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return decode_access_token(authorization[7:])


def get_required_user_id(
    authorization: Optional[str] = Header(default=None),
) -> str:
    """Return the user_id from Bearer token; raise 401 if missing/invalid."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization token")
    user_id = decode_access_token(authorization[7:])
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user_id


# ── Constants & models ──────────────────────────────────────────────

MIN_TEXT_LENGTH = 50
MAX_TEXT_LENGTH = 100_000

ANOMALY_THRESHOLD = 0.7


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


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

def process_analysis_job(
    analysis_id: str,
    text: str,
    user_id: Optional[str] = None,
    url: Optional[str] = None,
):
    import sqlite3
    from classifier import get_classifier
    from anomaly import get_anomaly_detector
    from explainer import get_explainer

    try:
        sentences = split_into_sentences(text)
        
        classifier = get_classifier()
        anomaly_detector = get_anomaly_detector()
        explainer = get_explainer()

        risk_summary = {"safe": 0, "watch": 0, "danger": 0, "unusual": 0}
        clauses_data = []

        for i, sentence in enumerate(sentences):
            class_res = classifier.classify(sentence)
            risk = class_res["risk"]
            confidence = class_res["confidence"]

            anomaly_score = anomaly_detector.compute_anomaly_score(sentence)

            exp_res = explainer.generate_explanation(sentence, risk)

            if risk in ("safe", "watch", "danger"):
                risk_summary[risk] += 1
            else:
                risk_summary["watch"] += 1

            if anomaly_score >= ANOMALY_THRESHOLD:
                risk_summary["unusual"] += 1

            clauses_data.append({
                "id": str(uuid.uuid4()),
                "analysis_id": analysis_id,
                "position": i,
                "text": sentence,
                "risk": risk,
                "confidence": confidence,
                "anomaly_score": anomaly_score,
                "category": exp_res["category"],
                "explanation": json.dumps(exp_res["explanation"]),
            })

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

        if user_id:
            analysis_result = {
                "analysis_id": analysis_id,
                "clause_count": len(sentences),
                "risk_summary": risk_summary,
            }
            c.execute(
                "INSERT INTO history (id, user_id, url, analysis_result) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), user_id, url, json.dumps(analysis_result)),
            )

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


@app.post("/api/register")
async def register(request: RegisterRequest):
    if len(request.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    user_id = str(uuid.uuid4())
    pw_hash = hash_password(request.password)

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
            (user_id, request.username, pw_hash),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=409, detail="Username already taken")
    conn.close()

    token = create_access_token(user_id)
    return {"token": token, "user_id": user_id, "username": request.username}


@app.post("/api/login")
async def login(request: LoginRequest):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (request.username,),
    ).fetchone()
    conn.close()

    if not row or not verify_password(request.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(row["id"])
    return {"token": token, "user_id": row["id"], "username": row["username"]}


@app.get("/api/history")
async def get_history(user_id: str = Depends(get_required_user_id)):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, url, analysis_result, created_at FROM history "
        "WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()

    return {
        "history": [
            {
                "id": row["id"],
                "url": row["url"],
                "analysis_result": json.loads(row["analysis_result"])
                if row["analysis_result"]
                else None,
                "created_at": row["created_at"],
            }
            for row in rows
        ]
    }


@app.post("/api/analyze")
async def create_analysis(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    user_id: Optional[str] = Depends(get_optional_user_id),
):
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

    background_tasks.add_task(process_analysis_job, analysis_id, text, user_id, url)

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
        "raw_text": row["raw_text"],
        "status": row["status"],
        "clause_count": row["clause_count"],
        "risk_summary": json.loads(row["risk_summary"]),
        "created_at": row["created_at"],
        "completed_at": row["completed_at"],
    }

def _parse_clause_row(row) -> dict:
    d = dict(row)
    raw = d.get("explanation", "")
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict) and "summary" in parsed:
            d["explanation"] = parsed
        else:
            d["explanation"] = {"summary": str(parsed) if parsed else raw, "unusual": "", "risks": ""}
    except (json.JSONDecodeError, TypeError):
        d["explanation"] = {"summary": raw, "unusual": "", "risks": ""}
    return d


@app.get("/api/analyses/{analysis_id}/clauses")
async def get_clauses(analysis_id: str, sort: str = "position"):
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

    order_clauses = {
        "anomaly": "anomaly_score DESC, position ASC",
        "confidence": "confidence DESC, position ASC",
        "risk": "CASE risk WHEN 'danger' THEN 0 WHEN 'watch' THEN 1 WHEN 'safe' THEN 2 ELSE 3 END ASC, position ASC",
        "position": "position ASC",
    }
    order_by = order_clauses.get(sort, order_clauses["position"])

    rows = c.execute(
        f"SELECT * FROM clauses WHERE analysis_id = ? ORDER BY {order_by}",
        (analysis_id,),
    ).fetchall()
    conn.close()

    clauses = [_parse_clause_row(row) for row in rows]
    return {"clauses": clauses}
