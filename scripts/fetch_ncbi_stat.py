#!/usr/bin/env python3
"""Build longitudinal abundance profiles from public NCBI SRA STAT results."""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import time
import urllib.request
from collections import defaultdict
from collections.abc import Iterable
from datetime import date
from pathlib import Path

RUNINFO_URL = "https://trace.ncbi.nlm.nih.gov/Traces/sra-db-be/runinfo?acc={project}"
TAXONOMY_URL = (
    "https://www.ncbi.nlm.nih.gov/Traces/sra-db-be/"
    "run_taxonomy?acc={run}&cluster_name=public"
)
USER_AGENT = "Wastewater-Watch/0.1 (public research data integration)"
SITE_NAMES = {
    "PL": "Point Loma WTP",
    "SB": "South Bay WRP",
    "SJ": "San Jose Creek WRP",
}
RESERVED_COLUMNS = [
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
]


def fetch_text(url: str, attempts: int = 3) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read().decode("utf-8")
        except Exception as error:  # pragma: no cover - exercised only on network failure
            last_error = error
            if attempt + 1 < attempts:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}") from last_error


def parse_sample_name(sample_name: str) -> tuple[str, date] | None:
    match = re.match(
        r"^(?P<site>[A-Z]+)_(?P<month>\d{1,2})_(?P<day>\d{1,2})_(?P<year>\d{2,4})",
        sample_name,
    )
    if not match:
        return None
    year = int(match.group("year"))
    if year < 100:
        year += 2000
    return (
        match.group("site"),
        date(year, int(match.group("month")), int(match.group("day"))),
    )


def select_runs(
    rows: Iterable[dict[str, str]], site_codes: set[str], per_site: int
) -> list[dict[str, str]]:
    by_site_date: dict[tuple[str, date], dict[str, str]] = {}
    for row in rows:
        if row["LibraryStrategy"] != "RNA-Seq":
            continue
        if not row["SampleName"].endswith("_INF_unenriched"):
            continue
        parsed = parse_sample_name(row["SampleName"])
        if parsed is None:
            continue
        site_code, collected_at = parsed
        if site_code not in site_codes:
            continue
        row["_site_code"] = site_code
        row["_collected_at"] = collected_at.isoformat()
        key = (site_code, collected_at)
        existing = by_site_date.get(key)
        if existing is None or int(row["spots"]) > int(existing["spots"]):
            by_site_date[key] = row

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in by_site_date.values():
        grouped[row["_site_code"]].append(row)

    selected: list[dict[str, str]] = []
    for site_code in sorted(site_codes):
        site_rows = sorted(grouped[site_code], key=lambda row: row["_collected_at"])
        if len(site_rows) < 6:
            raise ValueError(f"{site_code} has only {len(site_rows)} usable longitudinal runs")
        selected.extend(site_rows[-per_site:])
    return sorted(selected, key=lambda row: (row["_site_code"], row["_collected_at"]))


def taxonomy_profile(run: str) -> dict:
    payload = json.loads(fetch_text(TAXONOMY_URL.format(run=run)))
    if not payload or not payload[0].get("tax_totals"):
        raise ValueError(f"NCBI STAT returned no taxonomy data for {run}")
    return payload[0]


def build_profiles(
    selected_runs: list[dict[str, str]], top_n: int
) -> tuple[list[dict], list[str]]:
    raw_profiles: list[tuple[dict[str, str], dict]] = []
    global_counts: dict[str, int] = defaultdict(int)
    for index, run in enumerate(selected_runs, start=1):
        accession = run["Run"]
        print(f"[{index}/{len(selected_runs)}] Fetching NCBI STAT taxonomy for {accession}")
        profile = taxonomy_profile(accession)
        raw_profiles.append((run, profile))
        for taxon in profile["tax_table"]:
            if taxon.get("rank") != "genus":
                continue
            name = taxon["org"]
            if name.startswith("unclassified") or name == "Homo":
                continue
            global_counts[name] += int(taxon.get("total_count", 0))

    selected_taxa = [
        name
        for name, _ in sorted(
            global_counts.items(), key=lambda item: (-item[1], item[0])
        )[:top_n]
    ]
    feature_columns = [*selected_taxa, "Other identified genera"]

    rows: list[dict] = []
    for run, profile in raw_profiles:
        totals = profile["tax_totals"]
        genus_counts = {
            taxon["org"]: int(taxon.get("total_count", 0))
            for taxon in profile["tax_table"]
            if taxon.get("rank") == "genus"
            and not taxon["org"].startswith("unclassified")
            and taxon["org"] != "Homo"
        }
        genus_total = sum(genus_counts.values())
        if genus_total == 0:
            raise ValueError(f"{run['Run']} has no genus-level NCBI STAT assignments")
        selected_total = sum(genus_counts.get(taxon, 0) for taxon in selected_taxa)
        analyzed = int(totals["analysed"])
        identified = int(totals["identified"])
        human = next(
            (
                int(taxon.get("total_count", 0))
                for taxon in profile["tax_table"]
                if int(taxon["tax_id"]) == 9606
            ),
            0,
        )
        identified_fraction = identified / analyzed if analyzed else 0
        row = {
            "sample_id": run["Run"],
            "site_id": run["_site_code"].lower(),
            "site_name": SITE_NAMES[run["_site_code"]],
            "region": "Southern California",
            "collected_at": run["_collected_at"],
            "reads_millions": round(analyzed / 1_000_000, 3),
            "host_read_fraction": round(human / analyzed, 6) if analyzed else 0,
            "identified_fraction": round(identified_fraction, 6),
            "qc_status": (
                "review" if analyzed < 1_000_000 or identified_fraction < 0.01 else "pass"
            ),
            "bioproject": run["BioProject"],
            "biosample": run["BioSample"],
            "sra_run": run["Run"],
            "profile_method": f"NCBI STAT {totals.get('version', 'unknown')}",
            "source_url": f"https://www.ncbi.nlm.nih.gov/sra/{run['Run']}",
        }
        for taxon in selected_taxa:
            row[taxon] = round(genus_counts.get(taxon, 0) / genus_total * 100, 6)
        row["Other identified genera"] = round(
            (genus_total - selected_total) / genus_total * 100, 6
        )
        rows.append(row)
    return rows, feature_columns


def write_profiles(output: Path, rows: list[dict], feature_columns: list[str]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [*RESERVED_COLUMNS, *feature_columns]
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default="PRJNA729801")
    parser.add_argument("--sites", default="SJ,SB,PL")
    parser.add_argument("--per-site", type=int, default=12)
    parser.add_argument("--top-genera", type=int, default=7)
    parser.add_argument(
        "--output", type=Path, default=Path("data/ncbi/profiles.csv")
    )
    args = parser.parse_args()

    manifest_text = fetch_text(RUNINFO_URL.format(project=args.project))
    manifest_rows = list(csv.DictReader(io.StringIO(manifest_text)))
    selected = select_runs(
        manifest_rows,
        {site.strip().upper() for site in args.sites.split(",") if site.strip()},
        args.per_site,
    )
    profiles, feature_columns = build_profiles(selected, args.top_genera)
    write_profiles(args.output, profiles, feature_columns)
    print(
        f"Wrote {len(profiles)} real SRA-derived profiles with "
        f"{len(feature_columns)} features to {args.output}"
    )


if __name__ == "__main__":
    main()
