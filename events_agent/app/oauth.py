import secrets
import base64
import httpx
import json
from urllib.parse import urlencode, parse_qs
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from supabase import create_client
from events_agent.infra.settings import settings
from events_agent.infra.logging import get_logger
from events_agent.infra.crypto import encrypt_token

logger = get_logger().bind(service="oauth")
router = APIRouter()

class OAuthHandler:
    def __init__(self):
        self.state_secret = settings.oauth_state_secret
        self._supabase = None
        
    @property
    def supabase(self):
        """Lazy initialization of Supabase client"""
        if self._supabase is None:
            if not settings.supabase_url or not settings.supabase_key:
                raise ValueError("Supabase URL and key must be configured for OAuth")
            self._supabase = create_client(settings.supabase_url, settings.supabase_key)
        return self._supabase
    
    def generate_state(self, user_id: str) -> str:
        """Generate a secure state parameter for OAuth"""
        nonce = secrets.token_urlsafe(32)
        state_data = f"{user_id}:{nonce}"
        return base64.urlsafe_b64encode(state_data.encode()).decode()
    
    def build_supabase_oauth_url(self, user_id: str) -> str:
        """Build Supabase OAuth URL using pure Supabase client"""
        # Don't use custom state - let Supabase handle state internally
        # Dynamic redirect URL based on environment
        redirect_url = f"{settings.base_url}/auth/success?user_id={user_id}"
        
        # Pure Supabase OAuth - let Supabase handle everything
        try:
            response = self.supabase.auth.sign_in_with_oauth({
                "provider": "google",
                "options": {
                    "redirect_to": redirect_url,
                    "scopes": "https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/calendar.events",
                    "query_params": {
                        "access_type": "offline",  # Request refresh token
                        "prompt": "consent",       # Force consent screen for refresh token
                        "include_granted_scopes": "true"  # Include all granted scopes
                    }
                }
            })
            
            if response.url:
                logger.info("supabase_oauth_url_generated", user_id=user_id, url_length=len(response.url))
                return response.url
            else:
                logger.warning("supabase_oauth_response_missing_url", user_id=user_id)
                # Fallback to manual URL building if needed
                params = {
                    'provider': 'google',
                    'redirect_to': redirect_url,
                    'scopes': 'https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/calendar.events',
                    'access_type': 'offline',
                    'prompt': 'consent',
                    'include_granted_scopes': 'true'
                }
                base_url = f"{settings.supabase_url}/auth/v1/authorize"
                manual_url = f"{base_url}?{urlencode(params)}"
                logger.info("using_manual_oauth_url", user_id=user_id, url_length=len(manual_url))
                return manual_url
                
        except Exception as e:
            logger.error("supabase_oauth_url_generation_failed", error=str(e))
            # Fallback to manual URL building
            params = {
                'provider': 'google',
                'redirect_to': redirect_url,
                'scopes': 'https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/calendar.events',
                'access_type': 'offline',
                'prompt': 'consent'
            }
            base_url = f"{settings.supabase_url}/auth/v1/authorize"
            return f"{base_url}?{urlencode(params)}"
    
    async def is_user_connected(self, discord_id: str) -> bool:
        """Check if a user has connected their Google Calendar using pure Supabase"""
        try:
            # Use service role key for backend operations
            if not settings.supabase_url:
                logger.error("supabase_url_not_configured")
                return False
                
            supabase_key = settings.supabase_service_role_key or settings.supabase_key
            if not supabase_key:
                logger.error("no_supabase_key_configured")
                return False
                
            supabase_client = create_client(settings.supabase_url, supabase_key)
            
            result = supabase_client.table("users").select("token_ciphertext").eq("discord_id", discord_id).execute()
            
            # User is connected if they exist and have encrypted tokens
            is_connected = bool(result.data and result.data[0].get("token_ciphertext"))
            logger.info("user_connection_check", discord_id=discord_id, connected=is_connected)
            return is_connected
        except Exception as e:
            logger.error("user_connection_check_failed", discord_id=discord_id, error=str(e))
        return False

oauth_handler = OAuthHandler()

