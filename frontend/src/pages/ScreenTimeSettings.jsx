import { useEffect, useState } from 'react'
import { updateScreenTime } from '../api.js'

function browserTimezone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'
  } catch {
    return 'UTC'
  }
}

// The "Set limits" card from the board: a daily minute limit and/or an
// allowed-hours window. Leaving a field blank turns that rule off.
// `status` comes from useScreenTime in App, so today's usage stays live.
export default function ScreenTimeSettings({ childId, childName, status, loadError, onSaved }) {
  const [limit, setLimit] = useState('')
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [loaded, setLoaded] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState(null)

  // Fill the form once, from the first status load. Later status updates
  // (heartbeats) only refresh the usage line, never the parent's edits.
  useEffect(() => {
    if (!status || loaded) return
    setLimit(status.daily_limit_minutes == null ? '' : String(status.daily_limit_minutes))
    setStart(status.allowed_start ?? '')
    setEnd(status.allowed_end ?? '')
    setLoaded(true)
  }, [status, loaded])

  async function save(rules) {
    setSaving(true)
    setSaved(false)
    setError(null)
    try {
      const next = await updateScreenTime(childId, {
        daily_limit_minutes: rules.limit === '' ? null : Number.parseInt(rules.limit, 10),
        allowed_start: rules.start || null,
        allowed_end: rules.end || null,
        timezone: browserTimezone(),
      })
      onSaved(next)
      setSaved(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  function handleSubmit(event) {
    event.preventDefault()
    save({ limit, start, end })
  }

  function handleClear() {
    setLimit('')
    setStart('')
    setEnd('')
    save({ limit: '', start: '', end: '' })
  }

  return (
    <section className="card">
      <div className="card__header">
        <div className="card__title">
          <span className="card__title-icon">⏱️</span> Screen Time
        </div>
        {status?.locked && <span className="badge badge--high">Locked</span>}
      </div>
      <p className="card__subtitle">
        Limit how long and when {childName} can use the app. Leave a field blank to turn it off.
      </p>

      {!loaded ? (
        loadError ? (
          <p className="error-banner" role="alert">Something went wrong: {loadError}</p>
        ) : (
          <p className="loading-state">Loading…</p>
        )
      ) : (
        <form onSubmit={handleSubmit}>
          <p className="screen-time-usage">
            Today: <strong>{status.minutes_used} min</strong> used
            {status.daily_limit_minutes != null && ` of ${status.daily_limit_minutes}`}
          </p>
          <div className="field">
            <label className="field__label" htmlFor="screen-time-limit">
              Daily limit (minutes)
            </label>
            <input
              id="screen-time-limit"
              type="number"
              min="1"
              max="1440"
              step="1"
              value={limit}
              onChange={(e) => setLimit(e.target.value)}
              placeholder="No limit"
            />
          </div>
          <div className="field-row">
            <div className="field">
              <label className="field__label" htmlFor="screen-time-start">
                Allowed from
              </label>
              <input
                id="screen-time-start"
                type="time"
                value={start}
                onChange={(e) => setStart(e.target.value)}
              />
            </div>
            <div className="field">
              <label className="field__label" htmlFor="screen-time-end">
                Allowed until
              </label>
              <input
                id="screen-time-end"
                type="time"
                value={end}
                onChange={(e) => setEnd(e.target.value)}
              />
            </div>
          </div>
          <div className="btn-group">
            <button className="btn" type="submit" disabled={saving}>
              {saving ? 'Saving…' : 'Save'}
            </button>
            <button className="btn btn--ghost" type="button" onClick={handleClear} disabled={saving}>
              Clear limits
            </button>
          </div>
        </form>
      )}

      {saved && !error && <p className="info-banner section-gap">✅ Screen time rules saved.</p>}
      {error && <p className="error-banner" role="alert">Something went wrong: {error}</p>}
    </section>
  )
}
