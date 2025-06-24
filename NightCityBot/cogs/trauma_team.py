import discord
from discord.ext import commands
from NightCityBot.utils.constants import TRAUMA_ROLE_COSTS
import config


class TraumaTeam(commands.Cog):
    """Commands related to Trauma Team assistance."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(aliases=["calltrauma", "trauma"])
    async def call_trauma(self, ctx: commands.Context) -> None:
        """Ping the Trauma Team role with the user's plan."""
        trauma_channel = ctx.guild.get_channel(config.TRAUMA_FORUM_CHANNEL_ID)
        if trauma_channel is None:
            await ctx.send("⚠️ Trauma Team channel not found.")
            return

        plan_role = next((r for r in ctx.author.roles if r.name in TRAUMA_ROLE_COSTS), None)
        if not plan_role:
            await ctx.send("⚠️ You don't have a Trauma Team plan role.")
            return

        mention = f"<@&{config.TRAUMA_TEAM_ROLE_ID}>"
        message = f"{mention} <@{ctx.author.id}> with **{plan_role.name}** is in need of assistance."

        if isinstance(trauma_channel, discord.TextChannel):
            await trauma_channel.send(message)
        elif isinstance(trauma_channel, discord.ForumChannel):
            created = await trauma_channel.create_thread(
                name=f"Trauma-{ctx.author.name}-{ctx.author.id}",
                content=message,
                reason="Trauma Team assistance request",
            )
            # ensure thread is returned consistently across discord.py versions
            thread = created.thread if hasattr(created, "thread") else created
            if isinstance(thread, discord.Thread):
                await thread.edit(archived=False)
        else:
            await ctx.send("⚠️ Trauma Team channel not found.")
            return

        await ctx.send("🚑 Trauma Team notified.")
