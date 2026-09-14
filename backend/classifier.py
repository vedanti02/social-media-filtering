"""Message toxicity classifier.

Rule-based stand-in for a real model: scores text against a small weighted
keyword list and buckets the result into low/medium/high toxicity. Same
return shape (score + label) as a model-backed classifier would use, so this
can be swapped for toxic-bert later without touching callers.

TODO: plug in toxic-bert here (e.g. transformers pipeline "unitary/toxic-bert").
"""

# Toxicity keyword weights (0-1). Grouped loosely by severity; values are
# rough estimates for demo purposes, not a real harm-severity study.
TOXIC_TERMS: dict[str, float] = {
    # mild insults / name-calling
    "stupid": 0.15,
    "idiot": 0.15,
    "dumb": 0.15,
    "loser": 0.15,
    "shut up": 0.2,
    "ugly": 0.15,
    "freak": 0.2,

    # harassment / bullying
    "hate you": 0.35,
    "nobody likes you": 0.4,
    "worthless": 0.45,
    "no one wants you": 0.45,

    # threats / violence
    "kill you": 0.9,
    "kill yourself": 0.95,
    "hurt you": 0.7,
    "beat you up": 0.7,
    "come find you": 0.6,

    # sexual content
    "send nudes": 0.9,
    "send pics": 0.5,
    "nude pic": 0.85,
}

# Score thresholds for bucketing into a toxicity level.
MEDIUM_THRESHOLD = 0.35
HIGH_THRESHOLD = 0.7


def classify(text: str) -> dict:
    """Return a toxicity score and level ("low" | "medium" | "high") for text."""
    normalized = text.lower()

    score = sum(weight for term, weight in TOXIC_TERMS.items() if term in normalized)
    score = min(score, 1.0)

    if score >= HIGH_THRESHOLD:
        level = "high"
    elif score >= MEDIUM_THRESHOLD:
        level = "medium"
    else:
        level = "low"

    return {"score": round(score, 2), "label": level}
