"""LLM transport regression tests.

OmniRoute combos carry their own provider-connection auth server-side, so the
client must never attach a per-request session id (x-opencode-session). It
may still send an optional OMNIROUTE_API_KEY Bearer token.
"""
from app.utils.managers.ai_assistant import AIAssistant


def test_client_never_sends_session_header(app, monkeypatch):
    # Even an explicit session id env var must be ignored by the client.
    monkeypatch.setenv("OMNIROUTE_SESSION_ID", "ses_fake-for-probe-1234567890")
    assistant = AIAssistant()
    headers = assistant.client.default_headers
    assert "x-opencode-session" not in headers


def test_client_bearer_propagates_from_env(app, monkeypatch):
    monkeypatch.setenv("OMNIROUTE_API_KEY", "my-test-key")
    assistant = AIAssistant()
    assert assistant.client.auth_headers.get("Authorization") == "Bearer my-test-key"


def test_client_survives_without_api_key(app, monkeypatch):
    monkeypatch.delenv("OMNIROUTE_API_KEY", raising=False)
    assistant = AIAssistant()
    assert assistant.client.auth_headers.get("Authorization") == "Bearer not-needed"