from __future__ import annotations

import json
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .crypto import decrypt_text
from .settings import settings
from ..domain.models import User


async def get_user_token_by_discord_id(session: AsyncSession, discord_id: str) -> Optional[Dict[str, Any]]:
    stmt = select(User).where(User.discord_id == str(discord_id))
    res = await session.execute(stmt)
    user = res.scalars().first()
    if not user or not user.token_ciphertext:
        return None
    plaintext = decrypt_text(user.token_ciphertext)
    return json.loads(plaintext)


