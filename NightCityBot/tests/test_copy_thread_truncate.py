from typing import List
from unittest.mock import AsyncMock, MagicMock
import discord

async def run(suite, ctx) -> List[str]:
    """Ensure long thread posts are truncated when archived."""
    logs: List[str] = []
    cog = suite.bot.get_cog('CharacterManager')
    if not cog:
        logs.append('❌ CharacterManager cog not loaded')
        return logs

    dest = MagicMock(spec=discord.ForumChannel)
    new_thread = MagicMock(spec=discord.Thread)
    new_thread.send = AsyncMock()
    dest.create_thread = AsyncMock(return_value=new_thread)

    first = MagicMock()
    first.content = 'A' * 2100
    first.attachments = []
    second = MagicMock()
    second.content = 'B'
    second.attachments = []

    async def history(*args, **kwargs):
        yield first
        yield second

    thread = MagicMock(spec=discord.Thread)
    thread.history = history
    thread.delete = AsyncMock()
    thread.name = 'Example'
    thread.id = 123

    ok = await cog._copy_thread(thread, dest)

    if not ok:
        logs.append('❌ copy failed')
        return logs

    try:
        dest.create_thread.assert_awaited()
        new_thread.send.assert_awaited()
        content = dest.create_thread.await_args.kwargs.get('content')
        if content is None:
            content = dest.create_thread.await_args.args[1]
        if len(content) <= 2000 and new_thread.send.await_count == 2:
            logs.append('✅ truncated')
        else:
            logs.append('❌ not truncated')
    except Exception as e:
        logs.append(f'❌ exception {e}')

    return logs
