// One fetch helper per backend route. Base URL comes from VITE_API_URL in
// production (set in Vercel); falls back to the local FastAPI dev server.
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const TOKEN_KEY = 'auth_token'

// localStorage can throw (private windows, blocked site data) -- fall back to no token.
export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token) {
  try {
    localStorage.setItem(TOKEN_KEY, token)
  } catch {
    /* ignore */
  }
}

export function clearToken() {
  try {
    localStorage.removeItem(TOKEN_KEY)
  } catch {
    /* ignore */
  }
}

// App registers a callback so any request that comes back 401 while logged in
// (expired/invalid token) sends the user back to the login page.
let onUnauthorized = () => {}
export function setUnauthorizedHandler(fn) {
  onUnauthorized = fn
}

async function request(path, options = {}) {
  const token = getToken()
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })
  if (!res.ok) {
    if (res.status === 401 && token) {
      clearToken()
      onUnauthorized()
    }
    const body = await res.json().catch(() => null)
    throw new Error(typeof body?.detail === 'string' ? body.detail : `${res.status} ${res.statusText}`)
  }
  return res.json()
}

// POST /auth/signup  -> { token, parent_id, parent_name, child_id, child_name }
export function signup({ name, email, password, childName }) {
  return request('/auth/signup', {
    method: 'POST',
    body: JSON.stringify({ name, email, password, child_name: childName }),
  })
}

// POST /auth/login  -> same shape as signup
export function login(email, password) {
  return request('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) })
}

// POST /auth/logout
export function logout() {
  return request('/auth/logout', { method: 'POST' })
}

// GET /auth/me  -> { parent_id, parent_name, child_id, child_name }
export function getMe() {
  return request('/auth/me')
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

// GET /reports/weekly/{child_id}?period=daily|weekly
export function getWeeklyReport(childId, period = 'weekly') {
  return request(`/reports/weekly/${childId}?period=${period}`)
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

// POST /blocked-senders
export function blockSender(childId, sender) {
  return request('/blocked-senders', {
    method: 'POST',
    body: JSON.stringify({ child_id: childId, sender }),
  })
}

// GET /blocked-senders/{child_id}
export function getBlockedSenders(childId) {
  return request(`/blocked-senders/${childId}`)
}

// DELETE /blocked-senders/{id}
export function unblockSender(id) {
  return request(`/blocked-senders/${id}`, { method: 'DELETE' })
}

// GET /parents/{parent_id}
export function getParent(parentId) {
  return request(`/parents/${parentId}`)
}

// PATCH /parents/{parent_id}/notify-channel
export function updateNotifyChannel(parentId, channel) {
  return request(`/parents/${parentId}/notify-channel`, {
    method: 'PATCH',
    body: JSON.stringify({ channel }),
  })
}
