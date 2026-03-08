<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# ClauseFlag

ClauseFlag is a software solution that allows users to paste Terms of Service and Privacy Policy text, and automatically extracts and classifies clauses by risk level (*safe / watch / danger*). It highlights anomalous clauses compared to a corpus baseline and provides plain-language explanations for why each clause is concerning.

## Tech Stack
* **Frontend:** React, TypeScript, Tailwind CSS, Vite
* **Backend:** Python, FastAPI, SQLite
* **Machine Learning Pipelines:** Hugging Face Transformers (`facebook/bart-large-mnli` for zero-shot classification, `sentence-transformers/all-MiniLM-L6-v2` for anomaly scoring)

---

## Running Locally

Our application is split into a **Python Backend** and a **React Frontend**. You need to run both concurrently in separate terminal windows.

### 1. Start the Python Backend
The backend handles the ML classification. The first time you run analysis, it will download the Hugging Face models (~1.6GB) into memory.

**Prerequisites:** Python 3.9+

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the FastAPI server (runs on `http://127.0.0.1:8000`):
   ```bash
   uvicorn main:app --port 8000 --reload
   ```

### 2. Start the React Frontend

**Prerequisites:** Node.js

1. Open a **new** terminal window and keep it at the `ClauseFlag` root directory.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
4. Click the link provided in the terminal (usually `http://localhost:5173`) to open the app in your browser!

### 3. Generate Training Dataset (Optional)
If you need to regenerate the SQLite database seed data or extend the local training CSV/JSON files:
```bash
python generate_data.py
```
