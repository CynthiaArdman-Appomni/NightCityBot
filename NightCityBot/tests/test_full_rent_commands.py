from typing import List
import os
from unittest.mock import AsyncMock, patch
import config

async def run(suite, ctx) -> List[str]:
    """Test all rent-related commands."""
    logs = []
    try:
        user = await suite.get_test_user(ctx)
        logs.append("→ Expected: All rent-related commands should complete without error.")

        if os.path.exists(config.LAST_RENT_FILE):
            os.remove(config.LAST_RENT_FILE)

        economy = suite.bot.get_cog('Economy')
        cyber = suite.bot.get_cog('CyberwareManager')
        with (
            patch.object(economy.unbelievaboat, "update_balance", new=AsyncMock(return_value=True)),
            patch.object(cyber.unbelievaboat, "update_balance", new=AsyncMock(return_value=True)),
            patch("NightCityBot.cogs.cyberware.save_json_file", new=AsyncMock()),
        ):
            await economy.simulate_rent(ctx)
            logs.append("✅ simulate_rent (global) executed")

            await economy.simulate_rent(ctx, target_user=user)
            logs.append("✅ simulate_rent (specific user) executed")

            await cyber.simulate_cyberware(ctx, str(user.id))
            logs.append("✅ simulate_cyberware executed")

        logs.append("→ Result: ✅ All rent commands executed.")
    except Exception as e:
        logs.append(f"❌ Exception in test_full_rent_commands: {e}")
    return logs
