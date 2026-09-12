// TODO: fetch with getAlerts(parentId) from ../api.js and store in state.
export default function Alerts() {
  const alerts = []

  return (
    <section>
      <h2>Alerts</h2>
      <ul>
        {alerts.map((alert) => (
          <li key={alert.id}>{alert.reason}</li>
        ))}
      </ul>
    </section>
  )
}
