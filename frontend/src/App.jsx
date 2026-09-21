import { useEffect, useState } from 'react'
import { clearToken, getMe, getToken, logout, setUnauthorizedHandler } from './api.js'
import AuthPage from './pages/AuthPage.jsx'
import ComposeMessage from './pages/ComposeMessage.jsx'
import ChildInbox from './pages/ChildInbox.jsx'
import Alerts from './pages/Alerts.jsx'
import WeeklyReport from './pages/WeeklyReport.jsx'
import Blocklist from './pages/Blocklist.jsx'
import NotificationSettings from './pages/NotificationSettings.jsx'

// TODO: add routing (e.g. react-router); for now render all pages behind a login.
export default function App() {
  // The logged-in parent + their child, from /auth/me or the login/signup
  // response. null means logged out.
  const [user, setUser] = useState(null)
  // True while we check a stored token on first load, so the login form
  // doesn't flash before the dashboard for someone who's already logged in.
  const [checking, setChecking] = useState(() => Boolean(getToken()))
  // Bumped after a message is sent, so the child inbox and the alert list
  // both pick up the new message without a manual page refresh.
  const [refreshKey, setRefreshKey] = useState(0)
  // Bumped after a sender is blocked/unblocked, so the Blocklist card
  // reflects a block made from the Alert popup without a manual refresh.
  const [blocklistKey, setBlocklistKey] = useState(0)

  useEffect(() => {
    setUnauthorizedHandler(() => setUser(null))
    if (!getToken()) return
    getMe()
      .then(setUser)
      .catch(() => clearToken())
      .finally(() => setChecking(false))
  }, [])

  async function handleLogout() {
    await logout().catch(() => {})
    clearToken()
    setUser(null)
  }

  if (checking) return null
  if (!user) return <AuthPage onAuth={setUser} />

  return (
    <div>
      <header className="app-header">
        <div className="app-header__inner">
          <div className="app-header__badge">🛡️</div>
          <div>
            <h1>Child Safety Messaging</h1>
            <p className="app-header__subtitle">
              Monitoring &amp; alerts dashboard for {user.child_name}'s account
            </p>
          </div>
          <div className="app-header__user">
            <span className="app-header__user-name">{user.parent_name}</span>
            <button className="btn btn--ghost btn--sm" type="button" onClick={handleLogout}>
              Log out
            </button>
          </div>
        </div>
      </header>

      <main className="app-shell">
        <section className="view-group view-group--child">
          <div className="view-group__header">
            <h2 className="view-group__title">📱 What {user.child_name} sees</h2>
            <p className="view-group__desc">The child's side — send a message, watch it get moderated.</p>
          </div>
          <div className="view-group__grid">
            <div className="view-group__col">
              <ComposeMessage childId={user.child_id} onSent={() => setRefreshKey((k) => k + 1)} />
              <Blocklist childId={user.child_id} childName={user.child_name} refreshKey={blocklistKey} />
            </div>
            <ChildInbox childId={user.child_id} childName={user.child_name} refreshKey={refreshKey} />
          </div>
        </section>

        <section className="view-group">
          <div className="view-group__header">
            <h2 className="view-group__title">🛡️ Parent dashboard</h2>
            <p className="view-group__desc">What the parent sees — alerts, trends, and controls.</p>
          </div>
          <div className="view-group__grid">
            <Alerts
              parentId={user.parent_id}
              childId={user.child_id}
              childName={user.child_name}
              refreshKey={refreshKey}
              onBlocked={() => setBlocklistKey((k) => k + 1)}
            />
            <WeeklyReport childId={user.child_id} childName={user.child_name} refreshKey={refreshKey} />
            <NotificationSettings parentId={user.parent_id} />
          </div>
        </section>
      </main>
    </div>
  )
}
