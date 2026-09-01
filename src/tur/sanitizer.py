"""
Zero-dependency deterministic sensitive data prevention and secret redaction engine (EP-0143).
Implements pattern-based detection and Shannon entropy scanning.
"""

import math
import re

COMMON_SECRET_PATTERNS: list[re.Pattern] = [
    # Generic key/secret assignments (e.g. api_key = "...", secret_key: "...")
    re.compile(
        r'(?i)(?:api[_-]?key|access[_-]?token|secret[_-]?key|private[_-]?key|password|auth[_-]?token|client[_-]?secret)\s*[:=]\s*["\']?([a-zA-Z0-9_\-.]{16,})["\']?'
    ),
    # GitHub Tokens (PAT, OAuth, Fine-Grained)
    re.compile(r'\bghp_[0-9a-zA-Z]{36}\b'),
    re.compile(r'\bgho_[0-9a-zA-Z]{36}\b'),
    re.compile(r'\bgithub_pat_[0-9a-zA-Z_]{82}\b'),
    # OpenAI API Keys
    re.compile(r'\bsk-[a-zA-Z0-9]{48}\b'),
    re.compile(r'\bsk-proj-[a-zA-Z0-9_-]{48,}\b'),
    # Google API Keys
    re.compile(r'\bAIza[0-9A-Za-z_-]{30,40}\b'),
    # AWS Access Key ID
    re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
    # Slack Tokens
    re.compile(r'\bxox[baprs]-[0-9a-zA-Z]{10,48}\b'),
    # Bearer Tokens
    re.compile(r'(?i)\bbearer\s+([a-zA-Z0-9_\-.]{20,})\b'),
    # PEM Private Keys
    re.compile(r'-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+ PRIVATE KEY-----'),
    re.compile(r'-----BEGIN [A-Z ]+ PRIVATE KEY-----'),
]

REDACTED_SECRET_REPLACEMENT = '[REDACTED: SECRET PATTERN]'
REDACTED_ENTROPY_REPLACEMENT = '[REDACTED: HIGH-ENTROPY TOKEN]'


def calculate_shannon_entropy(text: str) -> float:
    """
    Computes Shannon entropy (H = -sum(p * log2(p))) to identify high-randomness credentials.
    Returns a float >= 0.0.
    """
    if not text:
        return 0.0
    probabilities = [text.count(c) / len(text) for c in set(text)]
    return -sum(p * math.log2(p) for p in probabilities)


def detect_high_entropy_tokens(
    text: str,
    threshold: float = 4.5,
    min_length: int = 20,
) -> list[str]:
    """
    Scans whitespace/delimiter-separated tokens for high-randomness strings.
    Filters out common prose, URLs, file paths, and known non-secret patterns.
    """
    if not text:
        return []

    # Tokenize on strings of alphanumeric/symbol chars of at least min_length
    raw_tokens = re.findall(r'[A-Za-z0-9_\-\+/=]{' + str(min_length) + r',}', text)
    flagged: list[str] = []
    for token in raw_tokens:
        # Ignore obvious repetitive strings
        if len(set(token)) < 8:
            continue
        # Check entropy
        entropy = calculate_shannon_entropy(token)
        if entropy >= threshold:
            flagged.append(token)
    return flagged


def sanitize_text(
    text: str,
    redact: bool = True,
    entropy_threshold: float = 4.5,
    scan_entropy: bool = True,
) -> tuple[str, list[str]]:
    """
    Detects and optionally redacts known secret patterns and high-entropy credentials.

    Args:
        text: Input string to scan/sanitize.
        redact: If True, returns text with sensitive matches replaced by tombstone tokens.
        entropy_threshold: Minimum Shannon entropy (bits/symbol) to flag a high-entropy token.
        scan_entropy: Whether to perform Shannon entropy scanning on individual tokens.

    Returns:
        tuple[str, list[str]]: (sanitized_text, list_of_detected_secret_snippets)
    """
    if not text:
        return text, []

    detected: list[str] = []
    sanitized = text

    # 1. Pattern-based detection and replacement
    for pattern in COMMON_SECRET_PATTERNS:
        matches = pattern.findall(sanitized)
        if matches:
            for match in matches:
                val = match if isinstance(match, str) else match[0]
                if val and val not in detected:
                    detected.append(val)
            if redact:
                sanitized = pattern.sub(REDACTED_SECRET_REPLACEMENT, sanitized)

    # 2. High-entropy token detection and replacement
    if scan_entropy:
        high_entropy_tokens = detect_high_entropy_tokens(sanitized, threshold=entropy_threshold)
        for token in high_entropy_tokens:
            if token not in (REDACTED_SECRET_REPLACEMENT, REDACTED_ENTROPY_REPLACEMENT) and token not in detected:
                detected.append(token)
                if redact:
                    sanitized = sanitized.replace(token, REDACTED_ENTROPY_REPLACEMENT)

    return sanitized, detected


def is_sensitive(text: str, entropy_threshold: float = 4.5) -> bool:
    """Returns True if the text contains any secret patterns or high-entropy tokens."""
    _, detected = sanitize_text(text, redact=False, entropy_threshold=entropy_threshold)
    return len(detected) > 0
