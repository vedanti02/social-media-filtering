import { useEffect, useState } from 'react'
import { getBlockedSenders, unblockSender } from '../api.js'

// TODO: fetch blocked words, wire addBlockedWord / removeBlockedWord from ../api.js.
export default function Blocklist({ childId, childName, refreshKey }) {
  const [senders, setSenders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const words = []

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    getBlockedSenders(childId)
      .then((data) => {
        if (!cancelled) setSenders(data)
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

  async function handleUnblock(sender) {
    // Optimistic remove; roll back if the request fails.
    setSenders((prev) => prev.filter((s) => s.id !== sender.id))
    try {
      await unblockSender(sender.id)
    } catch (err) {
      setSenders((prev) => [...prev, sender].sort((a, b) => a.id - b.id))
      setError(err.message)
    }
  }

  return (
    <section className="card">
      <div className="card__header">
        <div className="card__title">
          <span className="card__title-icon">🚫</span> Blocklist
        </div>
        {!loading && senders.length > 0 && (
          <span className="card__count">{senders.length} blocked</span>
        )}
      </div>
      <p className="card__subtitle">
        Senders blocked for {childName} — every future message from them is auto-flagged.
      </p>

      {error && <p className="error-banner" role="alert">Something went wrong: {error}</p>}
      {loading ? (
        <p className="loading-state">Loading…</p>
      ) : senders.length === 0 ? (
        <p className="empty-state">No one is blocked yet.</p>
      ) : (
        <ul className="blocklist-list">
          {senders.map((sender) => (
            <li key={sender.id} className="blocklist-row">
              <span className="blocklist-row__name">{sender.sender}</span>
              <button className="btn btn--ghost btn--sm" onClick={() => handleUnblock(sender)}>
                Unblock
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="section-gap">
        {words.length === 0 ? (
          <div className="coming-soon">Word-based blocklist is coming soon.</div>
        ) : (
          <ul className="alert-list">
            {words.map((entry) => (
              <li key={entry.id} className="alert-card">
                {entry.word}
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
