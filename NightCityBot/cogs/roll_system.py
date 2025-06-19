import logging
import random
import re

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

class RollSystem(commands.Cog):
    """Cog providing dice rolling utilities."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the roll system."""
        self.bot = bot

    @commands.command()
    async def roll(self, ctx, *, dice: str):
        original_sender = getattr(ctx, "original_author", None)
        skip_log = getattr(ctx, "skip_dm_log", False)

        # Extract user mention if present
        match = re.search(r"(?:<@!?)?([0-9]{15,20})>?", dice)
        mentioned_user = None
        if match:
            user_id = int(match.group(1))
            mentioned_user = ctx.guild.get_member(user_id)
            if mentioned_user:
                dice = re.sub(r"(?:<@!?)?[0-9]{17,20}(?:>)?", "", dice).strip()

        roller = mentioned_user or ctx.author

        if original_sender:
            try:
                await ctx.message.delete()
            except Exception as e:
                logger.warning("Couldn't delete relayed !roll command: %s", e)
            await self.loggable_roll(
                roller,
                ctx.channel,
                dice,
                original_sender=original_sender,
                log_user=ctx.author,
                skip_log=skip_log,
            )
        else:
            await self.loggable_roll(
                roller,
                ctx.channel,
                dice,
                log_user=ctx.author,
                skip_log=skip_log,
            )

    async def loggable_roll(
        self,
        author,
        channel,
        dice: str,
        *,
        original_sender=None,
        log_user=None,
        skip_log=False,
    ):
        pattern = r'(?:(\d*)d)?(\d+)([+-]\d+)?'
        m = re.fullmatch(pattern, dice.replace(' ', ''))
        if not m:
            await channel.send('🎲 Format: `!roll XdY+Z` (e.g. `!roll 2d6+3`)')
            return

        n_dice, sides, mod = m.groups()
        n_dice = int(n_dice) if n_dice else 1
        sides = int(sides)
        mod = int(mod) if mod else 0

        role_names = [getattr(r, "name", "") for r in getattr(author, "roles", [])]
        bonus = 2 if "Netrunner Level 3" in role_names else 1 if "Netrunner Level 2" in role_names else 0

        rolls = [random.randint(1, sides) for _ in range(n_dice)]
        total = sum(rolls) + mod + bonus

        name = author.display_name
        header = f'🎲 {name} rolled: {n_dice}d{sides}{f"+{mod}" if mod else ""}\n'
        body = f'**Results:** {", ".join(map(str, rolls))}\n**Total:** {total}'
        if bonus:
            body += f' (includes +{bonus} Netrunner bonus)'
        result = header + body

        await channel.send(result)

        # Determine which user's thread should receive the log
        log_target = log_user or author

        # Log to DM thread if actual DM, or if relayed with original_sender
        if skip_log:
            return
        if isinstance(channel, discord.DMChannel) and not original_sender:
            thread = await self.bot.get_cog('DMHandler').get_or_create_dm_thread(log_target)
            if isinstance(thread, discord.abc.Messageable):
                await thread.send(
                    f"📥 **{log_target.display_name} used:** `!roll {dice}`\n\n{result}"
                )
        elif original_sender:
            thread = await self.bot.get_cog('DMHandler').get_or_create_dm_thread(log_target)
            if isinstance(thread, discord.abc.Messageable):
                await thread.send(
                    f"📤 **{original_sender.display_name} rolled as {author.display_name}** → `!roll {dice}`\n\n{result}"
                )

