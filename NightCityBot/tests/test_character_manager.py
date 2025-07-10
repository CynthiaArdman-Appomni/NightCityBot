from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config


async def run(suite, ctx) -> List[str]:
    """Test retire/unretire and search commands."""
    logs: List[str] = []
    cog = suite.bot.get_cog("CharacterManager")
    if not cog:
        logs.append("❌ CharacterManager cog not loaded")
        return logs

    retired_tag = MagicMock(id=1, name="Retired")
    src_forum = MagicMock(spec=discord.ForumChannel)
    dest_forum = MagicMock(spec=discord.ForumChannel)
    src_forum.available_tags = [retired_tag]
    src_forum.name = "Chars"
    dest_forum.name = "Retired"
    dest_forum.id = 99
    src_forum.id = 42

    thread = MagicMock(spec=discord.Thread)
    thread.id = 555
    thread.name = "Example"
    thread.applied_tags = [retired_tag]

    async def iter_threads(_):
        yield thread

    with patch.object(
        ctx.guild,
        "get_channel",
        side_effect=lambda cid: (
            src_forum if cid == config.CHARACTER_SHEETS_CHANNEL_ID else dest_forum
        ),
    ), patch.object(cog, "_iter_all_threads", iter_threads), patch.object(
        cog, "_move_thread", new=AsyncMock()
    ) as mock_move:
        ctx.send = AsyncMock()
        await cog.retire(ctx)
        suite.assert_called(logs, mock_move, "_move_thread")

    with patch.object(
        cog.bot, "fetch_channel", new=AsyncMock(return_value=thread)
    ), patch.object(cog, "_move_thread", new=AsyncMock()) as mock_move2, patch.object(
        ctx.guild,
        "get_channel",
        side_effect=lambda cid: (
            src_forum if cid == config.CHARACTER_SHEETS_CHANNEL_ID else dest_forum
        ),
    ):
        ctx.send = AsyncMock()
        thread.parent_id = dest_forum.id
        await cog.unretire(ctx, thread.id)
        suite.assert_called(logs, mock_move2, "_move_thread")

    message = MagicMock()
    message.content = "Johnny Silverhand is legendary."

    async def history(*args, **kwargs):
        yield message

    thread.history = history

    with patch.object(cog, "_iter_all_threads", iter_threads), patch.object(
        ctx.guild,
        "get_channel",
        side_effect=lambda cid: (
            src_forum if cid == config.CHARACTER_SHEETS_CHANNEL_ID else dest_forum
        ),
    ):
        ctx.send = AsyncMock()
        await cog.search_characters(ctx, keyword="silver")
        suite.assert_send(logs, ctx.send, "send")

    return logs
