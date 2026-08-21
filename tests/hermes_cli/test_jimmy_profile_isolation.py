"""Anti-overlap: bound profile middleware + multi-user session claims."""

from __future__ import annotations

import secrets
from unittest.mock import MagicMock

import pytest
from fastapi.responses import JSONResponse
from starlette.requests import Request

import plugins.dashboard_auth.basic as basic_plugin
from hermes_cli.dashboard_auth.middleware import _enforce_bound_profile


def _request_with_query(query: str) -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/api/sessions",
        "raw_path": b"/api/sessions",
        "query_string": query.encode("latin-1"),
        "headers": [],
        "client": ("127.0.0.1", 123),
        "server": ("test", 80),
    }
    return Request(scope)


def test_bound_profile_rejects_foreign_query():
    session = MagicMock()
    session.profile = "jimmy1"
    req = _request_with_query("profile=jimmy2")
    err = _enforce_bound_profile(req, session)
    assert isinstance(err, JSONResponse)
    assert err.status_code == 403


def test_bound_profile_forces_query_when_missing():
    session = MagicMock()
    session.profile = "jimmy1"
    req = _request_with_query("")
    err = _enforce_bound_profile(req, session)
    assert err is None
    assert req.scope["query_string"] == b"profile=jimmy1"
    assert req.state.bound_profile == "jimmy1"


def test_bound_profile_allows_matching_query():
    session = MagicMock()
    session.profile = "jimmy2"
    req = _request_with_query("profile=jimmy2&x=1")
    err = _enforce_bound_profile(req, session)
    assert err is None
    assert b"profile=jimmy2" in req.scope["query_string"]


def test_unbound_session_leaves_query_alone():
    session = MagicMock()
    session.profile = ""
    req = _request_with_query("profile=jimmy3")
    err = _enforce_bound_profile(req, session)
    assert err is None
    assert req.scope["query_string"] == b"profile=jimmy3"


def test_four_users_independent_session_claims():
    users = [
        {
            "username": f"jimmy{i}",
            "password_hash": basic_plugin.hash_password(f"pw{i}"),
            "profile": f"jimmy{i}",
        }
        for i in range(1, 5)
    ]
    provider = basic_plugin.BasicAuthProvider(
        users=users, secret=secrets.token_bytes(32)
    )
    sessions = [
        provider.complete_password_login(username=f"jimmy{i}", password=f"pw{i}")
        for i in range(1, 5)
    ]
    profiles = {s.profile for s in sessions}
    assert profiles == {"jimmy1", "jimmy2", "jimmy3", "jimmy4"}
    # Tokens verify only for their own profile claim
    for s in sessions:
        v = provider.verify_session(access_token=s.access_token)
        assert v is not None
        assert v.profile == s.profile
        assert v.user_id == s.user_id
