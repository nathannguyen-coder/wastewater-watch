# Wastewater Watch

Wastewater Watch is a defensive wastewater-surveillance portfolio project. It
turns longitudinal microbial community profiles into site-aware anomaly signals,
quality-control evidence, and an analyst-facing review experience.

The dashboard uses read-derived taxonomy profiles from 31 public NCBI Sequence
Read Archive runs in [BioProject PRJNA729801](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA729801).
These unenriched wastewater metatranscriptomes were collected at three Southern
California treatment plants. They are historical research data, not current
surveillance or evidence of an outbreak.

## What this demonstrates

- Reproducible metagenomics workflow design with Nextflow and containers
- Compositional-data analysis using centered log-ratio transforms
- Site-aware robust anomaly detection and feature-level explanations
- Typed FastAPI endpoints with explicit scientific caveats
- A responsive React/TypeScript analyst dashboard
- Unit, API integration, production-build, and browser-level end-to-end tests

## Architecture

```text
NCBI SRA RunInfo + STAT taxonomy
          │
          ▼
QC → host filtering → taxonomic profiling
          │
          ▼
Validated abundance profiles
          │
          ▼
Robust CLR anomaly engine → FastAPI → analyst dashboard
```

## Run locally

Requirements: Python 3.9+, Node.js 20+.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -e '.[dev]'

cd apps/web
npm install
cd ../..
```

Start the API:

```bash
.venv/bin/uvicorn apps.api.main:app --reload
```

In another terminal, start the web application:

```bash
cd apps/web
npm run dev
```

Open `http://127.0.0.1:5173`. The dashboard opens on Point Loma WTP. Every sample
links back to its NCBI SRA run and includes its BioSample and profiler version.

## Rebuild the NCBI dataset

The committed profile table can be regenerated from NCBI's public RunInfo and
STAT endpoints:

```bash
.venv/bin/python scripts/fetch_ncbi_stat.py
```

The script selects unenriched RNA-seq runs, keeps one run per site and collection
date, aggregates genus-level read assignments, and records the exact accessions.
It downloads metadata and taxonomy summaries, not raw FASTQ files.

## Verify

```bash
.venv/bin/ruff check .
.venv/bin/pytest
cd apps/web && npm run lint && npm run build
```

The browser test starts the API and web development server automatically:

```bash
cd apps/web
npx playwright install chromium
npm run test:e2e
```

## Run with Docker

```bash
docker compose up --build
```

The application is then available at `http://127.0.0.1:8080`.

## Raw-read extension

The optional workflow in [`workflows/nextflow`](workflows/nextflow) accepts
paired-end shotgun metagenomic FASTQ files. It performs read QC, mandatory
human-read filtering, and MetaPhlAn profiling. This is a separate path from the
dashboard's lightweight NCBI STAT import and intentionally stops short of genome
assembly and binning.

Before running it, review the sample metadata and ensure that:

1. The data are authorized for local processing.
2. The supplied Bowtie2 index is an appropriate human reference.
3. Reference database versions are pinned and recorded.
4. Compute and storage are sufficient for the selected public samples.

See [Data sheet](docs/data-sheet.md), [Model card](docs/model-card.md), and
[Safety and interpretation](docs/safety.md).

## Safety boundary

This project supports defensive detection, data quality review, and public-health
decision support. It does not optimize biological properties, provide pathogen
engineering guidance, diagnose disease, or establish that an outbreak exists.
