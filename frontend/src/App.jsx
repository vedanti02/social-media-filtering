import { useState } from 'react'
import ComposeMessage from './pages/ComposeMessage.jsx'
import ChildInbox from './pages/ChildInbox.jsx'
import Alerts from './pages/Alerts.jsx'
import WeeklyReport from './pages/WeeklyReport.jsx'
import Blocklist from './pages/Blocklist.jsx'

// TODO: add routing (e.g. react-router) and auth; for now render all pages.
export default function App() {
  // Bumped after a message is sent, so the child inbox and the alert list
  // both pick up the new message without a manual page refresh.
  const [refreshKey, setRefreshKey] = useState(0)
  // Bumped after a sender is blocked/unblocked, so the Blocklist card
  // reflects a block made from the Alert popup without a manual refresh.
  const [blocklistKey, setBlocklistKey] = useState(0)

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

      <main className="app-shell">
        <section className="view-group view-group--child">
          <div className="view-group__header">
            <h2 className="view-group__title">📱 What Alex sees</h2>
            <p className="view-group__desc">The child's side — send a message, watch it get moderated.</p>
          </div>
          <div className="view-group__grid">
            <div className="view-group__col">
              <ComposeMessage onSent={() => setRefreshKey((k) => k + 1)} />
              <Blocklist refreshKey={blocklistKey} />
            </div>
            <ChildInbox refreshKey={refreshKey} />
          </div>
        </section>

        <section className="view-group">
          <div className="view-group__header">
            <h2 className="view-group__title">🛡️ Parent dashboard</h2>
            <p className="view-group__desc">What the parent sees — alerts, trends, and controls.</p>
          </div>
          <div className="view-group__grid">
            <Alerts refreshKey={refreshKey} onBlocked={() => setBlocklistKey((k) => k + 1)} />
            <WeeklyReport refreshKey={refreshKey} />
          </div>
        </section>
      </main>
    </div>
  )
}
