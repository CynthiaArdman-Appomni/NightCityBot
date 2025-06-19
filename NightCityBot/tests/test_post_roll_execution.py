from typing import List

async def run(suite, ctx) -> List[str]:
    """Test roll execution via post command."""
    logs = []
    try:
        thread = ctx.test_rp_channel
        admin_cog = suite.bot.get_cog('Admin')
        await admin_cog.post(ctx, thread.name, message="!roll 1d20+1")
        logs.append("✅ !post <thread> !roll d20+1 executed in reused RP channel")
    except Exception as e:
        logs.append(f"❌ Exception in test_post_roll_execution: {e}")
    return logs
