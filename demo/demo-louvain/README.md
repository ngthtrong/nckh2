# demo-louvain

FastAPI service for reading rescue report data and returning Louvain communities.

It also includes an interactive dashboard at `/` and `/dashboard` that calls the API endpoints directly.

## Run locally

```bash
cd demo/demo-louvain
uvicorn app.main:app --reload
```

## Environment

- `DATABASE_URL` optional.
- Default: SQLite dataset created by `review3/scripts/*` at `review3/data/review3.sqlite`.

## Endpoints

- `GET /` or `GET /dashboard`
- `GET /health`
- `GET /reports`
- `GET /louvain/summary`
- `GET /louvain/communities`
- `GET /louvain/communities/{community_id}`
- `GET /louvain/graph`
