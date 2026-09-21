import { useEffect, useState } from 'react'
import { getWeeklyReport } from '../api.js'

const PERIODS = [
  { key: 'daily', label: 'Daily' },
  { key: 'weekly', label: 'Weekly' },
]

// Compares the current period's flagged-message count to the immediately
// preceding period of the same length (see backend/main.py weekly_report).
// trend_pct is null when there's no prior-period activity to compare against.
function TrendBadge({ trendPct }) {
  if (trendPct === null || trendPct === undefined) {
    return <span className="trend-badge trend-badge--neutral">New activity — no prior period to compare</span>
  }
  if (trendPct === 0) {
    return <span className="trend-badge trend-badge--neutral">No change vs. last period</span>
  }
  const up = trendPct > 0
  return (
    <span className={`trend-badge ${up ? 'trend-badge--up' : 'trend-badge--down'}`}>
      {up ? '▲' : '▼'} {Math.abs(trendPct)}% vs. last period
    </span>
  )
}

export default function WeeklyReport({ childId, childName, refreshKey }) {
  const [period, setPeriod] = useState('weekly')
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    getWeeklyReport(childId, period)
      .then((data) => {
        if (!cancelled) setReport(data)
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
  }, [period, refreshKey])

  return (
    <section className="card">
      <div className="card__header">
        <div className="card__title">
          <span className="card__title-icon">📊</span> Activity Report
        </div>
      </div>
      <p className="card__subtitle">A summary of messages, flags, and blocks for {childName}.</p>

      <div className="preset-row">
        {PERIODS.map((p) => (
          <button
            key={p.key}
            type="button"
            className={`preset-btn ${period === p.key ? 'preset-btn--active' : ''}`}
            onClick={() => setPeriod(p.key)}
          >
            {p.label}
          </button>
        ))}
      </div>

      {error && <p className="error-banner" role="alert">Something went wrong: {error}</p>}

      {loading ? (
        <p className="loading-state">Loading…</p>
      ) : report ? (
        <>
          <ul className="report-stats">
            <li className="report-stat">
              <span className="report-stat__value">{report.total_messages}</span>
              <span className="report-stat__label">messages</span>
            </li>
            <li className="report-stat">
              <span className="report-stat__value">{report.flagged}</span>
              <span className="report-stat__label">flagged</span>
            </li>
            <li className="report-stat">
              <span className="report-stat__value">{report.blocked}</span>
              <span className="report-stat__label">blocked</span>
            </li>
          </ul>
          <TrendBadge trendPct={report.trend_pct} />
        </>
      ) : (
        <p className="empty-state">No report data yet.</p>
      )}
    </section>
  )
}
