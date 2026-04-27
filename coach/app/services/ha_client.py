import logging
import os

import httpx

logger = logging.getLogger(__name__)
_HA_API = "http://supervisor/core/api"


async def get_ha_state(entity_id: str) -> dict | None:
    token = os.getenv("SUPERVISOR_TOKEN", "")
    if not token or not entity_id:
        return None
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(
                f"{_HA_API}/states/{entity_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            if r.status_code == 200:
                return r.json()
    except Exception as e:
        logger.debug(f"HA state fetch failed for {entity_id}: {e}")
    return None
