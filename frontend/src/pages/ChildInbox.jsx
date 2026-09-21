import { useEffect, useState } from 'react'
import { getMessages } from '../api.js'

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

// This is the "Automated Moderate Actions" card from the board:
// low -> shown normally, medium -> shown behind a warning, high -> hidden.
export default function ChildInbox({ childId, childName, refreshKey }) {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  // ids the child has chosen to reveal past a medium-toxicity warning.
  const [revealed, setRevealed] = useState(() => new Set())

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    getMessages(childId)
      .then((data) => {
        if (!cancelled) setMessages(data)
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

  function reveal(id) {
    setRevealed((prev) => new Set(prev).add(id))
  }

  return (
    <section className="card">
      <div className="card__header">
        <div className="card__title">
          <span className="card__title-icon">📱</span> {childName}'s Inbox
        </div>
      </div>
      <p className="card__subtitle">
        What the child actually sees — moderated automatically by toxicity level.
      </p>

      {error && <p className="error-banner" role="alert">Something went wrong: {error}</p>}
      {loading ? (
        <p className="loading-state">Loading…</p>
      ) : messages.length === 0 ? (
        <p className="empty-state">No messages yet — send one to see it show up here.</p>
      ) : (
        <ul className="message-list">
          {messages.map((message) => (
            <li key={message.id} className={`message-bubble message-bubble--${message.status}`}>
              <div className="message-bubble__meta">
                <span>{message.sender}</span>
                <span>{relativeTime(message.created_at)}</span>
              </div>

              {message.status === 'high' ? (
                <div className="message-hidden">🚫 Message hidden for your safety</div>
              ) : message.status === 'medium' && !revealed.has(message.id) ? (
                <div className="message-warning">
                  <span className="message-warning__label">⚠️ This message might not be nice</span>
                  <button className="message-reveal-btn" onClick={() => reveal(message.id)}>
                    Show me anyway
                  </button>
                </div>
              ) : (
                <div className="message-bubble__text">
                  {message.status === 'medium' && <span className="message-warning__label">⚠️ </span>}
                  {message.text}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