@router.get("/connect/{user_id}")
async def connect_google_calendar(user_id: str):
    """Serve OAuth connection page with client-side Supabase auth"""
    
    # Check if Supabase is configured
    try:
        # This will trigger the lazy initialization and fail if not configured
        _ = oauth_handler.supabase
    except ValueError as e:
        return HTMLResponse("""
        <html>
            <head><title>Service Configuration Error</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1>⚙️ Service Not Configured</h1>
                <p>OAuth service is not currently configured.</p>
                <p>Please contact an administrator.</p>
            </body>
        </html>
        """, status_code=503)
    
    # Validate user_id
    if not user_id or not user_id.isdigit():
        return HTMLResponse("""
        <html>
            <head><title>Invalid User</title></head>
            <body>
                <h1>❌ Invalid User ID</h1>
                <p>Please use the Discord bot command to connect.</p>
            </body>
        </html>
        """, status_code=400)
    
    # Return page with client-side Supabase OAuth
    return HTMLResponse(f"""
    <html>
        <head>
            <title>Connect Google Calendar</title>
            <script src="https://unpkg.com/@supabase/supabase-js@2"></script>
            <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
            <meta http-equiv="Pragma" content="no-cache">
            <meta http-equiv="Expires" content="0">
        </head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h1>🔗 Connect Google Calendar</h1>
            <p>Click the button below to connect your Google Calendar account.</p>
            
            <button id="connectBtn" onclick="connectGoogle()" 
                    style="background: #4285f4; color: white; border: none; padding: 15px 30px; 
                           border-radius: 5px; font-size: 16px; cursor: pointer; margin: 20px;">
                � Connect Google Calendar
            </button>
            
            <div id="status" style="margin-top: 20px;"></div>
            <div id="debug" style="background: #f8f9fa; padding: 15px; margin: 20px 0; border-radius: 5px; 
                                   font-family: monospace; font-size: 12px; text-align: left; display: none;">
                <strong>Debug Info:</strong><br>
                <div id="debug-content"></div>
            </div>
            
            <script>
                // Initialize Supabase client with safer approach
                console.log('Initializing Supabase client...');
                console.log('Supabase global available:', typeof window.supabase !== 'undefined');
                
                // Use window.supabase explicitly to avoid scoping issues
                let supabaseClient;
                
                try {{
                    supabaseClient = window.supabase.createClient(
                        '{settings.supabase_url}',
                        '{settings.supabase_key}'
                    );
                    console.log('Supabase client initialized successfully');
                }} catch (initError) {{
                    console.error('Failed to initialize Supabase client:', initError);
                    document.getElementById('status').innerHTML = '❌ Failed to initialize Supabase: ' + initError.message;
                }}
                
                console.log('User ID: {user_id}');
                
                async function connectGoogle() {{
                    const connectBtn = document.getElementById('connectBtn');
                    const status = document.getElementById('status');
                    const debug = document.getElementById('debug');
                    
                    connectBtn.disabled = true;
                    connectBtn.textContent = '🔄 Connecting...';
                    status.innerHTML = 'Starting Google OAuth...';
                    debug.style.display = 'block';
                    
                    try {{
                        if (!supabaseClient) {{
                            throw new Error('Supabase client not initialized');
                        }}
                        
                        // Use Supabase client-side OAuth
                        console.log('Calling signInWithOAuth...');
                        const {{ data, error }} = await supabaseClient.auth.signInWithOAuth({{
                            provider: 'google',
                            options: {{
                                scopes: 'https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/calendar.events',
                                queryParams: {{
                                    access_type: 'offline',
                                    prompt: 'consent'
                                }},
                                redirectTo: '{settings.base_url}/auth/success?user_id={user_id}'
                            }}
                        }});
                        
                        console.log('OAuth response:', {{ data, error }});
                        
                        if (error) {{
                            console.error('Supabase OAuth error:', error);
                            status.innerHTML = '❌ OAuth failed: ' + error.message;
                            document.getElementById('debug-content').innerHTML = 
                                'Error: ' + JSON.stringify(error, null, 2);
                        }} else {{
                            console.log('OAuth initiated successfully');
                            status.innerHTML = '✅ Redirecting to Google...';
                            // The redirect should happen automatically
                        }}
                        
                    }} catch (err) {{
                        console.error('Connection error:', err);
                        status.innerHTML = '❌ Connection failed: ' + err.message;
                        document.getElementById('debug-content').innerHTML = 
                            'Exception: ' + err.toString() + '<br>Stack: ' + (err.stack || 'No stack trace');
                    }}
                    
                    connectBtn.disabled = false;
                    connectBtn.textContent = '🚀 Connect Google Calendar';
                }}
                
                // Handle OAuth callback if we're on the success page
                if (window.location.pathname.includes('/auth/success')) {{
                    handleOAuthCallback();
                }}
                
                async function handleOAuthCallback() {{
                    console.log('Handling OAuth callback...');
                    const status = document.getElementById('status');
                    const debug = document.getElementById('debug');
                    
                    status.innerHTML = '🔄 Processing OAuth response...';
                    debug.style.display = 'block';
                    
                    try {{
                        if (!supabaseClient) {{
                            throw new Error('Supabase client not initialized');
                        }}
                        
                        // Get session from Supabase
                        const {{ data: {{ session }}, error }} = await supabaseClient.auth.getSession();
                        
                        if (error) {{
                            console.error('Session error:', error);
                            status.innerHTML = '❌ Failed to get session: ' + error.message;
                            return;
                        }}
                        
                        if (session?.provider_token) {{
                            console.log('Found provider token!');
                            status.innerHTML = '✅ Tokens found! Storing in database...';
                            
                            // Send tokens to our server
                            const response = await fetch('/auth/store-tokens', {{
                                method: 'POST',
                                headers: {{
                                    'Content-Type': 'application/json'
                                }},
                                body: JSON.stringify({{
                                    user_id: '{user_id}',
                                    access_token: session.provider_token,
                                    refresh_token: session.provider_refresh_token
                                }})
                            }});
                            
                            if (response.ok) {{
                                status.innerHTML = '✅ Google Calendar connected successfully!';
                                setTimeout(() => window.close(), 3000);
                            }} else {{
                                const errorText = await response.text();
                                status.innerHTML = '❌ Failed to store tokens: ' + errorText;
                            }}
                            
                        }} else {{
                            console.log('No provider token found');
                            status.innerHTML = '⚠️ No provider tokens found in session';
                            document.getElementById('debug-content').innerHTML = 
                                'Session data: ' + JSON.stringify(session, null, 2);
                        }}
                        
                    }} catch (err) {{
                        console.error('Callback processing error:', err);
                        status.innerHTML = '❌ Processing failed: ' + err.message;
                        document.getElementById('debug-content').innerHTML = 
                            'Exception: ' + err.toString();
                    }}
                }}
            </script>
        </body>
    </html>
    """)


