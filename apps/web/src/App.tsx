import { useCallback, useEffect, useMemo, useState } from "react"

import { api } from "./api"
import type { Alert, Sample, Site, Summary, Timeline } from "./types"

const TAXON_COLORS = [
  "#0f6172",
  "#ef6a3a",
  "#799246",
  "#9b7cbc",
  "#e6b84f",
  "#4c83c3",
  "#bb566d",
  "#7d7469",
]

function formatDate(value: string, compact = false) {
  const date = new Date(`${value}T00:00:00`)
  return new Intl.DateTimeFormat("en-US", {
    month: compact ? "short" : "long",
    day: "numeric",
    year: compact ? undefined : "numeric",
  }).format(date)
}

function statusLabel(status: Sample["status"]) {
  return {
    baseline: "Building baseline",
    normal: "Within baseline",
    watch: "Watch",
    alert: "Review now",
    quality_review: "QC review",
  }[status]
}

function StatusDot({ status }: { status: Sample["status"] | Site["latest_status"] }) {
  return <span className={`status-dot status-${status}`} aria-hidden="true" />
}

function LoadingScreen() {
  return (
    <div className="state-page" role="status">
      <div className="brand-mark" aria-hidden="true">W</div>
      <p className="eyebrow">Preparing surveillance workspace</p>
      <h1>Reading community profiles…</h1>
      <div className="loading-line"><span /></div>
    </div>
  )
}

function ErrorScreen({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="state-page state-error" role="alert">
      <div className="brand-mark" aria-hidden="true">!</div>
      <p className="eyebrow">Connection interrupted</p>
      <h1>The surveillance API is unavailable.</h1>
      <p>{message}</p>
      <button className="primary-button" onClick={onRetry}>Try again</button>
    </div>
  )
}

function ScoreChart({
  timeline,
  selectedSampleId,
  onSelect,
}: {
  timeline: Timeline
  selectedSampleId: string
  onSelect: (sample: Sample) => void
}) {
  const width = 760
  const height = 250
  const inset = { top: 18, right: 18, bottom: 42, left: 36 }
  const scored = timeline.samples.filter((sample) => sample.anomaly_score !== null)
  const maxScore = Math.max(
    timeline.score_thresholds.alert + 1,
    ...scored.map((sample) => sample.anomaly_score ?? 0),
  )
  const x = (index: number) =>
    inset.left + (index / Math.max(timeline.samples.length - 1, 1)) * (width - inset.left - inset.right)
  const y = (value: number) =>
    inset.top + (1 - value / maxScore) * (height - inset.top - inset.bottom)
  const path = scored
    .map((sample) => {
      const index = timeline.samples.findIndex((item) => item.id === sample.id)
      return `${x(index)},${y(sample.anomaly_score ?? 0)}`
    })
    .join(" ")

  return (
    <div className="chart-wrap">
      <svg
        className="score-chart"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={`Anomaly scores over time for ${timeline.site.name}`}
      >
        <line className="grid-line" x1={inset.left} x2={width - inset.right} y1={y(timeline.score_thresholds.alert)} y2={y(timeline.score_thresholds.alert)} />
        <line className="grid-line watch-line" x1={inset.left} x2={width - inset.right} y1={y(timeline.score_thresholds.watch)} y2={y(timeline.score_thresholds.watch)} />
        <text className="threshold-label" x={width - inset.right} y={y(timeline.score_thresholds.alert) - 7}>ALERT {timeline.score_thresholds.alert}</text>
        <text className="threshold-label" x={width - inset.right} y={y(timeline.score_thresholds.watch) - 7}>WATCH {timeline.score_thresholds.watch}</text>
        {path && <polyline className="score-line" points={path} />}
        {timeline.samples.map((sample, index) => {
          const value = sample.anomaly_score
          const pointY = value === null ? height - inset.bottom : y(value)
          const selected = sample.id === selectedSampleId
          return (
            <g
              key={sample.id}
              className="chart-point"
              role="button"
              tabIndex={0}
              aria-label={`${formatDate(sample.collected_at)}: ${statusLabel(sample.status)}${value === null ? "" : `, score ${value}`}`}
              onClick={() => onSelect(sample)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") onSelect(sample)
              }}
            >
              <circle
                cx={x(index)}
                cy={pointY}
                r={selected ? 8 : 5.5}
                className={`point-${sample.status}${selected ? " is-selected" : ""}`}
              />
              {(index === 0 || index === timeline.samples.length - 1 || sample.status === "alert") && (
                <text className="date-label" x={x(index)} y={height - 13}>
                  {formatDate(sample.collected_at, true)}
                </text>
              )}
            </g>
          )
        })}
      </svg>
    </div>
  )
}

