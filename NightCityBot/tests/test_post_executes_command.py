from typing import List

async def run(suite, ctx) -> List[str]:
    """Test posting commands to channels."""
    logs = []
    try:
        rp_channel = ctx.test_rp_channel
        ctx.message.attachments = []
        admin_cog = suite.bot.get_cog('Admin')
        await admin_cog.post(ctx, rp_channel.name, message="!roll 1d4")
        logs.append("✅ !post executed and command sent in reused RP channel")
    except Exception as e:
        logs.append(f"❌ Exception in test_post_executes_command: {e}")
    return logs