@router.get("/auth/debug")
async def debug_oauth(request: Request):
    """Debug OAuth configuration"""
    query_params = dict(request.query_params)
    
    return HTMLResponse(f"""
    <html>
        <head><title>OAuth Debug Info</title></head>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h1>🔍 OAuth Debug Information</h1>
            
            <h2>Environment:</h2>
            <ul>
                <li><strong>Base URL:</strong> {settings.base_url}</li>
                <li><strong>Supabase URL:</strong> {settings.supabase_url}</li>
                <li><strong>Has OAuth Secret:</strong> {bool(settings.oauth_state_secret)}</li>
            </ul>
            
            <h2>Query Parameters:</h2>
            <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px;">
{json.dumps(query_params, indent=2)}
            </pre>
            
            <h2>Expected Redirect URLs:</h2>
            <ul>
                <li><code>{settings.base_url}/auth/success</code></li>
                <li><code>{settings.base_url}/auth/success?user_id=YOUR_USER_ID</code></li>
            </ul>
            
            <p><a href="/connect/123456789">Test Connect Page</a></p>
        </body>
    </html>
    """)

@router.post("/auth/store-tokens")
async def store_tokens(request: Request):
    """Store Google OAuth tokens received from client-side auth"""
    try:
        # Check if Supabase is configured
        try:
            _ = oauth_handler.supabase
        except ValueError:
            return JSONResponse(
                content={"error": "OAuth service not configured"}, 
                status_code=503
            )
            
        body = await request.json()
        user_id = body.get('user_id')
        access_token = body.get('access_token') 
        refresh_token = body.get('refresh_token')
        
        if not user_id or not access_token:
            return JSONResponse(
                content={"error": "Missing user_id or access_token"}, 
                status_code=400
            )
        
        logger.info("storing_client_side_tokens", user_id=user_id, has_refresh=bool(refresh_token))
        
        # Store tokens using our existing function
        await store_google_tokens(user_id, access_token, refresh_token)
        
        return JSONResponse(content={"success": True, "message": "Tokens stored successfully"})
        
    except Exception as e:
        logger.error("token_storage_api_error", error=str(e))
        return JSONResponse(
            content={"error": f"Failed to store tokens: {str(e)}"}, 
            status_code=500
        )


