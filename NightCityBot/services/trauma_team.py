from typing import Optional, List
import discord
from NightCityBot.utils.constants import TRAUMA_ROLE_COSTS
import config


class TraumaTeamService:
    def __init__(self, bot):
        self.bot = bot

    async def process_trauma_team_payment(
            self,
            member: discord.Member,
            *,
            log: Optional[List[str]] = None,
            dry_run: bool = False,
    ) -> None:
        """Process Trauma Team subscription payment for a member."""
        control = self.bot.get_cog('SystemControl')
        if control and not control.is_enabled('trauma_team'):
            if log is not None:
                log.append('⚠️ Trauma Team system disabled.')
            return
        if any(r.id == config.LOA_ROLE_ID for r in member.roles):
            if log is not None:
                log.append("🛑 Skipping Trauma payment due to LOA.")
            return
        trauma_channel = self.bot.get_channel(config.TRAUMA_FORUM_CHANNEL_ID)
        if not isinstance(trauma_channel, discord.ForumChannel):
            if log is not None:
                log.append("⚠️ TT forum channel not found.")
            return

        balance = await self.bot.get_cog('Economy').unbelievaboat.get_balance(member.id)
        if not balance:
            if log is not None:
                log.append("⚠️ Could not fetch balance for Trauma processing.")
            return

        cash = balance["cash"]
        bank = balance["bank"]

        trauma_role = next(
            (r for r in member.roles if r.name in TRAUMA_ROLE_COSTS),
            None
                )
        if not trauma_role:
            return  # no subscription

        cost = TRAUMA_ROLE_COSTS[trauma_role.name]
        if log is not None:
            log.append(f"🔎 {trauma_role.name} → Subscription: ${cost}")
            log.append(f"💊 Deducting ${cost} for Trauma Team plan: {trauma_role.name}")

        # Find user's trauma thread
        thread_name_suffix = f"- {member.id}"
        target_thread = next(
            (t for t in trauma_channel.threads if t.name.endswith(thread_name_suffix)),
            None
        )
        if not target_thread:
            if log is not None:
                log.append(f"⚠️ Could not locate Trauma Team thread for <@{member.id}>")
            return

        if cash + bank < cost:
            mention = f"<@&{config.TRAUMA_TEAM_ROLE_ID}>"
            if not dry_run:
                await target_thread.send(
                    f"❌ Payment for **{trauma_role.name}** (${cost}) by <@{member.id}> failed."
                    f"\n## {mention} Subscription suspended."
                )
            if log is not None:
                log.append("❌ Insufficient funds for Trauma payment.")
            return

        payload = {
            "cash": -min(cash, cost),
            "bank": -(cost - min(cash, cost)),
        }
        economy = self.bot.get_cog("Economy")
        success = True
        if not dry_run and economy:
            await economy.backup_balances([member], label="cyberware_before")
            success = await economy.unbelievaboat.update_balance(
                member.id,
                payload,
                reason="Trauma Team Subscription"
            )
            if success:
                await economy.backup_balances([member], label="cyberware_after")

        if success:
            if not dry_run:
                await target_thread.send(
                    f"✅ **Payment Successful** — <@{member.id}> paid `${cost}` for **{trauma_role.name}** coverage."
                )
            if log is not None:
                log.append(
                    "✅ Trauma Team payment completed." if not dry_run else "✅ (Simulated) Trauma Team payment would succeed."
                )
        else:
            if not dry_run:
                await target_thread.send(
                    f"⚠️ **Deduction failed** for <@{member.id}> despite available funds."
                )
            if log is not None:
                log.append("⚠️ PATCH failed for Trauma Team payment.")
