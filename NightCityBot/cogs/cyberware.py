import discord
from discord.ext import commands, tasks
from datetime import datetime, time
from zoneinfo import ZoneInfo
from typing import Dict, Optional, List
from pathlib import Path

import config
from NightCityBot.utils.helpers import load_json_file, save_json_file
from NightCityBot.services.unbelievaboat import UnbelievaBoatAPI
from NightCityBot.utils.permissions import is_ripperdoc, is_fixer

MAX_COST = {
    "medium": 2000,
    "high": 5000,
    "extreme": 10000,
}
BASE_FACTOR = {k: v / 128 for k, v in MAX_COST.items()}


class CyberwareManager(commands.Cog):
    """Handle weekly cyberware check-ups and medication costs."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.unbelievaboat = UnbelievaBoatAPI(config.UNBELIEVABOAT_API_TOKEN)
        self.data: Dict[str, int] = {}
        self.bot.loop.create_task(self.load_data())
        self.weekly_check.start()

    async def load_data(self):
        path = Path(config.CYBERWARE_LOG_FILE)
        self.data = await load_json_file(path, default={})

    def cog_unload(self):
        self.weekly_check.cancel()

    def calculate_cost(self, level: str, weeks: int) -> int:
        """Return the medication cost for a given cyberware level and streak."""
        base = BASE_FACTOR[level]
        cost = int(base * (2 ** (weeks - 1)))
        return min(cost, MAX_COST[level])

    @tasks.loop(time=time(hour=0, tzinfo=ZoneInfo(getattr(config, "TIMEZONE", "UTC"))))
    async def weekly_check(self):
        """Run every day and trigger processing each Saturday."""
        control = self.bot.get_cog('SystemControl')
        if control and not control.is_enabled('cyberware'):
            return
        if datetime.now(ZoneInfo(getattr(config, "TIMEZONE", "UTC"))).weekday() != 5:  # Saturday
            return
        await self.process_week()

    async def process_week(
        self,
        *,
        dry_run: bool = False,
        log: Optional[List[str]] = None,
        target_member: Optional[discord.Member] = None,
    ):
        """Apply weekly check-up logic and deduct medication costs."""
        control = self.bot.get_cog('SystemControl')
        if control and not control.is_enabled('cyberware'):
            return
        guild = self.bot.get_guild(config.GUILD_ID)
        if not guild:
            return

        checkup_role = guild.get_role(config.CYBER_CHECKUP_ROLE_ID)
        medium_role = guild.get_role(config.CYBER_MEDIUM_ROLE_ID)
        high_role = guild.get_role(config.CYBER_HIGH_ROLE_ID)
        extreme_role = guild.get_role(config.CYBER_EXTREME_ROLE_ID)
        loa_role = guild.get_role(config.LOA_ROLE_ID)
        log_channel = guild.get_channel(
            getattr(config, "RIPPERDOC_LOG_CHANNEL_ID", config.RENT_LOG_CHANNEL_ID)
        )

        members = [target_member] if target_member else guild.members
        for member in members:
            if loa_role and loa_role in member.roles:
                continue
            role_level = None
            if extreme_role and extreme_role in member.roles:
                role_level = "extreme"
            elif high_role and high_role in member.roles:
                role_level = "high"
            elif medium_role and medium_role in member.roles:
                role_level = "medium"

            user_id = str(member.id)
            weeks = self.data.get(user_id, 0)

            has_checkup = checkup_role in member.roles if checkup_role else False

            if role_level is None:
                if weeks:
                    self.data.pop(user_id, None)
                continue

            if not has_checkup:
                # Give the checkup role and reset streak without charging
                if weeks:
                    weeks = 0
                if checkup_role:
                    if not dry_run:
                        await member.add_roles(checkup_role, reason="Weekly cyberware check")
                    if log is not None:
                        log.append(
                            f"{'Would give' if dry_run else 'Gave'} checkup role to <@{member.id}>"
                        )
                if not dry_run:
                    self.data[user_id] = 0
                continue

            # User kept the checkup role for another week → charge them
            weeks += 1
            cost = self.calculate_cost(role_level, weeks)
            if log is not None:
                log.append(f"Processing <@{member.id}> — week {weeks} cost ${cost}")
            balance = await self.unbelievaboat.get_balance(member.id)
            if not balance:
                if log_channel and not dry_run:
                    await log_channel.send(
                        f"⚠️ Could not fetch balance for <@{member.id}> to process cyberware meds."
                    )
                if log is not None and dry_run:
                    log.append(f"Would notify missing balance for <@{member.id}>")
                continue

            if dry_run:
                check = await self.unbelievaboat.verify_balance_ops(member.id)
                if log is not None:
                    log.append("🔄 Balance check passed." if check else "⚠️ Balance update check failed.")

            total = balance.get("cash", 0) + balance.get("bank", 0)
            if total < cost:
                if log_channel and not dry_run:
                    await log_channel.send(
                        f"🚨 <@{member.id}> cannot pay ${cost} for immunosuppressants and is in danger of cyberpsychosis."
                    )
                if log is not None and dry_run:
                    log.append(
                        f"Would warn insufficient funds for <@{member.id}> (${cost})"
                    )
            else:
                success = True
                if not dry_run:
                    success = await self.unbelievaboat.update_balance(
                        member.id, {"cash": -cost}, reason="Cyberware medication"
                    )
                if log_channel:
                    if success and not dry_run:
                        await log_channel.send(
                            f"✅ Deducted ${cost} for cyberware meds from <@{member.id}> (week {weeks})."
                        )
                    elif not success and not dry_run:
                        await log_channel.send(
                            f"❌ Could not deduct ${cost} from <@{member.id}> for cyberware meds."
                        )
                if log is not None and dry_run:
                    log.append(
                        f"✅ Would deduct ${cost} from <@{member.id}> for cyberware meds (week {weeks})."
                    )

            if not dry_run:
                self.data[user_id] = weeks
            elif log is not None:
                log.append(f"Streak would become {weeks} week(s) for <@{member.id}>")
        if not dry_run:
            await save_json_file(Path(config.CYBERWARE_LOG_FILE), self.data)
        elif log is not None:
            log.append("Simulation complete. No changes saved.")

    @commands.command()
    @commands.check_any(is_ripperdoc(), is_fixer(), commands.has_permissions(administrator=True))
    async def simulate_cyberware(
        self,
        ctx,
        member: Optional[str] = None,
        weeks: Optional[int] = None,
    ):
        """Simulate weekly cyberware costs.

        With no arguments, performs a full dry-run of the weekly process. When
        ``member`` and ``weeks`` are provided, it simply calculates how much that
        user would owe on the given week.
        """

        resolved_member: Optional[discord.Member] = None
        if member:
            try:
                resolved_member = await commands.MemberConverter().convert(ctx, member)
            except commands.BadArgument:
                await ctx.send("❌ Could not resolve user.")
                return

        # Specific user/week cost preview
        if resolved_member and weeks is not None:
            guild = ctx.guild
            medium_role = guild.get_role(config.CYBER_MEDIUM_ROLE_ID)
            high_role = guild.get_role(config.CYBER_HIGH_ROLE_ID)
            extreme_role = guild.get_role(config.CYBER_EXTREME_ROLE_ID)
            level = None
            if extreme_role and extreme_role in resolved_member.roles:
                level = "extreme"
            elif high_role and high_role in resolved_member.roles:
                level = "high"
            elif medium_role and medium_role in resolved_member.roles:
                level = "medium"

            if level is None:
                await ctx.send(f"{resolved_member.display_name} has no cyberware role.")
                return

            cost = self.calculate_cost(level, weeks)
            await ctx.send(
                f"💊 {resolved_member.display_name} would pay ${cost} for week {weeks}."
            )
            return

        # Global dry-run simulation or single-user when member is provided
        logs: List[str] = []
        await self.process_week(dry_run=True, log=logs, target_member=resolved_member)
        summary = "\n".join(logs) if logs else "✅ Simulation complete."
        await ctx.send(summary)
        admin_cog = self.bot.get_cog('Admin')
        if admin_cog:
            await admin_cog.log_audit(ctx.author, summary)

    @commands.command()
    @is_ripperdoc()
    async def checkup(self, ctx, member: discord.Member):
        """Remove the weekly cyberware checkup role from a member."""
        control = self.bot.get_cog('SystemControl')
        if control and not control.is_enabled('cyberware'):
            await ctx.send("⚠️ The cyberware system is currently disabled.")
            return
        guild = ctx.guild
        role = guild.get_role(config.CYBER_CHECKUP_ROLE_ID)
        if role is None:
            await ctx.send("⚠️ Checkup role is not configured.")
            return

        if role not in member.roles:
            await ctx.send(f"{member.display_name} does not have the checkup role.")
            return

        await member.remove_roles(role, reason="Cyberware check-up completed")
        await ctx.send(f"✅ Removed checkup role from {member.display_name}.")


        log_channel = ctx.guild.get_channel(
            getattr(config, "RIPPERDOC_LOG_CHANNEL_ID", config.RENT_LOG_CHANNEL_ID)
        )
        if log_channel:
            await log_channel.send(
                f"Ripperdoc {ctx.author.display_name} did a checkup on {member.display_name}"
            )

        self.data[str(member.id)] = 0
        await save_json_file(Path(config.CYBERWARE_LOG_FILE), self.data)

    @commands.command(aliases=["weekswithoutcheckup"])
    @commands.check_any(is_ripperdoc(), is_fixer())
    async def weeks_without_checkup(self, ctx, member: discord.Member):
        """Show how many weeks a member has gone without a checkup."""
        weeks = self.data.get(str(member.id), 0)
        await ctx.send(f"{member.display_name} has gone {weeks} week(s) without a checkup.")