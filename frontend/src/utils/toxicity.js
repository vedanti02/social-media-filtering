// Mirrors MEDIUM_THRESHOLD / HIGH_THRESHOLD in backend/classifier.py, so a
// score displayed here gets the same low/medium/high bucket the backend used
// to decide what to do with the message. Keep these two in sync.
const MEDIUM_THRESHOLD = 0.35
const HIGH_THRESHOLD = 0.7

export function confidenceLevel(score) {
  if (score >= HIGH_THRESHOLD) return 'high'
  if (score >= MEDIUM_THRESHOLD) return 'medium'
  return 'low'
}

export function confidencePercent(score) {
  return Math.round(score * 100)
}
