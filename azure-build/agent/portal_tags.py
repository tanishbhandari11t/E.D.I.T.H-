"""Conversation-context helpers (formerly Nous Portal request tags).

Keeps ``set``/``get``/``reset`` conversation context for ambient session
correlation. Product-attribution Portal tags are no longer emitted.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import List, Optional

# ── Ambient conversation context ─────────────────────────────────────────────
#
# The main agent loop knows its ``session_id``; auxiliary call sites often do
# not. The agent loop publishes the active conversation id here so callers can
# still read it without threading ``session_id`` through every site.
#
# ContextVar (not a module global) so concurrent agents in one process —
# gateway sessions, delegate_task subagents, batch runners — never see each
# other's conversation id.
_conversation_id: ContextVar[Optional[str]] = ContextVar(
    "nous_portal_conversation_id", default=None
)


def set_conversation_context(conversation_id: Optional[str]):
    """Publish the active conversation id for ambient context.

    Called by the agent loop at turn entry with the conversation's stable
    id (the session-lineage ROOT id). Pass ``None`` to clear. Returns the
    ContextVar token so callers can ``reset_conversation_context(token)``
    on turn exit.
    """
    return _conversation_id.set(conversation_id or None)


def reset_conversation_context(token) -> None:
    """Restore the previous conversation context (pair with ``set_...``)."""
    try:
        _conversation_id.reset(token)
    except Exception:
        # Token from another Context (e.g. reset on a different thread) —
        # fall back to clearing rather than raising in cleanup paths.
        _conversation_id.set(None)


def get_conversation_context() -> Optional[str]:
    """Return the ambient conversation id, or ``None`` when unset."""
    return _conversation_id.get()


def hermes_client_tag() -> str:
    """Formerly returned a Nous Portal ``client=...`` tag; now empty."""
    return ""


def conversation_tag(session_id: str) -> str:
    """Return a ``conversation=...`` tag string for a Hermes session id."""
    return f"conversation={session_id}"


def nous_portal_tags(session_id: str | None = None) -> List[str]:
    """Formerly returned Nous Portal product tags; always empty now.

    Kept as a stable API for call sites that still extend ``extra_body['tags']``.
    Conversation context helpers above remain available for non-tag uses.
    """
    del session_id
    return []
