"""
Custom exceptions for AgenticOS.
"""


class AgenticOSException(Exception):
    """Base exception for all AgenticOS errors."""
    pass


class AgentNotFoundError(AgenticOSException):
    """Raised when agent is not registered."""
    pass


class CapabilityNotFoundError(AgenticOSException):
    """Raised when required capability is unavailable."""
    pass


class MessageRoutingError(AgenticOSException):
    """Raised when message cannot be routed."""
    pass


class TaskExecutionError(AgenticOSException):
    """Raised when task execution fails."""
    pass


class ConfigurationError(AgenticOSException):
    """Raised when configuration is invalid."""
    pass


class AuthenticationError(AgenticOSException):
    """Raised when authentication fails."""
    pass


class RateLimitExceededError(AgenticOSException):
    """Raised when rate limit is exceeded."""
    pass


class WorkflowExecutionError(AgenticOSException):
    """Raised when workflow execution fails."""
    pass


class GuardrailViolationError(AgenticOSException):
    """Raised when action violates guardrails."""
    pass

