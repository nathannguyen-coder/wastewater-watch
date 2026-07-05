from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def test_health_and_summary_endpoints() -> None:
    assert client.get("/api/health").json() == {
        "status": "ok",
        "data_mode": "ncbi_sra",
    }
    response = client.get("/api/summary")
    assert response.status_code == 200
    assert response.json()["sites_monitored"] == 3
    assert response.json()["source_project"] == "PRJNA729801"


def test_timeline_endpoint_returns_complete_samples() -> None:
    response = client.get("/api/sites/pl/timeline")
    assert response.status_code == 200
    payload = response.json()
    assert payload["site"]["name"] == "Point Loma WTP"
    assert len(payload["samples"]) == 12
    assert any(sample["status"] == "alert" for sample in payload["samples"])
    assert all(sample["bioproject"] == "PRJNA729801" for sample in payload["samples"])


def test_unknown_resources_return_404() -> None:
    assert client.get("/api/sites/unknown/timeline").status_code == 404
    assert client.get("/api/alerts/unknown").status_code == 404
