# ClauseFlag
An end-to-end ML platform that unmasks predatory fine print in Terms of Service. Using a fine-tuned NLP pipeline, ClauseFlag automatically extracts, analyzes, and classifies legal jargon into clear risk levels (Safe, Watch, Danger).

## The Problem
Users rarely read Terms of Service agreements, often unknowingly consenting to invasive data practices or mandatory arbitration. ClauseFlag acts as a protective layer, automating the review process and highlighting anomalous clauses compared to industry baselines.

## Tech Stack
Frontend: React, TypeScript, Tailwind CSS

Backend: Python (FastAPI), PostgreSQL, Redis (Task Queue)

ML/NLP: Hugging Face (DistilBERT), PyTorch, Scikit-learn

DevOps: Docker Compose, GitHub Actions, Structlog

## Machine Learning Approach
ClauseFlag is built with production ML patterns, moving beyond a simple API wrapper:

Data Strategy: Trained on a hybrid corpus combining the OPP-115 privacy policy dataset and community-rated labels from ToS;DR.

Sequence Classification: Fine-tuned DistilBERT model identifies clause boundaries and predicts risk categories.

Anomaly Detection: Generates document embeddings and scores new clauses using cosine distance from the corpus centroid to flag highly unusual legal traps.

## System Architecture
Ingestion: User submits raw text or a URL via the UI.

Queueing: FastAPI pushes the job to a Redis task queue to prevent blocking.

Processing: Background workers handle text extraction (readability-lxml), sentence segmentation, and model inference.

Delivery: Results are cached in Redis, persisted to PostgreSQL, and rendered interactively on the frontend.

