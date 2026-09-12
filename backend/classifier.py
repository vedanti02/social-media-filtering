"""Message toxicity classifier."""


def classify(text: str) -> dict:
    """Return a toxicity score and label for the given text.

    TODO: plug in toxic-bert here (e.g. transformers pipeline "unitary/toxic-bert").
    """
    return {"score": 0.0, "label": "safe"}