function Composition({ sample }: { sample: Sample }) {
  const entries = Object.entries(sample.abundances).sort((a, b) => b[1] - a[1])
  return (
    <div className="composition">
      <div className="composition-strip" aria-label="Relative abundance composition">
        {entries.map(([taxon, abundance], index) => (
          <span
            key={taxon}
            style={{ width: `${abundance * 100}%`, background: TAXON_COLORS[index] }}
            title={`${taxon}: ${(abundance * 100).toFixed(1)}%`}
          />
        ))}
      </div>
      <div className="taxa-list">
        {entries.slice(0, 5).map(([taxon, abundance], index) => (
          <div className="taxon-row" key={taxon}>
            <span className="taxon-swatch" style={{ background: TAXON_COLORS[index] }} />
            <span>{taxon}</span>
            <div className="taxon-track"><i style={{ width: `${abundance * 250}%` }} /></div>
            <strong>{(abundance * 100).toFixed(1)}%</strong>
          </div>
        ))}
      </div>
    </div>
  )
}

function AlertInspector({ alert, sample }: { alert?: Alert; sample: Sample }) {
  if (sample.status === "quality_review") {
    return (
      <aside className="inspector inspector-quality">
        <p className="eyebrow">Quality gate</p>
        <h2>Hold this sample for review.</h2>
        <p>Low read depth or elevated host-read fraction can make apparent community changes unreliable.</p>
        <dl className="mini-stats">
          <div><dt>Reads</dt><dd>{sample.reads_millions.toFixed(1)}M</dd></div>
          <div><dt>Host fraction</dt><dd>{(sample.host_read_fraction * 100).toFixed(1)}%</dd></div>
        </dl>
      </aside>
    )
  }

  if (!alert) {
    return (
      <aside className="inspector inspector-clear">
        <p className="eyebrow">Analyst review</p>
        <div className="clear-symbol" aria-hidden="true">✓</div>
        <h2>No alert for this sample.</h2>
        <p>
          {sample.status === "baseline"
            ? "The site-specific reference window is still being established."
            : "The community profile is within its site-specific baseline."}
        </p>
        <p className="caveat">Absence of an alert does not establish absence of a public-health concern.</p>
      </aside>
    )
  }

  return (
    <aside className={`inspector inspector-${alert.severity}`}>
      <div className="inspector-heading">
        <span className="alert-icon" aria-hidden="true">↗</span>
        <span className="severity">{alert.severity}</span>
      </div>
      <p className="eyebrow">Analyst review · {formatDate(alert.collected_at)}</p>
      <h2>{alert.title}</h2>
      <p className="alert-summary">{alert.summary}</p>
      <div className="score-block">
        <span>Robust CLR anomaly score</span>
        <strong>{alert.score.toFixed(2)}</strong>
      </div>
      <h3>Largest contributions</h3>
      <div className="contributors">
        {alert.contributors.slice(0, 3).map((contributor) => (
          <div key={contributor.taxon}>
            <span>{contributor.taxon}</span>
            <strong>{contributor.direction} · {Math.round(contributor.contribution * 100)}%</strong>
          </div>
        ))}
      </div>
      <p className="caveat">{alert.caveat}</p>
    </aside>
  )
}

