from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import config

async def run(suite, ctx) -> List[str]:
    """Ensure missed weeks increment the cyberware streak."""
    logs: List[str] = []
    manager = suite.bot.get_cog('CyberwareManager')
    if not manager:
        logs.append("❌ CyberwareManager cog not loaded")
        return logs
    guild = MagicMock()
    check = discord.Object(id=config.CYBER_CHECKUP_ROLE_ID)
    medium = discord.Object(id=config.CYBER_MEDIUM_ROLE_ID)
    guild.get_role.side_effect = lambda rid: {config.CYBER_CHECKUP_ROLE_ID: check,
                                              config.CYBER_MEDIUM_ROLE_ID: medium}.get(rid)
    member = MagicMock(spec=discord.Member)
    member.id = 1
    member.roles = [medium, check]
    member.add_roles = AsyncMock()
    guild.members = [member]
    log_channel = MagicMock()
    log_channel.send = AsyncMock()
    guild.get_channel.return_value = log_channel
    manager.data[str(member.id)] = {
        "weeks": 1,
        "last": (datetime.utcnow() - timedelta(days=14)).isoformat(),
    }
    manager.last_run = datetime.utcnow() - timedelta(days=14)
    with (
        patch.object(suite.bot, "get_guild", return_value=guild),
        patch.object(manager.unbelievaboat, "get_balance", new=AsyncMock(return_value={"cash": 5000, "bank": 0})),
        patch.object(manager.unbelievaboat, "update_balance", new=AsyncMock(return_value=True)),
        patch("NightCityBot.cogs.cyberware.save_json_file", new=AsyncMock()),
    ):
        await manager.process_week()
    entry = manager.data.get(str(member.id))
    result = entry.get("weeks") if isinstance(entry, dict) else None
    if result == 3:
        logs.append("✅ streak advanced by missed weeks")
    else:
        logs.append(f"❌ streak incorrect: {result}")
    return logs
