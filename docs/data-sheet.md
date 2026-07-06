# Data sheet: NCBI SRA wastewater profiles

## Dataset

`data/ncbi/profiles.csv` contains 31 historical wastewater profiles from
[NCBI BioProject PRJNA729801](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA729801):
12 Point Loma WTP runs, 12 San Jose Creek WRP runs, and 7 South Bay WRP runs.
Collection dates span August 2020 through January 2021.

## Selection and processing

`scripts/fetch_ncbi_stat.py` downloads NCBI RunInfo, retains records whose
library strategy is `RNA-Seq` and sample name ends in `_INF_unenriched`, and
deduplicates site/date pairs by retaining the run with the most spots. It then
downloads [NCBI STAT](https://www.ncbi.nlm.nih.gov/sra/docs/sra-taxonomy-analysis-tool/)
read-derived taxonomy results.

The table contains the seven most abundant genera across the selected runs plus
`Other identified genera`, normalized to 100%. `reads_millions` is STAT's
analyzed-read count. The human-read and identified fractions are retained as QC
signals.

## Provenance

Every row records its BioProject, BioSample, SRA run, NCBI URL, and STAT version.
The source study is described in
[Rothman et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC8579973/).
No raw reads or individual-level records are committed to this repository.

## Known limitations

- The 31-run subset is small and uneven across sites.
- NCBI STAT assignments are reference- and algorithm-dependent.
- Genus aggregation discards strain/species detail and unidentified reads.
- Flow, precipitation, extraction batch, and other covariates are not modeled.
- Static anomaly thresholds have not been calibrated to epidemiological events.
- Human-read fraction is a taxonomy signal, not a validated privacy screen.
- This dataset cannot estimate sensitivity, specificity, or public-health utility.
