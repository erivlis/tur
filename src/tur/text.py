"""
src/tur/text.py - Canonical Text Processing, Tokenization, and Regex Substrate.
"""
from __future__ import annotations

import functools
import re

# Canonical compiled regular expression patterns
WORD_RE: re.Pattern[str] = re.compile(r'\w+')
TOKEN_RE: re.Pattern[str] = re.compile(r'\w+|[^\w\s]', re.UNICODE)
SAFE_IDENTIFIER_RE: re.Pattern[str] = re.compile(r'^[a-zA-Z0-9_.-]+$')
SESSION_ID_RE: re.Pattern[str] = re.compile(r'^[a-zA-Z0-9_-]+$')
SNAKE_IDENTIFIER_RE: re.Pattern[str] = re.compile(r'^[a-z0-9_]+$')
QUERY_DELIMITER_RE: re.Pattern[str] = re.compile(r'[^a-zA-Z0-9_\-]+')


def tokenize_words(text: str) -> list[str]:
    """
    Extracts alphanumeric words from text.
    Standardized tokenizer for keyword overlap and graph seed discovery.
    """
    if not text:
        return []
    return WORD_RE.findall(text)


def tokenize_approx(text: str) -> list[str]:
    """
    Approximates subword BPE tokenization by splitting alphanumeric words
    and punctuation into individual atomic tokens.
    """
    if not text:
        return []
    return TOKEN_RE.findall(text)


def tokenize_query(query: str, min_length: int = 2) -> list[str]:
    """
    Normalizes and extracts alphanumeric query tokens for semantic recall and
    HippoRAG Personalized PageRank seed activation.
    """
    if not query:
        return []
    query_lower = query.lower().strip()
    return [t for t in QUERY_DELIMITER_RE.split(query_lower) if len(t) >= min_length]


def is_safe_identifier(value: str) -> bool:
    """Validates that a string contains only safe alphanumeric, underscore, dot, or hyphen characters."""
    if not value:
        return False
    return bool(SAFE_IDENTIFIER_RE.match(value))


def is_session_identifier(value: str) -> bool:
    """Validates session identifier syntax."""
    if not value:
        return False
    return bool(SESSION_ID_RE.match(value))


def is_snake_identifier(value: str) -> bool:
    """Validates snake_case identifiers (used for edge types and canonical node labels)."""
    if not value:
        return False
    return bool(SNAKE_IDENTIFIER_RE.match(value))


@functools.lru_cache(maxsize=32)
def get_entropy_pattern(min_length: int) -> re.Pattern[str]:
    """
    Returns a memoized compiled regex pattern for detecting high-entropy token candidates
    of at least `min_length` characters.
    """
    return re.compile(rf'[A-Za-z0-9_\-\+/=]{{{min_length},}}')
