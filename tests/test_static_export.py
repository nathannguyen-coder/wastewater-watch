import json
from pathlib import Path

from scripts.export_static_dashboard import export_snapshot

DATA_PATH = Path(__file__).parents[1] / "data" / "ncbi" / "profiles.csv"


def test_static_export_preserves_api_shape_and_provenance(tmp_path: Path) -> None:
    output_path = tmp_path / "dashboard.json"
    export_snapshot(DATA_PATH, output_path)
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["summary"]["data_mode"] == "ncbi_sra"
    assert payload["summary"]["source_project"] == "PRJNA729801"
    assert len(payload["sites"]) == 3
    assert set(payload["timelines"]) == {"pl", "sb", "sj"}
    point_loma = payload["timelines"]["pl"]
    assert point_loma["samples"][0]["source_url"].startswith(
        "https://www.ncbi.nlm.nih.gov/sra/"
    )
