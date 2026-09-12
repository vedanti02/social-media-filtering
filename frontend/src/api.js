// One fetch helper per backend route. Base URL matches the FastAPI dev server.
const BASE_URL = 'http://localhost:8000'

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

// GET /alerts/{parent_id}
export function getAlerts(parentId) {
  return request(`/alerts/${parentId}`)
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
