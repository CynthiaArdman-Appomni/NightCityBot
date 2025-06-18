from typing import List
import asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime
import config

async def run(suite, ctx) -> List[str]:
    logs = []
    control = suite.bot.get_cog('SystemControl')
    if control:
        await control.set_status('open_shop', True)
    economy = suite.bot.get_cog('Economy')
    ctx.channel = ctx.guild.get_channel(config.BUSINESS_ACTIVITY_CHANNEL_ID)

    storage = {}

    async def fake_load(*_, **__):
        return storage.get("data", {})

    async def fake_save(_, data):
        storage["data"] = data

    ctx.send = AsyncMock()
    sunday = datetime(2025, 6, 15)
    with (
        patch("NightCityBot.utils.helpers.get_tz_now", return_value=sunday),
        patch("NightCityBot.cogs.economy.load_json_file", new=fake_load),
        patch("NightCityBot.cogs.economy.save_json_file", new=fake_save),
        patch.object(economy.unbelievaboat, "update_balance", new=AsyncMock()),
    ):
        await asyncio.gather(
            economy.open_shop(ctx),
            economy.open_shop(ctx),
        )

    entries = storage.get("data", {}).get(str(ctx.author.id), [])
    msgs = [c.args[0] for c in ctx.send.call_args_list]
    if len(entries) == 1 and any("already" in m for m in msgs):
        logs.append("✅ concurrent open_shop calls serialized")
    else:
        logs.append("❌ concurrency issue in open_shop")
    return logs