function App() {
  const [summary, setSummary] = useState<Summary | null>(null)
  const [sites, setSites] = useState<Site[]>([])
  const [timeline, setTimeline] = useState<Timeline | null>(null)
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [selectedSiteId, setSelectedSiteId] = useState("pl")
  const [selectedSampleId, setSelectedSampleId] = useState("")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const loadWorkspace = useCallback(async () => {
    setLoading(true)
    setError("")
    try {
      const [nextSummary, nextSites] = await Promise.all([api.summary(), api.sites()])
      const initialSite = nextSites.some((site) => site.id === selectedSiteId)
        ? selectedSiteId
        : nextSites[0]?.id
      if (!initialSite) throw new Error("No monitoring sites were returned")
      const [nextTimeline, nextAlerts] = await Promise.all([
        api.timeline(initialSite),
        api.alerts(initialSite),
      ])
      setSummary(nextSummary)
      setSites(nextSites)
      setSelectedSiteId(initialSite)
      setTimeline(nextTimeline)
      setAlerts(nextAlerts)
      setSelectedSampleId(
        nextAlerts[0]?.sample_id ?? nextTimeline.samples.at(-1)?.id ?? "",
      )
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Unknown error")
    } finally {
      setLoading(false)
    }
  }, [selectedSiteId])

  useEffect(() => {
    void loadWorkspace()
    // Initial load only; site changes have a dedicated effect.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const changeSite = async (siteId: string) => {
    setSelectedSiteId(siteId)
    setTimeline(null)
    setError("")
    try {
      const [nextTimeline, nextAlerts] = await Promise.all([
        api.timeline(siteId),
        api.alerts(siteId),
      ])
      setTimeline(nextTimeline)
      setAlerts(nextAlerts)
      setSelectedSampleId(nextAlerts[0]?.sample_id ?? nextTimeline.samples.at(-1)?.id ?? "")
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Unknown error")
    }
  }

  const selectedSample = useMemo(
    () => timeline?.samples.find((sample) => sample.id === selectedSampleId)
      ?? timeline?.samples.at(-1),
    [selectedSampleId, timeline],
  )
  const selectedAlert = alerts.find((alert) => alert.sample_id === selectedSample?.id)

  if (loading) return <LoadingScreen />
  if (error && !summary) return <ErrorScreen message={error} onRetry={() => void loadWorkspace()} />
  if (!summary) return null

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#main">
          <span className="brand-mark">W</span>
          <span><strong>Wastewater</strong> Watch</span>
        </a>
        <div className="topbar-meta">
          <span className="demo-badge">
            {summary.data_mode === "ncbi_sra"
              ? `NCBI SRA · ${summary.source_project}`
              : "Demonstration data"}
          </span>
          <span>Model {summary.model_version}</span>
        </div>
      </header>

      <aside className="site-rail" aria-label="Monitoring sites">
        <p className="eyebrow">Monitoring network</p>
        <nav>
          {sites.map((site) => (
            <button
              key={site.id}
              className={site.id === selectedSiteId ? "is-active" : ""}
              onClick={() => void changeSite(site.id)}
              aria-pressed={site.id === selectedSiteId}
            >
              <StatusDot status={site.latest_status} />
              <span><strong>{site.name}</strong><small>{site.region}</small></span>
              <b>{site.sample_count}</b>
            </button>
          ))}
        </nav>
        <div className="rail-note">
          <span className="pulse" />
          <p><strong>Screening system online</strong><br />Last collection {formatDate(summary.latest_collection, true)}</p>
        </div>
      </aside>

      <main id="main">
        <section className="page-heading">
          <div>
            <p className="eyebrow">Wastewater community surveillance</p>
            <h1>{timeline?.site.name ?? "Loading site…"}</h1>
            <p>{timeline?.site.region} · longitudinal wastewater metatranscriptomic profiles</p>
          </div>
          <div className="network-summary">
            <p className="eyebrow">All monitoring locations · entire dataset</p>
            <div className="summary-cards" aria-label="Totals across all monitoring locations">
              <div><span>Locations</span><strong>{summary.sites_monitored}</strong></div>
              <div><span>Samples analyzed</span><strong>{summary.samples_processed}</strong></div>
              <div className="summary-alert"><span>Flagged samples</span><strong>{summary.active_alerts}</strong></div>
              <div><span>QC-held samples</span><strong>{summary.review_required}</strong></div>
            </div>
          </div>
        </section>

        {error && (
          <div className="inline-error" role="alert">
            <span>{error}</span>
            <button onClick={() => void changeSite(selectedSiteId)}>Retry</button>
          </div>
        )}

        {!timeline ? (
          <section className="panel panel-loading" role="status">Loading site profile…</section>
        ) : (
          <div className="workspace">
            <div className="primary-column">
              <section className="panel trend-panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Site-aware detection</p>
                    <h2>Community anomaly trajectory</h2>
                  </div>
                  <div className="legend"><span className="legend-normal">Within baseline</span><span className="legend-alert">Review</span></div>
                </div>
                <ScoreChart
                  timeline={timeline}
                  selectedSampleId={selectedSample?.id ?? ""}
                  onSelect={(sample) => setSelectedSampleId(sample.id)}
                />
              </section>

              {selectedSample && (
                <section className="panel sample-panel">
                  <div className="panel-heading">
                    <div>
                      <p className="eyebrow">Selected sample · {selectedSample.id}</p>
                      <h2>{formatDate(selectedSample.collected_at)}</h2>
                    </div>
                    <span className={`status-pill pill-${selectedSample.status}`}>
                      <StatusDot status={selectedSample.status} />
                      {statusLabel(selectedSample.status)}
                    </span>
                  </div>
                  <div className="sample-metrics">
                    <div><span>Sequenced reads</span><strong>{selectedSample.reads_millions.toFixed(1)}M</strong></div>
                    <div><span>Human-read signal</span><strong>{(selectedSample.host_read_fraction * 100).toFixed(2)}%</strong></div>
                    <div><span>Anomaly score</span><strong>{selectedSample.anomaly_score?.toFixed(2) ?? "—"}</strong></div>
                  </div>
                  {selectedSample.source_url && (
                    <div className="sample-provenance">
                      <div>
                        <span>Public source</span>
                        <a href={selectedSample.source_url} target="_blank" rel="noreferrer">
                          {selectedSample.sra_run} ↗
                        </a>
                      </div>
                      <div>
                        <span>BioSample</span>
                        <strong>{selectedSample.biosample}</strong>
                      </div>
                      <div>
                        <span>Taxonomy profile</span>
                        <strong>{selectedSample.profile_method}</strong>
                      </div>
                    </div>
                  )}
                  <h3>Relative community composition</h3>
                  <Composition sample={selectedSample} />
                </section>
              )}

              <section className="panel history-panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Provenance-preserving history</p>
                    <h2>Recent samples</h2>
                  </div>
                  <span>{timeline.samples.length} records</span>
                </div>
                <div className="sample-table" role="table" aria-label="Recent samples">
                  {timeline.samples.slice().reverse().map((sample) => (
                    <button
                      role="row"
                      key={sample.id}
                      className={sample.id === selectedSample?.id ? "is-selected" : ""}
                      onClick={() => setSelectedSampleId(sample.id)}
                    >
                      <span role="cell"><StatusDot status={sample.status} />{sample.id}</span>
                      <span role="cell">{formatDate(sample.collected_at, true)}</span>
                      <span role="cell">{sample.reads_millions.toFixed(1)}M reads</span>
                      <span role="cell">{statusLabel(sample.status)}</span>
                    </button>
                  ))}
                </div>
              </section>
            </div>

            {selectedSample && <AlertInspector alert={selectedAlert} sample={selectedSample} />}
          </div>
        )}
      </main>
    </div>
  )
}

export default App
