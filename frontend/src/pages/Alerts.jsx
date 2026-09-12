import { useEffect, useState } from 'react'
import { getAlerts, markAlertRead } from '../api.js'

// TODO: replace with the logged-in parent's id once auth exists.
const PARENT_ID = 1

// The backend stores UTC. SQLite drops the timezone, so the API may return a
// naive ISO string; treat anything without an offset as UTC.
function parseUtc(iso) {
  return new Date(/[zZ]|[+-]\d\d:\d\d$/.test(iso) ? iso : `${iso}Z`)
}

function relativeTime(iso) {
  const seconds = Math.max(0, Math.round((Date.now() - parseUtc(iso)) / 1000))
  const units = [
    ['day', 86400],
    ['hour', 3600],
    ['minute', 60],
  ]
  for (const [name, size] of units) {
    const value = Math.floor(seconds / size)
    if (value >= 1) return `${value} ${name}${value === 1 ? '' : 's'} ago`
  }
  return 'just now'
}

function formatCategory(category) {
  return category.replaceAll('_', ' ')
}

const styles = {
  list: { listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: '0.5rem' },
  card: {
    border: '1px solid #ccc',
    borderRadius: 6,
    padding: '0.75rem 1rem',
    cursor: 'pointer',
    background: '#fff',
  },
  unread: { borderLeft: '4px solid #d33', background: '#fff5f5', fontWeight: 600 },
  meta: { fontSize: '0.85rem', color: '#555', fontWeight: 400 },
  empty: { color: '#666', fontStyle: 'italic' },
}

export default function Alerts() {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    getAlerts(PARENT_ID)
      .then((data) => {
        if (!cancelled) setAlerts(data)
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  async function handleRead(alert) {
    if (alert.is_read) return
    // Optimistic update; roll back if the request fails.
    setAlerts((prev) => prev.map((a) => (a.id === alert.id ? { ...a, is_read: true } : a)))
    try {
      await markAlertRead(alert.id)
    } catch (err) {
      setAlerts((prev) => prev.map((a) => (a.id === alert.id ? { ...a, is_read: false } : a)))
      setError(err.message)
    }
  }

  return (
    <section>
      <h2>Alerts</h2>
      {error && <p role="alert">Something went wrong: {error}</p>}
      {loading ? (
        <p>Loading…</p>
      ) : alerts.length === 0 ? (
        <p style={styles.empty}>No alerts. Nothing severe has been caught.</p>
      ) : (
        <ul style={styles.list}>
          {alerts.map((alert) => (
            <li
              key={alert.id}
              style={{ ...styles.card, ...(alert.is_read ? {} : styles.unread) }}
              onClick={() => handleRead(alert)}
              aria-label={`${alert.is_read ? 'Read' : 'Unread'} alert: ${alert.category} from ${alert.sender}`}
            >
              <div>{formatCategory(alert.category)}</div>
              <div style={styles.meta}>
                from {alert.sender} · {relativeTime(alert.created_at)}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
