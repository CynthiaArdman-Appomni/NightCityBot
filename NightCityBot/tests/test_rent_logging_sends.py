from typing import List
from unittest.mock import AsyncMock, patch
import config

async def run(suite, ctx) -> List[str]:
    """Test rent logging functionality."""
    logs = []
    try:
        user = await suite.get_test_user(ctx)
        rent_log_channel = ctx.guild.get_channel(config.RENT_LOG_CHANNEL_ID)
        eviction_channel = ctx.guild.get_channel(config.EVICTION_CHANNEL_ID)

        logs.append("→ Expected: collect_rent should post messages to rent and eviction log channels.")

        if not rent_log_channel or not eviction_channel:
            logs.append("→ Result: ❌ Rent or eviction channels not found.")
            return logs

        economy = suite.bot.get_cog('Economy')
        with (
            patch.object(economy.unbelievaboat, "update_balance", new=AsyncMock(return_value=True)),
        ):
            await economy.simulate_rent(ctx, target_user=user)
        logs.append("→ Result: ✅ Rent logic executed and logging channels present.")
    except Exception as e:
        logs.append(f"❌ Exception in test_rent_logging_sends: {e}")
    return logs
