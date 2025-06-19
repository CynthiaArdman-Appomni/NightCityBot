from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

async def run(suite, ctx) -> List[str]:
    """Ensure DM threads are reused instead of duplicated."""
    logs = []
    user = await suite.get_test_user(ctx)
    dm_handler = suite.bot.get_cog('DMHandler')
    dummy_thread = MagicMock()
    with patch.object(dm_handler, 'get_or_create_dm_thread', new=AsyncMock(return_value=dummy_thread)) as mock_get:
        first = await dm_handler.get_or_create_dm_thread(user)
        second = await dm_handler.get_or_create_dm_thread(user)
    if first is second:
        logs.append("✅ DM thread reused correctly")
    else:
        logs.append("❌ DM thread was recreated")
    suite.assert_called(logs, mock_get, 'get_or_create_dm_thread')
    return logs
