import csv
import math
import statistics
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Optional

from .models import Alert, Contributor, Sample, Site, Summary, Timeline

METADATA_COLUMNS = {
    "sample_id",
    "site_id",
    "site_name",
    "region",
    "collected_at",
    "reads_millions",
    "host_read_fraction",
    "identified_fraction",
    "qc_status",
    "bioproject",
    "biosample",
    "sra_run",
    "profile_method",
    "source_url",
}

WATCH_THRESHOLD = 2.6
ALERT_THRESHOLD = 4.2
MIN_BASELINE_SAMPLES = 5
PSEUDOCOUNT = 1e-4
MODEL_VERSION = "robust-clr-1.0"


def _clr(values: Iterable[float]) -> list[float]:
    logged = [math.log(max(value, 0.0) + PSEUDOCOUNT) for value in values]
    center = statistics.fmean(logged)
    return [value - center for value in logged]


def _median(values: list[float]) -> float:
    return statistics.median(values)


def _robust_scale(values: list[float]) -> float:
    center = _median(values)
    mad = _median([abs(value - center) for value in values])
    return max(mad * 1.4826, 0.12)


def _status(score: Optional[float], qc_status: str) -> str:
    if qc_status == "review":
        return "quality_review"
    if score is None:
        return "baseline"
    if score >= ALERT_THRESHOLD:
        return "alert"
    if score >= WATCH_THRESHOLD:
        return "watch"
    return "normal"


