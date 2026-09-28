// The backend stores UTC. SQLite drops the timezone, so the API may return a
// naive ISO string; treat anything without an offset as UTC.
export function parseUtc(iso) {
  return new Date(/[zZ]|[+-]\d\d:\d\d$/.test(iso) ? iso : `${iso}Z`)
}

export function relativeTime(iso) {
  const seconds = Math.max(0, Math.round((Date.now() - parseUtc(iso)) / 1000))
  const units = [
    ['day', 86400],
    ['hour', 3600],
    ['minute', 60],
  ]
  for (const [name, size] of units) {
    const value = Math.floor(seconds / size)
    if (value >= 1) return `${value} ${name}${value === 1 ? '' : 's'} ago`
  }
  return 'just now'
}
