import discord
from discord.ext import commands
from typing import Optional
import config
from NightCityBot.utils.permissions import is_fixer
from NightCityBot.utils import constants
from NightCityBot.utils import startup_checks


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @is_fixer()
    async def post(self, ctx, destination: str, *, message: Optional[str] = None):
        """Posts a message to the specified channel or thread."""
        dest_channel = None

        # Resolve by ID
        if destination.isdigit():
            try:
                dest_channel = await ctx.guild.fetch_channel(int(destination))
            except discord.NotFound:
                dest_channel = None
        else:
            # Try finding by name or as a thread
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
                "`!open_shop` — Sundays only\n"
                "→ Log up to 4 openings per month. Each opening grants an immediate cash payout based on your business tier.\n"
                "→ Requires a Business role.\n"
                "`!attend` — Sundays only\n"
                "→ Verified players earn $250 every week they attend.\n"
                "`!due` — Estimate what you'll owe on the 1st."
            ),
            inline=False,
        )
    
        embed.add_field(
            name="🦾 Cyberware Maintenance",
            value=(
                "Players with cyberware roles receive a **Checkup** role every Monday. Remove it after your in-game check-up.\n"
                "If you still have the role the following week, immunosuppressant costs double each week. They start at about $15 for Medium, $40 for High, and $80 for Extreme.\n"
                "Costs cap after roughly 8 weeks at $2,000 / $5,000 / $10,000 respectively."
            ),
            inline=False,
        )
    
        embed.add_field(
            name="🏖️ Leave of Absence",
            value=(
                "`!start_loa` – pause your baseline fees, housing rent and Trauma Team while away.\n"
                "`!end_loa` – resume all costs when you return. Fixers can specify a member for both commands."
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
                "`!post <channel|thread> <message>` – send a message or execute a command in another location. Prefix the text with `!` to run it as a command.",
            ),
            (
                "📑 RP Management",
                "`!start_rp @users...` – create a locked RP channel for the listed users and ping Fixers.\n"
                "`!end_rp` – archive the current RP channel to the log forum and then delete it.",
            ),
            (
                "💵 Economy & Rent",
                "`!open_shop` – record a business opening on Sunday and grant passive income immediately.\n"
                "`!attend` – log weekly attendance for a $250 payout.\n"
                "`!due` – display a detailed breakdown of what a user owes on the 1st.\n"
                "`!collect_rent [@user] [-v]` – run the monthly rent cycle. `@user` targets one member and `-v` posts detailed logs.\n"
                "`!collect_housing @user` / `!collect_business @user` / `!collect_trauma @user` – charge specific housing, business or Trauma Team fees immediately.\n"
                "`!simulate_rent [@user] [-v]` – perform a dry run of rent collection using the same options.\n"
                "`!simulate_cyberware [@user] [week]` – preview cyberware medication costs globally or for a certain week.",
            ),
            (
                "🏖️ LOA & Cyberware",
                "`!start_loa [@user]` / `!end_loa [@user]` – toggle LOA for yourself or the specified member.\n"
                "`!checkup @user` – remove the checkup role once an in-character exam is completed.\n"
                "`!weeks_without_checkup @user` – show how many weeks a member has kept the role without a checkup.",
            ),
            (
                "⚙️ System Control",
                "`!enable_system <name>` / `!disable_system <name>` – turn major subsystems on or off.\n"
                "`!system_status` – display the current enable/disable flags.",
            ),
            (
                "🛠️ Admin Tools",
                "`!check_config` – re-run startup checks to verify channel and role IDs.\n"
                "`!test_bot [tests] [-silent] [-verbose]` – execute the built-in test suite. Results can be DMed when `-silent` is used and step details are shown with `-verbose`.\n"
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
            print(
                f"[DEBUG] Unknown command from {ctx.author}"
                f" in {getattr(ctx.channel, 'name', ctx.channel.id)}"
                f" ({ctx.channel.id}) → {ctx.message.content!r}"
            )
            await ctx.send("❌ Unknown command.")
            return
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("❌ Permission denied.")
            await self.log_audit(ctx.author, f"❌ Permission denied: {ctx.message.content}")
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
            print(f"[AUDIT] Skipped: Channel {config.AUDIT_LOG_CHANNEL_ID} is not a TextChannel")

        print(f"[AUDIT] {user}: {action_desc}")

    @commands.command(name="check_config", aliases=["config_check"])
    @commands.has_permissions(administrator=True)
    async def check_config(self, ctx):
        """Re-run startup configuration checks."""
        await ctx.send("🔍 Running configuration checks...")
        await startup_checks.verify_config(self.bot)
        await ctx.send("✅ Configuration check complete. See console for details.")
