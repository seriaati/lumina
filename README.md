# Lumina

![Banner](https://iili.io/drPpr4R.png)

![GitHub issues](https://img.shields.io/github/issues/seriaati/lumina)
![GitHub pull requests](https://img.shields.io/github/issues-pr/seriaati/lumina)
![GitHub Repo stars](https://img.shields.io/github/stars/seriaati/lumina?style=flat)
![GitHub forks](https://img.shields.io/github/forks/seriaati/lumina?style=flat)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/seriaati/lumina)
![Lines of code](https://tokei.rs/b1/github/seriaati/lumina?style=flat&category=code&type=Python)
![Commit activity](https://img.shields.io/github/commit-activity/w/seriaati/lumina/main)
![GitHub](https://img.shields.io/github/license/seriaati/lumina)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Lumina is a simple and minimal Discord bot that helps you organize your life.  
> 2-minute rule: If an action will take less than two minutes, it should be done at the moment it's defiend; otherwise, add it to Lumina.

## Installation

Lumina is available both as a user app and a server bot. Install Lumina by clicking [here](https://discord.com/oauth2/authorize?client_id=1284303963533082684).  
Since Lumina is a user app, you can use it in any servers, including DMs.  
Every single Lumina response can only be seen by you, reminders are sent through DMs.

## Features

### Reminders

Right click on a message or type any texts to set a reminder. Lumina will remind you at the specified time.  

- `/reminder set`
- `/reminder list`
- `/reminder remove`

### Birthday Reminder

Right click on any Discord user's avatar to set a birthday for them. Lumina will remind you when it's their birthday.  

- `/birthday set`
- `/birthday list`
- `/birthday remove`

### To-Do List

Lumina can help you keep track of your tasks, right click on any Discord message to add it to your to-do list

- `/todo add`
- `/todo list`
- `/todo remove`
- `/todo done`

## Questions, Issues, Feedback, Contributions

Whether you want to make any bug reports, feature requests, or contribute to translations, simply open an issue or pull request in this repository.  
If GitHub is not your type, you can find me on [Discord](https://discord.com/invite/b22kMKuwbS), my username is @seria_ati.

## Self Hosting

Lumina can be self-hosted using several methods. All methods require a Discord bot token, which you can obtain from the [Discord Developer Portal](https://discord.com/developers/applications).

### Prerequisites

- A Discord bot token

### Method 1: Docker

1. Pull the latest image:

   ```bash
   docker pull ghcr.io/seriaati/lumina:latest
   ```

2. Run the container:

   ```bash
   docker run -d \
     --name lumina \
     -e DISCORD_TOKEN=YourDiscordBotToken \
     -v lumina-data:/app/data \
     -v lumina-logs:/app/logs \
     --restart unless-stopped \
     ghcr.io/seriaati/lumina:latest
   ```

   **Note:** The `-v` flags create Docker volumes to persist your database and logs across container restarts.

### Method 2: Docker Compose

1. Create a `docker-compose.yml` file:

   ```yaml
   services:
     lumina:
       image: ghcr.io/seriaati/lumina:latest
       container_name: lumina
       restart: unless-stopped
       environment:
         - DISCORD_TOKEN=${DISCORD_TOKEN}
       volumes:
         - ./data:/app/data
         - ./logs:/app/logs
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
         interval: 30s
         timeout: 10s
         retries: 3
         start_period: 5s
   ```

2. Create a `.env` file in the same directory:

   ```env
   DISCORD_TOKEN=YourDiscordBotToken
   ```

3. Start the service:

   ```bash
   docker compose up -d
   ```

4. View logs:

   ```bash
   docker compose logs -f lumina
   ```

5. Stop the service:

   ```bash
   docker compose down
   ```

### Method 3: PM2 (Linux/macOS)

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and [PM2](https://pm2.keymetrics.io/):

   ```bash
   curl -sSf https://astral.sh/uv/install.sh | sh
   npm install -g pm2
   ```

2. Clone the repository:

   ```bash
   git clone https://github.com/seriaati/lumina.git
   cd lumina
   ```

3. Create a `.env` file:

   ```env
   DISCORD_TOKEN=YourDiscordBotToken
   ```

4. Install dependencies:

   ```bash
   uv sync --frozen
   ```

5. Start with PM2:

   ```bash
   pm2 start pm2.json
   ```

### Method 4: Manual (Development/Testing)

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/)

2. Clone the repository:

   ```bash
   git clone https://github.com/seriaati/lumina.git
   cd lumina
   ```

3. Create a `.env` file:

   ```env
   DISCORD_TOKEN=YourDiscordBotToken
   ```

4. Run the bot:

   ```bash
   uv run run.py
   ```

   This will automatically create a virtual environment and install dependencies on first run.

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_TOKEN` | Yes | - | Your Discord bot token |
| `DB_PATH` | No | `lumina.db` | Path to SQLite database file (Docker: `/app/data/lumina.db`) |

### Data Persistence

- **Database**: Lumina uses SQLite to store reminders, birthdays, todos, and notes
  - Docker: `/app/data/lumina.db`
  - Manual/PM2: `lumina.db` in the project root
- **Logs**: Application logs are stored in the `logs/` directory
  - Docker: `/app/logs/lumina.log`
  - Manual/PM2: `logs/lumina.log`
