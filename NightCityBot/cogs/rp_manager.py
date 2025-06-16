import re
import discord
from discord.ext import commands
from typing import Optional, List, cast
from NightCityBot.utils.permissions import is_fixer
from NightCityBot.utils.helpers import build_channel_name
import config


class RPManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user or message.author.bot:
            return
        if isinstance(message.channel, discord.TextChannel) and message.channel.name.startswith("text-rp-"):
            if message.content.strip().startswith("!"):
                ctx = await self.bot.get_context(message)
                admin = self.bot.get_cog('Admin')
                async def audit_send(content=None, **kwargs):
                    if admin and content:
                        await admin.log_audit(message.author, content)
                ctx.send = audit_send
                await self.bot.invoke(ctx)
                try:
                    await message.delete()
                except Exception:
                    pass
                return

    @commands.command(
        aliases=["startrp", "rp_start", "rpstart"]
    )
    @commands.has_permissions(administrator=True)
    async def start_rp(self, ctx, *user_identifiers: str):
        """Starts a private RP channel for the mentioned users."""
        guild = ctx.guild
        users = []

        for identifier in user_identifiers:
            if identifier.isdigit():
                member = guild.get_member(int(identifier))
            else:
                match = re.findall(r"<@!?(\d+)>", identifier)
                member = guild.get_member(int(match[0])) if match else None
            if member:
                users.append(member)

        if not users:
            await ctx.send("❌ Could not resolve any users.")
            return

        channel = await self.create_group_rp_channel(guild, users)
        mentions = " ".join(user.mention for user in users)
        fixer_role = await ctx.guild.fetch_role(config.FIXER_ROLE_ID)
        fixer_mention = fixer_role.mention if fixer_role else ""

        await channel.send(f"✅ RP session created! {mentions} {fixer_mention}")
        await ctx.send(f"✅ RP channel created: {channel.mention}")
        return channel

    @commands.command(
        aliases=["endrp", "rp_end", "rpend"]
    )
    @is_fixer()
    async def end_rp(self, ctx):
        """Ends the RP session in the current channel."""
        channel = ctx.channel
        if not channel.name.startswith("text-rp-"):
            await ctx.send("❌ This command can only be used in an RP session channel.")
            return

        await ctx.send("📝 Ending RP session, logging contents and deleting channel...")
        await self.end_rp_session(channel)

    async def create_group_rp_channel(
            self,
            guild: discord.Guild,
            users: list[discord.Member],
            category: Optional[discord.CategoryChannel] = None
    ):
        """Creates a private RP channel for a group of users."""
        usernames = [(user.name, user.id) for user in users]
        channel_name = build_channel_name(usernames)

        allowed_roles = {"Fixer", "Admin"}
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        for user in users:
            overwrites[user] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        for role in guild.roles:
            if role.name in allowed_roles:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        return await guild.create_text_channel(
            name=channel_name,
            overwrites=overwrites,
            category=category,
            reason="Creating private RP group channel"
        )

    async def end_rp_session(self, channel: discord.TextChannel):
        """Archives and ends an RP session."""
        log_channel = channel.guild.get_channel(config.GROUP_AUDIT_LOG_CHANNEL_ID)
        if not isinstance(log_channel, discord.ForumChannel):
            await channel.send(
                "⚠️ Logging failed: audit log channel is not a ForumChannel. "
                "Deleting session without logging."
            )
            await channel.delete(reason="RP session ended without log channel")
            return

        participants = channel.name.replace("text-rp-", "").split("-")
        thread_name = "GroupRP-" + "-".join(participants)

        created = await log_channel.create_thread(
            name=thread_name,
            content=f"📘 RP log for `{channel.name}`"
        )

        log_thread = created.thread if hasattr(created, "thread") else created
        log_thread = cast(discord.Thread, log_thread)

        async for msg in channel.history(limit=None, oldest_first=True):
            ts = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            content = msg.content or "*(No text content)*"
            entry = f"[{ts}] 📥 **Received from {msg.author.display_name}**:\n{content}"

            if msg.attachments:
                for attachment in msg.attachments:
                    entry += f"\n📎 Attachment: {attachment.url}"

            if len(entry) <= 2000:
                await log_thread.send(entry)
            else:
                chunks = [entry[i:i + 1990] for i in range(0, len(entry), 1990)]
                for chunk in chunks:
                    await log_thread.send(chunk)

        await channel.delete(reason="RP session ended and logged.")
