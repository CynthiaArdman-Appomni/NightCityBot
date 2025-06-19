import logging
import os
import json
from datetime import datetime, timedelta
import asyncio
from typing import Optional, List, Dict

import discord
from discord.ext import commands
from pathlib import Path
from NightCityBot.utils.permissions import is_fixer
from NightCityBot.utils.constants import (
    ROLE_COSTS_BUSINESS,
    ROLE_COSTS_HOUSING,
    BASELINE_LIVING_COST,
    TIER_0_INCOME_SCALE,
    OPEN_PERCENT,
    ATTEND_REWARD,
    TRAUMA_ROLE_COSTS,
)
from NightCityBot.utils import helpers

# Expose helper functions for tests that patch them directly
load_json_file = helpers.load_json_file
save_json_file = helpers.save_json_file
import config
from NightCityBot.services.unbelievaboat import UnbelievaBoatAPI
from NightCityBot.services.trauma_team import TraumaTeamService

logger = logging.getLogger(__name__)


class Economy(commands.Cog):
    """Cog managing player economy and automated rent."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the economy cog."""
        self.bot = bot
        self.unbelievaboat = UnbelievaBoatAPI(config.UNBELIEVABOAT_API_TOKEN)
        self.trauma_service = TraumaTeamService(bot)
        self.open_log_lock = asyncio.Lock()
        self.attend_lock = asyncio.Lock()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user or message.author.bot:
            return
        channel_id = message.channel.id
        parent_id = getattr(message.channel, 'parent_id', None)
        if channel_id == config.BUSINESS_ACTIVITY_CHANNEL_ID or parent_id == config.BUSINESS_ACTIVITY_CHANNEL_ID:

            if not message.content.strip().startswith(("!open_shop", "!openshop", "!os")):
                try:
                    await message.delete()
                except Exception:
                    pass
                admin = self.bot.get_cog('Admin')
                if admin:
                    await admin.log_audit(
                        message.author,
                        f"🗑️ Deleted message in {message.channel.mention}: {message.content}"
                    )
        if channel_id == config.ATTENDANCE_CHANNEL_ID or parent_id == config.ATTENDANCE_CHANNEL_ID:

            if not message.content.strip().startswith("!attend"):
                try:
                    await message.delete()
                except Exception:
                    pass
                admin = self.bot.get_cog('Admin')
                if admin:
                    await admin.log_audit(
                        message.author,
                        f"🗑️ Deleted message in {message.channel.mention}: {message.content}"
                    )

    def cog_unload(self):
        self.bot.loop.create_task(self.unbelievaboat.close())

    def calculate_passive_income(self, role: str, open_count: int) -> int:
        """Calculate passive income based on role and number of shop opens."""
        if role == "Business Tier 0":
            return TIER_0_INCOME_SCALE.get(open_count, 0)

        base_rent = ROLE_COSTS_BUSINESS.get(role, 500)
        return int(base_rent * OPEN_PERCENT[open_count])

    async def apply_passive_income(
            self,
            member: discord.Member,
            applicable_roles: List[str],
            business_open_log: Dict,
            log: List[str]
    ) -> tuple[Optional[int], Optional[int]]:
        """Apply passive income based on business opens and roles."""
        total_income = 0

        member_id_str = str(member.id)
        now = helpers.get_tz_now()
        opens_this_month = [
            ts
            for ts in business_open_log.get(member_id_str, [])
            if datetime.fromisoformat(ts).month == now.month
            and datetime.fromisoformat(ts).year == now.year
        ]
        open_count = min(len(opens_this_month), 4)

        for role in applicable_roles:
            if "Housing Tier" in role:
                continue

            income = self.calculate_passive_income(role, open_count)
            log.append(f"💰 Passive income for {role}: ${income} ({open_count} opens)")
            total_income += income

        if total_income > 0:
            success = await self.unbelievaboat.update_balance(
                member.id,
                {"cash": total_income},
                reason="Passive income"
            )
            if success:
                updated = await self.unbelievaboat.get_balance(member.id)
                log.append(f"➕ Added ${total_income} passive income.")
                if updated:
                    return updated["cash"], updated["bank"]

        current = await self.unbelievaboat.get_balance(member.id)
        if current:
            return current["cash"], current["bank"]
        return None, None

    @commands.command(aliases=["openshop", "os"])
    @commands.has_permissions(send_messages=True)
    async def open_shop(self, ctx):
        """Log a business opening and grant income immediately."""
        control = self.bot.get_cog('SystemControl')
        if control and not control.is_enabled('open_shop'):
            await ctx.send("⚠️ The open_shop system is currently disabled.")
            return
        if ctx.channel.id != config.BUSINESS_ACTIVITY_CHANNEL_ID:
            ch = ctx.guild.get_channel(config.BUSINESS_ACTIVITY_CHANNEL_ID)
            mention = ch.mention if ch else "#open_shop"
            await ctx.send(f"❌ Please use {mention} for this command.")
            return

        if not any(r.name.startswith("Business") for r in ctx.author.roles):
            await ctx.send("❌ You must have a business role to use this command.")
            return

        now = helpers.get_tz_now()
        if now.weekday() != 6:
            await ctx.send("❌ Business openings can only be logged on Sundays.")
            return

        user_id = str(ctx.author.id)
        now_str = now.isoformat()

        async with self.open_log_lock:
            data = await load_json_file(config.OPEN_LOG_FILE, default={})

            all_opens = data.get(user_id, [])
            this_month_opens = [
                datetime.fromisoformat(ts)
                for ts in all_opens
                if datetime.fromisoformat(ts).month == now.month and
                   datetime.fromisoformat(ts).year == now.year
            ]

            if any(ts.date() == now.date() for ts in this_month_opens):
                await ctx.send("❌ You've already logged a business opening today.")
                return

            open_count_before = min(len(this_month_opens), 4)
            open_count_after = min(open_count_before + 1, 4)
            open_count_total = len(this_month_opens) + 1

            all_opens.append(now_str)
            data[user_id] = all_opens
            await save_json_file(config.OPEN_LOG_FILE, data)

        reward = 0
        role_names = [r.name for r in ctx.author.roles]
        for role in role_names:
            if "Business Tier" in role:
                if role == "Business Tier 0":
                    total_after = TIER_0_INCOME_SCALE.get(open_count_after, 0)
                    total_before = TIER_0_INCOME_SCALE.get(open_count_before, 0)
                else:
                    base = ROLE_COSTS_BUSINESS.get(role, 500)
                    total_after = int(base * OPEN_PERCENT[open_count_after])
                    total_before = int(base * OPEN_PERCENT.get(open_count_before, 0))
                reward += total_after - total_before

        if reward > 0:
            await self.unbelievaboat.update_balance(ctx.author.id, {"cash": reward}, reason="Business activity reward")
            await ctx.send(f"✅ Business opening logged! You earned ${reward}. ({open_count_total} this month)")
        else:
            await ctx.send(f"✅ Business opening logged! ({open_count_total} this month)")

    @commands.command()
    async def attend(self, ctx):
        """Log attendance for players with the verified role and award cash."""
        control = self.bot.get_cog('SystemControl')
        if control and not control.is_enabled('attend'):
            await ctx.send("⚠️ The attend system is currently disabled.")
            return
        if ctx.channel.id != config.ATTENDANCE_CHANNEL_ID:
            ch = ctx.guild.get_channel(config.ATTENDANCE_CHANNEL_ID)
            mention = ch.mention if ch else "#attend"
            await ctx.send(f"❌ Please use {mention} for this command.")
            return
        if not any(r.id == config.VERIFIED_ROLE_ID for r in ctx.author.roles):
            await ctx.send("❌ You must be verified to use this command.")
            return

        now = helpers.get_tz_now()
        if now.weekday() != 6:
            await ctx.send("❌ Attendance can only be logged on Sundays.")
            return

        user_id = str(ctx.author.id)
        now_str = now.isoformat()

        async with self.attend_lock:
            data = await load_json_file(config.ATTEND_LOG_FILE, default={})

            all_logs = data.get(user_id, [])
            parsed = [datetime.fromisoformat(ts) for ts in all_logs]
            if parsed and (now - max(parsed)).days < 7:
                await ctx.send("❌ You've already logged attendance this week.")
                return

            all_logs.append(now_str)
            data[user_id] = all_logs
            await save_json_file(config.ATTEND_LOG_FILE, data)

        reward = ATTEND_REWARD
        await self.unbelievaboat.update_balance(ctx.author.id, {"cash": reward}, reason="Attendance reward")
        await ctx.send(f"✅ Attendance logged! You received ${reward}.")

    def calculate_due(self, member: discord.Member) -> tuple[int, List[str]]:
        """Calculate upcoming rent, baseline, cyberware and subscription costs."""
        details: List[str] = []
        total = 0
        role_names = [r.name for r in member.roles]
        loa_role = member.guild.get_role(config.LOA_ROLE_ID)
        on_loa = loa_role in member.roles if loa_role else False

        if on_loa:
            details.append("LOA active: baseline, housing, and Trauma Team skipped")
        else:
            total += BASELINE_LIVING_COST
            details.append(f"Baseline living cost: ${BASELINE_LIVING_COST}")
            for role in role_names:
                if "Housing Tier" in role:
                    amount = ROLE_COSTS_HOUSING.get(role, 0)
                    total += amount
                    details.append(f"{role}: ${amount}")

        for role in role_names:
            if "Business Tier" in role:
                amount = ROLE_COSTS_BUSINESS.get(role, 0)
                total += amount
                details.append(f"{role}: ${amount}")

        if not on_loa:
            trauma_role = next((r for r in member.roles if r.name in TRAUMA_ROLE_COSTS), None)
            if trauma_role:
                cost = TRAUMA_ROLE_COSTS[trauma_role.name]
                total += cost
                details.append(f"{trauma_role.name}: ${cost}")

            cyber = self.bot.get_cog('CyberwareManager')
            if cyber:
                guild = member.guild
                checkup_role = guild.get_role(config.CYBER_CHECKUP_ROLE_ID)
                medium = guild.get_role(config.CYBER_MEDIUM_ROLE_ID)
                high = guild.get_role(config.CYBER_HIGH_ROLE_ID)
                extreme = guild.get_role(config.CYBER_EXTREME_ROLE_ID)

                level = None
                if extreme and extreme in member.roles:
                    level = 'extreme'
                elif high and high in member.roles:
                    level = 'high'
                elif medium and medium in member.roles:
                    level = 'medium'

                if level:
                    weeks = cyber.data.get(str(member.id), 0)
                    if checkup_role and checkup_role in member.roles:
                        upcoming = weeks + 1
                        cost = cyber.calculate_cost(level, upcoming)
                        total += cost
                        details.append(f"Cyberware meds week {upcoming}: ${cost}")
                    else:
                        details.append("Cyberware checkup due — no med cost")

        return total, details

    @commands.command(name="due")
    async def due(self, ctx):
        """Show estimated amount you will owe on the 1st of the month.

        Includes upcoming cyberware medication costs if applicable.
        """
        logger.debug(
            "due command invoked by %s (%s) in %s (%s)",
            ctx.author,
            ctx.author.id,
            getattr(ctx.channel, 'name', ctx.channel.id),
            ctx.channel.id,
        )
        total, details = self.calculate_due(ctx.author)
        lines = [f"💸 **Estimated Due:** ${total}"] + [f"• {d}" for d in details]
        await ctx.send("\n".join(lines))

    async def backup_balances(self, members: List[discord.Member], path: Path) -> None:
        """Save current cash and bank balances for members."""
        data: Dict[str, Dict[str, int]] = {}
        for m in members:
            bal = await self.unbelievaboat.get_balance(m.id)
            if bal:
                data[str(m.id)] = {
                    "cash": bal.get("cash", 0),
                    "bank": bal.get("bank", 0),
                }
        await save_json_file(path, data)

    @commands.command(name="backup_balances")
    @commands.has_permissions(administrator=True)
    async def backup_balances_command(self, ctx):
        """Back up all member balances to a timestamped file."""
        members = ctx.guild.members
        backup_dir = Path(config.BALANCE_BACKUP_DIR)
        backup_dir.mkdir(exist_ok=True)
        file_path = backup_dir / f"manual_{datetime.utcnow():%Y%m%d_%H%M%S}.json"
        await self.backup_balances(members, file_path)
        await ctx.send(f"✅ Balances backed up to `{file_path.name}`")

    @commands.command(name="restore_balances")
    @commands.has_permissions(administrator=True)
    async def restore_balances_command(self, ctx, filename: str):
        """Restore member balances from a backup file."""
        backup_path = Path(config.BALANCE_BACKUP_DIR) / filename
        if not backup_path.exists():
            await ctx.send("❌ Backup file not found.")
            return
        data = await load_json_file(backup_path, default={})
        restored = 0
        for uid_str, bal in data.items():
            try:
                uid = int(uid_str)
            except ValueError:
                continue
            current = await self.unbelievaboat.get_balance(uid)
            if not current:
                continue
            payload = {}
            delta_cash = bal.get("cash", 0) - current.get("cash", 0)
            delta_bank = bal.get("bank", 0) - current.get("bank", 0)
            if delta_cash:
                payload["cash"] = delta_cash
            if delta_bank:
                payload["bank"] = delta_bank
            if payload:
                await self.unbelievaboat.update_balance(uid, payload, reason="Balance restore")
                restored += 1
        await ctx.send(f"✅ Restored balances for {restored} members from `{filename}`")

    async def deduct_flat_fee(self, member: discord.Member, cash: int, bank: int, log: List[str], amount: int = BASELINE_LIVING_COST, *, dry_run: bool = False) -> tuple[bool, int, int]:
        total = (cash or 0) + (bank or 0)
        if total < amount:
            log.append(f"❌ Insufficient funds for flat fee deduction (${amount}). Current balance: ${total}.")
            return False, cash, bank

        deduct_cash = min(cash, amount)
        deduct_bank = amount - deduct_cash
        payload: Dict[str, int] = {}
        if deduct_cash > 0:
            payload["cash"] = -deduct_cash
        if deduct_bank > 0:
            payload["bank"] = -deduct_bank

        success = True
        if not dry_run:
            success = await self.unbelievaboat.update_balance(
                member.id, payload, reason="Flat Monthly Fee"
            )
        if success:
            cash -= deduct_cash
            bank -= deduct_bank
            log.append(
                f"{'💸 Would deduct' if dry_run else '💸 Deducted'} flat monthly fee of ${amount} (Cash: ${deduct_cash}, Bank: ${deduct_bank})."
            )
        else:
            log.append("❌ Failed to deduct flat monthly fee.")

        return success, cash, bank

    async def process_housing_rent(
            self,
            member: discord.Member,
            roles: List[str],
            cash: int,
            bank: int,
            log: List[str],
            rent_log_channel: Optional[discord.TextChannel],
            eviction_channel: Optional[discord.TextChannel],
            *,
            dry_run: bool = False,
    ) -> tuple[int, int]:
        control = self.bot.get_cog('SystemControl')
        if control and not control.is_enabled('housing_rent'):
            log.append('⚠️ Housing rent system disabled.')
            return cash, bank
        housing_total = 0
        for role in roles:
            if "Housing Tier" in role:
                amount = ROLE_COSTS_HOUSING.get(role, 0)
                housing_total += amount
                log.append(f"🔎 Housing Role {role} → Rent: ${amount}")

        if housing_total == 0:
            return cash, bank

        total = (cash or 0) + (bank or 0)
        if total < housing_total:
            log.append(f"❌ Cannot pay housing rent of ${housing_total}. Would result in negative balance.")
            if eviction_channel:
                await eviction_channel.send(
                    f"🚨 <@{member.id}> — Housing Rent due: ${housing_total} — **FAILED** (insufficient funds) 🚨\n## You have **7 days** to pay or face eviction."
                )
            log.append(f"⚠️ Housing rent skipped for <@{member.id}> due to insufficient funds.")
            return cash, bank

        deduct_cash = min(cash, housing_total)
        deduct_bank = housing_total - deduct_cash
        payload: Dict[str, int] = {}
        if deduct_cash > 0:
            payload["cash"] = -deduct_cash
        if deduct_bank > 0:
            payload["bank"] = -deduct_bank

        success = True
        if not dry_run:
            success = await self.unbelievaboat.update_balance(
                member.id, payload, reason="Housing Rent"
            )
        if success:
            cash -= deduct_cash
            bank -= deduct_bank
            log.append(
                f"🧮 {'Would subtract' if dry_run else 'Subtracted'} housing rent ${housing_total} — ${deduct_cash} from cash, ${deduct_bank} from bank."
            )
            log.append(
                f"📈 Balance after housing rent — Cash: ${cash:,}, Bank: ${bank:,}, Total: {(cash or 0) + (bank or 0):,}"
            )
            log.append("✅ Housing Rent collection completed. Notice Sent to #rent")
            if rent_log_channel and not dry_run:
                await rent_log_channel.send(f"✅ <@{member.id}> — Housing Rent paid: ${housing_total}")
        else:
            log.append("❌ Failed to deduct housing rent despite having sufficient funds.")
        return cash, bank

    async def process_business_rent(
            self,
            member: discord.Member,
            roles: List[str],
            cash: int,
            bank: int,
            log: List[str],
            rent_log_channel: Optional[discord.TextChannel],
            eviction_channel: Optional[discord.TextChannel],
            *,
            dry_run: bool = False,
    ) -> tuple[int, int]:
        control = self.bot.get_cog('SystemControl')
        if control and not control.is_enabled('business_rent'):
            log.append('⚠️ Business rent system disabled.')
            return cash, bank
        business_total = 0
        for role in roles:
            if "Business Tier" in role:
                amount = ROLE_COSTS_BUSINESS.get(role, 0)
                business_total += amount
                log.append(f"🔎 Business Role {role} → Rent: ${amount}")

        if business_total == 0:
            return cash, bank

        total = (cash or 0) + (bank or 0)
        if total < business_total:
            log.append(f"❌ Cannot pay business rent of ${business_total}. Would result in negative balance.")
            if eviction_channel:
                await eviction_channel.send(
                    f"🚨 <@{member.id}> — Business Rent due: ${business_total} — **FAILED** (insufficient funds) 🚨\n## You have **7 days** to pay or face eviction."
                )
            log.append(f"⚠️ Business rent skipped for <@{member.id}> due to insufficient funds.")
            return cash, bank

        deduct_cash = min(cash, business_total)
        deduct_bank = business_total - deduct_cash
        payload: Dict[str, int] = {}
        if deduct_cash > 0:
            payload["cash"] = -deduct_cash
        if deduct_bank > 0:
            payload["bank"] = -deduct_bank

        success = True
        if not dry_run:
            success = await self.unbelievaboat.update_balance(
                member.id, payload, reason="Business Rent"
            )
        if success:
            cash -= deduct_cash
            bank -= deduct_bank
            log.append(
                f"🧮 {'Would subtract' if dry_run else 'Subtracted'} business rent ${business_total} — ${deduct_cash} from cash, ${deduct_bank} from bank."
            )
            log.append(
                f"📈 Balance after business rent — Cash: ${cash:,}, Bank: ${bank:,}, Total: {(cash or 0) + (bank or 0):,}"
            )
            log.append("✅ Business Rent collection completed. Notice Sent to #rent")
            if rent_log_channel and not dry_run:
                await rent_log_channel.send(f"✅ <@{member.id}> — Business Rent paid: ${business_total}")
        else:
            log.append("❌ Failed to deduct business rent despite having sufficient funds.")
        return cash, bank

    @commands.command(aliases=["collecthousing"])
    @commands.has_permissions(administrator=True)
    async def collect_housing(self, ctx, *args):
        """Manually collect housing rent from a single user"""
        converter = commands.MemberConverter()
        user = None
        verbose = False
        for arg in args:
            if arg.lower() in {"-v", "--verbose", "-verbose", "verbose"}:
                verbose = True
            elif user is None:
                try:
                    user = await converter.convert(ctx, arg)
                except commands.BadArgument:
                    continue
        if user is None:
            await ctx.send("❌ Could not resolve user.")
            return

        control = self.bot.get_cog('SystemControl')
        if control and not control.is_enabled('housing_rent'):
            await ctx.send('⚠️ The housing_rent system is currently disabled.')
            return
        admin_cog = self.bot.get_cog('Admin')
        log: List[str] = [f"🏠 Manual Housing Rent Collection for <@{user.id}>"]
        rent_log_channel = ctx.guild.get_channel(config.RENT_LOG_CHANNEL_ID)
        eviction_channel = ctx.guild.get_channel(config.EVICTION_CHANNEL_ID)
        await ctx.send(f"Working on <@{user.id}>")

        role_names = [r.name for r in user.roles]
        log.append(f"🧾 Roles: {role_names}")

        balance_data = await self.unbelievaboat.get_balance(user.id)
        if not balance_data:
            log.append("❌ Could not fetch balance.")
            await ctx.send(f"⚠️ Could not fetch balance for <@{user.id}>")
            if admin_cog:
                await admin_cog.log_audit(ctx.author, "\n".join(log))
            return

        cash = balance_data["cash"]
        bank = balance_data["bank"]
        start_cash = cash
        start_bank = bank
        total = (cash or 0) + (bank or 0)
        log.append(
            f"💵 Balance — Cash: ${cash:,}, Bank: ${bank:,}, Total: ${total:,}"
        )

        cash, bank = await self.process_housing_rent(user, role_names, cash, bank, log, rent_log_channel, eviction_channel)

        final = await self.unbelievaboat.get_balance(user.id)
        if final:
            final_cash = final.get("cash", 0)
            final_bank = final.get("bank", 0)
            final_total = final_cash + final_bank
        else:
            final_cash = cash
            final_bank = bank
            final_total = final_cash + final_bank
        log.append(
            f"📊 Final balance — Cash: ${final_cash:,}, Bank: ${final_bank:,}, Total: ${final_total:,}"
        )

        summary = "\n".join(log)
        if verbose:
            await ctx.send(summary)
        else:
            await ctx.send(
                f"✅ Completed for <@{user.id}>\n"
                f"Before: Cash ${start_cash:,}, Bank ${start_bank:,}\n"
                f"After: Cash ${final_cash:,}, Bank ${final_bank:,}"
            )
        if admin_cog:
            await admin_cog.log_audit(ctx.author, summary)

    @commands.command(aliases=["collectbusiness"])
    @commands.has_permissions(administrator=True)
    async def collect_business(self, ctx, *args):
        """Manually collect business rent from a single user"""
        converter = commands.MemberConverter()
        user = None
        verbose = False
        for arg in args:
            if arg.lower() in {"-v", "--verbose", "-verbose", "verbose"}:
                verbose = True
            elif user is None:
                try:
                    user = await converter.convert(ctx, arg)
                except commands.BadArgument:
                    continue
        if user is None:
            await ctx.send("❌ Could not resolve user.")
            return
        control = self.bot.get_cog('SystemControl')
        if control and not control.is_enabled('business_rent'):
            await ctx.send('⚠️ The business_rent system is currently disabled.')
            return
        admin_cog = self.bot.get_cog('Admin')
        log: List[str] = [f"🏢 Manual Business Rent Collection for <@{user.id}>"]
        rent_log_channel = ctx.guild.get_channel(config.RENT_LOG_CHANNEL_ID)
        eviction_channel = ctx.guild.get_channel(config.EVICTION_CHANNEL_ID)
        await ctx.send(f"Working on <@{user.id}>")

        role_names = [r.name for r in user.roles]
        log.append(f"🧾 Roles: {role_names}")

        balance_data = await self.unbelievaboat.get_balance(user.id)
        if not balance_data:
            log.append("❌ Could not fetch balance.")
            await ctx.send(f"⚠️ Could not fetch balance for <@{user.id}>")
            if admin_cog:
                await admin_cog.log_audit(ctx.author, "\n".join(log))
            return

        cash = balance_data["cash"]
        bank = balance_data["bank"]
        start_cash = cash
        start_bank = bank
        total = (cash or 0) + (bank or 0)
        log.append(
            f"💵 Balance — Cash: ${cash:,}, Bank: ${bank:,}, Total: ${total:,}"
        )

        cash, bank = await self.process_business_rent(user, role_names, cash, bank, log, rent_log_channel, eviction_channel)

        final = await self.unbelievaboat.get_balance(user.id)
        if final:
            final_cash = final.get("cash", 0)
            final_bank = final.get("bank", 0)
            final_total = final_cash + final_bank
        else:
            final_cash = cash
            final_bank = bank
            final_total = final_cash + final_bank
        log.append(
            f"📊 Final balance — Cash: ${final_cash:,}, Bank: ${final_bank:,}, Total: ${final_total:,}"
        )

        summary = "\n".join(log)
        if verbose:
            await ctx.send(summary)
        else:
            await ctx.send(
                f"✅ Completed for <@{user.id}>\n"
                f"Before: Cash ${start_cash:,}, Bank ${start_bank:,}\n"
                f"After: Cash ${final_cash:,}, Bank ${final_bank:,}"
            )
        if admin_cog:
            await admin_cog.log_audit(ctx.author, summary)

    @commands.command(aliases=["collecttrauma"])
    @commands.has_permissions(administrator=True)
    async def collect_trauma(self, ctx, *args):
        converter = commands.MemberConverter()
        user = None
        verbose = False
        for arg in args:
            if arg.lower() in {"-v", "--verbose", "-verbose", "verbose"}:
                verbose = True
            elif user is None:
                try:
                    user = await converter.convert(ctx, arg)
                except commands.BadArgument:
                    continue
        if user is None:
            await ctx.send("❌ Could not resolve user.")
            return
        """Manually collect Trauma Team subscription"""
        control = self.bot.get_cog('SystemControl')
        if control and not control.is_enabled('trauma_team'):
            await ctx.send('⚠️ The trauma_team system is currently disabled.')
            return
        admin_cog = self.bot.get_cog('Admin')
        log: List[str] = [f"💊 Manual Trauma Team Subscription Processing for <@{user.id}>"]
        balance_data = await self.unbelievaboat.get_balance(user.id)
        if not balance_data:
            log.append("❌ Could not fetch balance.")
            await ctx.send(f"⚠️ Could not fetch balance for <@{user.id}>")
            if admin_cog:
                await admin_cog.log_audit(ctx.author, "\n".join(log))
            return

        cash = balance_data["cash"]
        bank = balance_data["bank"]
        total = (cash or 0) + (bank or 0)
        log.append(f"💵 Balance — Cash: ${cash:,}, Bank: ${bank:,}, Total: ${total:,}")

        await ctx.send(f"Working on <@{user.id}>")
        await self.trauma_service.process_trauma_team_payment(user, log=log)

        final = await self.unbelievaboat.get_balance(user.id)
        if final:
            final_cash = final.get("cash", 0)
            final_bank = final.get("bank", 0)
            final_total = final_cash + final_bank
        else:
            final_cash = cash
            final_bank = bank
            final_total = final_cash + final_bank
        log.append(
            f"📊 Final balance — Cash: ${final_cash:,}, Bank: ${final_bank:,}, Total: ${final_total:,}"
        )

        summary = "\n".join(log)
        if verbose:
            await ctx.send(summary)
        else:
            await ctx.send(
                f"✅ Completed for <@{user.id}>\n"
                f"Before: Cash ${cash:,}, Bank ${bank:,}\n"
                f"After: Cash ${final_cash:,}, Bank ${final_bank:,}"
            )
        if admin_cog:
            await admin_cog.log_audit(ctx.author, summary)

    async def run_rent_collection(
        self,
        ctx,
        *,
        target_user: Optional[discord.Member] = None,
        dry_run: bool = False,
        verbose: bool = False,
    ):

        """Internal helper for rent collection and simulation.

        When ``verbose`` is ``False`` only minimal status messages are sent.
        """
        await ctx.send("🧪 Starting rent simulation..." if dry_run else "🚦 Starting rent collection...")

        audit_lines: List[str] = []
        if not target_user:
            if Path(config.OPEN_LOG_FILE).exists():
                business_open_log = await load_json_file(config.OPEN_LOG_FILE, default={})
                if not dry_run:
                    backup_base = f"open_history_{datetime.utcnow():%B_%Y}.json"
                    backup_path = Path(backup_base)
                    counter = 1
                    while backup_path.exists():
                        backup_path = Path(f"{backup_base}_{counter}")
                        counter += 1
                    Path(config.OPEN_LOG_FILE).rename(backup_path)
            else:
                business_open_log = {}

            if not dry_run:
                await save_json_file(config.OPEN_LOG_FILE, {})
        else:
            if Path(config.OPEN_LOG_FILE).exists():
                business_open_log = await load_json_file(config.OPEN_LOG_FILE, default={})
            else:
                business_open_log = {}

        if not target_user and Path(config.LAST_RENT_FILE).exists():
            try:
                data = await load_json_file(config.LAST_RENT_FILE, default=None)
                last_run = datetime.fromisoformat(data["last_run"])
            except Exception:
                last_run = None
            if last_run and datetime.utcnow() - last_run < timedelta(days=30):
                await ctx.send("⚠️ Rent already collected in the last 30 days.")
                return
        if not target_user and not dry_run:
            with open(config.LAST_RENT_FILE, "w") as f:
                json.dump({"last_run": datetime.utcnow().isoformat()}, f)

        members_to_process: List[discord.Member] = []
        for m in ctx.guild.members:
            if target_user and m.id == target_user.id:
                members_to_process = [m]
                break
            if not target_user and any("Tier" in r.name for r in m.roles):
                members_to_process.append(m)
        if not members_to_process:
            await ctx.send("❌ No matching members found.")
            return

        backup_dir = Path(config.BALANCE_BACKUP_DIR)
        backup_dir.mkdir(exist_ok=True)
        backup_file = backup_dir / f"balances_{datetime.utcnow():%Y%m%d_%H%M%S}.json"
        if not dry_run:
            await self.backup_balances(members_to_process, backup_file)

        eviction_channel = ctx.guild.get_channel(config.EVICTION_CHANNEL_ID)
        rent_log_channel = ctx.guild.get_channel(config.RENT_LOG_CHANNEL_ID)
        admin_cog = self.bot.get_cog('Admin')

        for member in members_to_process:
            try:
                log: List[str] = [f"🔍 **Working on:** <@{member.id}>"]
                if not verbose:
                    await ctx.send(f"Working on <@{member.id}>")

                role_names = [r.name for r in member.roles]
                app_roles = [r for r in role_names if "Tier" in r]
                log.append(f"🏷️ Detected roles: {', '.join(app_roles) or 'None'}")

                loa_role = member.guild.get_role(config.LOA_ROLE_ID)
                on_loa = loa_role in member.roles if loa_role else False
                if on_loa:
                    log.append("🏖️ Member is on LOA — skipping personal fees.")

                bal = await self.unbelievaboat.get_balance(member.id)
                if not bal:
                    log.append("⚠️ Could not fetch balance.")
                    summary = "\n".join(log)
                    if verbose:
                        await ctx.send(summary)
                    else:
                        await ctx.send(f"⚠️ Could not fetch balance for <@{member.id}>")
                    if dry_run and admin_cog:
                        await admin_cog.log_audit(ctx.author, summary)
                    continue
                cash, bank = bal["cash"], bal["bank"]
                log.append(f"💵 Starting balance — Cash: ${cash:,}, Bank: ${bank:,}, Total: {(cash or 0) + (bank or 0):,}")

                if dry_run:
                    check = await self.unbelievaboat.verify_balance_ops(member.id)
                    log.append("🔄 Balance check passed." if check else "⚠️ Balance update check failed.")

                if not on_loa:
                    base_ok, cash, bank = await self.deduct_flat_fee(member, cash, bank, log, BASELINE_LIVING_COST, dry_run=dry_run)
                    if not base_ok:
                        if eviction_channel:
                            if not dry_run:
                                await eviction_channel.send(
                                    f"⚠️ <@{member.id}> could not pay baseline living cost (${BASELINE_LIVING_COST})."
                                )
                        log.append("❌ Skipping remaining rent steps.")
                        summary = "\n".join(log)
                        if verbose:
                            await ctx.send(summary)
                        else:
                            await ctx.send(f"❌ Skipping remaining rent steps for <@{member.id}>")
                        if dry_run and admin_cog:
                            await admin_cog.log_audit(ctx.author, summary)
                        continue

                cash, bank = await self.process_housing_rent(member, app_roles, cash, bank, log, rent_log_channel, eviction_channel, dry_run=dry_run) if not on_loa else (cash, bank)
                cash, bank = await self.process_business_rent(member, app_roles, cash, bank, log, rent_log_channel, eviction_channel, dry_run=dry_run)

                if not on_loa:
                    await self.trauma_service.process_trauma_team_payment(member, log=log, dry_run=dry_run)

                if not dry_run:
                    final = await self.unbelievaboat.get_balance(member.id)
                    if final:
                        cash = final.get("cash", 0)
                        bank = final.get("bank", 0)

                log.append(
                    f"📊 {'Projected' if dry_run else 'Final'} balance — Cash: ${cash:,}, Bank: ${bank:,}, Total: {(cash or 0) + (bank or 0):,}"
                )

                summary = "\n".join(log)
                if verbose:
                    await ctx.send(summary)
                else:
                    await ctx.send(f"✅ Completed for <@{member.id}>")
                if dry_run and admin_cog:
                    await admin_cog.log_audit(ctx.author, summary)
                audit_lines.append(summary)

            except Exception as e:
                await ctx.send(f"❌ Error processing <@{member.id}>: `{e}`")
                if dry_run and admin_cog:
                    await admin_cog.log_audit(ctx.author, f"Error processing <@{member.id}>: {e}")
                audit_lines.append(f"Error processing <@{member.id}>: {e}")

        end_msg = "✅ Rent simulation completed." if dry_run else "✅ Rent collection completed."
        await ctx.send(end_msg)
        if dry_run and admin_cog:
            await admin_cog.log_audit(ctx.author, end_msg)
        if not dry_run:
            audit_lines.append(end_msg)
            audit_dir = Path(getattr(config, "RENT_AUDIT_DIR", "rent_audits"))
            audit_dir.mkdir(exist_ok=True)
            log_file = audit_dir / f"rent_audit_{datetime.utcnow():%B_%Y}.log"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write("\n".join(audit_lines) + "\n")

    @commands.command(aliases=["collectrent"])
    @commands.has_permissions(administrator=True)
    async def collect_rent(self, ctx, *args, target_user: Optional[discord.Member] = None):
        """Global or per-member rent collection.

        Pass ``-v``/``--verbose`` to include detailed output.
        """
        verbose = False
        if target_user is None:
            converter = commands.MemberConverter()
            remaining = []
            for arg in args:
                if arg.lower() in {"-v", "--verbose", "-verbose", "verbose"}:
                    verbose = True
                else:
                    remaining.append(arg)
            for arg in remaining:
                try:
                    target_user = await converter.convert(ctx, arg)
                    break
                except commands.BadArgument:
                    continue
        else:
            for arg in args:
                if arg.lower() in {"-v", "--verbose", "-verbose", "verbose"}:
                    verbose = True
                    break
        await self.run_rent_collection(ctx, target_user=target_user, dry_run=False, verbose=verbose)

    @commands.command(aliases=["simulaterent"])
    @commands.has_permissions(administrator=True)
    async def simulate_rent(self, ctx, *args, target_user: Optional[discord.Member] = None):
        """Simulate rent collection without applying changes.

        Pass ``-v``/``--verbose`` to include detailed output.
        """
        verbose = False
        if target_user is None:
            converter = commands.MemberConverter()
            remaining = []
            for arg in args:
                if arg.lower() in {"-v", "--verbose", "-verbose", "verbose"}:
                    verbose = True
                else:
                    remaining.append(arg)
            for arg in remaining:
                try:
                    target_user = await converter.convert(ctx, arg)
                    break
                except commands.BadArgument:
                    continue
        else:
            for arg in args:
                if arg.lower() in {"-v", "--verbose", "-verbose", "verbose"}:
                    verbose = True
                    break
        await self.run_rent_collection(ctx, target_user=target_user, dry_run=True, verbose=verbose)