@router.get("/auth/success")
async def auth_success(request: Request):
    """Handle OAuth success callback - redirect to client-side handling"""
    
    # Check if Supabase is configured
    try:
        _ = oauth_handler.supabase
    except ValueError:
        return HTMLResponse("""
        <html>
            <head><title>Service Configuration Error</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1>⚙️ Service Not Configured</h1>
                <p>OAuth service is not currently configured.</p>
                <p>Please contact an administrator.</p>
            </body>
        </html>
        """, status_code=503)
    
    query_params = dict(request.query_params)
    user_id = query_params.get('user_id')
    
    # Log all query parameters for debugging
    logger.info("oauth_success_callback", query_params=query_params, user_id=user_id)
    
    # Check for OAuth error parameters
    error = query_params.get('error')
    error_description = query_params.get('error_description')
    
    if error:
        logger.error("oauth_callback_error", error=error, description=error_description)
        return HTMLResponse(f"""
        <html>
            <head><title>OAuth Error</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1>❌ OAuth Error</h1>
                <p><strong>Error:</strong> {error}</p>
                <p><strong>Description:</strong> {error_description or 'No description provided'}</p>
                <div style="background: #f8f9fa; padding: 15px; margin: 20px 0; border-radius: 5px; font-family: monospace; font-size: 12px;">
                    <strong>Query Parameters:</strong><br>
                    {dict(query_params)}
                </div>
                <p>Please try connecting again from Discord.</p>
            </body>
        </html>
        """, status_code=400)
    
    if not user_id:
        return HTMLResponse("""
        <html>
            <head><title>OAuth Error</title></head>
            <body>
                <h1>❌ Missing User ID</h1>
                <p>Please use the Discord bot command to connect.</p>
            </body>
        </html>
        """, status_code=400)
    
    # Redirect to client-side OAuth page with user_id
    return HTMLResponse(f"""
    <html>
        <head>
            <title>Processing OAuth...</title>
            <script src="https://unpkg.com/@supabase/supabase-js@2"></script>
        </head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h1>🔄 Processing OAuth Response...</h1>
            <p id="status">Checking for OAuth tokens...</p>
            
            <script>
                // Initialize Supabase client
                console.log('Processing OAuth response page...');
                console.log('Supabase global available:', typeof supabase !== 'undefined');
                
                const supabaseClient = supabase.createClient(
                    '{settings.supabase_url}',
                    '{settings.supabase_key}'
                );
                
                async function processOAuthResponse() {{
                    const status = document.getElementById('status');
                    
                    try {{
                        // Get current session from Supabase
                        const {{ data: {{ session }}, error }} = await supabaseClient.auth.getSession();
                        
                        console.log('Session data:', session);
                        console.log('Session error:', error);
                        
                        if (error) {{
                            status.innerHTML = '❌ Session error: ' + error.message;
                            return;
                        }}
                        
                        if (session?.provider_token) {{
                            status.innerHTML = '✅ Tokens found! Storing...';
                            
                            // Send tokens to server
                            const response = await fetch('/auth/store-tokens', {{
                                method: 'POST',
                                headers: {{ 'Content-Type': 'application/json' }},
                                body: JSON.stringify({{
                                    user_id: '{user_id}',
                                    access_token: session.provider_token,
                                    refresh_token: session.provider_refresh_token
                                }})
                            }});
                            
                            if (response.ok) {{
                                status.innerHTML = '✅ Google Calendar connected successfully!';
                                setTimeout(() => window.close(), 3000);
                            }} else {{
                                const errorText = await response.text();
                                status.innerHTML = '❌ Storage failed: ' + errorText;
                            }}
                        }} else {{
                            status.innerHTML = '⚠️ No provider tokens found. Please check Supabase Google provider configuration.';
                            console.log('Full session object:', JSON.stringify(session, null, 2));
                        }}
                        
                    }} catch (err) {{
                        console.error('Processing error:', err);
                        status.innerHTML = '❌ Processing failed: ' + err.message;
                    }}
                }}
                
                // Start processing
                processOAuthResponse();
            </script>
        </body>
    </html>
    """)


