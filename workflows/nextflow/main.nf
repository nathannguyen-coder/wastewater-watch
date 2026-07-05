nextflow.enable.dsl=2

include { FASTP } from "./modules/fastp"
include { REMOVE_HOST } from "./modules/remove_host"
include { METAPHLAN } from "./modules/metaphlan"

if (!params.input) {
    error "Missing --input samplesheet CSV"
}
if (!params.host_index) {
    error "Missing --host_index. Human-read removal is mandatory."
}
if (!params.metaphlan_db) {
    error "Missing --metaphlan_db"
}

Channel
    .fromPath(params.input, checkIfExists: true)
    .splitCsv(header: true)
    .map { row ->
        if (!row.sample_id || !row.read_1 || !row.read_2) {
            error "Samplesheet requires sample_id, read_1, and read_2"
        }
        tuple(
            [id: row.sample_id, site_id: row.site_id, collected_at: row.collected_at],
            [file(row.read_1, checkIfExists: true), file(row.read_2, checkIfExists: true)]
        )
    }
    .set { reads_ch }

host_index_ch = Channel
    .fromPath("${params.host_index}*.bt2*", checkIfExists: true)
    .collect()

metaphlan_db_ch = Channel.value(file(params.metaphlan_db, checkIfExists: true))

workflow {
    cleaned = FASTP(reads_ch)
    dehosted = REMOVE_HOST(cleaned.reads, host_index_ch)
    METAPHLAN(dehosted.reads, metaphlan_db_ch)
}
