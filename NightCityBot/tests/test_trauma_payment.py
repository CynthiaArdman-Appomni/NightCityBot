from typing import List

async def run(suite, ctx) -> List[str]:
    """Test Trauma Team subscription processing."""
    logs = []
    try:
        user = await suite.get_test_user(ctx)
        logs.append("→ Expected: collect_trauma should find thread and log subscription payment.")

        economy = suite.bot.get_cog('Economy')
        await economy.collect_trauma(ctx, f"<@{user.id}>")
        logs.append("→ Result: ✅ Trauma Team logic executed on live user (check #tt-plans-payment).")
    except Exception as e:
        logs.append(f"❌ Exception in test_trauma_payment: {e}")
    return logs
