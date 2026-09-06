"""Log the questions people ask, so gaps in the knowledge base become visible.

This is the feedback loop: after a week of real use, `questions.csv` tells you
what students actually wanted to know and where AskCBS had nothing to say.

Caveat worth knowing: Streamlit Community Cloud has an ephemeral filesystem, so
this log is wiped whenever the app restarts or redeploys. That's fine for an
early read on usage. To keep logs permanently, swap `_append` for a write to a
Google Sheet, Supabase table, or similar -- nothing else needs to change.
"""

import csv
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent.parent / "questions.csv"
FIELDS = ("timestamp", "question", "answered")

# Phrases the system prompt tells the model to use when the corpus falls short.
# Crude, but good enough to flag coverage gaps for review.
_GAP_MARKERS = (
    "don't have",
    "do not have",
    "isn't covered",
    "is not covered",
    "not in my",
    "check with",
    "i'd recommend reaching out",
)


def looks_unanswered(answer: str) -> bool:
    lowered = answer.lower()
    return any(marker in lowered for marker in _GAP_MARKERS)


def log_question(question: str, answer: str, log_path: Path = LOG_PATH) -> None:
    """Record one exchange. Never let a logging failure break the chat."""
    try:
        is_new = not log_path.exists()
        with log_path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            if is_new:
                writer.writeheader()
            writer.writerow(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "question": question,
                    "answered": "no" if looks_unanswered(answer) else "yes",
                }
            )
    except OSError:
        pass


def read_log(log_path: Path = LOG_PATH) -> list[dict]:
    if not log_path.exists():
        return []
    with log_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
