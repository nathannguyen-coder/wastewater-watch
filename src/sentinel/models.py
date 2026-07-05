from typing import Literal, Optional

from pydantic import BaseModel


class Site(BaseModel):
    id: str
    name: str
    region: str
    sample_count: int
    latest_sample: str
    latest_status: Literal["normal", "watch", "alert"]


class Contributor(BaseModel):
    taxon: str
    direction: Literal["higher", "lower"]
    contribution: float
    current_abundance: float
    baseline_abundance: float


class Sample(BaseModel):
    id: str
    site_id: str
    collected_at: str
    reads_millions: float
    host_read_fraction: float
    qc_status: Literal["pass", "review"]
    anomaly_score: Optional[float]
    status: Literal["baseline", "normal", "watch", "alert", "quality_review"]
    abundances: dict[str, float]
    top_contributors: list[Contributor]
    bioproject: Optional[str] = None
    biosample: Optional[str] = None
    sra_run: Optional[str] = None
    profile_method: Optional[str] = None
    source_url: Optional[str] = None
    identified_fraction: Optional[float] = None


class Timeline(BaseModel):
    site: Site
    samples: list[Sample]
    score_thresholds: dict[str, float]


class Alert(BaseModel):
    id: str
    site_id: str
    site_name: str
    sample_id: str
    collected_at: str
    severity: Literal["watch", "alert"]
    score: float
    title: str
    summary: str
    caveat: str
    contributors: list[Contributor]


class Summary(BaseModel):
    sites_monitored: int
    samples_processed: int
    active_alerts: int
    review_required: int
    latest_collection: str
    data_mode: Literal["demonstration", "ncbi_sra"]
    model_version: str
    source_project: Optional[str] = None
