# Calendar Agent

A comprehensive Discord bot that integrates with Google Calendar for seamless event management. Built with FastAPI, SQLAlchemy, and modern async Python for production-grade performance.

## Features

- **Discord Integration**: Native Discord slash commands for calendar management
- **Google Calendar Sync**: Full OAuth2 integration with Google Calendar API
- **Smart Reminders**: Automated event reminders with configurable timing
- **Timezone Support**: Multi-timezone awareness with user-specific settings
- **Natural Language**: Parse natural language date and time expressions
- **Security**: Encrypted token storage and secure OAuth flow
- **Monitoring**: Built-in Prometheus metrics and health checks
- **Production Ready**: Async architecture with comprehensive error handling and logging

## Quick Start

### Prerequisites

- Python 3.12+
- Discord Bot Token
- Google Cloud Project with Calendar API enabled
- Supabase account (or SQLite for development)

### Installation

1. **Clone and install dependencies:**
   ```bash
   git clone https://github.com/Rudra-Tiwari-codes/Calendar-Agent.git
   cd Calendar-Agent/events-agent
   uv sync
   ```

2. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```ini
   # Discord Configuration
   DISCORD_TOKEN=your_discord_bot_token_here
   
   # Database Configuration
   # For Supabase (production):
   DATABASE_URL=postgresql+asyncpg://postgres:[YOUR_PASSWORD]@db.[YOUR_PROJECT_ID].supabase.co:6543/postgres
   # For SQLite (development):
   # DATABASE_URL=sqlite+aiosqlite:///./events_agent.db
   
   # Application Settings
   DEFAULT_TZ=Australia/Melbourne
   HTTP_HOST=0.0.0.0
   HTTP_PORT=8000
   
   # Security
   FERNET_KEY=your_base64_32byte_encryption_key
   
   # Google OAuth Configuration
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   OAUTH_REDIRECT_URI=http://localhost:8000/oauth/callback
   
   # Supabase Configuration
   SUPABASE_URL=https://your_project.supabase.co
   SUPABASE_ANON_KEY=your_supabase_anon_key
   ```

3. **Initialize the database:**
   ```bash
   uv run alembic upgrade head
   ```

4. **Test the setup:**
   ```bash
   uv run python test_calendar_agent.py
   ```

5. **Run the application:**
   ```bash
   uv run python -m events_agent.main
   ```

## Discord Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/ping` | Test bot connectivity | `/ping` |
| `/connect` | Link your Google Calendar | `/connect` |
| `/addevent` | Create a new calendar event | `/addevent title:Team Meeting time:tomorrow 2pm attendees:user1@example.com,user2@example.com` |
| `/myevents` | List your upcoming events | `/myevents 5` (shows next 5 events) |
| `/set-tz` | Set your timezone | `/set-tz timezone:Australia/Melbourne` |
| `/suggest` | Find optimal meeting times | `/suggest duration_minutes:60 days_ahead:7` |

## API Endpoints

The bot also exposes a REST API for programmatic access:

- **`GET /healthz`** - Health check endpoint
- **`GET /readyz`** - Readiness check (verifies database connectivity)
- **`GET /metrics`** - Prometheus metrics for monitoring
- **`GET /oauth/callback`** - OAuth callback for Google Calendar integration

## Architecture

```
src/events_agent/
├── adapters/          # External service integrations (Google Calendar)
├── app/              # FastAPI application and OAuth handling
├── bot/              # Discord bot implementation
├── domain/           # Core business models and entities
├── infra/            # Infrastructure concerns (DB, logging, settings)
├── services/         # Business logic services
└── main.py           # Application entry point
```

### Key Components

- **Async Architecture**: Built on FastAPI and async SQLAlchemy for high performance
- **Clean Architecture**: Separation of concerns with adapters, domain, and infrastructure layers
- **Secure Token Storage**: Encrypted storage of OAuth tokens using Fernet encryption
- **Robust Error Handling**: Comprehensive error handling with structured logging
- **Database Migrations**: Alembic for schema management

## Testing

### Run the Test Suite

```bash
uv run python test_calendar_agent.py
```

This will test:
- Database connection
- Natural language parsing
- Google Calendar credentials
- Discord bot token
- Settings configuration
- Event details extraction

### Manual Testing Flow

1. **Start the bot:**
   ```bash
   uv run python -m events_agent.main
   ```

2. **Test Discord commands:**
   - Use `/ping` to verify bot is online
   - Use `/connect` to link Google Calendar
   - Use `/addevent` to create an event
   - Use `/myevents` to list events

3. **Verify Google Calendar:**
   - Check that events appear in your Google Calendar
   - Verify event details are correct

4. **Test reminders:**
   - Create an event with a reminder
   - Wait for the reminder notification in Discord

## Docker Deployment

```dockerfile
FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY . .
RUN pip install --no-cache-dir uv
RUN uv sync --frozen
CMD ["uv", "run", "python", "-m", "events_agent.main"]
```

## Development

### Database Migrations

```bash
# Create a new migration
uv run alembic revision -m "description_of_changes"

# Apply migrations
uv run alembic upgrade head

# Rollback migrations
uv run alembic downgrade -1
```

### Code Quality

```bash
# Linting with Ruff
uvx --from ruff ruff .

# Type checking with MyPy
uvx --from mypy mypy src

# Format code
uvx --from ruff ruff format .
```

## Monitoring and Observability

- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Prometheus Metrics**: Built-in metrics for monitoring bot performance
- **Health Checks**: Kubernetes-ready health and readiness endpoints
- **Error Tracking**: Comprehensive error handling and reporting

## Security Features

- **OAuth2 Flow**: Secure Google Calendar integration
- **Token Encryption**: Fernet encryption for stored OAuth tokens
- **Input Validation**: Pydantic models for request validation
- **Rate Limiting**: Built-in rate limiting for API endpoints

## Troubleshooting

### Common Issues

1. **Bot not responding:**
   - Check Discord token is correct
   - Verify bot has proper permissions in Discord server
   - Check logs for error messages

2. **Google Calendar not working:**
   - Verify Google credentials file exists
   - Check OAuth redirect URI is correct
   - Ensure Calendar API is enabled in Google Cloud Console

3. **Database connection issues:**
   - Check DATABASE_URL is correct
   - For Supabase: verify password and connection string
   - For SQLite: ensure write permissions

4. **Natural language parsing errors:**
   - Use specific time formats: "tomorrow 3pm", "next monday 2pm"
   - Include timezone in settings if needed

### Debug Mode

Set `LOG_LEVEL=DEBUG` in your `.env` file for detailed logging.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.

---

## API Keys Setup Guide

### Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section and create a bot
4. Copy the bot token to `DISCORD_TOKEN` in `.env`
5. Invite bot to your server with these permissions:
   - Send Messages
   - Use Slash Commands
   - Embed Links
   - Read Message History

### Google Calendar API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials (Web application)
5. Add `http://localhost:8000/oauth/callback` to authorized redirect URIs
6. Download credentials JSON file as `client_secret.json`
7. Copy client ID and secret to `.env`

### Supabase Setup

1. Go to [Supabase](https://supabase.com/)
2. Create a new project
3. Go to Settings > Database
4. Copy the connection string and update `DATABASE_URL`
5. Copy the anon key to `SUPABASE_ANON_KEY`

