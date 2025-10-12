
# Calendar Agent

A professional Discord bot for Google Calendar event management, built with FastAPI and asynchronous Python.

## Features
- Manage Google Calendar events via Discord
- OAuth integration for secure authentication
- Timezone support
- Supabase PostgreSQL backend

## Project Structure

```
events_agent/
	adapters/    # Integrations (Google Calendar)
	app/         # FastAPI app & OAuth
	bot/         # Discord bot
	domain/      # Business models
	infra/       # Infrastructure (DB, logging)
	services/    # Business logic
	main.py      # Entry point
```

## Setup

**Requirements:**
- Python 3.12+
- Discord Bot Token
- Google Cloud Project (Calendar API enabled)
- Supabase PostgreSQL database

**Installation:**
```powershell
git clone https://github.com/Rudra-Tiwari-codes/Calendar-Agent.git
cd Calendar-Agent/events-agent
uv sync
```

**Environment Variables:**
Create a `.env` file with:
```
DISCORD_TOKEN=your_token
DATABASE_URL=your_db_url
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
DEFAULT_TZ=Australia/Melbourne
FERNET_KEY=your_fernet_key
```

**Database Migration:**
```powershell
uv run alembic upgrade head
```

**Run the Bot:**
```powershell
uv run python -m events_agent.main
```

## Usage

Use Discord slash commands:
- `/ping` — Check bot status
- `/connect` — Link Google Calendar
- `/addevent` — Add event
- `/myevents` — List events
- `/set-tz` — Set timezone

Full Video Walkthrough:

Watch the full demo on YouTube: [https://youtu.be/p5IEfjwj8Gk](https://youtu.be/WL98aE5H1Xo)
