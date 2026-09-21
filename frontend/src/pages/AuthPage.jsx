import { useState } from 'react'
import { login, setToken, signup } from '../api.js'

export default function AuthPage({ onAuth }) {
  const [mode, setMode] = useState('login') // 'login' | 'signup'
  const [form, setForm] = useState({ name: '', childName: '', email: '', password: '' })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const isSignup = mode === 'signup'

  function update(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }))
  }

  function switchMode() {
    setMode(isSignup ? 'login' : 'signup')
    setError(null)
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (submitting) return
    setSubmitting(true)
    setError(null)
    try {
      const session = isSignup ? await signup(form) : await login(form.email, form.password)
      setToken(session.token)
      onAuth(session)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-shell">
      <section className="card auth-card">
        <div className="card__header">
          <div className="card__title">
            <span className="card__title-icon">🛡️</span> {isSignup ? 'Create your account' : 'Log in'}
          </div>
        </div>
        <p className="card__subtitle">
          {isSignup
            ? 'A parent account, with a profile for the child you want to protect.'
            : 'Log in to see your child’s activity and alerts.'}
        </p>

        <form onSubmit={handleSubmit}>
          {isSignup && (
            <>
              <div className="field">
                <label className="field__label" htmlFor="auth-name">Your name</label>
                <input id="auth-name" type="text" value={form.name} onChange={update('name')} required />
              </div>
              <div className="field">
                <label className="field__label" htmlFor="auth-child">Child’s name</label>
                <input id="auth-child" type="text" value={form.childName} onChange={update('childName')} required />
              </div>
            </>
          )}
          <div className="field">
            <label className="field__label" htmlFor="auth-email">Email</label>
            <input
              id="auth-email"
              type="email"
              autoComplete="email"
              value={form.email}
              onChange={update('email')}
              required
            />
          </div>
          <div className="field">
            <label className="field__label" htmlFor="auth-password">Password</label>
            <input
              id="auth-password"
              type="password"
              autoComplete={isSignup ? 'new-password' : 'current-password'}
              minLength={isSignup ? 8 : undefined}
              value={form.password}
              onChange={update('password')}
              required
            />
            {isSignup && <span className="field__hint">At least 8 characters.</span>}
          </div>
          <button className="btn" type="submit" disabled={submitting}>
            {submitting ? 'Please wait…' : isSignup ? 'Create account' : 'Log in'}
          </button>
        </form>

        {error && <p className="error-banner" role="alert">{error}</p>}

        <p className="auth-switch">
          {isSignup ? 'Already have an account?' : 'New here?'}{' '}
          <button type="button" className="link-btn" onClick={switchMode}>
            {isSignup ? 'Log in' : 'Create an account'}
          </button>
        </p>
      </section>
    </div>
  )
}
