import difflib
import logging

import discord
from discord.ext import commands
from NightCityBot.utils.permissions import is_fixer
import config


logger = logging.getLogger(__name__)


class CharacterManager(commands.Cog):
    """Manage character sheet threads."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _move_thread(
        self, thread: discord.Thread, destination: discord.ForumChannel
    ) -> bool:
        """Move ``thread`` to ``destination`` forum channel.

        Returns ``True`` if the thread was moved successfully.
        """
        try:
            await thread.edit(parent_id=destination.id)
        except Exception as e:  # discord.Forbidden, discord.NotFound, HTTPException
            logger.warning(
                "Failed to move thread %s (%s) to %s: %s",
                thread.name,
                thread.id,
                destination.name,
                e,
            )
            return False

        logger.info(
            "Moved thread %s (%s) to %s",
            thread.name,
            thread.id,
            destination.name,
        )
        return True

    async def _iter_all_threads(self, forum: discord.ForumChannel):
        """Yield all threads from ``forum`` including archived ones."""
        for t in forum.threads:
            yield t
        async for t in forum.archived_threads(limit=None):
            yield t

    def _match(self, query: str, text: str) -> bool:
        q = query.lower()
        t = text.lower()
        if q in t:
            return True
        return difflib.SequenceMatcher(None, q, t).ratio() > 0.6

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    @commands.command()
    @is_fixer()
    async def retire(self, ctx: commands.Context) -> None:
        """Move all threads tagged "Retired" to the retired forum."""
        src = ctx.guild.get_channel(config.CHARACTER_SHEETS_CHANNEL_ID)
        dest = ctx.guild.get_channel(config.RETIRED_SHEETS_CHANNEL_ID)
        if not isinstance(src, discord.ForumChannel) or not isinstance(
            dest, discord.ForumChannel
        ):
            await ctx.send("⚠️ Character forums not configured.")
            return
        retired_tag = discord.utils.get(src.available_tags, name="Retired")
        if not retired_tag:
            await ctx.send("⚠️ 'Retired' tag not found.")
            return
        moved = 0
        failed = 0
        async for thread in self._iter_all_threads(src):
            if any(tag.id == retired_tag.id for tag in thread.applied_tags):
                if await self._move_thread(thread, dest):
                    moved += 1
                else:
                    failed += 1
        message = f"✅ Moved {moved} thread(s) to {dest.name}."
        if failed:
            message += f" ❌ Failed to move {failed} thread(s). Check logs."
        await ctx.send(message)

    @commands.command()
    @is_fixer()
    async def unretire(self, ctx: commands.Context, thread_id: int) -> None:
        """Move a single thread back to the main forum."""
        src = ctx.guild.get_channel(config.CHARACTER_SHEETS_CHANNEL_ID)
        dest = ctx.guild.get_channel(config.RETIRED_SHEETS_CHANNEL_ID)
        if not isinstance(src, discord.ForumChannel) or not isinstance(
            dest, discord.ForumChannel
        ):
            await ctx.send("⚠️ Character forums not configured.")
            return
        try:
            thread = await self.bot.fetch_channel(thread_id)
        except discord.NotFound:
            await ctx.send("❌ Thread not found.")
            return
        if not isinstance(thread, discord.Thread) or thread.parent_id != dest.id:
            await ctx.send("❌ Invalid thread ID.")
            return
        await self._move_thread(thread, src)
        await ctx.send(f"✅ {thread.name} moved back to {src.name}.")

    @commands.command(aliases=["sheet_search", "search_sheets"])
    @is_fixer()
    async def search_characters(self, ctx: commands.Context, *, keyword: str) -> None:
        """Search character sheets for ``keyword``."""
        forums = []
        for cid in (
            config.CHARACTER_SHEETS_CHANNEL_ID,
            config.RETIRED_SHEETS_CHANNEL_ID,
        ):
            ch = ctx.guild.get_channel(cid)
            if isinstance(ch, discord.ForumChannel):
                forums.append(ch)
        if not forums:
            await ctx.send("⚠️ Character forums not configured.")
            return
        matches: list[tuple[discord.Thread, str]] = []
        for forum in forums:
            async for thread in self._iter_all_threads(forum):
                async for msg in thread.history(limit=20, oldest_first=True):
                    if msg.content and self._match(keyword, msg.content):
                        text = msg.content
                        loc = text.lower().find(keyword.lower())
                        if loc != -1:
                            start = max(0, loc - 30)
                            end = loc + len(keyword) + 30
                            snippet = text[start:end]
                        else:
                            snippet = text[:60]
                        matches.append((thread, snippet))
                        break
                if len(matches) >= 10:
                    break
            if len(matches) >= 10:
                break
        if not matches:
            await ctx.send("No results found.")
            return
        embed = discord.Embed(
            title=f"Results for '{keyword}'", color=discord.Color.blurple()
        )
        for th, snippet in matches:
            url = (
                th.jump_url
                if hasattr(th, "jump_url")
                else f"https://discord.com/channels/{th.guild.id}/{th.id}"
            )
            embed.add_field(name=th.name, value=f"{snippet}\n{url}", inline=False)
        await ctx.send(embed=embed)
