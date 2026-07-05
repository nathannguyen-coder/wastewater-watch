# Model card: robust CLR community anomaly detector

## Intended use

The model ranks wastewater community profiles for analyst review.
It is a screening tool for detecting departures from a site's own recent
baseline. It is not a diagnostic model and does not infer the cause of a shift.

## Inputs

- Relative abundance estimates for a consistent set of taxonomic features
- Monitoring-site identifier
- Collection date
- Read-depth and host-read-fraction quality indicators

The bundled real-data view uses genus-level NCBI STAT assignments from
PRJNA729801. Inputs from different wet-lab protocols, feature sets, or profiler
versions should not be mixed without validation.

## Method

1. Add a small pseudocount to accommodate zero values.
2. Apply a centered log-ratio transform.
3. Estimate a per-site, per-feature median and median absolute deviation using
   prior QC-passing samples.
4. Calculate robust standardized deviations.
5. Aggregate deviations with a root-mean-square score.
6. Report the largest feature contributions rather than a causal explanation.

The first five QC-passing samples establish the baseline and are not scored.
Samples failing QC are held for review and are not promoted to alerts or added
to the baseline. Samples at or above the watch threshold are also withheld from
the baseline until an operational review policy resolves them.

## Evaluation

The included deterministic fixture tests verify that:

- Stable site profiles remain below alert thresholds.
- A designed community shift is detected.
- Its largest taxonomic contributors are exposed.
- A low-depth, high-host-fraction sample is held by the quality gate.
- Unknown resources fail explicitly at the API boundary.

Browser tests separately verify the complete NCBI-backed analyst flow and SRA
provenance links. Neither test suite establishes external epidemiological
validity; representative controls and prospective validation are required.

## Limitations

- The bundled NCBI subset is historical, small, and uneven across sites.
- Taxonomic abundance estimates are reference- and profiler-dependent.
- Site, season, flow, extraction method, and sequencing batch can drive shifts.
- CLR results depend on the observed feature set and pseudocount.
- Static thresholds are illustrative and are not calibrated to outbreak risk.
- “Contribution” means contribution to statistical distance, not biological
  cause or public-health importance.

## Human oversight

Every alert includes a non-diagnostic caveat. Analysts should review sampling,
laboratory, environmental, and epidemiological context before escalation.
