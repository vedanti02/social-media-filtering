// TODO: fetch blocked words, wire addBlockedWord / removeBlockedWord from ../api.js.
export default function Blocklist() {
  const words = []

  return (
    <section>
      <h2>Blocklist</h2>
      <ul>
        {words.map((entry) => (
          <li key={entry.id}>{entry.word}</li>
        ))}
      </ul>
    </section>
  )
}
