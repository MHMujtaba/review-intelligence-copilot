# Review-Centric RAG Intelligence System

Lightweight local review intelligence system that loads review data directly from CSV, builds FAISS embeddings for each `reviewText`, and serves grounded multi-stage RAG answers through FastAPI and React.

## Constraints

- No Docker
- No containers
- No Kubernetes
- No SQL or external database
- CSV is the only data source
- Local file system cache plus FAISS only

## Stack

- Backend: FastAPI
- Frontend: React + Vite
- Retrieval: FAISS semantic search over `reviewText`
- Storage: local JSON cache and FAISS index files under `backend/data`

## Dataset schema

The CSV must contain:

- `asin`
- `helpful`
- `overall`
- `reviewText`
- `reviewTime`
- `unixReviewTime`
- `reviewerID`
- `reviewerName`
- `summary`

## Backend architecture

```text
backend/app/
  csv_loader/      pandas CSV loading
  preprocessing/   helpful parsing + derived features
  embeddings/      embedding providers and batching
  retrieval/       FAISS retrieval + query classification
  reranking/       semantic/helpfulness/rating scoring
  filtering/       short-review and duplicate cleanup
  generation/      structured context + grounded answers
  ml/              lightweight review quality classifier
  storage/         FAISS persistence
```

## Run locally

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API endpoints

- `POST /load_csv`
- `POST /embed`
- `POST /ask`
- `GET /summary/{asin}`
- `GET /insights/{asin}`
- `POST /search`

## Example flow

### 1. Load a local CSV

```json
POST /load_csv
{
  "file_path": "C:/data/reviews.csv",
  "chunksize": 5000
}
```

### 2. Build review embeddings

```json
POST /embed
{
  "asin": "B000123456",
  "batch_size": 64,
  "rebuild_index": true
}
```

### 3. Ask a grounded question

```json
POST /ask
{
  "asin": "B000123456",
  "query": "What do customers complain about most?",
  "max_results": 8
}
```
