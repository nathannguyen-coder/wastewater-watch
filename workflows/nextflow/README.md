# Real-read profiling extension

This optional workflow converts authorized paired-end shotgun metagenomic reads
into per-sample MetaPhlAn taxonomic profiles.

## Required inputs

- A CSV matching `samplesheet.example.csv`
- A Bowtie2 human-reference index prefix
- A local MetaPhlAn database directory
- Docker, Podman, or Singularity support through Nextflow

```bash
nextflow run workflows/nextflow/main.nf \
  -profile docker \
  --input workflows/nextflow/samplesheet.example.csv \
  --host_index /references/grch38/grch38 \
  --metaphlan_db /references/metaphlan \
  --outdir results
```

The example sample sheet contains placeholders and will not run until replaced
with authorized FASTQ paths.

The workflow intentionally discards host-aligned reads and retains only
unmapped paired reads. Inspect the pinned container versions and validate them
for your environment before processing operational data.
