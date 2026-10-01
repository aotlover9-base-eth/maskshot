import pytest
from maskshot.detector import SecretDetector

def test_detect_openai_key():
    detector = SecretDetector()
    text = "Here is my key: sk-proj-1234567890abcdef1234567890 for testing."
    matches = detector.scan_text(text)
    assert any(m.secret_type == "OpenAI API Key" for m in matches)
    assert "sk-proj-1234567890abcdef1234567890" in [m.value for m in matches]

def test_detect_github_pat():
    detector = SecretDetector()
    text = "export GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz0123456789"
    matches = detector.scan_text(text)
    assert any(m.secret_type == "GitHub Personal Access Token" for m in matches)

def test_detect_aws_access_key():
    detector = SecretDetector()
    text = "aws_access_key_id = AKIAIOSFODNN7EXAMPLE"
    matches = detector.scan_text(text)
    assert any(m.secret_type == "AWS Access Key ID" for m in matches)

def test_detect_database_url():
    detector = SecretDetector()
    text = "DATABASE_URL=postgres://user:pass123@db.prod.internal:5432/main"
    matches = detector.scan_text(text)
    assert any(m.secret_type == "Database Connection String" for m in matches)

def test_detect_email():
    detector = SecretDetector()
    text = "Reach me at contact@hyperdev.com for inquiries"
    matches = detector.scan_text(text)
    assert any(m.secret_type == "Email Address" for m in matches)

def test_detect_phone_number():
    detector = SecretDetector()
    text = "Call me at +91 9876543210 or 9123456780"
    matches = detector.scan_text(text)
    assert any(m.secret_type == "Phone Number (IN/Intl)" for m in matches)

def test_detect_ipv4():
    detector = SecretDetector()
    text = "Target server is at 192.168.1.105:8080"
    matches = detector.scan_text(text)
    assert any(m.secret_type == "IPv4 Address" for m in matches)

def test_benign_code_no_false_positive():
    detector = SecretDetector()
    text = "def calculate_total(items):\n    return sum(item.price for item in items)"
    matches = detector.scan_text(text)
    assert len(matches) == 0

def test_custom_keyword():
    detector = SecretDetector()
    detector.add_keyword_rule("ProjectNebula")
    text = "Deploying ProjectNebula to production"
    matches = detector.scan_text(text)
    assert len(matches) == 1
    assert matches[0].value == "ProjectNebula"
