import pytest
from autogen_mcp.memory import MemoryService
from autogen_mcp.security import is_url_allowed

# Integration/E2E: Memory blocks secrets end-to-end


def test_integration_memory_blocks_secrets():
    svc = MemoryService(collection="mem_e2e_block", summary_threshold=3)
    svc.ensure_collection()
    # Blocked in text
    with pytest.raises(ValueError):
        svc.write_event("thread", thread_id="t4", text="password=supersecret")
    # Blocked in metadata value
    with pytest.raises(ValueError):
        svc.write_event(
            "thread", thread_id="t4", text="ok", metadata={"api_key": "sk-abcdef"}
        )
    # Blocked in metadata key
    with pytest.raises(ValueError):
        svc.write_event("thread", thread_id="t4", text="ok", metadata={"secret": "foo"})


# Integration/E2E: Outbound call allowlist enforcement


def test_integration_outbound_call_allowlist():
    # Allowed
    assert is_url_allowed("https://api.github.com/repos/foo/bar")
    # Blocked
    assert not is_url_allowed("https://evil.com/api")
