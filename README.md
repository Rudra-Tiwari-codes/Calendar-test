src/events_agent/
├── adapters/          # External service integrations (Google Calendar)
├── app/              # FastAPI application and OAuth handling
├── bot/              # Discord bot implementation
├── domain/           # Core business models and entities
├── infra/            # Infrastructure concerns (DB, logging, settings)
├── services/         # Business logic services
└── main.py           # Application entry point

# Calendar Agent

Discord bot for Google Calendar event management. Built with FastAPI and async Python.

## Setup

**Requirements:**
- Python 3.12+
- Discord Bot Token
- Google Cloud Project (Calendar API enabled)
- Supabase PostgreSQL database

**Install:**
```bash
git clone https://github.com/Rudra-Tiwari-codes/Calendar-Agent.git
cd Calendar-Agent/events-agent
uv sync
```

**Environment:**
Create a `.env` file:
```
DISCORD_TOKEN=your_token
DATABASE_URL=your_db_url
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
DEFAULT_TZ=Australia/Melbourne
FERNET_KEY=your_fernet_key
```

**Migrate DB:**
```bash
uv run alembic upgrade head
```

**Run:**
```bash
uv run python -m events_agent.main
```

## Usage

Use Discord slash commands:
- /ping — Check bot status
- /connect — Link Google Calendar
- /addevent — Add event
- /myevents — List events
- /set-tz — Set timezone

## License

MIT

