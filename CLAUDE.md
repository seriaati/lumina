# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

### Environment Setup
```bash
# Bootstrap environment (do this first)
uv sync --frozen

# Run the bot locally (requires .env with DISCORD_TOKEN)
uv run run.py
```

### Code Quality & Validation
```bash
# Lint code (matches pre-commit hooks)
uvx ruff check .

# Format code
uvx ruff format .

# Type check (matches CI)
uvx pyright lumina/
```

## Architecture Overview

### Core Design
Lumina is a minimal Discord user app/bot for life organization (reminders, birthdays, todos, notes). All interactions are ephemeral or via DMs. The bot is built on:

- **Discord API**: `discord-py` with slash commands, context menus, and app commands
- **Database**: SQLite via `tortoise-orm` with auto-schema generation at startup
- **Localization**: YAML-based i18n in `l10n/` directory using `LocaleStr` pattern
- **Logging**: `loguru` with rotation (1 week) and retention (1 month)
- **Dependency Management**: `uv` with lockfile (`uv.lock`)

### Application Entry & Lifecycle

**Entry Point**: [run.py](run.py)
- Sets up loguru logger (stderr + file rotation)
- Loads `.env` for secrets
- Creates `Lumina` bot instance and `HealthCheckServer`
- Starts bot with `DISCORD_TOKEN`

**Bot Initialization**: [lumina/bot.py](lumina/bot.py)
1. Initialize Tortoise ORM with SQLite database (path from `DB_PATH` env var or `lumina.db`)
2. Load translations from `l10n/*.yaml`
3. Dynamically load cogs from `lumina/cogs/` (skips `health` cog in dev mode)
4. Load jishaku for debugging
5. Set up app command translator
6. Initialize `ReminderScheduler` to handle timed reminders

### Database Models & Schema

**Models**: [lumina/models.py](lumina/models.py)
- **LuminaUser**: User settings (timezone offset, language preference)
- **Reminder**: Scheduled reminders with datetime (UTC), text, optional message URL
- **Birthday**: Birthday tracking with leap year handling, early notification support
- **TodoTask**: Task tracking with done/undone state
- **Notes**: User notes with title and content

**Schema Management**: No migrations used. Tortoise generates schemas at startup via `Tortoise.generate_schemas()`. Models use Tortoise ORM fields and include embed builders for Discord responses.

### Reminder Scheduling System

