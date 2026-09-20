import { useState } from 'react'
import { createMessage } from '../api.js'

// TODO: replace with the logged-in child's id once auth/child-selection exists.
const CHILD_ID = 1

// Maps whatever status the classifier lands on to a label. Works for today's
// binary "safe"/"flagged" and won't break once the classifier moves to
// low/medium/high -- unrecognized statuses just fall back to a neutral look.
const STATUS_LABELS = {
  safe: 'Safe',
  low: 'Low',
  medium: 'Medium',
  warning: 'Medium',
  flagged: 'Flagged',
  high: 'High',
  blocked: 'Blocked',
}

// Quick-fill examples for demos, tuned to land in each bucket under the
// current keyword classifier (see backend/classifier.py TOXIC_TERMS).
const PRESETS = [
  { label: 'Low example', text: 'hey want to hang out after school?' },
  { label: 'Medium example', text: "you're worthless and nobody actually likes you" },
  { label: 'High example', text: "I'm going to kill you tomorrow" },
]

export default function ComposeMessage({ onSent }) {
  const [sender, setSender] = useState('')
  const [text, setText] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  async function handleSubmit(event) {
    event.preventDefault()
    if (!text.trim() || submitting) return
    setSubmitting(true)
    setError(null)
    setResult(null)
    try {
      const message = await createMessage({
        child_id: CHILD_ID,
        text,
        sender: sender.trim() || 'me',
      })
      setResult(message)
      setText('')
      onSent?.()
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const statusKey = result?.status ?? ''
  const statusLabel = STATUS_LABELS[statusKey] || statusKey

  return (
    <section className="card">
      <div className="card__header">
        <div className="card__title">
          <span className="card__title-icon">✉️</span> Send a Message
        </div>
      </div>
      <p className="card__subtitle">
        Try it out: send a message as the child would, and see how it's handled.
      </p>

      <div className="preset-row">
        {PRESETS.map((preset) => (
          <button
            key={preset.label}
            type="button"
            className="preset-btn"
            onClick={() => setText(preset.text)}
          >
            {preset.label}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit}>
        <div className="field">
          <label className="field__label" htmlFor="compose-sender">
            From
          </label>
          <input
            id="compose-sender"
            type="text"
            value={sender}
            onChange={(e) => setSender(e.target.value)}
            placeholder="e.g. your name"
          />
        </div>
        <div className="field">
          <label className="field__label" htmlFor="compose-text">
            Message
          </label>
          <textarea
            id="compose-text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Type a message to analyze…"
            required
          />
        </div>
        <button className="btn" type="submit" disabled={submitting}>
          {submitting ? 'Analyzing…' : 'Send'}
        </button>
      </form>

      {error && <p className="error-banner" role="alert">Something went wrong: {error}</p>}

      {result && (
        <div className={`result-panel result-panel--${statusKey}`}>
          <span className={`badge badge--${statusKey}`}>{statusLabel}</span>
          <span className="result-panel__score">toxicity score: {result.score.toFixed(2)}</span>
        </div>
      )}
    </section>
  )
}
