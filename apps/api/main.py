import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from sentinel import SentinelRepository
from sentinel.models import Alert, Site, Summary, Timeline

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = Path(
    os.environ.get("SENTINEL_DATA_PATH", ROOT / "data" / "ncbi" / "profiles.csv")
)
repository = SentinelRepository(DATA_PATH)

app = FastAPI(
    title="Wastewater Watch API",
    version="0.1.0",
    description="Defensive demonstration API for wastewater community anomaly review.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "data_mode": repository.summary().data_mode}


@app.get("/api/summary", response_model=Summary)
def summary() -> Summary:
    return repository.summary()


@app.get("/api/sites", response_model=list[Site])
def sites() -> list[Site]:
    return repository.sites()


@app.get("/api/sites/{site_id}/timeline", response_model=Timeline)
def timeline(site_id: str) -> Timeline:
    result = repository.timeline(site_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Unknown site: {site_id}")
    return result


@app.get("/api/alerts", response_model=list[Alert])
def alerts(site_id: Optional[str] = Query(default=None)) -> list[Alert]:
    return repository.alerts(site_id)


@app.get("/api/alerts/{alert_id}", response_model=Alert)
def alert(alert_id: str) -> Alert:
    result = repository.alert(alert_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Unknown alert: {alert_id}")
    return result
