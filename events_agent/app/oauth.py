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
        
        # Use Supabase Auth for Google OAuth
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
    access_token = query_params.get('access_token')
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
                if (window.location.hash && window.location.hash.includes('access_token')) {{
                    console.log('Found tokens in fragment, extracting...');
                    const fragmentParams = new URLSearchParams(window.location.hash.substring(1));
                    const accessToken = fragmentParams.get('access_token');
                    const refreshToken = fragmentParams.get('refresh_token');
                    
                    if (accessToken) {{
                        console.log('Redirecting with tokens...');
                        // Redirect to self with tokens in query params
                        const newUrl = new URL(window.location);
                        newUrl.searchParams.set('access_token', accessToken);
                        if (refreshToken) {{
                            newUrl.searchParams.set('refresh_token', refreshToken);
                        }}
                        newUrl.hash = '';
                        window.location.replace(newUrl.href);
                        return;
                    }}
                }}
                
                // If no tokens found, just close after delay
                setTimeout(() => {{
                    document.getElementById('status').innerHTML = '⚠️ No tokens found in URL';
                    setTimeout(() => window.close(), 2000);
                }}, 2000);
            </script>
        </body>
    </html>
    """)

@router.get("/auth/callback")
async def oauth_callback(request: Request):
    """Handle OAuth callback from Google"""
    query_params = dict(request.query_params)
    
    # Check for errors
    if 'error' in query_params:
        error = query_params.get('error')
        error_description = query_params.get('error_description', 'Unknown error')
        logger.error("oauth_error", error=error, description=error_description)
        
        return HTMLResponse(f"""
        <html>
            <head><title>OAuth Error</title></head>
            <body>
                <h1>❌ OAuth Error</h1>
                <p><strong>Error:</strong> {error}</p>
                <p><strong>Description:</strong> {error_description}</p>
                <p>Please try again or contact support if this error persists.</p>
                <script>setTimeout(() => window.close(), 5000);</script>
            </body>
        </html>
        """)
    
    # Get authorization code and state
    code = query_params.get('code')
    state = query_params.get('state')
    
    if not code:
        logger.error("oauth_missing_code")
        return HTMLResponse("""
        <html>
            <head><title>OAuth Error</title></head>
            <body>
                <h1>❌ Missing Authorization Code</h1>
                <p>No authorization code received from Google.</p>
                <script>setTimeout(() => window.close(), 5000);</script>
            </body>
        </html>
        """)
    
    if not state:
        logger.error("oauth_missing_state")
        return HTMLResponse("""
        <html>
            <head><title>OAuth Error</title></head>
            <body>
                <h1>❌ Missing State Parameter</h1>
                <p>No state parameter received. This may be a security issue.</p>
                <script>setTimeout(() => window.close(), 5000);</script>
            </body>
        </html>
        """)
    
    # Verify state and extract user ID
    try:
        decoded = base64.urlsafe_b64decode(state.encode()).decode()
        user_id, nonce = decoded.split(':', 1)
        logger.info("oauth_success", user_id=user_id, code_length=len(code))
    except Exception as e:
        logger.error("oauth_invalid_state", error=str(e))
        return HTMLResponse("""
        <html>
            <head><title>OAuth Error</title></head>
            <body>
                <h1>❌ Invalid State Parameter</h1>
                <p>The state parameter is invalid or corrupted.</p>
                <script>setTimeout(() => window.close(), 5000);</script>
            </body>
        </html>
        """)
    
    try:
        async with httpx.AsyncClient() as client:
            token_data = {
                'client_id': settings.google_client_id,
                'client_secret': settings.google_client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': settings.oauth_redirect_uri,
            }
            
            logger.info("exchanging_code_for_tokens", user_id=user_id)
            
            response = await client.post(
                'https://oauth2.googleapis.com/token',
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code != 200:
                logger.error("token_exchange_failed", status=response.status_code, error=response.text)
                raise Exception(f"Token exchange failed: {response.status_code}")
            
            tokens = response.json()
            logger.info("tokens_received", user_id=user_id, has_refresh=bool(tokens.get('refresh_token')))
            
            # Store tokens in database
            async for session in session_scope():
                user_repo = UserRepository(session)
                
                # Get or create user
                user = await user_repo.get_or_create_user(discord_id=user_id)
                logger.info("user_ready", discord_id=user_id, user_id=user.id)
                
                # Get Google user info to extract google_sub
                user_info_response = await client.get(
                    f'https://www.googleapis.com/oauth2/v1/userinfo?access_token={tokens["access_token"]}'
                )
                
                google_sub = None
                if user_info_response.status_code == 200:
                    user_info = user_info_response.json()
                    google_sub = user_info.get('id')
                    logger.info("google_user_info_received", google_sub=google_sub)
                
                # Encrypt and store tokens
                encrypted_tokens = encrypt_token(json.dumps(tokens))
                await user_repo.update_user_token(user_id, encrypted_tokens, google_sub or "")
                
                logger.info("tokens_stored", user_id=user.id, discord_id=user_id)
                break
    
    except Exception as e:
        logger.error("oauth_completion_failed", user_id=user_id, error=str(e))
        return HTMLResponse(f"""
        <html>
            <head><title>OAuth Error</title></head>
            <body>
                <h1>❌ OAuth Completion Failed</h1>
                <p>Failed to complete OAuth setup: {str(e)}</p>
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
            <p>Your Google Calendar has been successfully connected to your Discord account.</p>
            <p><strong>User ID:</strong> {user_id}</p>
            <p>You can now close this window and use calendar commands in Discord!</p>
            <script>setTimeout(() => window.close(), 3000);</script>
        </body>
    </html>
    """)