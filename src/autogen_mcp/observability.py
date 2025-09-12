import logging
import json
import os
import sys
import uuid
from typing import Optional


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "level": record.levelname,
            "time": self.formatTime(record, self.datefmt),
            "msg": record.getMessage(),
            "logger": record.name,
        }
        if hasattr(record, "correlation_id"):
            log_record["correlation_id"] = record.correlation_id
        if hasattr(record, "extra"):
            log_record.update(record.extra)
        return json.dumps(log_record)


def get_logger(
    name: str, correlation_id: Optional[str] = None, verbosity: Optional[str] = None
):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    logger.setLevel(
        getattr(logging, (verbosity or os.getenv("LOG_LEVEL", "INFO")).upper())
    )
    logger.propagate = False

    # Attach correlation_id to all log records
    def filter_func(record):
        record.correlation_id = (
            correlation_id or os.getenv("CORRELATION_ID") or str(uuid.uuid4())
        )
        return True

    logger.addFilter(filter_func)
    return logger


# Example usage
if __name__ == "__main__":
    logger = get_logger(
        "autogen.observability", correlation_id="session-1234", verbosity="DEBUG"
    )
    logger.info("Agent turn started", extra={"extra": {"agent": "Coder", "step": 1}})
    logger.debug("Tool call", extra={"extra": {"tool": "search", "query": "foo"}})
    logger.warning("Timeout", extra={"extra": {"timeout": 30}})
    logger.info("Agent turn finished", extra={"extra": {"duration": 2.5}})
