"""Load and assemble the AskCBS knowledge base.

The corpus is small enough (~5k words) to pass entirely in the system prompt,
so there is no vector store here on purpose. If the corpus grows past roughly
40k words, swap this module for a retrieval step -- the rest of the app won't
need to change.
"""

from dataclasses import dataclass
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"


@dataclass(frozen=True)
class Source:
    """One knowledge file and how it should be described to the model."""

    filename: str
    label: str
    description: str


SOURCES = (
    Source(
        filename="campus_facts.md",
        label="CAMPUS & NYC FACTS",
        description=(
            "Buildings, floors, microwaves, hardware, logins, traditions, "
            "the evening shuttle, subway, housing, groceries, gym, health services."
        ),
    ),
    Source(
        filename="recruiting_clubs.md",
        label="CLUBS & RECRUITING PLAYBOOKS",
        description=(
            "The full club directory plus per-industry recruiting timelines and "
            "advice written by club co-presidents."
        ),
    ),
)


def load_sources(knowledge_dir: Path = KNOWLEDGE_DIR) -> list[tuple[Source, str]]:
    """Read every knowledge file. Raises if one is missing so failures are loud."""
    loaded = []
    for source in SOURCES:
        path = knowledge_dir / source.filename
        if not path.exists():
            raise FileNotFoundError(f"Knowledge file not found: {path}")
        loaded.append((source, path.read_text(encoding="utf-8")))
    return loaded


def build_corpus(knowledge_dir: Path = KNOWLEDGE_DIR) -> str:
    """Assemble all knowledge files into one delimited block for the system prompt."""
    parts = []
    for source, text in load_sources(knowledge_dir):
        parts.append(
            f"<document source=\"{source.label}\">\n"
            f"<about>{source.description}</about>\n\n"
            f"{text}\n"
            f"</document>"
        )
    return "\n\n".join(parts)


def corpus_stats(knowledge_dir: Path = KNOWLEDGE_DIR) -> dict[str, int]:
    """Word count per source, for the sidebar."""
    return {
        source.label: len(text.split())
        for source, text in load_sources(knowledge_dir)
    }
