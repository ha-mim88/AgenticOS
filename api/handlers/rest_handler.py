"""
REST API handlers.
"""

import logging

logger = logging.getLogger(__name__)


async def handle_rest_request(request):
    """Handle REST API request."""
    # TODO: Implement REST endpoint handling
    return {"status": "ok"}


__all__ = ["handle_rest_request"]

