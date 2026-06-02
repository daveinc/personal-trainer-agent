import asyncio
import json
import logging
import os

import httpx

logger = logging.getLogger(__name__)

_HA_API = "http://supervisor/core/api"


async def _listen():
    token = os.getenv("SUPERVISOR_TOKEN", "")
    if not token:
        logger.warning("SUPERVISOR_TOKEN not set — event stream disabled")
        return

    from app.routes.action_router import handle_action

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "GET",
            f"{_HA_API}/stream",
            headers={"Authorization": f"Bearer {token}"},
        ) as resp:
            async for line in resp.aiter_lines():
                if not line.startswith("data:"):
                    continue
                try:
                    payload = json.loads(line[5:].strip())
                except json.JSONDecodeError:
                    continue

                if payload.get("event_type") != "mobile_app_notification_action":
                    continue

                action = payload.get("data", {}).get("action", "")
                logger.info(f"HA event action: {action!r}")

                if action.startswith("coach_"):
                    parts = action.split("_")
                    if len(parts) != 3:
                        continue
                    try:
                        slot_id = int(parts[1])
                    except ValueError:
                        continue
                    verb = parts[2]
                    await handle_action(slot_id, verb)

                elif action.startswith("EVENT_"):
                    from app.routes.action_router import handle_event_action
                    # format: EVENT_{VERB}_{title}
                    remainder = action[len("EVENT_"):]
                    for verb in ("DONE_", "SKIP_", "SNOOZE_"):
                        if remainder.startswith(verb):
                            event_title = remainder[len(verb):]
                            await handle_event_action(event_title, verb.rstrip("_").lower())
                            break


async def run_event_listener():
    logger.info("HA event listener started")
    while True:
        try:
            await _listen()
        except Exception as e:
            logger.error(f"Event stream error: {e}")
        await asyncio.sleep(5)
