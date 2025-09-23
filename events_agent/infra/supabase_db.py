"""
Supabase REST API database adapter to bypass PostgreSQL connection restrictions.
Uses HTTPS which works through university firewalls.
"""
from __future__ import annotations

import asyncio
from typing import Optional, List, Dict, Any
from supabase import create_client, Client
from ..infra.settings import settings
from ..infra.logging import get_logger

logger = get_logger().bind(service="supabase_db")

class SupabaseDB:
    """Supabase REST API database interface"""
    
    def __init__(self):
        if not settings.supabase_url:
            raise ValueError("Supabase URL must be configured")
        
        # Use service role key for backend operations (can bypass RLS), fallback to anon key
        supabase_key = settings.supabase_service_role_key or settings.supabase_key
        if not supabase_key:
            raise ValueError("Neither service role key nor anon key configured")
        
        self.client: Client = create_client(settings.supabase_url, supabase_key)
        logger.info("supabase_client_initialized", 
                   key_type="service_role" if settings.supabase_service_role_key else "anon")
    
    async def create_user(self, discord_id: str, google_tokens: Dict[str, Any]) -> bool:
        """Create or update a user with Google tokens"""
        try:
            data = {
                "discord_id": discord_id,
                "google_access_token": google_tokens.get("access_token"),
                "google_refresh_token": google_tokens.get("refresh_token"),
                "google_token_expiry": google_tokens.get("expires_at"),
                "email": google_tokens.get("email"),
                "timezone": "Australia/Melbourne"
            }
            
            # Upsert user (insert or update)
            result = self.client.table("users").upsert(data).execute()
            logger.info("user_created_or_updated", discord_id=discord_id)
            return True
        except Exception as e:
            logger.error("user_creation_failed", discord_id=discord_id, error=str(e))
            return False
    
    async def get_user_tokens(self, discord_id: str) -> Optional[Dict[str, Any]]:
        """Get user's Google tokens"""
        try:
            result = self.client.table("users").select("*").eq("discord_id", discord_id).execute()
            if result.data:
                user_data = result.data[0]
                return {
                    "access_token": user_data.get("google_access_token"),
                    "refresh_token": user_data.get("google_refresh_token"),
                    "expires_at": user_data.get("google_token_expiry"),
                    "email": user_data.get("email")
                }
            return None
        except Exception as e:
            logger.error("get_user_tokens_failed", discord_id=discord_id, error=str(e))
            return None
    
    async def create_event(self, event_data: Dict[str, Any]) -> bool:
        """Create a calendar event"""
        try:
            result = self.client.table("events").insert(event_data).execute()
            logger.info("event_created", event_id=result.data[0].get("id") if result.data else None)
            return True
        except Exception as e:
            logger.error("event_creation_failed", error=str(e))
            return False
    
    async def get_user_events(self, discord_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's recent events"""
        try:
            result = self.client.table("events").select("*").eq("discord_id", discord_id).limit(limit).execute()
            return result.data or []
        except Exception as e:
            logger.error("get_events_failed", discord_id=discord_id, error=str(e))
            return []

# Global instance
_supabase_db: Optional[SupabaseDB] = None

def get_supabase_db() -> SupabaseDB:
    """Get or create Supabase database instance"""
    global _supabase_db
    if _supabase_db is None:
        _supabase_db = SupabaseDB()
    return _supabase_db