// One fetch helper per backend route. Base URL comes from VITE_API_URL in
// production (set in Vercel); falls back to the local FastAPI dev server.
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

// POST /messages
export function createMessage(message) {
  // TODO: shape of `message` — { child_id, text, sender }
  return request('/messages', { method: 'POST', body: JSON.stringify(message) })
}

// GET /messages/{child_id}
export function getMessages(childId) {
  return request(`/messages/${childId}`)
}

// GET /reports/weekly/{child_id}
export function getWeeklyReport(childId) {
  return request(`/reports/weekly/${childId}`)
}

// GET /alerts/{parent_id}?limit=N  (newest first)
export function getAlerts(parentId, limit = 20) {
  return request(`/alerts/${parentId}?limit=${limit}`)
}

// PATCH /alerts/{alert_id}/read
export function markAlertRead(alertId) {
  return request(`/alerts/${alertId}/read`, { method: 'PATCH' })
}

// POST /blocklist
export function addBlockedWord(word, parentId) {
  return request('/blocklist', {
    method: 'POST',
    body: JSON.stringify({ word, parent_id: parentId }),
  })
}

// DELETE /blocklist/{word}
export function removeBlockedWord(word) {
  return request(`/blocklist/${encodeURIComponent(word)}`, { method: 'DELETE' })
}