**ReminderScheduler**: [lumina/bot.py:32-70](lumina/bot.py#L32-L70)
- Maintains a single active `asyncio.Task` for the next pending reminder
- Queries database for earliest unsent reminder, sleeps until that datetime
- On wake: sends DM to user, deletes reminder (or marks sent if DM fails)
- Reschedules next reminder after each send or schedule update
- Cogs call `bot.scheduler.schedule_reminder()` after create/delete operations

### Localization Architecture

**Translation System**: [lumina/l10n.py](lumina/l10n.py)
- `LocaleStr(key, params={})`: Represents translatable strings with placeholders
- `Translator.load()`: Loads all YAML files from `l10n/` directory at startup
- `Translator.translate()`: Resolves key against locale, falls back to en-US
- `AppCommandTranslator`: Discord.py translator for slash command names/descriptions

**Usage Pattern**:
```python
# In embeds/descriptions
LocaleStr("reminder_created_embed_title")
LocaleStr("reminder_created_embed_description", params={"dt": format_dt(...)})

# In slash command definitions
app_commands.locale_str("Set reminder", key="reminder_set_command_name")
```

**Translation Files**: `l10n/en-US.yaml` (required source), `l10n/zh-TW.yaml` (Traditional Chinese)

### Command Structure (Cogs)

**Cog Pattern**: [lumina/cogs/](lumina/cogs/)
- All cogs inherit from `commands.GroupCog` with localized group names
- Commands use `@app_commands.command` with `locale_str` for i18n
- Context menus use `app_commands.ContextMenu` with localized names
- All responses use `ephemeral=True` (user-only visibility)
- Error handling delegated to custom `CommandTree`

**Key Cogs**:
- **reminder.py**: Natural language time parsing via `dateparser`, handles hours pattern (`1h`), timezone-aware datetime conversion
- **birthday.py**: Leap year handling, early notifications, Discord user integration
- **todo.py**: Task management with done/undone state, strikethrough rendering
- **settings.py**: User timezone/language preferences
- **schedule.py**: Background task for birthday notifications (daily 9am user time)
- **health.py**: HTTP healthcheck endpoint (port 8080) for Docker

### Error Handling

**Custom CommandTree**: [lumina/command_tree.py](lumina/command_tree.py)
- Overrides `on_error` to catch all command exceptions
- Uses `bot.create_error_embed()` to generate localized error embeds
- Sends ephemeral error messages to user
- Known exceptions handled via `LuminaError` subclasses in [lumina/exceptions.py](lumina/exceptions.py)

**Error Handler**: [lumina/error_handler.py](lumina/error_handler.py)
- `create_error_embed()`: Converts exceptions to Discord embeds
- `LuminaError` subclasses have `title` and `description` as `LocaleStr`
- Unknown errors show generic message with developer contact link

### Custom Components

**UI Components**: [lumina/components.py](lumina/components.py)
- `Modal`: Base modal with translation support
- `TextInput`: Localized text input fields
- `Paginator`: Embed pagination with navigation buttons

### Type System

**Custom Types**: [lumina/types.py](lumina/types.py)
- `Interaction = discord.Interaction[Lumina]`: Typed interaction with bot reference
- `UserOrMember`: Union type for Discord users/members

## Code Conventions

### Import Order
All files start with `from __future__ import annotations` (Ruff requirement). Imports follow Ruff isort settings.

### Error Handling Pattern
```python
# Raise custom exceptions in commands
if reminder is None:
    raise ReminderNotFoundError

# Exception handled in CommandTree.on_error
# Converted to localized embed via error_handler.create_error_embed()
```

### Timezone Pattern
- User timezone stored as hour offset from UTC (SmallIntField)
- `get_now(timezone)` returns timezone-aware datetime
- All reminders stored in UTC, converted to user timezone for display
- Natural language parsing uses user timezone context

### Embed Pattern
Models have embed builder methods:
```python
reminder.get_created_embed(locale)
reminder.get_removed_embed(locale)
Reminder.get_list_embed(locale, reminders=..., start=...)
```

### Database Access Pattern
```python
# Get or create user
user, _ = await LuminaUser.get_or_create(id=i.user.id)

# Create with relation
await Reminder.create(text=..., datetime=..., user=user)

# Query with prefetch
await Reminder.filter(sent=False).order_by("datetime").first().prefetch_related("user")

# Update specific fields
reminder.sent = True
await reminder.save(update_fields=("sent",))
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_TOKEN` | Yes | - | Discord bot token |
| `DB_PATH` | No | `lumina.db` | SQLite database path (use `/app/data/lumina.db` in containers) |
| `ENV` | No | `dev` | Environment mode (`dev` skips health cog) |

## Deployment Context

- **Docker**: Uses `/app/data/lumina.db` for persistence, `/app/logs/lumina.log` for logs
- **Local/PM2**: Uses `lumina.db` in project root, `logs/lumina.log`
- **Health Check**: HTTP server on port 8080 at `/health` (prod only, see [lumina/health.py](lumina/health.py))

## Development Workflow

1. **Always bootstrap first**: `uv sync --frozen`
2. **Type check before commit**: `uvx pyright lumina/` (must pass, matches CI)
3. **Lint before commit**: `uvx ruff check .` and `uvx ruff format .`
4. **Pre-commit hooks available**: Ruff and Ruff-format (optional but recommended)
5. **No unit tests**: Validation relies entirely on Pyright and Ruff
6. **Schemas auto-generate**: No migration files needed, Tortoise handles schema changes at startup

## Known Constraints

- **Python 3.11+ required** (see `pyproject.toml`)
- **Python 3.12 target** (see `.python-version` and `ruff.toml`)
- **No uvloop on Windows** (CI explicitly uninstalls it for consistency)
- **Pyright must pass**: CI runs `uvx pyright lumina/` with zero tolerance for errors
- **Discord intents**: Limited to `emojis`, `messages`, `guilds` (no member/presence intents)
- **No traditional testing**: No pytest, unittest, or test files in repo
