import secrets
import base64
import httpx
import json
from urllib.parse import urlencode, parse_qs
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from events_agent.infra.settings import settings
from events_agent.infra.logging import get_logger
from events_agent.infra.db import session_scope
from events_agent.infra.event_repository import UserRepository
from events_agent.infra.crypto import encrypt_token

logger = get_logger().bind(service="oauth")
router = APIRouter()

class OAuthHandler:
    def __init__(self):
        self.state_secret = settings.oauth_state_secret
    
    def generate_state(self, user_id: str) -> str:
        """Generate a secure state parameter for OAuth"""
        nonce = secrets.token_urlsafe(32)
        state_data = f"{user_id}:{nonce}"
        return base64.urlsafe_b64encode(state_data.encode()).decode()
    
    def build_supabase_oauth_url(self, user_id: str) -> str:
        """Build Supabase OAuth URL with state parameter"""
        state = self.generate_state(user_id)
        
        # Use Supabase Auth for Google OAuth - Supabase manages everything
        params = {
            'provider': 'google',
            'redirect_to': f'http://localhost:8000/auth/success?state={state}&user_id={user_id}',
            'scopes': 'https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/calendar.events'
        }
        
        base_url = f"{settings.supabase_url}/auth/v1/authorize"
        return f"{base_url}?{urlencode(params)}"

oauth_handler = OAuthHandler()

@router.get("/auth/success")
async def oauth_success(request: Request):
    """Handle OAuth success callback from Supabase"""
    query_params = dict(request.query_params)
    user_id = query_params.get('user_id')
    state = query_params.get('state')
    
    # Check for tokens in query parameters (after JavaScript redirect)
    access_token = query_params.get('access_token')  # This will be the Google provider_token
    refresh_token = query_params.get('refresh_token')
    
    logger.info("supabase_oauth_callback", user_id=user_id, has_state=bool(state), has_access_token=bool(access_token))
    
    if access_token and user_id:
        # We have tokens - store them
        try:
            async with httpx.AsyncClient() as client:
                # Get Google user info
                user_info_response = await client.get(
                    f'https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}'
                )
                
                google_sub = None
                if user_info_response.status_code == 200:
                    user_info = user_info_response.json()
                    google_sub = user_info.get('id')
                    logger.info("google_user_info_received", google_sub=google_sub)
                
                # Store tokens in database
                async for session in session_scope():
                    user_repo = UserRepository(session)
                    
                    # Get or create user
                    user = await user_repo.get_or_create_user(discord_id=user_id)
                    logger.info("user_ready", discord_id=user_id, user_id=user.id)
                    
                    # Create token structure
                    tokens = {
                        'access_token': access_token,
                        'token_type': 'Bearer',
                        'scope': 'https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/calendar.events'
                    }
                    
                    if refresh_token:
                        tokens['refresh_token'] = refresh_token
                    
                    # Encrypt and store tokens
                    encrypted_tokens = encrypt_token(json.dumps(tokens))
                    await user_repo.update_user_token(user_id, encrypted_tokens, google_sub or "")
                    
                    logger.info("supabase_tokens_stored", user_id=user.id, discord_id=user_id)
                    break
                    
        except Exception as e:
            logger.error("supabase_token_storage_failed", user_id=user_id, error=str(e))
            return HTMLResponse(f"""
            <html>
                <head><title>OAuth Error</title></head>
                <body>
                    <h1>❌ Token Storage Failed</h1>
                    <p>Failed to store tokens: {str(e)}</p>
                    <p>Please try connecting again.</p>
                    <script>setTimeout(() => window.close(), 5000);</script>
                </body>
            </html>
            """)
    
    return HTMLResponse(f"""
    <html>
        <head><title>OAuth Success</title></head>
        <body>
            <h1>✅ Google Calendar Connected!</h1>
            <p>Your Google Calendar has been successfully connected via Supabase!</p>
            <p><strong>User ID:</strong> {user_id}</p>
            <p><strong>Status:</strong> <span id="status">{"✅ Tokens stored successfully!" if access_token else "🔄 Extracting tokens from URL..."}</span></p>
            <p>You can now close this window and use calendar commands in Discord!</p>
            <script>
                console.log('Full URL:', window.location.href);
                console.log('Hash:', window.location.hash);
                console.log('Search:', window.location.search);
                
                // Check if we already have tokens in query params
                const currentParams = new URLSearchParams(window.location.search);
                if (currentParams.get('access_token')) {{
                    document.getElementById('status').innerHTML = '✅ Tokens stored successfully!';
                    setTimeout(() => window.close(), 3000);
                    return;
                }}
                
                // Extract tokens from URL fragment if present
                if (window.location.hash && window.location.hash.length > 1) {{
                    console.log('Found hash fragment, checking for provider_token...');
                    
                    // Get the hash without the #
                    const hashString = window.location.hash.substring(1);
                    console.log('Hash string:', hashString);
                    
                    // Look for provider_token directly in the string
                    const providerTokenMatch = hashString.match(/provider_token=([^&]+)/);
                    const refreshTokenMatch = hashString.match(/refresh_token=([^&]+)/);
                    
                    if (providerTokenMatch) {{
                        // Decode in case values are URL-encoded
                        const providerToken = decodeURIComponent(providerTokenMatch[1]);
                        const refreshToken = refreshTokenMatch ? decodeURIComponent(refreshTokenMatch[1]) : null;
                        
                        console.log('Found provider_token:', providerToken.substring(0, 20) + '...');
                        console.log('Found refresh_token:', refreshToken);
                        
                        // Update status while redirecting for storage
                        const statusEl = document.getElementById('status');
                        if (statusEl) {{
                            statusEl.innerHTML = '📦 Storing tokens...';
                        }}

                        // Redirect to self with Google tokens in query params
                        const newUrl = new URL(window.location);
                        newUrl.searchParams.set('access_token', providerToken);
                        if (refreshToken) {{
                            newUrl.searchParams.set('refresh_token', refreshToken);
                        }}
                        newUrl.hash = '';
                        console.log('Redirecting to:', newUrl.href);
                        window.location.replace(newUrl.href);
                        return;
                    }} else {{
                        console.log('No provider_token found in hash');
                    }}
                }}
                
                // If no provider_token found, show error after delay
                setTimeout(() => {{
                    document.getElementById('status').innerHTML = '⚠️ No Google OAuth token found in URL';
                    setTimeout(() => window.close(), 2000);
                }}, 2000);
            </script>
        </body>
    </html>
    """)