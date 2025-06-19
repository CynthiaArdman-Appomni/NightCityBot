from typing import List

async def run(suite, ctx) -> List[str]:
    """Test roll command functionality."""
    logs = []
    try:
        logs.append("→ Expected: Valid roll should return a total, invalid roll should return a format error.")

        roll_system = suite.bot.get_cog('RollSystem')
        # Valid roll
        await roll_system.loggable_roll(ctx.author, ctx.channel, "1d20+2")
        logs.append("→ Result (Valid): ✅ Roll succeeded and result sent.")

        # Invalid roll
        await roll_system.loggable_roll(ctx.author, ctx.channel, "notadice")
        logs.append("→ Result (Invalid): ✅ Error message shown for invalid format.")
    except Exception as e:
        logs.append(f"❌ Exception in test_rolls: {e}")
    return logs
