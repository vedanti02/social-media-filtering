import { useEffect, useState } from 'react'
import { addBlockedWord, getBlockedSenders, getBlockedWords, removeBlockedWord, unblockSender } from '../api.js'

export default function Blocklist({ childId, childName, refreshKey }) {
  const [senders, setSenders] = useState([])
  const [words, setWords] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [newWord, setNewWord] = useState('')
  const [addingWord, setAddingWord] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    Promise.all([getBlockedSenders(childId), getBlockedWords()])
      .then(([senderData, wordData]) => {
        if (!cancelled) {
          setSenders(senderData)
          setWords(wordData)
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [refreshKey])

  async function handleUnblock(sender) {
    // Optimistic remove; roll back if the request fails.
    setSenders((prev) => prev.filter((s) => s.id !== sender.id))
    try {
      await unblockSender(sender.id)
    } catch (err) {
      setSenders((prev) => [...prev, sender].sort((a, b) => a.id - b.id))
      setError(err.message)
    }
  }

  async function handleAddWord(event) {
    event.preventDefault()
    const word = newWord.trim()
    if (!word || addingWord) return
    setAddingWord(true)
    setError(null)
    try {
      const created = await addBlockedWord(word)
      setWords((prev) => (prev.some((w) => w.id === created.id) ? prev : [...prev, created]))
      setNewWord('')
    } catch (err) {
      setError(err.message)
    } finally {
      setAddingWord(false)
    }
  }

  async function handleRemoveWord(entry) {
    setWords((prev) => prev.filter((w) => w.id !== entry.id))
    try {
      await removeBlockedWord(entry.word)
    } catch (err) {
      setWords((prev) => [...prev, entry].sort((a, b) => a.id - b.id))
      setError(err.message)
    }
  }

  return (
    <section className="card">
      <div className="card__header">
        <div className="card__title">
          <span className="card__title-icon">🚫</span> Blocklist
        </div>
        {!loading && senders.length > 0 && (
          <span className="card__count">{senders.length} blocked</span>
        )}
      </div>
      <p className="card__subtitle">
        Senders blocked for {childName} — every future message from them is auto-flagged.
      </p>

      {error && <p className="error-banner" role="alert">Something went wrong: {error}</p>}
      {loading ? (
        <p className="loading-state">Loading…</p>
      ) : senders.length === 0 ? (
        <p className="empty-state">No one is blocked yet.</p>
      ) : (
        <ul className="blocklist-list">
          {senders.map((sender) => (
            <li key={sender.id} className="blocklist-row">
              <span className="blocklist-row__name">{sender.sender}</span>
              <button className="btn btn--ghost btn--sm" onClick={() => handleUnblock(sender)}>
                Unblock
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="section-gap">
        <p className="card__subtitle">
          Words that automatically mark a message high-toxicity, regardless of who sent it.
        </p>
        <form className="inline-form" onSubmit={handleAddWord}>
          <input
            type="text"
            value={newWord}
            onChange={(e) => setNewWord(e.target.value)}
            placeholder="Add a word or phrase…"
            aria-label="New blocked word"
          />
          <button className="btn btn--sm" type="submit" disabled={addingWord || !newWord.trim()}>
            Add
          </button>
        </form>

        {!loading && words.length === 0 ? (
          <p className="empty-state">No words blocked yet.</p>
        ) : (
          <ul className="blocklist-list">
            {words.map((entry) => (
              <li key={entry.id} className="blocklist-row">
                <span className="blocklist-row__name">{entry.word}</span>
                <button className="btn btn--ghost btn--sm" onClick={() => handleRemoveWord(entry)}>
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
