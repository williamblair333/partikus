"""
Minimal Anthropic API client using only stdlib (no external deps).

Uses the system CA bundle at /etc/ssl/certs/ca-certificates.crt so it works
inside FreeCAD's AppImage environment.
"""

import json
import os
import ssl
import urllib.error
import urllib.request

_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
_API_VERSION   = "2023-06-01"

_CA_PATHS = [
    "/etc/ssl/certs/ca-certificates.crt",
    "/usr/lib/ssl/certs/ca-certificates.crt",
    "/etc/ssl/cert.pem",
]


def _ssl_context():
    for ca in _CA_PATHS:
        if os.path.exists(ca):
            return ssl.create_default_context(cafile=ca)
    return ssl.create_default_context()


def call(messages, system="", model="claude-sonnet-4-6", max_tokens=4096, timeout=60):
    """
    POST to the Anthropic Messages API and return the parsed response dict.

    Raises:
        RuntimeError: ANTHROPIC_API_KEY not set
        RuntimeError: HTTP error from the API
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY environment variable is not set. "
            "Export it before using the partikus.ai module."
        )

    payload = {"model": model, "max_tokens": max_tokens, "messages": messages}
    if system:
        payload["system"] = system

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        _ANTHROPIC_URL,
        data=data,
        headers={
            "x-api-key": api_key,
            "anthropic-version": _API_VERSION,
            "content-type": "application/json",
        },
        method="POST",
    )

    ctx = _ssl_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Anthropic API error {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error reaching Anthropic API: {e.reason}") from e


def text_from(response):
    """Extract the first text content block from an API response dict."""
    for block in response.get("content", []):
        if block.get("type") == "text":
            return block["text"]
    return ""
