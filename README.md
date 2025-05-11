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

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
1. Clone the repository
1. Create a `.env` file:

   ```env
   DISCORD_TOKEN=YourDiscordBotToken
   ```

1. `uv run run.py`
