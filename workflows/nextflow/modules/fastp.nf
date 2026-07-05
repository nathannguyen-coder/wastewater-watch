process FASTP {
    tag "${meta.id}"
    publishDir "${params.outdir}/qc", mode: "copy", pattern: "*.{html,json}"

    input:
    tuple val(meta), path(reads)

    output:
    tuple val(meta), path("${meta.id}_clean_R{1,2}.fastq.gz"), emit: reads
    path "${meta.id}.fastp.html"
    path "${meta.id}.fastp.json"

    script:
    """
    fastp \
      --in1 ${reads[0]} \
      --in2 ${reads[1]} \
      --out1 ${meta.id}_clean_R1.fastq.gz \
      --out2 ${meta.id}_clean_R2.fastq.gz \
      --html ${meta.id}.fastp.html \
      --json ${meta.id}.fastp.json \
      --thread ${task.cpus}
    """
}
