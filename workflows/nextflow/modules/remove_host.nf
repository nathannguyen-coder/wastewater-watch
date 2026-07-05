process REMOVE_HOST {
    tag "${meta.id}"
    publishDir "${params.outdir}/dehosted", mode: "copy"

    input:
    tuple val(meta), path(reads)
    path host_index_files

    output:
    tuple val(meta), path("${meta.id}_dehosted_R{1,2}.fastq.gz"), emit: reads

    script:
    def host_index_prefix = host_index_files[0].name.replaceFirst(/\.(rev\.)?[0-9]+\.bt2l?$/, "")
    """
    bowtie2 \
      --very-sensitive \
      --threads ${task.cpus} \
      -x ${host_index_prefix} \
      -1 ${reads[0]} \
      -2 ${reads[1]} \
      --un-conc-gz ${meta.id}_dehosted_R%.fastq.gz \
      -S /dev/null
    """
}
