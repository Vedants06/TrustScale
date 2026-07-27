"""Structured logging setup for all TrustScale services."""

import structlog


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Create a structured logger for a service or module.

    Args:
        name: Name of the service or module.

    Returns:
        Configured structlog logger instance.
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    return structlog.get_logger(name)