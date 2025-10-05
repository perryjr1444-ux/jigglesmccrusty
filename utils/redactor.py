import hashlib
import base64
import re
from typing import Tuple, Dict, Optional

_TOKEN_PREFIX = "TOK_"


def _stable_token(value: str, prefix: Optional[str] = None) -> str:
    """
    Deterministic token – same input always yields same token.
    
    Args:
        value: The value to tokenize
        prefix: Optional prefix for the token (defaults to TOK_)
    
    Returns:
        A stable, deterministic token string
    """
    digest = hashlib.sha256(value.encode()).digest()
    b64 = base64.urlsafe_b64encode(digest[:9]).decode()  # ~12 chars
    pfx = prefix or _TOKEN_PREFIX
    return f"{pfx}{b64}"


def tokenize(value: str, prefix: Optional[str] = None) -> str:
    """
    Generate a deterministic token for a given value.
    Same input always produces the same token.
    
    Args:
        value: The value to tokenize
        prefix: Optional prefix for the token
    
    Returns:
        A deterministic token string
    """
    return _stable_token(value, prefix)


def redact(text: str, patterns: Optional[Dict[str, str]] = None) -> Tuple[str, Dict[str, str]]:
    """
    Scan for email addresses, phone numbers and generic secrets.
    Returns (redacted_text, map[token] = original_value).
    
    Args:
        text: The text to redact
        patterns: Optional custom patterns dict {regex: pattern_name}
    
    Returns:
        Tuple of (redacted_text, token_map)
    """
    token_map = {}

    # Default patterns – replace with more exhaustive ones as needed
    default_patterns = {
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}": "email",
        r"\b\d{3}[-.\s]??\d{2}[-.\s]??\d{4}\b": "ssn",  # US SSN pattern
        r"\b(?:\+?\d{1,3})?[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b": "phone",
    }
    
    patterns_to_use = patterns if patterns is not None else default_patterns

    def repl(match):
        val = match.group(0)
        token = _stable_token(val)
        token_map[token] = val
        return token

    redacted = text
    for regex in patterns_to_use.keys():
        redacted = re.sub(regex, repl, redacted, flags=re.IGNORECASE)

    return redacted, token_map


def restore(redacted_text: str, token_map: Dict[str, str]) -> str:
    """
    Restore original values from redacted text using the token map.
    
    Args:
        redacted_text: Text with tokens
        token_map: Map of token -> original_value
    
    Returns:
        Text with original values restored
    """
    restored = redacted_text
    for token, original in token_map.items():
        restored = restored.replace(token, original)
    return restored
