from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from .dashboard import get_dashboard_html
from .clustering import run_louvain
from .db import fetch_reports


app = FastAPI(title="Demo Louvain API", version="1.0.0")


@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page():
    return HTMLResponse(get_dashboard_html())


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/reports")
def list_reports():
    reports = fetch_reports()
    return {"count": len(reports), "items": reports}


@app.get("/louvain/summary")
def louvain_summary():
    reports = fetch_reports()
    result = run_louvain(reports)
    return {
        "nodes": result["nodes"],
        "edges": result["edges"],
        "community_count": len(result["communities"]),
        "modularity": result["modularity"],
    }


@app.get("/louvain/communities")
def louvain_communities():
    reports = fetch_reports()
    result = run_louvain(reports)
    return {
        "community_count": len(result["communities"]),
        "modularity": result["modularity"],
        "communities": result["communities"],
    }


@app.get("/louvain/communities/{community_id}")
def louvain_community_detail(community_id: int):
    reports = fetch_reports()
    result = run_louvain(reports)
    for community in result["communities"]:
        if community["community_id"] == community_id:
            return community
    raise HTTPException(status_code=404, detail="Community not found")


@app.get("/louvain/graph")
def louvain_graph():
    reports = fetch_reports()
    result = run_louvain(reports)
    return {
        "nodes": result["nodes"],
        "edges": result["edges"],
        "graph": result["graph"],
    }
