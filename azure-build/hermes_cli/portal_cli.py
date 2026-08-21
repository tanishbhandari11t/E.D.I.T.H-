"""``hermes portal`` — removed (Nous Portal / Tool Gateway)."""
from __future__ import annotations

import sys


_REMOVED = (
    "Nous Portal CLI was removed. "
    "Configure models with `hermes model` and tools with `hermes tools`."
)


def _cmd_removed(args) -> int:
    print(_REMOVED, file=sys.stderr)
    return 1


def portal_command(args) -> int:
    """Top-level dispatch for `hermes portal <subcommand>`."""
    return _cmd_removed(args)


def add_parser(subparsers) -> None:
    """Register ``hermes portal`` (stubs that report removal)."""
    portal = subparsers.add_parser(
        "portal",
        help="(removed) Nous Portal — use hermes model / hermes tools",
        description=_REMOVED,
    )
    portal.set_defaults(func=portal_command)
    sub = portal.add_subparsers(dest="portal_command")
    for name, help_text in (
        ("login", "removed"),
        ("info", "removed"),
        ("status", "removed"),
        ("open", "removed"),
        ("tools", "removed"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.set_defaults(func=portal_command)
