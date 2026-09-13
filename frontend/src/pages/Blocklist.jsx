// TODO: fetch blocked words, wire addBlockedWord / removeBlockedWord from ../api.js.
export default function Blocklist() {
  const words = []

  return (
    <section className="card">
      <div className="card__header">
        <div className="card__title">
          <span className="card__title-icon">🚫</span> Blocklist
        </div>
      </div>
      <p className="card__subtitle">Words and phrases to always flag, regardless of score.</p>

      {words.length === 0 ? (
        <div className="coming-soon">Blocklist management is coming soon.</div>
      ) : (
        <ul className="alert-list">
          {words.map((entry) => (
            <li key={entry.id} className="alert-card">
              {entry.word}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
