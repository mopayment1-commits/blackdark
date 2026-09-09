"""Anonymous visitor HTTP middleware export."""

from anonymous_visitor.authorization import enforce_anonymous_boundary

__all__ = ["enforce_anonymous_boundary"]
