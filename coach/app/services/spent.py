"""Spent integration — server-side proxy for financial data."""
import logging
import os
from datetime import date
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_SESSION_COOKIE: str | None = None


def _spent_url() -> str:
    return os.getenv("SPENT_URL", "http://127.0.0.1:3000").rstrip("/")


def _spent_username() -> str:
    return os.getenv("SPENT_USERNAME", "")


def _spent_password() -> str:
    return os.getenv("SPENT_PASSWORD", "")


def _configured() -> bool:
    return bool(_spent_url() and _spent_username() and _spent_password())


async def _login(client: httpx.AsyncClient) -> bool:
    global _SESSION_COOKIE
    try:
        r = await client.post(
            f"{_spent_url()}/api/auth/login",
            json={"username": _spent_username(), "password": _spent_password()},
        )
        if r.status_code == 200:
            # Store the session cookie value for reuse
            _SESSION_COOKIE = r.cookies.get("session", None)
            logger.debug("Spent login succeeded")
            return True
        logger.warning("Spent login failed: HTTP %s", r.status_code)
        return False
    except Exception as e:
        logger.error("Spent login error: %s", e)
        return False


async def _get(path: str) -> dict[str, Any] | None:
    """GET a Spent API endpoint, login if needed."""
    global _SESSION_COOKIE
    if not _configured():
        return None

    async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
        cookies = {"session": _SESSION_COOKIE} if _SESSION_COOKIE else {}
        r = await client.get(f"{_spent_url()}{path}", cookies=cookies)

        if r.status_code == 401 or r.status_code == 403:
            # Re-login and retry once
            if not await _login(client):
                return None
            cookies = {"session": _SESSION_COOKIE} if _SESSION_COOKIE else {}
            r = await client.get(f"{_spent_url()}{path}", cookies=cookies)

        if r.status_code == 200:
            return r.json()

        logger.warning("Spent API %s returned %s", path, r.status_code)
        return None


async def get_monthly_pulse() -> dict[str, Any] | None:
    """Return this month's financial summary from Spent.

    Returns None if Spent is not configured or unreachable.
    Result shape (subset of /api/summary):
        {
          "period_total": float,     # total spent this month
          "income_total": float,     # total income this month
          "total_budget": float,     # monthly budget target
          "percent_spent": float,    # 0-100
          "days_until_payday": int,
          "top_categories": [{"name": str, "spent": float, "budget": float}, ...],
          "credit_cards": [{"name": str, "spent": float, "budget": float}, ...],
        }
    """
    now = date.today()
    from_str = f"{now.year}-{now.month:02d}-01"
    import calendar
    last_day = calendar.monthrange(now.year, now.month)[1]
    to_str = f"{now.year}-{now.month:02d}-{last_day:02d}"

    try:
        data = await _get(f"/api/summary?from={from_str}&to={to_str}")
        if data is None:
            return None

        top_cats = sorted(
            [
                {
                    "name": c.get("categoryName", ""),
                    "spent": c.get("spent", 0),
                    "budget": c.get("budget", 0),
                    "percent": c.get("percentSpent", 0),
                }
                for c in data.get("categoriesWithData", [])
                if not c.get("isParent") and c.get("spent", 0) > 0
            ],
            key=lambda x: x["spent"],
            reverse=True,
        )[:5]

        credit_cards = [
            {
                "name": cc.get("providerName", ""),
                "spent": cc.get("totalSpent", 0),
                "budget": cc.get("monthlyBudget") or 0,
            }
            for cc in data.get("creditCards", [])
        ]

        return {
            "period_total": data.get("periodTotal", 0),
            "income_total": data.get("incomeTotal", 0),
            "total_budget": data.get("totalBudget", 0),
            "percent_spent": data.get("overallPercentSpent", 0),
            "days_until_payday": data.get("daysUntilPayday", 0),
            "pace_phrase": data.get("pacePhrase", ""),
            "top_categories": top_cats,
            "credit_cards": credit_cards,
        }
    except Exception as e:
        logger.error("Spent pulse error: %s", e)
        return None
