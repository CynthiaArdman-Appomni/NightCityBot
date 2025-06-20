from typing import List

async def run(suite, ctx) -> List[str]:
    """Verify cyberware medication cost escalation."""
    logs = []
    manager = suite.bot.get_cog('CyberwareManager')
    if not manager:
        logs.append("❌ CyberwareManager cog not loaded")
        return logs
    try:
        week1 = manager.calculate_cost('medium', 1)
        week8 = manager.calculate_cost('extreme', 8)
        if week1 < week8 == 10000:
            logs.append("✅ Cyberware costs escalate and cap correctly")
        else:
            logs.append(f"❌ Unexpected cost results: week1={week1}, week8={week8}")
    except Exception as e:
        logs.append(f"❌ Exception in test_cyberware_costs: {e}")
    return logs
