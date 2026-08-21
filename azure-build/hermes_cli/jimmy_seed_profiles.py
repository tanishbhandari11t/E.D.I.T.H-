#!/usr/bin/env python3
"""Seed four isolated Jimmy profiles sharing Azure OpenAI credentials.

Run inside the container (or with HERMES_HOME set) on first boot:

    python -m hermes_cli.jimmy_seed_profiles

Creates profiles jimmy1..jimmy4 under the profiles root, writes matching
model config, enables gateway.multiplex_profiles on the default home, and
never copies Telegram tokens between profiles.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

JIMMY_PROFILES = ("jimmy1", "jimmy2", "jimmy3", "jimmy4")


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return raw if isinstance(raw, dict) else {}


def _dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )


def _azure_model_block() -> dict[str, Any]:
    endpoint = (
        os.environ.get("AZURE_FOUNDRY_BASE_URL")
        or os.environ.get("AZURE_OPENAI_ENDPOINT")
        or ""
    ).rstrip("/")
    model = (
        os.environ.get("AZURE_OPENAI_DEPLOYMENT")
        or os.environ.get("HERMES_MODEL")
        or "gpt-5.6-sol"
    )
    block: dict[str, Any] = {
        "default": model,
        "provider": "azure-foundry",
        "api_mode": "chat_completions",
    }
    if endpoint:
        if not endpoint.endswith("/openai/v1"):
            if "openai.azure.com" in endpoint and "/openai" not in endpoint:
                endpoint = endpoint + "/openai/v1"
        block["base_url"] = endpoint
    return block


def _scrub_wal_sidecars(home: Path) -> None:
    """Drop stale ``*-wal`` / ``*-shm`` files left by a prior WAL attempt.

    Safe only before other processes open the DB (container CMD runs seed
    before ``hermes dashboard``). On Azure Files these sidecars are a common
    source of indefinite locks once WAL was attempted.
    """
    for pattern in ("*.db-wal", "*.db-shm", "state.db-wal", "state.db-shm"):
        for path in home.glob(pattern):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass


def _force_delete_journal(home: Path) -> None:
    """Convert ``state.db`` off WAL before the dashboard opens it.

    ``apply_wal_with_fallback`` refuses to live-downgrade an on-disk WAL DB.
    On Azure Files that leaves sessions permanently hung. At boot (seed-only
    process) we can safely flip the header to DELETE or recreate an empty store.
    """
    import sqlite3

    db = home / "state.db"
    _scrub_wal_sidecars(home)
    if not db.is_file():
        return
    try:
        conn = sqlite3.connect(f"file:{db}?mode=rw", uri=True, timeout=8.0)
        try:
            row = conn.execute("PRAGMA journal_mode=DELETE").fetchone()
            mode = (row[0] if row else "").lower()
            if mode != "delete":
                raise RuntimeError(f"journal_mode stayed {mode!r}")
            conn.commit()
        finally:
            conn.close()
    except Exception as exc:
        print(f"seed: recreating {db} after journal convert failed: {exc}")
        for path in (db, Path(str(db) + "-wal"), Path(str(db) + "-shm")):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass


def _ensure_profile(profiles_root: Path, name: str, model: dict[str, Any]) -> Path:
    home = profiles_root / name
    home.mkdir(parents=True, exist_ok=True)
    (home / "memories").mkdir(exist_ok=True)
    (home / "skills").mkdir(exist_ok=True)
    (home / "sessions").mkdir(exist_ok=True)
    cfg_path = home / "config.yaml"
    cfg = _load_yaml(cfg_path)
    cfg["model"] = {**(cfg.get("model") or {}), **model}
    gateway = cfg.get("gateway") if isinstance(cfg.get("gateway"), dict) else {}
    gateway = dict(gateway)
    # Per-profile gateways are driven by the default multiplex parent.
    cfg["gateway"] = gateway
    database = dict(cfg["database"]) if isinstance(cfg.get("database"), dict) else {}
    database["journal_mode"] = "delete"
    cfg["database"] = database
    _dump_yaml(cfg_path, cfg)
    _force_delete_journal(home)
    env_path = home / ".env"
    if not env_path.exists():
        env_path.write_text(
            "# Per-user secrets only (e.g. TELEGRAM_BOT_TOKEN). "
            "Azure OpenAI is shared from the process env.\n",
            encoding="utf-8",
        )
    soul = home / "SOUL.md"
    if not soul.exists():
        soul.write_text(
            "You are Jimmy, an intelligent AI assistant. "
            "You are helpful, knowledgeable, and direct.\n",
            encoding="utf-8",
        )
    return home


def seed_jimmy_profiles(*, hermes_home: Path | None = None) -> list[Path]:
    from hermes_constants import get_hermes_home
    from hermes_cli.profiles import _get_profiles_root

    home = Path(hermes_home or get_hermes_home())
    home.mkdir(parents=True, exist_ok=True)
    profiles_root = _get_profiles_root()
    profiles_root.mkdir(parents=True, exist_ok=True)

    model = _azure_model_block()

    # Default home: multiplex all four profile gateways; shared model.
    default_cfg_path = home / "config.yaml"
    default_cfg = _load_yaml(default_cfg_path)
    default_cfg["model"] = {**(default_cfg.get("model") or {}), **model}
    gateway = (
        dict(default_cfg["gateway"])
        if isinstance(default_cfg.get("gateway"), dict)
        else {}
    )
    gateway["multiplex_profiles"] = True
    default_cfg["gateway"] = gateway

    # Azure Files (SMB) cannot host SQLite WAL safely — PRAGMA WAL can hang
    # indefinitely instead of raising, which surfaces as /api/sessions timeouts
    # and "Internal server error" in the dashboard. Force DELETE journal mode.
    database = (
        dict(default_cfg["database"])
        if isinstance(default_cfg.get("database"), dict)
        else {}
    )
    database["journal_mode"] = "delete"
    default_cfg["database"] = database
    _force_delete_journal(home)

    # Wire multi-user basic auth when JIMMY*_PASSWORD present and users empty.
    dash = (
        dict(default_cfg["dashboard"])
        if isinstance(default_cfg.get("dashboard"), dict)
        else {}
    )
    basic = (
        dict(dash["basic_auth"])
        if isinstance(dash.get("basic_auth"), dict)
        else {}
    )
    if not basic.get("users"):
        users = []
        for i, name in enumerate(JIMMY_PROFILES, start=1):
            pw = os.environ.get(f"JIMMY{i}_PASSWORD", "").strip()
            if not pw:
                continue
            users.append(
                {
                    "username": os.environ.get(f"JIMMY{i}_USERNAME", name).strip()
                    or name,
                    "password": pw,
                    "profile": name,
                }
            )
        if users:
            basic["users"] = users
            if os.environ.get("HERMES_DASHBOARD_BASIC_AUTH_SECRET"):
                basic["secret"] = os.environ["HERMES_DASHBOARD_BASIC_AUTH_SECRET"]
            dash["basic_auth"] = basic
            default_cfg["dashboard"] = dash

    _dump_yaml(default_cfg_path, default_cfg)

    created = [_ensure_profile(profiles_root, name, model) for name in JIMMY_PROFILES]
    return created


def main() -> None:
    paths = seed_jimmy_profiles()
    for p in paths:
        print(f"seeded {p}")


if __name__ == "__main__":
    main()
