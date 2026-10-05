import { useEffect, useState } from 'react'
import { getParent, sendDigest, updateAlertFrequency, updateNotifyChannel } from '../api.js'

const CHANNELS = [
  { value: 'email', label: '✉️ Email' },
  { value: 'push', label: '📲 Push' },
]

const FREQUENCIES = [
  { value: 'instant', label: '⚡ Instant' },
  { value: 'weekly', label: '🗓️ Weekly digest' },
]

function digestSummary(digest) {
  if (!digest.sent) return 'No alerts in the last 7 days, so there was nothing to send.'
  const alerts = `${digest.total_alerts} alert${digest.total_alerts === 1 ? '' : 's'}`
  const senders = `${digest.senders.length} sender${digest.senders.length === 1 ? '' : 's'}`
  return `Digest sent: ${alerts} from ${senders}.`
}

export default function NotificationSettings({ parentId }) {
  const [channel, setChannel] = useState(null)
  const [frequency, setFrequency] = useState(null)
  const [digestMessage, setDigestMessage] = useState(null)
  const [sendingDigest, setSendingDigest] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    getParent(parentId)
      .then((parent) => {
        if (cancelled) return
        setChannel(parent.notify_channel)
        setFrequency(parent.alert_frequency)
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

  async function handleFrequency(value) {
    if (value === frequency) return
    const previous = frequency
    // Optimistic update; roll back if the request fails.
    setFrequency(value)
    setDigestMessage(null)
    try {
      await updateAlertFrequency(parentId, value)
    } catch (err) {
      setFrequency(previous)
      setError(err.message)
    }
  }

  async function handleSendDigest() {
    setSendingDigest(true)
    setDigestMessage(null)
    try {
      setDigestMessage(digestSummary(await sendDigest(parentId)))
    } catch (err) {
      setError(err.message)
    } finally {
      setSendingDigest(false)
    }
  }

  return (
    <section className="card">
      <div className="card__header">
        <div className="card__title">
          <span className="card__title-icon">🔔</span> Notifications
        </div>
      </div>
      <p className="card__subtitle">How and when you'd like to hear about high-toxicity alerts.</p>

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

      {!loading && frequency && (
        <div className="section-gap">
          <p className="field__label">When</p>
          <div className="btn-group section-gap--sm">
            {FREQUENCIES.map(({ value, label }) => (
              <button
                key={value}
                className={value === frequency ? 'btn' : 'btn btn--ghost'}
                aria-pressed={value === frequency}
                onClick={() => handleFrequency(value)}
              >
                {label}
              </button>
            ))}
          </div>
          {frequency === 'weekly' && (
            <>
              <p className="field__hint section-gap--sm">
                Alerts still appear in your inbox right away; notifications are bundled into one
                summary each week.
              </p>
              <button
                className="btn btn--ghost btn--sm section-gap--sm"
                onClick={handleSendDigest}
                disabled={sendingDigest}
              >
                {sendingDigest ? 'Sending…' : 'Send digest now'}
              </button>
            </>
          )}
          {digestMessage && <p className="info-banner section-gap--sm">{digestMessage}</p>}
        </div>
      )}
    </section>
  )
}
