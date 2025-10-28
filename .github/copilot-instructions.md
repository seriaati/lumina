# Copilot Coding Agent Onboarding for lumina

Use this doc as your fast path to understand, build, lint, type-check, and run this repo without guesswork. Prefer following these steps exactly; search only if something here is incomplete or incorrect.

## What this repository is

- Lumina is a minimal Discord bot that helps users organize life: reminders, birthdays, todos, notes. All responses are ephemeral/DMs to the user.
- Runtime: Python 3.12 (see `.python-version`), Discord API via `discord-py`, SQLite via `tortoise-orm`, logging via `loguru`, i18n via YAML in `l10n/`.
- Dependency/runtime manager: [uv](https://docs.astral.sh/uv/). Lockfile: `uv.lock`. No traditional tests present.
- Type checking: Pyright (see `.github/workflows/pyright.yml` and `[tool.pyright]` in `pyproject.toml`).
- Lint/format: Ruff (`ruff.toml` and pre-commit hooks).

Repo size is small-to-medium (single Python package `lumina/` plus a few configs). Entry point is `run.py`.

## Always do this first (bootstrap)

- Ensure Python 3.12 is available (repo uses `.python-version=3.12`).
- Ensure `uv` is installed and on PATH. If not, install it per uv docs.
- Create/sync the virtual environment using the lockfile:
  - Windows PowerShell (pwsh):
    - `uv sync --frozen`
  - Notes:
    - This creates/updates `.venv/` and installs pinned runtime deps.
    - On Windows, `uvloop` is not installed; CI uninstalls it on Linux for consistency.

## Build, lint, type-check, and run

There is no "build" step in the packaging sense; you work in a venv. Use uv for all commands.

- Lint & format (fast; should pass):
  - `uvx ruff format --check .` to assert formatting (use `uvx ruff format .` to apply).
  - `uvx ruff check .` to run lint per `ruff.toml` (target-version py312, line-length 120, various rulesets; see file for ignores).
- Type check (mirrors CI):
  - `uvx pyright lumina/`
  - Pyright is configured in `pyproject.toml` with `venv = ".venv"` and `typeCheckingMode = "standard"`.
- Run locally (requires secrets):
  - Precondition: a `.env` file with `DISCORD_TOKEN=...` in repo root (or set the env var in your shell).
  - Command: `uv run run.py`
  - Side effects: creates `lumina.db` (SQLite) and `logs/lumina.log` on first run; connects to Discord; loads cogs from `lumina/cogs/` and schedules reminders.
  - Without `DISCORD_TOKEN`, running will fail with `KeyError: 'DISCORD_TOKEN'` and during shutdown you may see a `tortoise.exceptions.ConfigurationError` (benign on early exit).

## Validation pipeline / CI

- GitHub Actions workflows:
  - `.github/workflows/pyright.yml`: On push/PR to `main`, installs uv, runs `uv sync --frozen`, uninstalls `uvloop`, and runs Pyright in `lumina/`. Your PR must have 0 Pyright errors.
  - `.github/workflows/release.yml`: Creates a release on push to `main` using a custom action.
  - `.github/workflows/bump-version.yml`: Manual version bump and release using custom actions.
- Pre-commit: `.pre-commit-config.yaml` enables Ruff and Ruff format; if you enable pre-commit locally, `pre-commit run -a` should pass. CI does not run pre-commit, but conform to Ruff.

## Project layout and key files

- Root
  - `run.py`: Application entrypoint. Loads `.env`, configures loguru, runs the bot.
  - `pyproject.toml`: Project metadata, Python requirement (>=3.11), dependencies, and Pyright config. No build-system section; use uv (no `pip install -e .` required).
  - `ruff.toml`: Lint/format rules. Target Python 3.12.
  - `.python-version`: 3.12 (use this Python).
  - `.pre-commit-config.yaml`: Ruff and Ruff-format hooks.
  - `.github/workflows/*.yml`: CI workflows (Pyright, releases, version bump).
  - `uv.lock`: uv lockfile for dependency pinning.
  - `pm2.json`: Process manager config for Linux paths (not used on Windows).
  - `l10n/*.yaml`: English and Traditional Chinese localization resources.
  - `README.md`: Install/run instructions (uv-based).
- Package `lumina/`
  - `bot.py`: Discord `commands.Bot` subclass `Lumina`. Sets intents, loads cogs, initializes Tortoise ORM with SQLite `lumina.db`, loads translator, schedules reminders, and provides helpers like `dm_user` and `create_error_embed`.
  - `command_tree.py`: Custom `discord.app_commands.CommandTree` with unified error handling that emits localized embeds.
  - `models.py`: Tortoise ORM models for `LuminaUser`, `Birthday`, `Reminder`, `TodoTask`, `Notes` with embed builders and utility methods. Central to data layer.
  - `cogs/*.py`: Feature modules (admin, birthday, health, reminder, schedule, settings, todo). These register slash/context commands and use models/utilities.
  - `embeds.py`, `exceptions.py`, `error_handler.py`, `utils.py`, `constants.py`, `l10n.py`, `components.py`, `types.py`, etc.: UI/UX helpers, error types, localization loader, custom types (notably `type Interaction = discord.Interaction[Lumina]`).

## Practical guidance for making changes

- Before coding:
  - Always run `uv sync --frozen` to ensure the venv matches `uv.lock`.
  - Always run `uvx ruff format --check .` and `uvx ruff check .` to see the current linting baseline.
  - Always run `uvx pyright lumina/` to type-check; CI will do the same and fail your PR if issues are introduced.
- While coding:
  - Prefer editing/adding cogs under `lumina/cogs/` for new commands.
  - When touching models, consider migrations are not used; schemas are generated at startup. Adjust embed text via localized strings in `l10n/*.yaml`.
  - Keep imports consistent with Ruff isort settings (required import: `from __future__ import annotations`).
- After coding:
  - Re-run Ruff (format and check) and Pyright. Ensure both PASS.
  - If your change affects runtime behavior, you can smoke-test with `uv run run.py` (requires a valid `DISCORD_TOKEN`); otherwise rely on type-checking and linting.

## Known pitfalls and their mitigations

- Running without `DISCORD_TOKEN` will raise a `KeyError` and can trigger a benign Tortoise "DB configuration not initialised" error during shutdown; this is expected when aborting before startup completes.
- Windows: `uvloop` is not installed; if you copy CI steps verbatim, `uv pip uninstall uvloop` will print a warning that it’s not installed. Safe to ignore on Windows.
- There are no unit tests; validation relies on Ruff and Pyright. Don’t invent test commands.
- For CI parity, run Pyright in the `lumina/` directory, not the repo root.

## Quick commands (pwsh)

- Bootstrap: `uv sync --frozen`
- Lint: `uvx ruff check .`
- Format: `uvx ruff format .`
- Type-check: `uvx pyright lumina/`
- Run (requires `.env` with token): `uv run run.py`

## Final note

Trust these instructions as the source of truth for this repo’s workflow. Only perform additional searches if you find these steps incomplete or see concrete errors that contradict this document.
