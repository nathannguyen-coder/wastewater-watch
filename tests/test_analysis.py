from pathlib import Path

from sentinel import SentinelRepository

DATA_PATH = Path(__file__).parents[1] / "data" / "demo" / "profiles.csv"


def test_repository_builds_site_aware_summary() -> None:
    repository = SentinelRepository(DATA_PATH)
    summary = repository.summary()

    assert summary.sites_monitored == 3
    assert summary.samples_processed == 30
    assert summary.review_required == 1
    assert summary.data_mode == "demonstration"


def test_harbor_shift_is_explained() -> None:
    repository = SentinelRepository(DATA_PATH)
    alerts = repository.alerts("harbor")

    assert alerts
    strongest = max(alerts, key=lambda alert: alert.score)
    assert strongest.sample_id == "HBR-260222"
    assert strongest.severity == "alert"
    assert strongest.contributors[0].taxon in {"Acinetobacter", "Pseudomonas"}
    assert "not evidence of an outbreak" in strongest.caveat


def test_low_quality_sample_is_not_promoted_to_alert() -> None:
    repository = SentinelRepository(DATA_PATH)
    timeline = repository.timeline("northgate")

    assert timeline is not None
    low_quality = next(sample for sample in timeline.samples if sample.id == "NTH-260215")
    assert low_quality.status == "quality_review"
    assert all(alert.sample_id != low_quality.id for alert in repository.alerts())


def test_unknown_site_returns_none() -> None:
    repository = SentinelRepository(DATA_PATH)
    assert repository.timeline("missing") is None
