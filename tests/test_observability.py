import io
import json
import logging
from autogen_mcp.observability import get_logger, JsonFormatter


def test_json_formatter_basic():
    record = logging.LogRecord(
        name="autogen.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    record.correlation_id = "cid-123"
    record.extra = {"foo": "bar"}
    formatter = JsonFormatter()
    out = formatter.format(record)
    data = json.loads(out)
    assert data["level"] == "INFO"
    assert data["msg"] == "Test message"
    assert data["correlation_id"] == "cid-123"
    assert data["foo"] == "bar"


def test_get_logger_and_correlation_id(monkeypatch):
    logger = get_logger("autogen.test", correlation_id="cid-xyz", verbosity="DEBUG")
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(JsonFormatter())
    logger.handlers = [handler]
    logger.info("Hello", extra={"extra": {"x": 1}})
    logger.debug("Debug", extra={"extra": {"y": 2}})
    logs = buf.getvalue().splitlines()
    for line in logs:
        data = json.loads(line)
        assert data["correlation_id"] == "cid-xyz"
        assert data["logger"] == "autogen.test"
    assert any("Hello" in line for line in logs)
    assert any("Debug" in line for line in logs)


def test_logger_env_verbosity(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    logger = get_logger("autogen.testenv")
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(JsonFormatter())
    logger.handlers = [handler]
    logger.info("Should not appear")
    logger.warning("Should appear")
    logs = buf.getvalue().splitlines()
    assert any("Should appear" in line for line in logs)
    assert not any("Should not appear" in line for line in logs)
