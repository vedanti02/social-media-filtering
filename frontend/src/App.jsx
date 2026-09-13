import ComposeMessage from './pages/ComposeMessage.jsx'
import Alerts from './pages/Alerts.jsx'
import WeeklyReport from './pages/WeeklyReport.jsx'
import Blocklist from './pages/Blocklist.jsx'

// TODO: add routing (e.g. react-router) and auth; for now render all pages.
export default function App() {
  return (
    <div>
      <header className="app-header">
        <div className="app-header__inner">
          <div className="app-header__badge">🛡️</div>
          <div>
            <h1>Child Safety Messaging</h1>
            <p className="app-header__subtitle">
              Monitoring &amp; alerts dashboard for Alex's account
            </p>
          </div>
        </div>
      </header>

      <main className="app-main">
        <div className="app-main__col">
          <ComposeMessage />
          <Alerts />
        </div>
        <div className="app-main__col">
          <WeeklyReport />
          <Blocklist />
        </div>
      </main>
    </div>
  )
}
