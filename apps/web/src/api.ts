import type { Alert, Site, Summary, Timeline } from "./types"

type StaticDashboard = {
  summary: Summary
  sites: Site[]
  timelines: Record<string, Timeline>
  alerts: Record<string, Alert[]>
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path)
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`Request failed (${response.status}): ${detail}`)
  }
  return response.json() as Promise<T>
}

const liveApi = {
  summary: () => getJson<Summary>("/api/summary"),
  sites: () => getJson<Site[]>("/api/sites"),
  timeline: (siteId: string) =>
    getJson<Timeline>(`/api/sites/${siteId}/timeline`),
  alerts: (siteId: string) =>
    getJson<Alert[]>(`/api/alerts?site_id=${encodeURIComponent(siteId)}`),
}

let snapshotRequest: Promise<StaticDashboard> | undefined

function staticDashboard() {
  snapshotRequest ??= getJson<StaticDashboard>(
    `${import.meta.env.BASE_URL}data/dashboard.json`,
  )
  return snapshotRequest
}

const staticApi = {
  summary: async () => (await staticDashboard()).summary,
  sites: async () => (await staticDashboard()).sites,
  timeline: async (siteId: string) => {
    const timeline = (await staticDashboard()).timelines[siteId]
    if (!timeline) throw new Error(`Unknown monitoring location: ${siteId}`)
    return timeline
  },
  alerts: async (siteId: string) => (await staticDashboard()).alerts[siteId] ?? [],
}

export const api = import.meta.env.VITE_STATIC_MODE === "true" ? staticApi : liveApi
