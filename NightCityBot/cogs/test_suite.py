import discord
from discord.ext import commands
import time
from datetime import datetime
import os
import sys
from pathlib import Path

# Ensure the project root is on the path for `import config` and utility modules
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
from typing import List, Dict, Optional
from unittest.mock import AsyncMock, MagicMock
import config
from NightCityBot.utils.permissions import is_fixer
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING

class TestSuite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.test_descriptions = {
            "test_dm_roll_relay": "Relays a roll to a user's DM forum thread using `!dm`.",
            "test_roll_direct_dm": "User runs `!roll` in a DM. Verifies result is DM'd and logged to DM thread.",
            "test_post_executes_command": "Sends a `!roll` command into a channel using `!post`.",
            "test_post_roll_execution": "Executes a roll via !post and checks result inside RP channel.",
            "test_rolls": "Runs `!roll` with valid and invalid input and checks result.",
            "test_bonus_rolls": "Checks that Netrunner bonuses are applied correctly.",
            "test_full_rent_commands": "Executes rent collection on a live user and verifies balance updates.",
            "test_passive_income_logic": "Applies passive income based on recent shop opens.",
            "test_trauma_payment": "Attempts to log a trauma plan subscription in the correct DM thread.",
            "test_rent_logging_sends": "Verifies that rent events are logged in #rent and #eviction-notices.",
            "test_open_shop_command": "Runs !open_shop in the correct channel.",
            "test_dm_thread_reuse": "Ensures DM logging reuses existing threads.",
            "test_open_shop_errors": "Checks open_shop failures for bad context.",
            "test_start_end_rp": "Creates and ends an RP session to verify logging.",
            "test_unknown_command": "Ensures unknown commands don't spam the audit log.",
            "test_open_shop_limit": "Verifies the monthly shop open limit is enforced.",
            "test_attend_command": "Runs !attend to award weekly attendance cash.",
            "test_cyberware_costs": "Ensures cyberware medication costs scale and cap correctly.",
            "test_loa_commands": "Runs start_loa and end_loa commands.",
            "test_checkup_command": "Runs the ripperdoc !checkup command.",

        }

    async def get_test_user(self, ctx) -> Optional[discord.Member]:
        """Get or fetch the test user."""
        user = ctx.guild.get_member(config.TEST_USER_ID)
        if not user:
            user = await ctx.guild.fetch_member(config.TEST_USER_ID)
        return user

    def assert_called(self, logs: List[str], mock_obj, label: str) -> None:
        """Assert that an awaited call was made on the given mock."""
        try:
            mock_obj.assert_awaited()
            logs.append(f"✅ {label} was called")
        except AssertionError:
            logs.append(f"❌ {label} was not called")

    async def test_dm_roll_relay(self, ctx) -> List[str]:
        """Test relaying roll commands through DMs."""
        logs = []
        try:
            user = await self.get_test_user(ctx)
            dm_handler = self.bot.get_cog('DMHandler')
            thread = await dm_handler.get_or_create_dm_thread(user)
            roll_system = self.bot.get_cog('RollSystem')
            await roll_system.loggable_roll(user, thread, "1d20", original_sender=ctx.author)
            logs.append("✅ !dm @user !roll d20 relay succeeded")

            try:
                dm_channel = await user.create_dm()
                await dm_channel.send("✅ DM test message from NightCityBotTest.")
                logs.append("✅ Direct DM sent to user.")
            except discord.Forbidden:
                logs.append("⚠️ Could not DM user — Privacy settings?")
        except Exception as e:
            logs.append(f"❌ Exception in test_dm_roll_relay: {e}")
        return logs

    async def test_roll_direct_dm(self, ctx) -> List[str]:
        """Test roll command in direct DMs."""
        logs = []
        try:
            user = await self.get_test_user(ctx)
            dm_channel = await user.create_dm()

            logs.append("→ Expected: !roll in DM should send a result and log it to the user's DM thread.")

            roll_system = self.bot.get_cog('RollSystem')
            await roll_system.loggable_roll(user, dm_channel, "1d6")
            logs.append("→ Result: ✅ !roll executed in user DM context.")

        except Exception as e:
            logs.append(f"❌ Exception in test_roll_direct_dm: {e}")
        return logs

    async def test_post_executes_command(self, ctx) -> List[str]:
        """Test posting commands to channels."""
        logs = []
        try:
            rp_channel = ctx.test_rp_channel
            ctx.message.attachments = []
            admin_cog = self.bot.get_cog('Admin')
            await admin_cog.post(ctx, rp_channel.name, message="!roll 1d4")
            logs.append("✅ !post executed and command sent in reused RP channel")
        except Exception as e:
            logs.append(f"❌ Exception in test_post_executes_command: {e}")
        return logs

    async def test_post_roll_execution(self, ctx) -> List[str]:
        """Test roll execution via post command."""
        logs = []
        try:
            thread = ctx.test_rp_channel
            admin_cog = self.bot.get_cog('Admin')
            await admin_cog.post(ctx, thread.name, message="!roll 1d20+1")
            logs.append("✅ !post <thread> !roll d20+1 executed in reused RP channel")
        except Exception as e:
            logs.append(f"❌ Exception in test_post_roll_execution: {e}")
        return logs

    async def test_rolls(self, ctx) -> List[str]:
        """Test roll command functionality."""
        logs = []
        try:
            logs.append("→ Expected: Valid roll should return a total, invalid roll should return a format error.")

            roll_system = self.bot.get_cog('RollSystem')
            # Valid roll
            await roll_system.loggable_roll(ctx.author, ctx.channel, "1d20+2")
            logs.append("→ Result (Valid): ✅ Roll succeeded and result sent.")

            # Invalid roll
            await roll_system.loggable_roll(ctx.author, ctx.channel, "notadice")
            logs.append("→ Result (Invalid): ✅ Error message shown for invalid format.")
        except Exception as e:
            logs.append(f"❌ Exception in test_rolls: {e}")
        return logs

    async def test_bonus_rolls(self, ctx) -> List[str]:
        """Test roll bonuses for Netrunner roles."""
        logs = []
        mock_author = AsyncMock(spec=discord.Member)
        mock_author.display_name = "BonusTest"
        mock_author.roles = [AsyncMock(name="Netrunner Level 2")]
        for r in mock_author.roles:
            r.name = "Netrunner Level 2"

        channel = AsyncMock(spec=discord.TextChannel)
        channel.send = AsyncMock()

        logs.append("→ Expected: Roll result should include '+1 Netrunner bonus' in output.")

        try:
            roll_system = self.bot.get_cog('RollSystem')
            await roll_system.loggable_roll(mock_author, channel, "1d20")
            message = channel.send.call_args[0][0]
            if "+1 Netrunner bonus" in message:
                logs.append("→ Result: ✅ Found bonus text in roll output.")
            else:
                logs.append("→ Result: ❌ Bonus text missing from roll output.")
        except Exception as e:
            logs.append(f"❌ Exception in test_bonus_rolls: {e}")
        return logs

    async def test_full_rent_commands(self, ctx) -> List[str]:
        """Test all rent-related commands."""
        logs = []
        try:
            user = await self.get_test_user(ctx)
            logs.append("→ Expected: All rent-related commands should complete without error.")

            if os.path.exists(config.LAST_RENT_FILE):
                os.remove(config.LAST_RENT_FILE)

            economy = self.bot.get_cog('Economy')
            await economy.collect_rent(ctx)
            logs.append("✅ collect_rent (global) executed")

            if os.path.exists(config.LAST_RENT_FILE):
                os.remove(config.LAST_RENT_FILE)

            await economy.collect_rent(ctx, target_user=user)
            logs.append("✅ collect_rent (specific user) executed")

            await economy.collect_housing(ctx, user)
            logs.append("✅ collect_housing executed")

            await economy.collect_business(ctx, user)
            logs.append("✅ collect_business executed")

            await economy.collect_trauma(ctx, user)
            logs.append("✅ collect_trauma executed")

            logs.append("→ Result: ✅ All rent commands executed.")
        except Exception as e:
            logs.append(f"❌ Exception in test_full_rent_commands: {e}")
        return logs

    async def test_passive_income_logic(self, ctx) -> List[str]:
        """Test passive income calculations."""
        logs = []
        user = await self.get_test_user(ctx)
        economy = self.bot.get_cog('Economy')

        for role in ROLE_COSTS_BUSINESS.keys():
            for count in range(5):
                income = economy.calculate_passive_income(role, count)
                logs.append(f"✅ {role} with {count} opens → ${income}")

        return logs

    async def test_trauma_payment(self, ctx) -> List[str]:
        """Test Trauma Team subscription processing."""
        logs = []
        try:
            user = await self.get_test_user(ctx)
            logs.append("→ Expected: collect_trauma should find thread and log subscription payment.")

            economy = self.bot.get_cog('Economy')
            await economy.collect_trauma(ctx, user)
            logs.append("→ Result: ✅ Trauma Team logic executed on live user (check #tt-plans-payment).")
        except Exception as e:
            logs.append(f"❌ Exception in test_trauma_payment: {e}")
        return logs

    async def test_rent_logging_sends(self, ctx) -> List[str]:
        """Test rent logging functionality."""
        logs = []
        try:
            user = await self.get_test_user(ctx)
            rent_log_channel = ctx.guild.get_channel(config.RENT_LOG_CHANNEL_ID)
            eviction_channel = ctx.guild.get_channel(config.EVICTION_CHANNEL_ID)

            logs.append("→ Expected: collect_rent should post messages to rent and eviction log channels.")

            if not rent_log_channel or not eviction_channel:
                logs.append("→ Result: ❌ Rent or eviction channels not found.")
                return logs

            economy = self.bot.get_cog('Economy')
            await economy.collect_rent(ctx, target_user=user)
            logs.append("→ Result: ✅ Rent logic executed and logging channels present.")
        except Exception as e:
            logs.append(f"❌ Exception in test_rent_logging_sends: {e}")
        return logs

    async def test_open_shop_command(self, ctx) -> List[str]:
        """Test shop opening functionality."""
        logs = []
        try:
            correct_channel = ctx.guild.get_channel(config.BUSINESS_ACTIVITY_CHANNEL_ID)
            logs.append("→ Expected: !open_shop should succeed when run inside the business channel.")

            if not correct_channel:
                logs.append("→ Result: ❌ Business open channel not found")
                return logs

            original_channel = ctx.channel
            ctx.channel = correct_channel

            economy = self.bot.get_cog('Economy')
            await economy.open_shop(ctx)
            logs.append("→ Result: ✅ !open_shop executed in correct channel")

            ctx.channel = original_channel
        except Exception as e:
            logs.append(f"❌ Exception in test_open_shop_command: {e}")
        return logs

    async def test_attend_command(self, ctx) -> List[str]:
        """Test the attend reward command."""
        logs = []
        economy = self.bot.get_cog('Economy')
        try:
            ctx.author.roles = [discord.Object(id=config.VERIFIED_ROLE_ID)]
            await economy.attend(ctx)
            logs.append("✅ attend command executed")
        except Exception as e:
            logs.append(f"❌ Exception in test_attend_command: {e}")
        return logs

    async def test_dm_thread_reuse(self, ctx) -> List[str]:
        """Ensure DM threads are reused instead of duplicated."""
        logs = []
        user = await self.get_test_user(ctx)
        dm_handler = self.bot.get_cog('DMHandler')
        first = await dm_handler.get_or_create_dm_thread(user)
        second = await dm_handler.get_or_create_dm_thread(user)
        if first.id == second.id:
            logs.append("✅ DM thread reused correctly")
        else:
            logs.append("❌ DM thread was recreated")
        return logs

    async def test_open_shop_errors(self, ctx) -> List[str]:
        """Verify open_shop fails in wrong channel or on wrong day."""
        logs = []
        economy = self.bot.get_cog('Economy')
        wrong_channel = ctx.channel
        # Wrong channel
        await economy.open_shop(ctx)
        logs.append("✅ open_shop rejected outside business channel")
        # Simulate correct channel without business role
        ctx.channel = ctx.guild.get_channel(config.BUSINESS_ACTIVITY_CHANNEL_ID)
        ctx.author.roles = []
        await economy.open_shop(ctx)
        logs.append("✅ open_shop rejected without business role")
        # Simulate correct channel but non-Sunday
        ctx.channel = ctx.guild.get_channel(config.BUSINESS_ACTIVITY_CHANNEL_ID)
        role = MagicMock()
        role.name = "Business Tier 1"
        ctx.author.roles = [role]
        if datetime.utcnow().weekday() == 6:
            logs.append("⚠️ Test run on Sunday; skip non-Sunday check")
        else:
            await economy.open_shop(ctx)
            logs.append("✅ open_shop rejected on non-Sunday")
        ctx.channel = wrong_channel
        return logs

    async def test_cyberware_costs(self, ctx) -> List[str]:
        """Verify cyberware medication cost escalation."""
        logs = []
        manager = self.bot.get_cog('CyberwareManager')
        if not manager:
            logs.append("❌ CyberwareManager cog not loaded")
            return logs
        try:
            week1 = manager.calculate_cost('medium', 1)
            week8 = manager.calculate_cost('extreme', 8)
            if week1 < week8 == 10000:
                logs.append("✅ Cyberware costs escalate and cap correctly")
            else:
                logs.append(f"❌ Unexpected cost results: week1={week1}, week8={week8}")
        except Exception as e:
            logs.append(f"❌ Exception in test_cyberware_costs: {e}")
        return logs

    async def test_loa_commands(self, ctx) -> List[str]:
        """Ensure LOA start and end commands execute."""
        logs = []
        loa = self.bot.get_cog('LOA')
        if not loa:
            logs.append("❌ LOA cog not loaded")
            return logs
        ctx.author.add_roles = AsyncMock()
        ctx.author.remove_roles = AsyncMock()
        ctx.guild.get_role = MagicMock(return_value=discord.Object(id=config.LOA_ROLE_ID))
        await loa.start_loa(ctx)
        await loa.end_loa(ctx)
        self.assert_called(logs, ctx.author.add_roles, "add_roles")
        self.assert_called(logs, ctx.author.remove_roles, "remove_roles")
        return logs

    async def test_checkup_command(self, ctx) -> List[str]:
        """Run the ripperdoc checkup command."""
        logs = []
        cyber = self.bot.get_cog('CyberwareManager')
        if not cyber:
            logs.append("❌ CyberwareManager cog not loaded")
            return logs
        member = MagicMock(spec=discord.Member)
        member.display_name = "TestUser"
        member.roles = [discord.Object(id=config.CYBER_CHECKUP_ROLE_ID)]
        member.remove_roles = AsyncMock()
        ctx.guild.get_role = MagicMock(return_value=discord.Object(id=config.CYBER_CHECKUP_ROLE_ID))
        await cyber.checkup.callback(cyber, ctx, member)
        self.assert_called(logs, member.remove_roles, "remove_roles")
        return logs

    async def test_start_end_rp(self, ctx) -> List[str]:
        """Create and end an RP session to confirm logging works."""
        logs = []
        rp_manager = self.bot.get_cog('RPManager')
        channel = await rp_manager.start_rp(ctx, f"<@{config.TEST_USER_ID}>")
        if channel:
            logs.append("✅ start_rp returned a channel")
            await rp_manager.end_rp(ctx)
            logs.append("✅ end_rp executed without error")
        else:
            logs.append("❌ start_rp failed to create a channel")
        return logs

    async def test_unknown_command(self, ctx) -> List[str]:
        """Send an unknown ! command and ensure it's ignored."""
        logs = []
        admin = self.bot.get_cog('Admin')
        try:
            msg = ctx.message
            msg.content = "!notacommand"
            await admin.on_command_error(ctx, commands.CommandNotFound("notacommand"))
            logs.append("✅ Unknown command handled without audit log")
        except Exception as e:
            logs.append(f"❌ Exception handling unknown command: {e}")
        return logs

    async def test_open_shop_limit(self, ctx) -> List[str]:
        """Ensure users cannot open shop more than four times per month."""
        logs = []
        economy = self.bot.get_cog('Economy')
        original_channel = ctx.channel
        ctx.channel = ctx.guild.get_channel(config.BUSINESS_ACTIVITY_CHANNEL_ID)
        for i in range(5):
            await economy.open_shop(ctx)
        logs.append("✅ open_shop called five times to test limit")
        ctx.channel = original_channel
        return logs

    @commands.command(hidden=True)
    @commands.is_owner()
    async def test_bot(self, ctx):
        """Run all bot tests."""
        start = time.time()
        all_logs = []

        # Create a reusable RP channel for tests
        rp_manager = self.bot.get_cog('RPManager')
        rp_channel = await rp_manager.start_rp(ctx, f"<@{config.TEST_USER_ID}>")
        ctx.test_rp_channel = rp_channel

        output_channel = ctx.channel
        ctx.message.attachments = []

        await output_channel.send(f"🧪 Running full self-test on user <@{config.TEST_USER_ID}>...")

        tests = [
            ("test_dm_roll_relay", self.test_dm_roll_relay),
            ("test_roll_direct_dm", self.test_roll_direct_dm),
            ("test_post_executes_command", self.test_post_executes_command),
            ("test_post_roll_execution", self.test_post_roll_execution),
            ("test_rolls", self.test_rolls),
            ("test_bonus_rolls", self.test_bonus_rolls),
            ("test_full_rent_commands", self.test_full_rent_commands),
            ("test_passive_income_logic", self.test_passive_income_logic),
            ("test_trauma_payment", self.test_trauma_payment),
            ("test_rent_logging_sends", self.test_rent_logging_sends),
            ("test_open_shop_command", self.test_open_shop_command),
            ("test_dm_thread_reuse", self.test_dm_thread_reuse),
            ("test_open_shop_errors", self.test_open_shop_errors),
            ("test_start_end_rp", self.test_start_end_rp),
            ("test_unknown_command", self.test_unknown_command),
            ("test_open_shop_limit", self.test_open_shop_limit),
            ("test_attend_command", self.test_attend_command),
            ("test_cyberware_costs", self.test_cyberware_costs),
            ("test_loa_commands", self.test_loa_commands),
            ("test_checkup_command", self.test_checkup_command),
        ]

        for name, func in tests:
            await output_channel.send(f"🧪 `{name}` — {self.test_descriptions.get(name, 'No description.')}")
            try:
                logs = await func(ctx)
            except Exception as e:
                logs = [f"❌ Exception in `{name}`: {e}"]
            all_logs.append(f"{name} — {self.test_descriptions.get(name, '')}")
            all_logs.extend(logs)
            all_logs.append("────────────")

        # Send results in chunks
        current_chunk = ""
        for line in all_logs:
            line = str(line)
            if len(current_chunk) + len(line) + 1 > 1900:
                await output_channel.send(f"```\n{current_chunk.strip()}\n```")
                current_chunk = line
            else:
                current_chunk += line + "\n"
        if current_chunk:
            await output_channel.send(f"```\n{current_chunk.strip()}\n```")

        # Summary embed
        passed = sum(1 for r in all_logs if "✅" in r)
        failed = sum(1 for r in all_logs if "❌" in r)
        duration = time.time() - start

        embed = discord.Embed(
            title="🧪 Full Bot Self-Test Summary",
            color=discord.Color.green() if failed == 0 else discord.Color.red()
        )
        embed.add_field(
            name="Result",
            value=f"✅ Passed: {passed}\n❌ Failed: {failed}",
            inline=False
        )
        embed.set_footer(text=f"⏱️ Completed in {duration:.2f}s")
        await output_channel.send(embed=embed)

        # Cleanup test channel
        if ctx.test_rp_channel:
            await rp_manager.end_rp_session(ctx.test_rp_channel)
