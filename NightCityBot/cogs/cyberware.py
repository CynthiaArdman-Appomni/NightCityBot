import discord
from discord.ext import commands, tasks
from datetime import datetime
from typing import Dict
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

    @tasks.loop(hours=24)
    async def weekly_check(self):
        """Run every day and trigger processing each Saturday."""
        control = self.bot.get_cog('SystemControl')
        if control and not control.is_enabled('cyberware'):
            return
        if datetime.utcnow().weekday() != 5:  # Saturday
            return
        await self.process_week()

    async def process_week(self):
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

        for member in guild.members:
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
                    await member.add_roles(checkup_role, reason="Weekly cyberware check")
                self.data[user_id] = 0
                continue

            # User kept the checkup role for another week → charge them
            weeks += 1
            cost = self.calculate_cost(role_level, weeks)
            balance = await self.unbelievaboat.get_balance(member.id)
            if not balance:
                if log_channel:
                    await log_channel.send(
                        f"⚠️ Could not fetch balance for <@{member.id}> to process cyberware meds."
                    )
                continue

            total = balance.get("cash", 0) + balance.get("bank", 0)
            if total < cost:
                if log_channel:
                    await log_channel.send(
                        f"🚨 <@{member.id}> cannot pay ${cost} for immunosuppressants and is in danger of cyberpsychosis."
                    )
            else:
                success = await self.unbelievaboat.update_balance(
                    member.id, {"cash": -cost}, reason="Cyberware medication"
                )
                if log_channel:
                    if success:
                        await log_channel.send(
                            f"✅ Deducted ${cost} for cyberware meds from <@{member.id}> (week {weeks})."
                        )
                    else:
                        await log_channel.send(
                            f"❌ Could not deduct ${cost} from <@{member.id}> for cyberware meds."
                        )

            self.data[user_id] = weeks

        await save_json_file(Path(config.CYBERWARE_LOG_FILE), self.data)

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