import hashlib
import base64
import re
from typing import Tuple, Dict

_TOKEN_PREFIX = "TOK_"


def _stable_token(value: str) -> str:
    """Deterministic token – same input always yields same token."""
    digest = hashlib.sha256(value.encode()).digest()
    b64 = base64.urlsafe_b64encode(digest[:9]).decode()  # ~12 chars
    return f"{_TOKEN_PREFIX}{b64}"


def redact(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Scan for email addresses, phone numbers and generic secrets.
    Returns (redacted_text, map[token] = original_value).
    """
    token_map = {}

    # Very simple regexes – replace with more exhaustive ones as needed
    patterns = {
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}": "email",
        r"\b\d{3}[-.\s]??\d{2}[-.\s]??\d{4}\b": "ssn",  # US SSN pattern
        r"\b(?:\+?\d{1,3})?[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b": "phone",
    }

    def repl(match):
        val = match.group(0)
        token = _stable_token(val)
        token_map[token] = val
        return token

    redacted = text
    for regex in patterns.keys():
        redacted = re.sub(regex, repl, redacted, flags=re.IGNORECASE)

    return redacted, token_map
