#!/usr/bin/env python3
"""Export the API responses used by the dashboard as one static JSON snapshot."""

import argparse
import json
from pathlib import Path

from sentinel import SentinelRepository


def export_snapshot(data_path: Path, output_path: Path) -> None:
    repository = SentinelRepository(data_path)
    sites = repository.sites()
    snapshot = {
        "summary": repository.summary().model_dump(),
        "sites": [site.model_dump() for site in sites],
        "timelines": {
            site.id: repository.timeline(site.id).model_dump() for site in sites
        },
        "alerts": {
            site.id: [alert.model_dump() for alert in repository.alerts(site.id)]
            for site in sites
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(snapshot, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/ncbi/profiles.csv"),
        help="Profile CSV consumed by the anomaly repository",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("apps/web/public/data/dashboard.json"),
        help="Static JSON snapshot written for the frontend build",
    )
    args = parser.parse_args()
    export_snapshot(args.input, args.output)


if __name__ == "__main__":
    main()
