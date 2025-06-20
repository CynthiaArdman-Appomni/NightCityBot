import logging

import discord
from discord.ext import commands
from typing import Optional
import config
from NightCityBot.utils.permissions import is_fixer
from NightCityBot.utils import constants

logger = logging.getLogger(__name__)


class Admin(commands.Cog):
    """Administrative commands and global error handler."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the admin cog."""
        self.bot = bot

    @commands.command()
    @is_fixer()
    async def post(self, ctx, destination: str, *, message: Optional[str] = None):
        """Posts a message to the specified channel or thread."""
        dest_channel = None

        # Normalize destination string
        destination = destination.strip()
        if destination.startswith("<#") and destination.endswith(">"):
            destination = destination[2:-1]
        if destination.startswith("#"):
            destination = destination[1:]

        if destination.isdigit():
            try:
                dest_channel = await ctx.guild.fetch_channel(int(destination))
            except discord.NotFound:
                dest_channel = None
        else:
            dest_channel = discord.utils.get(ctx.guild.text_channels, name=destination)
            if dest_channel is None:
                for channel in ctx.guild.text_channels:
                    threads = channel.threads
                    dest_channel = discord.utils.get(threads, name=destination)
                    if dest_channel:
                        break

        if dest_channel is None:
            await ctx.send(f"❌ Couldn't find channel/thread '{destination}'.")
            return

        files = [await attachment.to_file() for attachment in ctx.message.attachments]

        if message or files:
            if message and message.strip().startswith("!"):
                command_text = message.strip()
                fake_msg = ctx.message
                fake_msg.content = command_text
                fake_ctx = await self.bot.get_context(fake_msg)
                fake_ctx.channel = dest_channel
                fake_ctx.author = ctx.author
                setattr(fake_ctx, "original_author", ctx.author)
                setattr(fake_ctx, "skip_dm_log", True)

                await self.bot.invoke(fake_ctx)
                await self.log_audit(ctx.author, f"✅ Executed `{command_text}` in {dest_channel.mention}.")
            else:
                await dest_channel.send(content=message, files=files)
                await self.log_audit(ctx.author, f"✅ Posted anonymously to {dest_channel.mention}.")
        else:
            await ctx.send("❌ Provide a message or attachment.")
        try:
            await ctx.message.delete()
            await self.log_audit(ctx.author, f"🗑️ Deleted command: {ctx.message.content}")
        except Exception:
            pass

    @commands.command(name="help")
    async def block_help(self, ctx):
        await ctx.send("❌ `!help` is disabled. Use `!helpme` or `!helpfixer` instead.")

    @commands.command(name="helpme")
    async def helpme(self, ctx):
        """Display help for regular users."""
        embed = discord.Embed(
            title="📘 NCRP Bot — Player Help",
            description="Basic commands for RP, rent, and rolling dice. Use `!helpfixer` if you're a Fixer.",
            color=discord.Color.teal()
        )

        embed.add_field(
            name="🎲 Dice Rolls",
            value=(
                "`!roll [XdY+Z]` – roll dice using standard notation, e.g. `!roll 2d6+1`. "
                "Mention another user to roll for them.\n"
                "Netrunner Level 2 grants +1 and Level 3 grants +2 to the total. "
                "Rolls made in DMs are recorded in your private log thread."
            ),
            inline=False,
        )

        embed.add_field(
            name="💰 Rent & Cost of Living",
            value=(
                "Everyone pays a **$500/month** baseline fee for survival (food, water, etc).\n"
                "Even if you don't have a house or business — you're still eating Prepack.\n\n"
                "`!open_shop` (aliases: !openshop, !os) — Sundays only\n"
                "→ Log up to 4 openings per month. Each opening grants an immediate cash payout based on your business tier.\n"
                "→ Requires a Business role.\n"
                "`!attend` — Sundays only\n"
                "→ Verified players earn $250 every week they attend.\n"
                "`!due` — Estimate what you'll owe on the 1st."
            ),
            inline=False,
        )
    
    
        embed.add_field(
            name="🏖️ Leave of Absence",
            value=(
                "`!start_loa` (aliases: !startloa, !loa_start, !loastart) – pause your baseline fees, housing rent and Trauma Team while away.\n"
                "`!end_loa` (aliases: !endloa, !loa_end, !loaend) – resume all costs when you return. Fixers can specify a member for both commands."
            ),
            inline=False,
        )

        embed.set_footer(text="Use !roll, pay your rent, stay alive.")
        await ctx.send(embed=embed)

    @commands.command(name="helpfixer")
    async def helpfixer(self, ctx):
        """Display help for fixers."""
        def embed_len(e: discord.Embed) -> int:
            total = len(e.title or "") + len(e.description or "")
            if e.footer and e.footer.text:
                total += len(e.footer.text)
            for f in e.fields:
                total += len(f.name) + len(str(f.value))
            return total

        fields = [
            (
                "✉️ Messaging Tools",
                "`!dm @user <text>` – send an anonymous DM with optional attachments. The conversation is logged in a private thread. Use `!roll` within that thread to relay dice results.\n"
                "`!post <channel|thread> <message>` – send a message or execute a command in another location.",
            ),
            (
                "📑 RP Management",
                "`!start_rp @users...` (aliases: !startrp, !rp_start, !rpstart) – create a locked RP channel for the listed users and ping Fixers.\n"
                "`!end_rp` (aliases: !endrp, !rp_end, !rpend) – archive the current RP channel to the log forum and then delete it.",
            ),
            (
                "💵 Economy & Rent",
                "`!open_shop` (aliases: !openshop, !os) – record a business opening on Sunday and grant passive income immediately.\n"
                "`!attend` – log weekly attendance for a $250 payout.\n"
                "`!due` – display a detailed breakdown of what a user owes on the 1st.\n"
                "`!collect_rent [@user] [-v] [-force]` (alias: !collectrent) – run the monthly rent cycle. Use `-force` to ignore the 30 day limit.\n"
                "`!collect_housing @user [-v] [-force]` / `!collect_business @user [-v] [-force]` / `!collect_trauma @user [-v] [-force]` – charge specific fees with optional verbose logs. (aliases: !collecthousing / !collectbusiness / !collecttrauma)\n"
                "`!simulate_rent [@user] [-v]` (alias: !simulaterent) – perform a dry run of rent collection using the same options.\n"
                "`!simulate_cyberware [@user] [week]` – preview cyberware medication costs globally or for a certain week.\n"
                "`!backup_balances` – save all member balances to a timestamped file.\n"
                "`!restore_balances <file>` – restore balances from a backup file.",
            ),
            (
                "🏖️ LOA & Cyberware",
                "`!start_loa [@user]` (aliases: !startloa, !loa_start, !loastart) / `!end_loa [@user]` (aliases: !endloa, !loa_end, !loaend) – toggle LOA for yourself or the specified member.\n"
                "`!checkup @user` (aliases: !check-up, !check_up, !cu, !cup) – remove the checkup role once an in-character exam is completed.\n"
                "`!weeks_without_checkup @user` (aliases: !wwocup, !wwc) – show how many weeks a member has kept the role without a checkup.",
            ),
            (
                "⚙️ System Control",
                "`!enable_system <name>` / `!disable_system <name>` (aliases: !es/!ds) – toggle major subsystems.\n"
                "`!system_status` – display the current enable/disable flags.",
            ),
            (
                "🛠️ Admin Tools",
                "`!test_bot [tests] [-silent] [-verbose]` – execute the built-in test suite. Results can be DMed when `-silent` is used and step details are shown with `-verbose`. Prefixes run groups of tests.\n"
                "`!list_tests` – show all available self-test names.\n"
                "`!test__bot [pattern]` – run the PyTest suite optionally filtering by pattern.",
            ),
        ]

        embeds = []
        current = discord.Embed(
            title="🛠️ NCRP Bot — Fixer & Admin Help",
            description="Advanced commands for messaging, RP management, rent, and testing.",
            color=discord.Color.purple(),
        )
        for name, value in fields:
            if embed_len(current) + len(name) + len(value) > 5800:
                current.set_footer(text="Fixer tools by MedusaCascade | v1.2")
                embeds.append(current)
                current = discord.Embed(
                    title="🛠️ NCRP Bot — Fixer & Admin Help (cont.)",
                    color=discord.Color.purple(),
                )
            current.add_field(name=name, value=value, inline=False)

        current.set_footer(text="Fixer tools by MedusaCascade | v1.2")
        embeds.append(current)

        for e in embeds:
            await ctx.send(embed=e)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Global error handler for commands."""
        # Ignore errors triggered by other bots to avoid feedback loops
        if getattr(ctx.author, "bot", False):
            return
        if isinstance(error, commands.CommandNotFound):
            # Ignore specific economy bot commands entirely
            cmd = ctx.message.content.lstrip(self.bot.command_prefix).split()[0].lower()
            if cmd in constants.UNBELIEVABOAT_COMMANDS:
                return
            # Otherwise show a basic notice but do not audit
            logger.debug(
                "Unknown command from %s in %s (%s) → %r",
                ctx.author,
                getattr(ctx.channel, 'name', ctx.channel.id),
                ctx.channel.id,
                ctx.message.content,
            )
            await ctx.send("❌ Unknown command.")
            return
        elif isinstance(error, commands.CheckFailure):
            reason = str(error) or "Permission denied."
            await ctx.send(f"❌ {reason}")
            await self.log_audit(ctx.author, f"❌ {reason}: {ctx.message.content}")
        else:
            await ctx.send(f"⚠️ Error: {str(error)}")
            await self.log_audit(ctx.author, f"⚠️ Error: {ctx.message.content} → {str(error)}")

    async def log_audit(self, user, action_desc):
        """Log an audit entry to the audit channel."""
        audit_channel = self.bot.get_channel(config.AUDIT_LOG_CHANNEL_ID)

        if isinstance(audit_channel, discord.TextChannel):
            embed = discord.Embed(title="📝 Audit Log", color=discord.Color.blue())
            embed.add_field(name="User", value=f"{user} ({user.id})", inline=False)
            embed.add_field(name="Action", value=action_desc, inline=False)
            await audit_channel.send(embed=embed)
        else:
            logger.warning(
                "Skipped audit log: channel %s is not a TextChannel",
                config.AUDIT_LOG_CHANNEL_ID,
            )
        logger.info("AUDIT %s: %s", user, action_desc)

