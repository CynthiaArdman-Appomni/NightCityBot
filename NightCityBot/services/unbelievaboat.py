import aiohttp
import asyncio
from typing import Dict, Optional
import config

class UnbelievaBoatAPI:
    def __init__(self, api_token: str, session: Optional[aiohttp.ClientSession] = None):
        self.api_token = api_token
        self.base_url = f"https://unbelievaboat.com/api/v1/guilds/{config.GUILD_ID}"
        self.headers = {
            "Authorization": api_token,
            "Content-Type": "application/json"
        }
        self.session = session or aiohttp.ClientSession()

    async def _request(self, method: str, url: str, **kwargs) -> Optional[aiohttp.ClientResponse]:
        """Internal helper with basic retries."""
        for attempt in range(3):
            try:
                async with self.session.request(method, url, headers=self.headers, timeout=10, **kwargs) as resp:
                    if resp.status == 429 and attempt < 2:
                        retry_after = int(resp.headers.get("Retry-After", "1"))
                        await asyncio.sleep(retry_after)
                        continue
                    return resp
            except aiohttp.ClientError as e:
                print(f"❌ {method.upper()} failed: {e}")
                await asyncio.sleep(2 ** attempt)
        return None

    async def close(self) -> None:
        await self.session.close()

    async def get_balance(self, user_id: int) -> Optional[Dict]:
        """Get a user's balance from UnbelievaBoat."""
        url = f"{self.base_url}/users/{user_id}"
        resp = await self._request("get", url)
        if resp and resp.status == 200:
            try:
                return await resp.json()
            except Exception:
                pass
        elif resp is not None:
            text = await resp.text()
            print(f"❌ GET failed: {resp.status} — {text}")
        return None

    async def update_balance(
        self,
        user_id: int,
        amount_dict: Dict,
        reason: str = "Automated rent/income"
    ) -> bool:
        """Update a user's balance on UnbelievaBoat."""
        url = f"{self.base_url}/users/{user_id}"
        payload = amount_dict.copy()
        payload["reason"] = reason

        resp = await self._request("patch", url, json=payload)
        if resp and resp.status == 200:
            return True
        if resp is not None:
            error = await resp.text()
            print(f"❌ PATCH failed: {resp.status} — {error}")
        return False

    async def verify_balance_ops(self, user_id: int) -> bool:
        """Test updating a balance without affecting the final amount."""
        minus = await self.update_balance(user_id, {"cash": -1}, reason="Simulation check")
        if not minus:
            return False
        plus = await self.update_balance(user_id, {"cash": 1}, reason="Simulation check")
        return minus and plus
