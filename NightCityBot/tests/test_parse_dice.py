from typing import List
from NightCityBot.utils.helpers import parse_dice


async def run(suite, ctx) -> List[str]:
    logs: List[str] = []
    try:
        if parse_dice("2d6+1") == (2, 6, 1):
            logs.append("✅ parsed 2d6+1")
        else:
            logs.append("❌ failed to parse 2d6+1")
        if parse_dice("bad") is None:
            logs.append("✅ invalid dice returns None")
        else:
            logs.append("❌ invalid dice did not return None")
    except Exception as e:
        logs.append(f"❌ Exception in test_parse_dice: {e}")
    return logs
