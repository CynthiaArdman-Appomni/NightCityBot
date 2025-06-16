import discord
from discord.ext import commands
from typing import Optional

import config
from NightCityBot.utils.permissions import is_fixer


class LOA(commands.Cog):
    """Manage Leave of Absence status."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_loa_role(self, guild: discord.Guild) -> Optional[discord.abc.Snowflake]:
        """Return a minimal role object for the LOA role ID.

        The real :class:`discord.Role` object is not required for the
        add/remove role operations performed in the tests. Returning a simple
        :class:`~discord.Object` avoids issues when the role is represented by a
        mock object lacking comparison methods.
        """
        role = guild.get_role(config.LOA_ROLE_ID)
        if role is None:
            return discord.Object(id=config.LOA_ROLE_ID)
        return discord.Object(id=role.id)

    @commands.command()
    async def start_loa(self, ctx, member: Optional[discord.Member] = None):
        """Start a leave of absence. Fixers may specify a member."""
        control = self.bot.get_cog('SystemControl')
        if control and not control.is_enabled('loa'):
            await ctx.send("⚠️ The LOA system is currently disabled.")
            return
        guild = ctx.guild
        loa_role = self.get_loa_role(guild)
        if loa_role is None:
            await ctx.send("⚠️ LOA role is not configured.")
            return

        target = member or ctx.author
        if member and not any(r.name == config.FIXER_ROLE_NAME for r in ctx.author.roles):
            await ctx.send("❌ Permission denied.")
            return

        # Compare by ID to avoid issues with mocked Role equality
        if any(r.id == loa_role.id for r in target.roles):
            await ctx.send(f"{target.display_name} is already on LOA.")
            return

        await target.add_roles(loa_role, reason="LOA start")
        if target == ctx.author:
            await ctx.send("✅ You are now on LOA.")
        else:
            await ctx.send(f"✅ {target.display_name} is now on LOA.")

    @commands.command()
    async def end_loa(self, ctx, member: Optional[discord.Member] = None):
        """End a leave of absence. Fixers may specify a member."""
        control = self.bot.get_cog('SystemControl')
        if control and not control.is_enabled('loa'):
            await ctx.send("⚠️ The LOA system is currently disabled.")
            return
        guild = ctx.guild
        loa_role = self.get_loa_role(guild)
        if loa_role is None:
            await ctx.send("⚠️ LOA role is not configured.")
            return

        target = member or ctx.author
        if member and not any(r.name == config.FIXER_ROLE_NAME for r in ctx.author.roles):
            await ctx.send("❌ Permission denied.")
            return

        # Compare by ID to avoid issues with mocked Role equality
        if not any(r.id == loa_role.id for r in target.roles):
            await ctx.send(f"{target.display_name} is not currently on LOA.")
            return

        await target.remove_roles(loa_role, reason="LOA end")
        if target == ctx.author:
            await ctx.send("✅ Your LOA has ended.")
        else:
            await ctx.send(f"✅ {target.display_name}'s LOA has ended.")
