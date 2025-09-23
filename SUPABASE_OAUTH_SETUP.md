# Supabase OAuth Setup Guide

This project uses **Supabase's built-in OAuth** for Google Calendar integration. This means you don't need to handle OAuth tokens manually or use `client_secret.json` files.

## Setup Steps

### 1. Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable **Google Calendar API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client IDs**
5. Choose **Web application**
6. In **Authorized redirect URIs**, add:
   ```
   https://[YOUR_PROJECT_ID].supabase.co/auth/v1/callback
   ```
7. Copy the **Client ID** and **Client Secret**

### 2. Supabase Dashboard Setup

1. Go to your [Supabase Dashboard](https://supabase.com/dashboard)
2. Navigate to **Authentication** → **Providers**
3. Find **Google** and click **Configure**
4. Enable the Google provider
5. Paste your **Client ID** and **Client Secret** from step 1
6. In **Scopes**, add:
   ```
   https://www.googleapis.com/auth/calendar
   https://www.googleapis.com/auth/calendar.events
   ```
7. Save the configuration

### 3. Environment Configuration

Your `.env` file should only need:

```ini
# Supabase Configuration
SUPABASE_URL=https://[YOUR_PROJECT_ID].supabase.co
SUPABASE_KEY=[YOUR_SUPABASE_ANON_KEY]

# Optional: Only if you need them for other services
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

## How It Works

1. User runs `/connect` command in Discord
2. Bot generates a Supabase OAuth URL pointing to: `https://[PROJECT].supabase.co/auth/v1/authorize?provider=google`
3. User authorizes via Google OAuth (managed by Supabase)
4. Supabase redirects to your app's `/auth/success` endpoint with tokens
5. Your app extracts and stores the Google provider tokens

## Benefits of Supabase OAuth

✅ **No manual token exchange** - Supabase handles it  
✅ **No client_secret.json files** - Credentials stored securely in Supabase  
✅ **Automatic token refresh** - Supabase can handle refresh tokens  
✅ **Better security** - OAuth flow managed by Supabase infrastructure  
✅ **Simpler deployment** - No credential files to manage  

## What NOT to do

❌ Don't download `client_secret.json` files  
❌ Don't set up manual OAuth redirect URIs in your app  
❌ Don't manually exchange authorization codes for tokens  
❌ Don't store Google credentials in your `.env` for OAuth (only for other Google APIs if needed)

## Testing

After setup, test with:

```bash
uv run python test_calendar_agent.py
```

The test will verify your Supabase OAuth configuration is working properly.