async def store_google_tokens(user_id: str, access_token: str, refresh_token: str | None = None):
    """Store Google OAuth tokens for a user using pure Supabase"""
    logger.info("store_google_tokens_start", discord_id=user_id, has_refresh=bool(refresh_token))
    
    # Get Google user info
    google_sub = None
    google_email = None
    
    try:
        async with httpx.AsyncClient() as client:
            user_info_response = await client.get(
                f'https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}'
            )
            
            if user_info_response.status_code == 200:
                user_info = user_info_response.json()
                google_sub = user_info.get('id')
                google_email = user_info.get('email')
                logger.info("google_user_info_received", google_sub=google_sub, email=google_email)
            else:
                logger.warning("google_user_info_failed", status=user_info_response.status_code)
    except Exception as e:
        logger.warning("google_user_info_error", error=str(e))
    
    # Create token structure for Google Calendar API
    tokens = {
        'access_token': access_token,
        'token_type': 'Bearer',
        'scope': 'https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/calendar.events'
    }
    
    if refresh_token:
        tokens['refresh_token'] = refresh_token
    
    # Use pure Supabase with service role key
    try:
        logger.info("encrypting_tokens", discord_id=user_id)
        encrypted_tokens = encrypt_token(json.dumps(tokens))
        logger.info("tokens_encrypted_successfully", discord_id=user_id)
        
        # Use service role key for backend operations (bypasses RLS)
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise Exception("Supabase URL or service role key not configured")
            
        logger.info("using_supabase_service_role", discord_id=user_id)
        
        from supabase import create_client
        supabase_client = create_client(settings.supabase_url, settings.supabase_service_role_key)
        
        # Store user data via Supabase REST API
        user_data = {
            "discord_id": user_id,
            "email": google_email,
            "google_sub": google_sub or "",
            "token_ciphertext": encrypted_tokens,
            "tz": "Australia/Melbourne"
        }
        
        # Use upsert to create or update user
        result = supabase_client.table("users").upsert(user_data, on_conflict="discord_id").execute()
        
        if result.data:
            logger.info("tokens_stored_via_supabase", discord_id=user_id, has_refresh=bool(refresh_token))
            return  # Success!
        else:
            raise Exception("Supabase upsert returned no data")
                
    except Exception as e:
        logger.error("token_storage_failed", discord_id=user_id, error=str(e), error_type=type(e).__name__)
        raise Exception(f"Token storage failed: {str(e)}")


def success_response(user_id: str) -> HTMLResponse:
    """Generate success response page"""
    return HTMLResponse(f"""
    <html>
        <head><title>Google Calendar Connected!</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h1 style="color: #28a745;">✅ Google Calendar Connected!</h1>
            <p>Your Google Calendar has been successfully connected!</p>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Discord User:</strong> {user_id}</p>
                <p><strong>Status:</strong> ✅ Ready to use calendar commands</p>
            </div>
            <p>You can now close this window and use calendar commands in Discord!</p>
            <p><em>Try: <code>/addevent title:Meeting time:tomorrow 2pm</code></em></p>
            <script>
                setTimeout(() => window.close(), 5000);
            </script>
        </body>
    </html>
    """)


def error_response(message: str) -> HTMLResponse:
    """Generate error response page"""
    return HTMLResponse(f"""
    <html>
        <head><title>OAuth Error</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h1 style="color: #dc3545;">❌ Connection Failed</h1>
            <p>{message}</p>
            <p>Please try connecting again.</p>
            <script>setTimeout(() => window.close(), 5000);</script>
        </body>
    </html>
    """)