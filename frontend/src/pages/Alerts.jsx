import { useEffect, useRef, useState } from 'react'
import { blockSender, getAlerts, markAlertRead } from '../api.js'

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

export default function Alerts({ parentId, childId, childName, refreshKey, onBlocked }) {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [popupAlert, setPopupAlert] = useState(null)
  const [blockedSender, setBlockedSender] = useState(null)

  // Tracks alert ids already seen, so a fresh fetch can tell which one (if
  // any) is genuinely new and worth popping up. null = "haven't loaded yet".
  const seenIds = useRef(null)

  useEffect(() => {
    let cancelled = false
    getAlerts(parentId)
      .then((data) => {
        if (cancelled) return
        if (seenIds.current) {
          const newOnes = data.filter((a) => !seenIds.current.has(a.id))
          if (newOnes.length > 0) setPopupAlert(newOnes[0])
        }
        seenIds.current = new Set(data.map((a) => a.id))
        setAlerts(data)
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
  }, [refreshKey])

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

  async function handleBlockSender(alert) {
    try {
      await blockSender(childId, alert.sender)
      setBlockedSender(alert.sender)
      onBlocked?.()
    } catch (err) {
      setError(err.message)
    } finally {
      handleRead(alert)
      setPopupAlert(null)
    }
  }

  function handleDismissPopup(alert) {
    handleRead(alert)
    setPopupAlert(null)
  }

  const unreadCount = alerts.filter((a) => !a.is_read).length

  return (
    <section className="card">
      <div className="card__header">
        <div className="card__title">
          <span className="card__title-icon">⚠️</span> Alerts
        </div>
        {!loading && alerts.length > 0 && (
          <span className="card__count">{unreadCount} unread</span>
        )}
      </div>
      <p className="card__subtitle">Severe messages caught by the safety scanner.</p>

      {error && <p className="error-banner" role="alert">Something went wrong: {error}</p>}
      {blockedSender && (
        <p className="info-banner">🚫 {blockedSender} is now blocked for {childName}.</p>
      )}
      {loading ? (
        <p className="loading-state">Loading…</p>
      ) : alerts.length === 0 ? (
        <p className="empty-state">No alerts. Nothing severe has been caught.</p>
      ) : (
        <ul className="alert-list">
          {alerts.map((alert) => (
            <li
              key={alert.id}
              className={`alert-card ${alert.is_read ? '' : 'alert-card--unread'}`}
              onClick={() => handleRead(alert)}
              aria-label={`${alert.is_read ? 'Read' : 'Unread'} alert: ${alert.category} from ${alert.sender}`}
            >
              <div className="alert-card__title">
                {!alert.is_read && <span className="alert-card__dot" />}
                {formatCategory(alert.category)}
              </div>
              <div className="alert-card__meta">
                from {alert.sender} · {relativeTime(alert.created_at)}
              </div>
            </li>
          ))}
        </ul>
      )}

      {popupAlert && (
        <div className="alert-popup" role="alertdialog" aria-label="New alert">
          <div className="alert-popup__header">
            <span className="alert-popup__title">
              ⚠️ New alert: {formatCategory(popupAlert.category)}
            </span>
            <button
              className="alert-popup__close"
              onClick={() => setPopupAlert(null)}
              aria-label="Close"
            >
              ×
            </button>
          </div>
          <p className="alert-popup__meta">from {popupAlert.sender}</p>
          <div className="alert-popup__actions">
            <button className="btn btn--danger" onClick={() => handleBlockSender(popupAlert)}>
              Block sender
            </button>
            <button className="btn btn--ghost" onClick={() => handleDismissPopup(popupAlert)}>
              Dismiss
            </button>
          </div>
        </div>
      )}
    </section>
  )
}
