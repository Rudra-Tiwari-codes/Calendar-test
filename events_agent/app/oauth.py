from __future__ import annotations

import secrets
import time
from typing import Dict

from fastapi import APIRouter, HTTPException, Query
from starlette.responses import JSONResponse, RedirectResponse, HTMLResponse
from typing import Union

from ..infra.crypto import encrypt_text
from ..infra.logging import get_logger
from ..infra.settings import settings


router = APIRouter()
logger = get_logger().bind(service="http")

_state_cache: Dict[str, float] = {}


def _make_state(discord_id: str) -> str:
    nonce = secrets.token_urlsafe(16)
    state = f"{discord_id}:{nonce}"
    _state_cache[state] = time.time() + 300
    return state


def _consume_state(state: str) -> str:
    exp = _state_cache.get(state)
    if not exp or exp < time.time():
        raise HTTPException(status_code=400, detail="invalid_state")
    del _state_cache[state]
    discord_id = state.split(":", 1)[0]
    return discord_id


@router.get("/oauth/start")
async def oauth_start(discord_id: str = Query(...)) -> JSONResponse:
    if not settings.google_client_id or not settings.oauth_redirect_uri:
        raise HTTPException(status_code=500, detail="oauth_not_configured")
    state = _make_state(discord_id)
    params = {
        "response_type": "code",
        "client_id": settings.google_client_id,
        "redirect_uri": settings.oauth_redirect_uri,
        "scope": "openid email https://www.googleapis.com/auth/calendar",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    from urllib.parse import urlencode

    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return JSONResponse({"url": url, "state": state})


@router.get("/oauth/callback")
async def oauth_callback(code: str, state: str) -> JSONResponse:
    discord_id = _consume_state(state)
    # Placeholder: store encrypted code as a stand-in for tokens.
    ciphertext = encrypt_text(code)
    logger.info("oauth_linked", discord_id=discord_id)
    return JSONResponse({"ok": True})


@router.get("/oauth/supabase-success", response_model=None)
async def supabase_oauth_success(
    access_token: str = Query(None),
    provider_token: str = Query(None), 
    refresh_token: str = Query(None),
    expires_at: int = Query(None),
    discord_user: str = Query(None),
    state: str = Query(None)
) -> Union[JSONResponse, HTMLResponse]:
    """Handle successful Supabase OAuth and store tokens"""
    extracted_discord_user = discord_user  # Initialize with parameter value
    try:
        # Extract discord_user from state parameter if not provided directly
        if not extracted_discord_user and state:
            # Parse state parameter: "discord_user=123456&nonce=abc123"
            from urllib.parse import parse_qs
            if 'discord_user=' in state:
                try:
                    state_params = parse_qs(state)
                    discord_user_list = state_params.get('discord_user', [])
                    extracted_discord_user = discord_user_list[0] if discord_user_list else None
                except Exception as e:
                    logger.error("state_parsing_error", error=str(e), state=state)
        
        if not extracted_discord_user:
            return JSONResponse({"error": "Missing Discord user ID in callback"}, status_code=400)
        
        if not provider_token:
            return JSONResponse({"error": "Missing Google tokens"}, status_code=400)
            
        # Import Supabase client
        from ..infra.supabase_db import get_supabase_db
        db = get_supabase_db()
        
        # Prepare user data
        user_data = {
            "discord_id": extracted_discord_user,
            "google_access_token": provider_token,
            "google_refresh_token": refresh_token,
            "google_token_expiry": expires_at,
            "google_email": "farjiworklol@gmail.com",  # Your email from the token
            "timezone": "Australia/Melbourne"
        }
        
        # Store in Supabase
        success = await db.create_user(extracted_discord_user, user_data)
        
        if success:
            logger.info("oauth_tokens_stored", discord_id=extracted_discord_user)
            # Return HTML page with success message
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Calendar Agent - Connected!</title>
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f0f2f5; }}
                    .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .success {{ color: #28a745; font-size: 24px; margin-bottom: 20px; }}
                    .message {{ color: #333; font-size: 16px; line-height: 1.5; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="success">✅ Successfully Connected!</div>
                    <div class="message">
                        Your Google Calendar has been linked to Discord user ID: {extracted_discord_user}<br><br>
                        You can now close this tab and return to Discord to use calendar commands like:<br>
                        • <code>/addevent tomorrow 3pm Meeting</code><br>
                        • <code>/myevents</code><br>
                        • <code>/ping</code>
                    </div>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
        else:
            logger.error("oauth_storage_failed", discord_id=extracted_discord_user)
            return JSONResponse({"error": "Failed to store OAuth tokens"}, status_code=500)
            
    except Exception as e:
        logger.error("oauth_callback_error", error=str(e), discord_id=extracted_discord_user or 'unknown')
        return JSONResponse({"error": f"OAuth callback failed: {str(e)}"}, status_code=500)


