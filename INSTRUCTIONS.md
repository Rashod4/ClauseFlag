# INSTRUCTIONS.md — AI-Ready Project Reference

> This file is designed for LLM-based coding assistants (Claude, GPT, Gemini, etc.)
> to quickly understand, build, run, and test ClauseFlag.

---

## 1. Project Overview

**ClauseFlag** is a web application that analyzes Terms of Service and Privacy Policy documents. Users paste legal text; the system splits it into clauses and classifies each clause as **safe**, **watch**, or **danger** using ML models, then displays results with confidence scores, anomaly scores, and plain-language explanations.

---

## 2. Architecture

The app is a **two-process** system:

```
┌──────────────────────────┐       ┌──────────────────────────────────────┐
│   React Frontend (Vite)  │       │        Python Backend (FastAPI)      │
│   Port 5173              │──────▶│        Port 8000                     │
│                          │ /api  │                                      │
│  src/App.tsx             │ proxy │  backend/main.py          (routes)   │
│  src/apiClient.ts        │       │  backend/classifier.py    (ML)       │
│                          │       │  backend/anomaly.py       (ML)       │
│                          │       │  backend/explainer.py     (rules)    │
└──────────────────────────┘       └──────────────────────────────────────┘
                                              │
                                              ▼
                                     clauseflag.db (SQLite)
```

- **Frontend** → React 18 + TypeScript + Tailwind CSS 4 + Vite 6
- **Backend** → Python 3.9+ + FastAPI + Uvicorn
- **ML Models** → Hugging Face `facebook/bart-large-mnli` (zero-shot classification) + `all-MiniLM-L6-v2` (sentence embeddings for anomaly detection)
- **Database** → SQLite (auto-created as `clauseflag.db` in project root)
- **Proxy** → Vite dev server proxies `/api/*` requests to `http://127.0.0.1:8000` (configured in `vite.config.ts`)

---

## 3. File Structure

```
ClauseFlag/
├── backend/                    # Python FastAPI backend
│   ├── main.py                 # FastAPI app, routes, DB init, background job orchestration
│   ├── classifier.py           # Zero-shot classification using facebook/bart-large-mnli
│   ├── anomaly.py              # Anomaly scoring using sentence-transformers/all-MiniLM-L6-v2
│   ├── explainer.py            # Rule-based explanation and category generation
│   ├── requirements.txt        # Python dependencies
│   └── server.log              # Backend log output (not committed)
├── data/
│   ├── training_dataset.json   # Corpus for anomaly detection baseline
│   └── training_dataset.csv    # CSV version of the same dataset
├── src/                        # React frontend source
│   ├── App.tsx                 # Main UI — input form, clause cards, risk filters
│   ├── apiClient.ts            # API client — POST /api/analyze, poll status, fetch clauses
│   ├── main.tsx                # React entry point
│   └── index.css               # Global styles
├── server.ts                   # UNUSED — alternative Express/Gemini backend (not active)
├── vite.config.ts              # Vite config — React plugin, Tailwind, /api proxy to :8000
├── package.json                # Node dependencies and npm scripts
├── .env.local                  # Environment variables (GEMINI_API_KEY — used by server.ts only)
├── tsconfig.json               # TypeScript config
├── generate_data.py            # Script to regenerate training dataset
└── INSTRUCTIONS.md             # This file
```

### Important notes
- `server.ts` in the project root is an **unused alternative backend** (Express + Gemini API). The **active backend** is `backend/main.py` (Python + FastAPI + Hugging Face).
- `.env.local` contains a `GEMINI_API_KEY` that is only used by `server.ts`. The active backend does **not** need this key.

---

## 4. Prerequisites

| Tool      | Version  | Purpose                          |
|-----------|----------|----------------------------------|
| Node.js   | 18+      | Frontend dev server and build    |
| npm       | 9+       | Node package manager             |
| Python    | 3.9+     | Backend server and ML pipelines  |
| pip       | latest   | Python package manager           |

---

## 5. Setup (First Time)

