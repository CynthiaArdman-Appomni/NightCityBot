from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config

async def run(suite, ctx) -> List[str]:
    """Auto-link DM threads when mapping is missing."""
    logs: List[str] = []
    dm_handler = suite.bot.get_cog('DMHandler')
    user = await suite.get_test_user(ctx)
    dm_handler.dm_threads = {}
    thread = MagicMock(spec=discord.Thread)
    thread.id = 4242
    thread.name = f"{user.name}-{user.id}"
    thread.send = AsyncMock()
    message = MagicMock()
    message.channel = thread
    message.content = "Hello"
    message.attachments = []
    fixer_role = MagicMock()
    fixer_role.name = config.FIXER_ROLE_NAME
    message.author = MagicMock(roles=[fixer_role], display_name="Fixer", id=1)
    message.delete = AsyncMock()
    with patch.object(dm_handler.bot, 'fetch_user', new=AsyncMock(return_value=user)), \
         patch.object(user, 'send', new=AsyncMock()) as send_mock:
        await dm_handler.handle_thread_message(message)
    suite.assert_called(logs, send_mock, 'user.send')
    if str(user.id) in dm_handler.dm_threads and dm_handler.dm_threads[str(user.id)] == thread.id:
        logs.append('✅ Thread auto-linked from name')
    else:
        logs.append('❌ Thread mapping not updated')
    return logs
