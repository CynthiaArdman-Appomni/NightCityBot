from typing import List
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import discord
import config

async def run(suite, ctx) -> List[str]:
    """Back up all character sheet threads."""
    logs: List[str] = []
    cog = suite.bot.get_cog('CharacterManager')
    if not cog:
        logs.append('❌ CharacterManager cog not loaded')
        return logs

    forum = MagicMock(spec=discord.ForumChannel)
    retired = MagicMock(spec=discord.ForumChannel)
    thread = MagicMock(spec=discord.Thread)
    thread.id = 123
    thread.name = 'Example'
    thread.applied_tags = []

    msg = MagicMock()
    msg.author.id = 1
    msg.author.display_name = 'Tester'
    msg.content = 'Hello'
    msg.created_at = datetime.utcnow()

    async def history(*args, **kwargs):
        yield msg

    thread.history = history

    async def iter_threads(_):
        yield thread

    ctx.guild.get_channel = MagicMock(side_effect=lambda cid: forum if cid == config.CHARACTER_SHEETS_CHANNEL_ID else retired)
    ctx.send = AsyncMock()

    saved = {}
    async def fake_save(path, data):
        saved['path'] = path
        saved['data'] = data
        return True

    with patch.object(cog, '_iter_all_threads', iter_threads), patch('NightCityBot.cogs.character_manager.save_json_file', new=fake_save):
        await cog.backup_sheets(ctx)
        suite.assert_send(logs, ctx.send, 'send')

    if saved.get('data', {}).get('id') == thread.id:
        logs.append('✅ sheet saved')
    else:
        logs.append('❌ sheet not saved')

    return logs
