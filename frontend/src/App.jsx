import Alerts from './pages/Alerts.jsx'
import WeeklyReport from './pages/WeeklyReport.jsx'
import Blocklist from './pages/Blocklist.jsx'

// TODO: add routing (e.g. react-router) and auth; for now render all pages.
export default function App() {
  return (
    <main>
      <h1>Child Safety Messaging</h1>
      <Alerts />
      <WeeklyReport />
      <Blocklist />
    </main>
  )
}