class SentinelRepository:
    def __init__(self, data_path: Path):
        self.data_path = data_path
        self._rows = self._load_rows()
        self._samples = self._analyze()
        self._sites = self._build_sites()
        self._alerts = self._build_alerts()

    def _load_rows(self) -> list[dict]:
        with self.data_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise ValueError("Profile dataset has no header")
            self.taxa = tuple(
                column for column in reader.fieldnames if column not in METADATA_COLUMNS
            )
            rows = list(reader)
        if not rows:
            raise ValueError("Demo profile dataset is empty")
        required = {
            "sample_id",
            "site_id",
            "site_name",
            "region",
            "collected_at",
            "reads_millions",
            "host_read_fraction",
            "qc_status",
            *self.taxa,
        }
        missing = required - set(rows[0])
        if missing:
            raise ValueError(f"Demo profile dataset is missing columns: {sorted(missing)}")
        for row in rows:
            total = sum(float(row[taxon]) for taxon in self.taxa)
            if not math.isclose(total, 100.0, abs_tol=0.05):
                message = (
                    f"{row['sample_id']} abundance values sum to {total}, expected 100"
                )
                raise ValueError(message)
        return sorted(rows, key=lambda row: (row["site_id"], row["collected_at"]))

    def _analyze(self) -> list[Sample]:
        by_site: dict[str, list[dict]] = defaultdict(list)
        for row in self._rows:
            by_site[row["site_id"]].append(row)

        samples: list[Sample] = []
        for site_rows in by_site.values():
            history: list[list[float]] = []
            abundance_history: list[list[float]] = []
            for row in site_rows:
                abundances = [float(row[taxon]) / 100 for taxon in self.taxa]
                transformed = _clr(abundances)
                score: Optional[float] = None
                contributors: list[Contributor] = []
                if len(history) >= MIN_BASELINE_SAMPLES:
                    columns = [list(column) for column in zip(*history)]
                    centers = [_median(column) for column in columns]
                    scales = [_robust_scale(column) for column in columns]
                    z_scores = [
                        (value - center) / scale
                        for value, center, scale in zip(transformed, centers, scales)
                    ]
                    score = round(math.sqrt(statistics.fmean(value**2 for value in z_scores)), 2)
                    baseline_abundances = [
                        _median(list(column)) for column in zip(*abundance_history)
                    ]
                    total_effect = sum(abs(value) for value in z_scores) or 1.0
                    ranked = sorted(
                        zip(self.taxa, z_scores, abundances, baseline_abundances),
                        key=lambda item: abs(item[1]),
                        reverse=True,
                    )[:4]
                    contributors = [
                        Contributor(
                            taxon=taxon,
                            direction="higher" if z_score > 0 else "lower",
                            contribution=round(abs(z_score) / total_effect, 3),
                            current_abundance=round(current, 4),
                            baseline_abundance=round(baseline, 4),
                        )
                        for taxon, z_score, current, baseline in ranked
                    ]

                qc_status = row["qc_status"]
                samples.append(
                    Sample(
                        id=row["sample_id"],
                        site_id=row["site_id"],
                        collected_at=row["collected_at"],
                        reads_millions=float(row["reads_millions"]),
                        host_read_fraction=float(row["host_read_fraction"]),
                        qc_status=qc_status,
                        anomaly_score=score,
                        status=_status(score, qc_status),
                        abundances={
                            taxon: round(abundance, 4)
                            for taxon, abundance in zip(self.taxa, abundances)
                        },
                        top_contributors=contributors,
                        bioproject=row.get("bioproject") or None,
                        biosample=row.get("biosample") or None,
                        sra_run=row.get("sra_run") or None,
                        profile_method=row.get("profile_method") or None,
                        source_url=row.get("source_url") or None,
                        identified_fraction=(
                            float(row["identified_fraction"])
                            if row.get("identified_fraction")
                            else None
                        ),
                    )
                )
                # Do not let an unresolved shift redefine its own reference window.
                if qc_status == "pass" and (score is None or score < WATCH_THRESHOLD):
                    history.append(transformed)
                    abundance_history.append(abundances)
        return samples

    def _build_sites(self) -> list[Site]:
        sites: list[Site] = []
        for site_id in sorted({row["site_id"] for row in self._rows}):
            rows = [row for row in self._rows if row["site_id"] == site_id]
            samples = [sample for sample in self._samples if sample.site_id == site_id]
            status_rank = {"alert": 3, "watch": 2, "normal": 1, "quality_review": 1, "baseline": 0}
            latest_status = max(samples, key=lambda sample: status_rank[sample.status]).status
            if latest_status not in {"alert", "watch"}:
                latest_status = "normal"
            sites.append(
                Site(
                    id=site_id,
                    name=rows[0]["site_name"],
                    region=rows[0]["region"],
                    sample_count=len(rows),
                    latest_sample=max(row["collected_at"] for row in rows),
                    latest_status=latest_status,
                )
            )
        return sites

    def _build_alerts(self) -> list[Alert]:
        site_names = {site.id: site.name for site in self._sites}
        alerts: list[Alert] = []
        for sample in self._samples:
            if sample.status not in {"watch", "alert"} or sample.anomaly_score is None:
                continue
            leader = sample.top_contributors[0] if sample.top_contributors else None
            signal = (
                f"{leader.taxon} was {leader.direction} than its site-specific baseline."
                if leader
                else "Multiple community features departed from baseline."
            )
            alerts.append(
                Alert(
                    id=f"alert-{sample.id}",
                    site_id=sample.site_id,
                    site_name=site_names[sample.site_id],
                    sample_id=sample.id,
                    collected_at=sample.collected_at,
                    severity=sample.status,
                    score=sample.anomaly_score,
                    title=f"Community shift at {site_names[sample.site_id]}",
                    summary=signal,
                    caveat=(
                        "This is a screening signal, not evidence of an outbreak. Review sampling, "
                        "laboratory, environmental, and epidemiological context before escalation."
                    ),
                    contributors=sample.top_contributors,
                )
            )
        return sorted(alerts, key=lambda alert: (alert.collected_at, alert.score), reverse=True)

    def summary(self) -> Summary:
        source_project = self._rows[0].get("bioproject") or None
        return Summary(
            sites_monitored=len(self._sites),
            samples_processed=len(self._samples),
            active_alerts=sum(alert.severity == "alert" for alert in self._alerts),
            review_required=sum(sample.qc_status == "review" for sample in self._samples),
            latest_collection=max(sample.collected_at for sample in self._samples),
            data_mode="ncbi_sra" if source_project else "demonstration",
            model_version=MODEL_VERSION,
            source_project=source_project,
        )

    def sites(self) -> list[Site]:
        return self._sites

    def timeline(self, site_id: str) -> Optional[Timeline]:
        site = next((site for site in self._sites if site.id == site_id), None)
        if site is None:
            return None
        return Timeline(
            site=site,
            samples=[sample for sample in self._samples if sample.site_id == site_id],
            score_thresholds={"watch": WATCH_THRESHOLD, "alert": ALERT_THRESHOLD},
        )

    def alerts(self, site_id: Optional[str] = None) -> list[Alert]:
        if site_id is None:
            return self._alerts
        return [alert for alert in self._alerts if alert.site_id == site_id]

    def alert(self, alert_id: str) -> Optional[Alert]:
        return next((alert for alert in self._alerts if alert.id == alert_id), None)