### Install frontend dependencies
```bash
npm install
```

### Install backend dependencies
```bash
pip install -r backend/requirements.txt
```

> **Note:** The first analysis request will download Hugging Face models (~1.6 GB) which can take several minutes. Subsequent runs use a cached version.

---

## 6. Running the App

### Option A: Single command (recommended)
```bash
npm run dev:all
```
This starts both the Vite frontend and the Python backend concurrently.

### Option B: Separate terminals
```bash
# Terminal 1 — Frontend (http://localhost:5173)
npm run dev

# Terminal 2 — Backend (http://127.0.0.1:8000)
npm run dev:backend
# or equivalently:
cd backend && python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### Available npm scripts
| Script            | Command                                  | Description                              |
|-------------------|------------------------------------------|------------------------------------------|
| `dev`             | `vite`                                   | Start Vite frontend only                 |
| `dev:backend`     | `cd backend && python3 -m uvicorn ...`   | Start Python backend only                |
| `dev:all`         | `concurrently` (both above)              | Start frontend + backend together        |
| `build`           | `vite build`                             | Production build of the frontend         |
| `preview`         | `vite preview`                           | Preview the production build             |
| `lint`            | `eslint src ...`                         | Lint TypeScript/React source             |
| `test`            | `vitest`                                 | Run frontend tests                       |

---

## 7. API Endpoints

All API routes are served by the Python backend on port 8000 and proxied through Vite at `/api/*`.

### `POST /api/analyze`
Start a new analysis job.

**Request body:**
```json
{ "text": "<full legal text to analyze>", "url": "<optional source URL>" }
```

**Response:**
```json
{ "id": "<analysis UUID>", "status": "processing" }
```

The analysis runs as a **background task** — the response returns immediately with status `"processing"`.

### `GET /api/analyses/{id}`
Poll analysis status.

**Response:**
```json
{
  "id": "<UUID>",
  "status": "processing" | "complete" | "failed",
  "clause_count": 42,
  "risk_summary": { "safe": 20, "watch": 15, "danger": 7 }
}
```

### `GET /api/analyses/{id}/clauses`
Fetch analyzed clauses (only returns data when status is `"complete"`).

**Response:**
```json
{
  "clauses": [
    {
      "id": "<UUID>",
      "text": "We may share your data...",
      "risk": "watch",
      "confidence": 0.76,
      "anomaly_score": 0.17,
      "category": "Data Sharing",
      "explanation": "Indicates information may be shared with external companies."
    }
  ]
}
```

---

## 8. Frontend–Backend Data Flow

1. User pastes text and clicks **"Analyze clauses"**.
2. `src/apiClient.ts` → `POST /api/analyze` with the raw text.
3. Backend creates a DB record with `status = "processing"` and kicks off a background job.
4. Frontend polls `GET /api/analyses/{id}` every 1 second (up to 10 minutes).
5. Background job in `backend/main.py`:
   - Splits text into sentences.
   - Runs **zero-shot classification** (`classifier.py`) on each sentence → `risk` + `confidence`.
   - Computes **anomaly score** (`anomaly.py`) by comparing sentence embeddings against the training corpus.
   - Generates **explanation and category** (`explainer.py`) using keyword rules.
   - Saves clauses to SQLite and updates analysis status to `"complete"`.
6. Frontend detects `status = "complete"` → fetches `GET /api/analyses/{id}/clauses`.
7. Clause cards render with risk badges, confidence %, anomaly %, category tags, and explanations.

---

## 9. ML Pipeline Details

### Classifier (`backend/classifier.py`)
- Model: `facebook/bart-large-mnli` via Hugging Face `transformers.pipeline("zero-shot-classification")`
- Labels: `["safe", "watch", "danger"]`
- Hypothesis template: `"This terms of service clause is {}."`
- Singleton pattern — model loaded once and reused.

### Anomaly Detector (`backend/anomaly.py`)
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Baseline corpus: `data/training_dataset.json`
- Method: encode input sentence → compute cosine similarity against all corpus embeddings → anomaly score = `1 - max_similarity`
- Score range: 0.0 (identical to corpus) to 1.0 (completely novel).

### Explainer (`backend/explainer.py`)
- Pure rule-based — no ML model.
- Keyword matching (e.g., "arbitration" → Dispute Resolution, "cookies" → Tracking).
- Falls back to generic explanations based on the risk level.

---

## 10. Database Schema

SQLite database auto-created at `clauseflag.db` in the project root.

### `analyses` table
| Column        | Type     | Description                              |
|---------------|----------|------------------------------------------|
| id            | TEXT PK  | UUID                                     |
| url           | TEXT     | Optional source URL                      |
| raw_text      | TEXT     | Full input text                          |
| status        | TEXT     | `processing`, `complete`, or `failed`    |
| clause_count  | INTEGER  | Number of extracted clauses              |
| risk_summary  | TEXT     | JSON string `{"safe":N,"watch":N,"danger":N}` |
| created_at    | DATETIME | Auto-set on insert                       |
| completed_at  | DATETIME | Set when analysis completes              |

### `clauses` table
| Column        | Type     | Description                              |
|---------------|----------|------------------------------------------|
| id            | TEXT PK  | UUID                                     |
| analysis_id   | TEXT FK  | References `analyses.id`                 |
| position      | INTEGER  | Clause index in the original text        |
| text          | TEXT     | The sentence text                        |
| risk          | TEXT     | `safe`, `watch`, or `danger`             |
| confidence    | REAL     | Model confidence (0.0–1.0)               |
| anomaly_score | REAL     | Anomaly score (0.0–1.0)                  |
| category      | TEXT     | e.g., "Data Sharing", "Tracking"         |
| explanation   | TEXT     | Plain-language explanation               |

---

## 11. Testing

### Frontend tests
```bash
npm test
```
Uses Vitest as the test runner.

### Manual testing
1. Start the app with `npm run dev:all`.
2. Open `http://localhost:5173`.
3. Paste any Terms of Service or Privacy Policy text.
4. Click **"Analyze clauses"** and wait for results (~30s–2min on first run).
5. Use the All / Safe / Watch / Danger filter buttons to filter results.

### Backend-only testing
```bash
# Test the backend API directly:
curl -X POST http://127.0.0.1:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "We may sell your personal data to third parties."}'

# Then poll with the returned ID:
curl http://127.0.0.1:8000/api/analyses/<id>
curl http://127.0.0.1:8000/api/analyses/<id>/clauses
```

---

## 12. Common Development Tasks

### Adding a new risk keyword/rule
Edit `backend/explainer.py` → add an entry to the `self.rules` dictionary in the `Explainer.__init__` method.

### Changing the classification model
Edit `backend/classifier.py` → change the `model` argument in `pipeline("zero-shot-classification", model="...")`.

### Resetting the database
Delete `clauseflag.db` from the project root. It will be auto-recreated on the next backend startup.

### Regenerating training data
```bash
python generate_data.py
```
This regenerates `data/training_dataset.json` and `data/training_dataset.csv`.

### Adding new frontend components
All React components are in `src/App.tsx`. The app uses Tailwind CSS 4 utility classes. Key types are defined in `src/apiClient.ts` (`Clause`, `AnalysisResponse`).

---

## 13. Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| "Failed to start analysis: Internal Server Error" | Python backend not running | Start it with `npm run dev:backend` or `npm run dev:all` |
| Models downloading on every run | Hugging Face cache missing | Ensure `~/.cache/huggingface/` is persistent |
| Port 8000 already in use | Another process on the port | `lsof -i :8000` then `kill <PID>` |
| Port 5173 already in use | Another Vite instance running | `lsof -i :5173` then `kill <PID>` |
| `ModuleNotFoundError: No module named 'fastapi'` | Python deps not installed | `pip install -r backend/requirements.txt` |
| Very slow first analysis (~2+ min) | ML models loading into memory | Normal on first run; subsequent analyses are faster |
