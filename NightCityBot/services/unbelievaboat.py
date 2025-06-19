import asyncio
import logging
from typing import Dict, Optional

import aiohttp
import config

logger = logging.getLogger(__name__)


class UnbelievaBoatAPI:
    """Minimal async wrapper for the UnbelievaBoat REST API."""

    def __init__(
        self, api_token: str, session: Optional[aiohttp.ClientSession] = None
    ) -> None:
        """Create a new API wrapper."""
        self.api_token = api_token
        self.base_url = f"https://unbelievaboat.com/api/v1/guilds/{config.GUILD_ID}"
        self.headers = {"Authorization": api_token, "Content-Type": "application/json"}
        self.session = session or aiohttp.ClientSession()

    async def close(self) -> None:
        await self.session.close()

    async def get_balance(self, user_id: int) -> Optional[Dict]:
        """Get a user's balance from UnbelievaBoat."""
        url = f"{self.base_url}/users/{user_id}"
        for attempt in range(3):
            try:
                async with self.session.get(url, headers=self.headers) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    logger.warning(
                        "Balance fetch failed (%s): %s", resp.status, await resp.text()
                    )
            except aiohttp.ClientError as e:
                logger.warning(
                    "Balance request error on attempt %s: %s", attempt + 1, e
                )
                await asyncio.sleep(1)
        return None

    async def update_balance(
        self, user_id: int, amount_dict: Dict, reason: str = "Automated rent/income"
    ) -> bool:
        """Update a user's balance on UnbelievaBoat."""
        url = f"{self.base_url}/users/{user_id}"
        payload = amount_dict.copy()
        payload["reason"] = reason

        for attempt in range(3):
            try:
                async with self.session.patch(
                    url, headers=self.headers, json=payload
                ) as resp:
                    if resp.status == 200:
                        return True
                    error = await resp.text()
                    logger.warning("PATCH failed (%s): %s", resp.status, error)
            except aiohttp.ClientError as e:
                logger.warning("Balance PATCH error on attempt %s: %s", attempt + 1, e)
            await asyncio.sleep(1)
        return False

    async def verify_balance_ops(self, user_id: int) -> bool:
        """Test updating a balance without affecting the final amount."""
        balance = await self.get_balance(user_id)
        if not balance:
            return False

        # Choose a field with at least $1 to avoid invalid negative balances
        target_field = "cash" if balance.get("cash", 0) > 0 else "bank"

        minus = await self.update_balance(
            user_id,
            {target_field: -1},
            reason="Simulation check",
        )
        if not minus:
            return False

        plus = await self.update_balance(
            user_id,
            {target_field: 1},
            reason="Simulation check",
        )
        return minus and plus
