from autogen_mcp.security import is_url_allowed


def test_is_url_allowed_accepts_allowed_domains():
    assert is_url_allowed("https://api.github.com/repos/foo/bar")
    assert is_url_allowed(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini"
    )
    assert is_url_allowed("http://localhost:6333/readyz")
    assert is_url_allowed("http://127.0.0.1:8000/health")


def test_is_url_allowed_rejects_disallowed_domains():
    assert not is_url_allowed("https://evil.com/api")
    assert not is_url_allowed("https://notgithub.com/api")
    assert not is_url_allowed("http://malicious.local/attack")
    assert not is_url_allowed("https://api.github.evil.com/repos/foo/bar")
