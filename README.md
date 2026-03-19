# ClauseFlag

ClauseFlag is a software solution that allows users to paste Terms of Service and Privacy Policy text, and automatically extracts and classifies clauses by risk level (*safe / watch / danger*). It highlights anomalous clauses compared to a corpus baseline and provides plain-language explanations for why each clause is concerning.

## Tech Stack
* **Frontend:** React, TypeScript, Tailwind CSS, Vite
* **Backend:** Python, FastAPI, SQLite
* **Machine Learning Pipelines:** Hugging Face Transformers (`facebook/bart-large-mnli` for zero-shot classification, `sentence-transformers/all-MiniLM-L6-v2` for anomaly scoring)

---

## Running Locally

Our application is split into a **Python Backend** and a **React Frontend**. You need to run both concurrently.

**Prerequisites:** Python 3.9+, Node.js

### Quick Start
```bash
npm run setup      # installs all dependencies (npm, pip, Playwright browser)
npm run dev:all    # starts both frontend and backend concurrently
```
The first analysis will download Hugging Face models (~1.6GB) into memory.

---

### Manual Setup (if you prefer step-by-step)

#### 1. Python Backend

1. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   python -m playwright install chromium
   ```
2. Start the FastAPI server (runs on `http://127.0.0.1:8000`):
   ```bash
   uvicorn main:app --port 8000 --reload
   ```

#### 2. React Frontend

1. From the project root, install and start:
   ```bash
   npm install
   npm run dev
   ```
2. Open `http://localhost:5173` in your browser.

### 3. Generate Training Dataset (Optional)
If you need to regenerate the SQLite database seed data or extend the local training CSV/JSON files:
```bash
python generate_data.py
```
