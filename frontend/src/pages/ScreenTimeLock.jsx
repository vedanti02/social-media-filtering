import { useCallback, useEffect, useRef, useState } from 'react'
import { getScreenTime, screenTimeHeartbeat } from '../api.js'

const HEARTBEAT_MS = 60_000

// The "Track usage" + "Enforce limit" cards from the board. Sends a heartbeat
// on load, once a minute, and whenever the tab comes back into view -- the
// backend credits at most one minute per 50s and decides whether the child
// is locked out, so reloading the page can't dodge the timer. While the tab
// is hidden it only reads the status. Heartbeats keep going while locked, so
// the screen unlocks by itself when the allowed window opens.
//
// Note: parent and child share one page in this demo, so time on the
// dashboard counts as the child's screen time.
//
// Returns [status, applySaved, loadError]; status is null until the first
// load. If the status can't be loaded the child's screens stay visible
// (fail open).
export function useScreenTime(childId) {
  const [status, setStatus] = useState(null)
  const [loadError, setLoadError] = useState(null)
  // Bumped on every save, so a heartbeat that was already in flight can't
  // land afterwards and overwrite the new rules with the old ones.
  const generation = useRef(0)

  useEffect(() => {
    let cancelled = false

    function tick() {
      const started = generation.current
      const visible = document.visibilityState === 'visible'
      ;(visible ? screenTimeHeartbeat(childId) : getScreenTime(childId))
        .then((data) => {
          if (!cancelled && started === generation.current) setStatus(data)
        })
        .catch((err) => {
          if (!cancelled) setLoadError(err.message)
        })
    }

    function handleVisibility() {
      if (document.visibilityState === 'visible') tick()
    }

    tick()
    const timer = setInterval(tick, HEARTBEAT_MS)
    document.addEventListener('visibilitychange', handleVisibility)
    return () => {
      cancelled = true
      clearInterval(timer)
      document.removeEventListener('visibilitychange', handleVisibility)
    }
  }, [childId])

  const applySaved = useCallback((data) => {
    generation.current += 1
    setStatus(data)
  }, [])

  return [status, applySaved, loadError]
}

// "⏱ 37 min left today" -- only shown when a daily limit is set.
export function ScreenTimePill({ status }) {
  if (!status || status.locked || status.minutes_remaining == null) return null
  return <span className="screen-time-pill">⏱ {status.minutes_remaining} min left today</span>
}

// Shown in place of the child's screens while they're locked out.
export default function ScreenTimeLock({ status, childName }) {
  const outsideHours = status.lock_reason === 'outside_hours'
  return (
    <section className="card lock-screen" role="status">
      <div className="lock-screen__icon">{outsideHours ? '🌙' : '⏰'}</div>
      <h3 className="lock-screen__title">
        {outsideHours ? 'Screen time is over' : "Time's up for today"}
      </h3>
      <p className="lock-screen__desc">
        {outsideHours
          ? `${childName} can use the app again at ${status.allowed_start}.`
          : `${childName} has used all ${status.daily_limit_minutes} minutes for today. The timer resets at midnight.`}
      </p>
    </section>
  )
}
