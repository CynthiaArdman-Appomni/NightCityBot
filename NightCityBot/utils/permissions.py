from discord.ext import commands
import discord
import config


def is_fixer():
    async def predicate(ctx):
        # in-guild messages
        if isinstance(ctx.author, discord.Member):
            return discord.utils.get(ctx.author.roles, name=config.FIXER_ROLE_NAME) is not None

        # DMs or thread-posts: fetch member object from main guild
        guild = ctx.bot.get_guild(config.GUILD_ID)
        if not guild:
            return False

        member = guild.get_member(ctx.author.id)
        if not member:
            try:
                member = await guild.fetch_member(ctx.author.id)
            except discord.NotFound:
                return False

        return discord.utils.get(member.roles, name=config.FIXER_ROLE_NAME) is not None

    return commands.check(predicate)


def is_ripperdoc():
    """Check that the command author has the Ripperdoc role."""

    async def predicate(ctx):
        guild = ctx.bot.get_guild(config.GUILD_ID)
        if not guild:
            return False

        member = ctx.author
        if not isinstance(member, discord.Member):
            member = guild.get_member(ctx.author.id)
            if not member:
                try:
                    member = await guild.fetch_member(ctx.author.id)
                except discord.NotFound:
                    return False

        return any(r.id == config.RIPPERDOC_ROLE_ID for r in getattr(member, "roles", []))

    return commands.check(predicate)
