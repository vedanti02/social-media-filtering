import { useEffect, useState } from 'react'
import { getParent, updateNotifyChannel } from '../api.js'

const CHANNELS = [
  { value: 'email', label: '✉️ Email' },
  { value: 'push', label: '📲 Push' },
]

export default function NotificationSettings({ parentId }) {
  const [channel, setChannel] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    getParent(parentId)
      .then((parent) => {
        if (!cancelled) setChannel(parent.notify_channel)
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

  async function handleSelect(value) {
    if (value === channel) return
    const previous = channel
    // Optimistic update; roll back if the request fails.
    setChannel(value)
    try {
      await updateNotifyChannel(parentId, value)
    } catch (err) {
      setChannel(previous)
      setError(err.message)
    }
  }

  return (
    <section className="card">
      <div className="card__header">
        <div className="card__title">
          <span className="card__title-icon">🔔</span> Notifications
        </div>
      </div>
      <p className="card__subtitle">How you'd like to hear about high-toxicity alerts.</p>

      {error && <p className="error-banner" role="alert">Something went wrong: {error}</p>}
      {loading ? (
        <p className="loading-state">Loading…</p>
      ) : (
        <div className="btn-group">
          {CHANNELS.map(({ value, label }) => (
            <button
              key={value}
              className={value === channel ? 'btn' : 'btn btn--ghost'}
              aria-pressed={value === channel}
              onClick={() => handleSelect(value)}
            >
              {label}
            </button>
          ))}
        </div>
      )}
    </section>
  )
}
