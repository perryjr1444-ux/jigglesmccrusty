"""Unit tests for the redactor utility."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from utils.redactor import redact, tokenize, restore, _stable_token


def test_stable_token_deterministic():
    """Test that stable_token generates the same token for the same input."""
    value = "test@example.com"
    token1 = _stable_token(value)
    token2 = _stable_token(value)
    assert token1 == token2
    assert token1.startswith("TOK_")


def test_stable_token_different_values():
    """Test that different values produce different tokens."""
    token1 = _stable_token("test1@example.com")
    token2 = _stable_token("test2@example.com")
    assert token1 != token2


def test_tokenize_function():
    """Test the public tokenize function."""
    value = "sensitive-data"
    token = tokenize(value)
    assert token.startswith("TOK_")
    
    # Test custom prefix
    custom_token = tokenize(value, prefix="CUSTOM_")
    assert custom_token.startswith("CUSTOM_")


def test_redact_email():
    """Test redacting email addresses."""
    text = "Contact us at support@example.com for help."
    redacted, token_map = redact(text)
    
    assert "support@example.com" not in redacted
    assert len(token_map) == 1
    assert "TOK_" in redacted
    
    # Verify token is stable
    token = list(token_map.keys())[0]
    assert token_map[token] == "support@example.com"


def test_redact_multiple_emails():
    """Test redacting multiple email addresses."""
    text = "Email alice@example.com or bob@test.org for info."
    redacted, token_map = redact(text)
    
    assert "alice@example.com" not in redacted
    assert "bob@test.org" not in redacted
    assert len(token_map) == 2


def test_redact_phone_number():
    """Test redacting phone numbers."""
    text = "Call me at 555-123-4567 today."
    redacted, token_map = redact(text)
    
    assert "555-123-4567" not in redacted
    assert len(token_map) == 1


def test_redact_ssn():
    """Test redacting SSN patterns."""
    text = "My SSN is 123-45-6789 for verification."
    redacted, token_map = redact(text)
    
    assert "123-45-6789" not in redacted
    assert len(token_map) == 1


def test_redact_mixed_pii():
    """Test redacting multiple types of PII in one text."""
    text = "Contact john@example.com at 555-123-4567. SSN: 123-45-6789"
    redacted, token_map = redact(text)
    
    assert "john@example.com" not in redacted
    assert "555-123-4567" not in redacted
    assert "123-45-6789" not in redacted
    assert len(token_map) == 3


def test_redact_custom_patterns():
    """Test redacting with custom patterns."""
    text = "API key: sk_test_123456789 and password: mySecretPass"
    patterns = {
        r"sk_test_\w+": "api_key",
        r"password:\s*\w+": "password",
    }
    redacted, token_map = redact(text, patterns=patterns)
    
    assert "sk_test_123456789" not in redacted
    assert "password: mySecretPass" not in redacted
    assert len(token_map) == 2


def test_redact_empty_text():
    """Test redacting empty text."""
    redacted, token_map = redact("")
    assert redacted == ""
    assert len(token_map) == 0


def test_redact_no_matches():
    """Test redacting text with no PII."""
    text = "This is just regular text with no sensitive information."
    redacted, token_map = redact(text)
    
    assert redacted == text
    assert len(token_map) == 0


def test_restore_redacted_text():
    """Test restoring original values from redacted text."""
    original = "Contact support@example.com for help at 555-123-4567."
    redacted, token_map = redact(original)
    restored = restore(redacted, token_map)
    
    assert restored == original


def test_restore_partial_tokens():
    """Test restoring when not all tokens are used."""
    redacted_text = "Hello TOK_abc123 world"
    token_map = {"TOK_abc123": "sensitive"}
    restored = restore(redacted_text, token_map)
    
    assert restored == "Hello sensitive world"


def test_redact_deterministic():
    """Test that redaction is deterministic across multiple calls."""
    text = "Email: test@example.com Phone: 555-1234"
    
    redacted1, token_map1 = redact(text)
    redacted2, token_map2 = redact(text)
    
    assert redacted1 == redacted2
    assert token_map1 == token_map2


def test_redact_case_insensitive():
    """Test that email redaction is case insensitive."""
    text = "Email: TEST@EXAMPLE.COM or test@example.com"
    redacted, token_map = redact(text)
    
    # Both emails should be redacted
    assert "TEST@EXAMPLE.COM" not in redacted
    assert "test@example.com" not in redacted
