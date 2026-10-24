"""Privacy-validator regression tests: metadata identifiers != personal telephone numbers."""
import importlib.util
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/"scripts"/"validate_release.py"
SPEC=importlib.util.spec_from_file_location("flowminute_release_validator",SCRIPT)
MODULE=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

def candidate(description="Legitimate public educational description"):
    return {"title":"FlowMinute Lab AI news", "description":description,
       "publish_at_ist":"2026-10-24T11:00:00+05:30",
       "publish_at_utc":"2026-10-24T05:30:00Z",
       "candidate_sha256":"7bd6319297fba469709467ac3416fd32be1a5efa9f25ee1d2c8c1dd016050fb9",
       "captions":[{"start":.5,"end":2.0,"text":"Model choice"}]}

def test_approved_technical_token_formats_are_not_pii():
    assert MODULE.validate(candidate(),[],editorial_only=False)==[]

def test_real_personal_phone_remains_blocked():
    errors=MODULE.validate(candidate("Call me on +91 98765 43210"),[],editorial_only=False)
    assert any("phone-like" in err for err in errors)

def test_embedded_email_remains_blocked():
    errors=MODULE.validate(candidate("Write to personal@example.com"),[],editorial_only=False)
    assert any("email" in err for err in errors)

def test_technical_tokens_do_not_disable_secret_detection():
    errors=MODULE.validate(candidate("api_key:abcdef12345678"),[],editorial_only=False)
    assert any("credential" in err for err in errors)
