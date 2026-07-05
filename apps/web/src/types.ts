export type Status =
  | "baseline"
  | "normal"
  | "watch"
  | "alert"
  | "quality_review"

export type Site = {
  id: string
  name: string
  region: string
  sample_count: number
  latest_sample: string
  latest_status: "normal" | "watch" | "alert"
}

export type Contributor = {
  taxon: string
  direction: "higher" | "lower"
  contribution: number
  current_abundance: number
  baseline_abundance: number
}

export type Sample = {
  id: string
  site_id: string
  collected_at: string
  reads_millions: number
  host_read_fraction: number
  qc_status: "pass" | "review"
  anomaly_score: number | null
  status: Status
  abundances: Record<string, number>
  top_contributors: Contributor[]
  bioproject: string | null
  biosample: string | null
  sra_run: string | null
  profile_method: string | null
  source_url: string | null
  identified_fraction: number | null
}

export type Timeline = {
  site: Site
  samples: Sample[]
  score_thresholds: {
    watch: number
    alert: number
  }
}

export type Alert = {
  id: string
  site_id: string
  site_name: string
  sample_id: string
  collected_at: string
  severity: "watch" | "alert"
  score: number
  title: string
  summary: string
  caveat: string
  contributors: Contributor[]
}

export type Summary = {
  sites_monitored: number
  samples_processed: number
  active_alerts: number
  review_required: number
  latest_collection: string
  data_mode: "demonstration" | "ncbi_sra"
  model_version: string
  source_project: string | null
}
