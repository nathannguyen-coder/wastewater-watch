process METAPHLAN {
    tag "${meta.id}"
    publishDir "${params.outdir}/profiles", mode: "copy"

    input:
    tuple val(meta), path(reads)
    path metaphlan_db

    output:
    tuple val(meta), path("${meta.id}.profile.tsv"), emit: profiles
    path "${meta.id}.bowtie2.bz2"

    script:
    """
    metaphlan \
      ${reads[0]},${reads[1]} \
      --input_type fastq \
      --nproc ${task.cpus} \
      --bowtie2out ${meta.id}.bowtie2.bz2 \
      --bowtie2db ${metaphlan_db} \
      --unknown_estimation \
      --output_file ${meta.id}.profile.tsv
    """
}
