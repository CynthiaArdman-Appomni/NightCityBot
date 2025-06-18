from typing import List
import config

async def run(suite, ctx) -> List[str]:
    """Verify connection to the UnbelievaBoat API."""
    logs: List[str] = []
    economy = suite.bot.get_cog('Economy')
    if not economy:
        logs.append("❌ Economy cog not loaded")
        return logs
    try:
        ok = await economy.unbelievaboat.verify_balance_ops(config.TEST_USER_ID)
        if ok:
            logs.append("✅ Verified UnbelievaBoat connectivity")
        else:
            logs.append("❌ Could not verify UnbelievaBoat connectivity")
    except Exception as e:
        logs.append(f"❌ Exception: {e}")
    return logs

