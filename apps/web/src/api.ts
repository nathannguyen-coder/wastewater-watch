import type { Alert, Site, Summary, Timeline } from "./types"

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path)
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`Request failed (${response.status}): ${detail}`)
  }
  return response.json() as Promise<T>
}

export const api = {
  summary: () => getJson<Summary>("/api/summary"),
  sites: () => getJson<Site[]>("/api/sites"),
  timeline: (siteId: string) =>
    getJson<Timeline>(`/api/sites/${siteId}/timeline`),
  alerts: (siteId: string) =>
    getJson<Alert[]>(`/api/alerts?site_id=${encodeURIComponent(siteId)}`),
}
