from __future__ import annotations

from pathlib import Path

import requests

from component_radar.http import DEFAULT_HEADERS, HttpClient, probable_blocked_html, save_no_results_html


class DummySession:
    def __init__(self):
        self.headers = {}
        self.calls = []
        self.response = None

    def get(self, url, timeout=None, headers=None):
        self.calls.append({"url": url, "timeout": timeout, "headers": headers})
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class Resp:
    def __init__(self, status_code=200, text="ok"):
        self.status_code = status_code
        self.text = text
        self.content = text.encode("utf-8")
        self.headers = {"Content-Type": "text/html"}
        self.history = []
        self.url = "https://x.test/final"


def test_http_client_default_headers():
    sess = DummySession()
    sess.response = Resp()
    client = HttpClient(session=sess)
    client.get("https://x.test")
    assert sess.headers["User-Agent"]
    assert sess.headers["Accept"] == DEFAULT_HEADERS["Accept"]


def test_http_client_user_agent_from_env(monkeypatch):
    monkeypatch.setenv("COMPONENT_RADAR_USER_AGENT", "UA-test")
    sess = DummySession()
    sess.response = Resp()
    client = HttpClient(session=sess)
    assert sess.headers["User-Agent"] == "UA-test"


def test_http_client_extra_headers():
    sess = DummySession()
    sess.response = Resp()
    client = HttpClient(session=sess)
    client.get("https://x.test", headers={"Referer": "https://ref.test"})
    assert sess.calls[0]["headers"]["Referer"] == "https://ref.test"


def test_probable_block_detection():
    assert probable_blocked_html("<html>Access Denied by Cloudflare</html>") is True
    assert probable_blocked_html("<html>produto lm308</html>") is False


def test_http_client_does_not_break_on_403():
    sess = DummySession()
    sess.response = Resp(status_code=403)
    client = HttpClient(session=sess, max_retries=0)
    resp = client.get("https://x.test")
    assert resp.status_code == 403


def test_save_no_results_html(tmp_path: Path):
    path = save_no_results_html("<html>sem itens</html>", "loja/x", "LM 308", root=tmp_path)
    assert path.exists()
    assert "loja_x_LM_308.html" in str(path)
    assert path.read_text(encoding="utf-8") == "<html>sem itens</html>"
