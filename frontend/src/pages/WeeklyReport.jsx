// TODO: fetch with getWeeklyReport(childId) from ../api.js and store in state.
export default function WeeklyReport() {
  const rows = []

  return (
    <section className="card">
      <div className="card__header">
        <div className="card__title">
          <span className="card__title-icon">📊</span> Weekly Report
        </div>
      </div>
      <p className="card__subtitle">A summary of messages, flags, and blocks from the last 7 days.</p>

      {rows.length === 0 ? (
        <div className="coming-soon">Weekly reports are coming soon.</div>
      ) : (
        <ul className="alert-list">
          {rows.map((row) => (
            <li key={row.id} className="alert-card">
              {row.label}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
