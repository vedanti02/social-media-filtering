// TODO: fetch with getWeeklyReport(childId) from ../api.js and store in state.
export default function WeeklyReport() {
  const rows = []

  return (
    <section>
      <h2>Weekly Report</h2>
      <ul>
        {rows.map((row) => (
          <li key={row.id}>{row.label}</li>
        ))}
      </ul>
    </section>
  )
}
