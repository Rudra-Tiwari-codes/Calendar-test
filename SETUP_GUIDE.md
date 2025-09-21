# Calendar Agent Setup Guide

## Quick Setup

### Step 1: Environment Setup
```bash
cd events-agent
cp .env.example .env
```

### Step 2: Fill in your .env file
```bash
# Discord Configuration
DISCORD_TOKEN=your_discord_bot_token

# Database Configuration (Supabase)
DATABASE_URL=postgresql+asyncpg://postgres:[YOUR_PASSWORD]@db.[YOUR_PROJECT_ID].supabase.co:5432/postgres
SUPABASE_URL=https://[YOUR_PROJECT_ID].supabase.co
SUPABASE_KEY=[YOUR_SUPABASE_ANON_KEY]

# Security (generate a key)
FERNET_KEY=[run: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"]

# Google OAuth (optional for now)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

### Step 3: Install Dependencies
```bash
# Option 1: Using uv (recommended)
uv sync

# Option 2: Using pip
pip install -r requirements.txt
```

### Step 4: Test Integration
```bash
python quick_test.py
```

### Step 5: Run the Bot
```bash
python run_bot.py
```

## Getting Your Supabase Credentials

1. Go to [supabase.com](https://supabase.com)
2. Sign up with dscubed email
3. Create new project
4. Go to Settings → API
5. Copy:
   - Project URL → `SUPABASE_URL`
   - anon/public key → `SUPABASE_KEY` 
6. Go to Settings → Database
7. Copy connection string → `DATABASE_URL`

## Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create New Application → "Calendar Agent"
3. Bot tab → Reset Token → Copy token → `DISCORD_TOKEN`
4. Bot Permissions: Send Messages, Use Slash Commands
5. Invite bot to your server

## Testing Your Setup

After running `quick_test.py`, you should see:
- Environment variables loaded
- Database connection successful
- Discord bot creation successful
- All imports working

## Test Commands in Discord

1. `/ping` - Test bot is online
2. `/addevent tomorrow 3pm Team meeting` - Create event
3. `/myevents` - List upcoming events  
4. `/set-tz America/New_York` - Set timezone

## Troubleshooting

**Database connection failed?**
- Check your Supabase credentials
- Ensure your IP is allowed in Supabase dashboard

**Discord bot not responding?**
- Verify bot token is correct
- Check bot has permissions in your server
- Ensure bot is invited with slash command permissions

**Import errors?**
- Run `uv sync` to install all dependencies
- Check you're in the events-agent directory

## Common Issues and Fixes

1. **"Table doesn't exist"** → Database migrations not run
   ```bash
   alembic upgrade head
   ```

2. **"Permission denied"** → Bot missing permissions in Discord server

3. **"Connection refused"** → Wrong database URL or Supabase project not active

4. **"Invalid token"** → Discord token expired, reset in Developer Portal

---

**Need help?** Run `python quick_test.py` and share the output!