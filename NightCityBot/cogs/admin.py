import discord
from discord.ext import commands
from typing import Optional
import config
from NightCityBot.utils.permissions import is_fixer
from NightCityBot.utils import constants


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
            name="🎲 RP Tools",
            value=(
                "`!roll [XdY+Z]`\n"
                "→ Roll dice in any channel or DM.\n"
                "→ Netrunner Level 2 = +1, Level 3 = +2 bonus.\n"
                "→ Roll results in DMs are logged privately."
            ),
            inline=False
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
            inline=False
        )

        embed.add_field(
            name="🦾 Cyberware Maintenance",
            value=(
                "Players with cyberware roles receive a **Checkup** role every Monday. Remove it after your in-game check-up.\n"
                "If you still have the role the following week, immunosuppressant costs double each week. They start at about $15 for Medium, $40 for High, and $80 for Extreme.\n"
                "Costs cap after roughly 8 weeks at $2,000 / $5,000 / $10,000 respectively."
            ),
            inline=False
        )

        embed.add_field(
            name="🏖️ Leave of Absence",
            value=(
                "Use `!start_loa` to pause housing rent, baseline fees, Trauma Team, and cyberware costs.\n"
                "`!end_loa` when you return. Business rent still applies."
            ),
            inline=False
        )

        embed.add_field(
            name="🦾 Ripperdoc",
            value=(
                "`!checkup @user` — Remove the weekly cyberware checkup role.\n"
                "`!weeks_without_checkup @user` — Show checkup streak."
            ),
            inline=False,
        )

        embed.set_footer(text="Use !roll, pay your rent, stay alive.")
        await ctx.send(embed=embed)

    @commands.command(name="helpfixer")
    async def helpfixer(self, ctx):
        """Display help for fixers."""
        embed = discord.Embed(
            title="🛠️ NCRP Bot — Fixer & Admin Help",
            description="Advanced commands for messaging, RP management, rent, and testing.",
            color=discord.Color.purple()
        )

        embed.add_field(
            name="✉️ Messaging Tools",
            value=(
                "`!dm @user <text>` — Send an anonymous DM to a user. Use `!roll` inside to relay a roll.\n"
                "`!post <channel|thread> <message>` — Post or run a command in another location."
            ),
            inline=False,
        )

        embed.add_field(
            name="📑 RP Management",
            value=(
                "`!start_rp @users` — Create a private RP channel for the listed users.\n"
                "`!end_rp` — Archive and delete the current RP session."
            ),
            inline=False,
        )

        embed.add_field(
            name="💵 Rent Commands",
            value=(
                "`!collect_rent [@user]` — Run monthly rent collection globally or for one user.\n"
                "`!collect_housing @user` — Charge housing rent immediately.\n"
                "`!collect_business @user` — Charge business rent immediately.\n"
                "`!collect_trauma @user` — Process Trauma Team subscription."
            ),
            inline=False,
        )

        embed.add_field(
            name="⚙️ System Control",
            value=(
                "`!enable_system <name>` — Turn a system on.\n"
                "`!disable_system <name>` — Turn a system off.\n"
                "`!system_status` — Show current system states."
            ),
            inline=False,
        )

        embed.add_field(
            name="🦾 Ripperdoc",
            value="`!checkup @user` — Remove the weekly cyberware checkup role.",
            inline=False,
        )

        embed.add_field(
            name="🧪 Testing",
            value="`!test_bot [tests]` — Run self-tests (bot owner only).",
            inline=False,
        )

        embed.set_footer(text="Fixer tools by MedusaCascade | v1.2")
        await ctx.send(embed=embed)

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
            print(f"[DEBUG] Unknown command from {ctx.author}: {ctx.message.content}")
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
