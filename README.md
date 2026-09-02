<p align="center">
  <img src="assets/banner.png" alt="E.D.I.T.H." width="100%">
</p>

# E.D.I.T.H.

**Even Dead, I'm The Hero.** A terminal-native AI coding agent: open your GitHub repos, navigate the tree like an IDE, edit files, run tests, and remember project decisions across sessions.

No dashboard. No browser chrome as the product. You run `edith` in a terminal.

```text
edith

> Open my Repo-Repair repo
> Show me the backend structure
> Open agents/orchestrator.py
> Create tests/integration/
> Run the tests
> Show me the diff
```

## What it does

| You ask | EDITH does |
|---|---|
| Open this GitHub repo | Locate a local clone or `gh repo clone` into a workspace |
| Show the structure | Tree the source, tests, and manifests — not `node_modules` |
| Open / find a file | `read_file` / `search_files` from the repo root |
| Create folders and files | Directories and files on disk |
| Edit code | Smallest patch that implements the plan |
| Run tests | The project's own runner (`pytest`, `npm test`, …) |
| What changed? | `git status` + `git diff` |
| Remember this decision | Cross-session memory (does not replace `MEMORY.md`) |

**It does not** commit, push, or open a PR unless you explicitly ask.

## Requirements

- Windows, macOS, or Linux
- [GitHub CLI](https://cli.github.com/) authenticated (`gh auth status`)
- Git
- A running EDITH / Hermes runtime (`edith` on PATH)

This tree is the EDITH-branded source checkout. The live Windows command is typically:

```text
%LOCALAPPDATA%\hermes\bin\edith.cmd
```

## GitHub → workspace

EDITH uses `gh` and the local `coding-workspace` skill (no GitHub MCP).

```text
understand → locate/clone → inspect → read → plan → edit → test → diff → stop
```

Default clone root if nothing local matches: `~/edith-workspaces/<repo>`  
(`%USERPROFILE%\edith-workspaces` on Windows). Override with `EDITH_WORKSPACE_ROOT`.

Named workspaces (optional bookkeeping, does not change CLI cwd):

```bash
hermes project create "Repo-Repair" "C:\Users\<you>\Desktop\PROJECTS\RepoRepair" --use
```

## Everyday commands

```bash
edith                          # interactive terminal session
edith -s coding-workspace      # preload the workspace skill
edith -z "Open my Repo-Repair repo and show the backend."
gh auth status                 # GitHub identity
hermes skills list             # coding-workspace should be enabled (local)
hermes project list            # named workspaces
```

## Coding loop

1. Understand the request.
2. Locate the repository (existing clone first, then `gh`).
3. Inspect structure and manifests (`pyproject.toml`, `package.json`, …).
4. Find and read the surrounding code.
5. Plan the exact files to touch. Inspect-only turns do not write.
6. Create or edit files.
7. Run the smallest relevant tests.
8. Show the diff.
9. Stop. Commit / push / PR only when you say so.

Destructive operations need confirmation: delete a directory or database, `git reset --hard`, `git push`.

## Roadmap (v1)

- [x] Terminal `edith` command and branding
- [x] GitHub via `gh` (no MCP)
- [x] `coding-workspace` skill
- [x] Cross-session memory
- [ ] Reliable create / edit / test / diff without inspect-only writes
- [ ] Playwright (later)
- [ ] Explicit commit → push → PR when you ask (last)

## License

MIT. See [LICENSE](LICENSE).

EDITH is a branded, terminal-first coding workflow on top of [Hermes Agent](https://github.com/NousResearch/hermes-agent) by [Nous Research](https://nousresearch.com). Upstream copyright remains; this checkout adds EDITH-specific branding, skills, and workspace conventions.
