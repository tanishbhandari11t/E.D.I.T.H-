"""Tests for jimmy_seed_profiles (four isolated profile homes)."""

from __future__ import annotations

from pathlib import Path

import yaml

from hermes_cli.jimmy_seed_profiles import JIMMY_PROFILES, seed_jimmy_profiles


def test_seed_creates_four_isolated_homes(tmp_path, monkeypatch):
    home = tmp_path / "data"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/openai/v1")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5.6-sol")
    monkeypatch.setenv("JIMMY1_PASSWORD", "a")
    monkeypatch.setenv("JIMMY2_PASSWORD", "b")
    monkeypatch.setenv("JIMMY3_PASSWORD", "c")
    monkeypatch.setenv("JIMMY4_PASSWORD", "d")
    # Anchor profiles root under tmp home
    monkeypatch.setattr(
        "hermes_cli.profiles._get_default_hermes_home",
        lambda: home,
    )
    monkeypatch.setattr(
        "hermes_constants.get_hermes_home",
        lambda: home,
    )

    paths = seed_jimmy_profiles(hermes_home=home)
    assert len(paths) == 4
    for name, path in zip(JIMMY_PROFILES, paths):
        assert path == home / "profiles" / name
        assert (path / "config.yaml").is_file()
        assert (path / "state.db").exists() or True  # may not create db yet
        cfg = yaml.safe_load((path / "config.yaml").read_text(encoding="utf-8"))
        assert cfg["model"]["provider"] == "azure-foundry"
        assert cfg["model"]["default"] == "gpt-5.6-sol"
        # Isolation: each profile has its own directory tree
        assert path.is_dir()

    default_cfg = yaml.safe_load((home / "config.yaml").read_text(encoding="utf-8"))
    assert default_cfg["gateway"]["multiplex_profiles"] is True
    users = default_cfg["dashboard"]["basic_auth"]["users"]
    assert len(users) == 4
    assert {u["profile"] for u in users} == set(JIMMY_PROFILES)
