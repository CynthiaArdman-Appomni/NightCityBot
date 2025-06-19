from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import config

async def run(suite, ctx) -> List[str]:
    """Test the attend reward command and its restrictions."""
    control = suite.bot.get_cog('SystemControl')
    if control:
        await control.set_status('attend', True)
    logs = []
    economy = suite.bot.get_cog('Economy')
    original_author = ctx.author
    mock_author = MagicMock(spec=discord.Member)
    mock_author.id = original_author.id
    mock_author.roles = [discord.Object(id=config.VERIFIED_ROLE_ID)]
    ctx.author = mock_author
    ctx.send = AsyncMock()
    original_channel = ctx.channel
    # Ensure the channel id matches the configured attendance channel so
    # subsequent checks don't fail due to a mismatched ID.
    original_channel.id = config.ATTENDANCE_CHANNEL_ID

    # Wrong channel should be rejected
    ctx.channel = MagicMock(id=9999)
    sunday = datetime(2025, 6, 15)
    with patch("NightCityBot.utils.helpers.get_tz_now", return_value=sunday):
        await economy.attend(ctx)
        msg = ctx.send.await_args[0][0]
        if "Please use" in msg:
            logs.append("✅ attend rejected in wrong channel")
        else:
            logs.append("❌ attend allowed in wrong channel")
    ctx.send.reset_mock()
    ctx.channel = original_channel

    # Non-Sunday should be rejected
    monday = datetime(2025, 6, 16)
    with (
        patch("NightCityBot.utils.helpers.get_tz_now", return_value=monday),
        patch("NightCityBot.cogs.economy.load_json_file", new=AsyncMock(return_value={})),
        patch("NightCityBot.cogs.economy.save_json_file", new=AsyncMock()),
    ):
        await economy.attend(ctx)
        msg = ctx.send.await_args[0][0]
        if "only be logged on Sundays" in msg:
            logs.append("✅ attend rejected on non-Sunday")
        else:
            logs.append("❌ attend did not reject non-Sunday")
    ctx.send.reset_mock()

    # Already attended this week should be rejected
    sunday = datetime(2025, 6, 15)
    prev = sunday - timedelta(days=3)
    with (
        patch("NightCityBot.utils.helpers.get_tz_now", return_value=sunday),
        patch(
            "NightCityBot.cogs.economy.load_json_file",
            new=AsyncMock(return_value={str(mock_author.id): [prev.isoformat()]}),
        ),
        patch("NightCityBot.cogs.economy.save_json_file", new=AsyncMock()),
    ):
        await economy.attend(ctx)
        msg = ctx.send.await_args[0][0]
        if "already logged attendance this week" in msg:
            logs.append("✅ attend rejected when used twice")
        else:
            logs.append("❌ attend did not enforce weekly limit")
    ctx.send.reset_mock()

    # Success when a week has passed
    prev2 = sunday - timedelta(days=7)
    with (
        patch("NightCityBot.utils.helpers.get_tz_now", return_value=sunday),
        patch(
            "NightCityBot.cogs.economy.load_json_file",
            new=AsyncMock(return_value={str(mock_author.id): [prev2.isoformat()]}),
        ),
        patch("NightCityBot.cogs.economy.save_json_file", new=AsyncMock()),
        patch.object(economy.unbelievaboat, "update_balance", new=AsyncMock()),
    ):
        await economy.attend(ctx)
        msg = ctx.send.await_args[0][0]
        if "Attendance logged" in msg:
            logs.append("✅ attend succeeded after cooldown")
        else:
            logs.append("❌ attend did not succeed after cooldown")

    ctx.author = original_author
    return logs
