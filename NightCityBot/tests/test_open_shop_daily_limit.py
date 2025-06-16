from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import config
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING

async def run(suite, ctx) -> List[str]:
    """Ensure users can't log a business opening twice on the same day."""
    control = suite.bot.get_cog('SystemControl')
    if control:
        await control.set_status('open_shop', True)
    logs = []
    economy = suite.bot.get_cog('Economy')
    original_channel = ctx.channel
    ctx.channel = ctx.guild.get_channel(config.BUSINESS_ACTIVITY_CHANNEL_ID)

    storage = {}

    async def fake_load(*_, **__):
        return storage.get("data", {})

    async def fake_save(path, data):
        storage["data"] = data

    ctx.send = AsyncMock()

    sunday = datetime(2025, 6, 15)
    with (
        patch("NightCityBot.cogs.economy.datetime") as mock_dt,
        patch("NightCityBot.cogs.economy.load_json_file", new=fake_load),
        patch("NightCityBot.cogs.economy.save_json_file", new=fake_save),
        patch.object(economy.unbelievaboat, "update_balance", new=AsyncMock()),
    ):
        mock_dt.utcnow.return_value = sunday
        mock_dt.fromisoformat = datetime.fromisoformat
        await economy.open_shop(ctx)
        await economy.open_shop(ctx)
    msg = ctx.send.call_args_list[-1][0][0]
    if "already logged a business opening today" in msg:
        logs.append("✅ open_shop rejected when used twice")
    else:
        logs.append("❌ open_shop did not enforce daily limit")
    ctx.channel = original_channel
    return logs
