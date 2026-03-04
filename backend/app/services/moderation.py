from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Kind = Literal["submission", "comment", "topic"]


@dataclass
class ModerationError(Exception):
    code: str
    message: str

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return self.message


# IMPORTANT: populate these lists in your deployment with the terms / phrases
# you consider hateful. They are intentionally left as placeholders here.
# Example (non-production): {"bad-slur-token"} – replace with real entries
# in a private, non-checked-in config.
HATEFUL_TERMS: set[str] = set()

# Phrases that clearly dehumanize a group, e.g. "<group> are animals".
# Keep these high-signal and conservative to reduce false positives.
DEHUMANIZING_PHRASES: set[str] = {
    # example placeholder; replace with real dehumanizing phrases if desired
    # "are animals",
    # "are vermin",
    # "are subhuman",
}


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def is_hateful(text: str) -> bool:
    """
    Return True if text matches our hate-only firewall:
    - contains a term from HATEFUL_TERMS, or
    - contains a simple dehumanizing phrase from DEHUMANIZING_PHRASES.
    """
    if not text:
        return False

    norm = _normalize(text)

    # Fast path: exact hateful terms (simple substring scan)
    for term in HATEFUL_TERMS:
        if term and term in norm:
            return True

    # Dehumanizing phrases (generic patterns; you can tune these or extend with regex)
    for phrase in DEHUMANIZING_PHRASES:
        if phrase and phrase in norm:
            return True

    return False


def ensure_not_hateful(text: str, *, kind: Kind) -> None:
    """
    Raise ModerationError if the provided text is considered hateful.

    kind is for context only (submission/comment/topic) so you can vary rules later.
    """
    if is_hateful(text):
        raise ModerationError(
            code="hateful_content",
            message="Message blocked: hateful or dehumanizing language is not allowed in this arena.",
        )

