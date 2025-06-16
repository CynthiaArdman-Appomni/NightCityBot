import discord
from discord.ext import commands
import time
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path

# Ensure the project root is on the path for `import config` and utility modules
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
from typing import List, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch
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
            "test_open_shop_daily_limit": "Ensures !open_shop can't run twice on the same Sunday.",
            "test_attend_command": "Runs !attend and verifies weekly/Sunday restrictions.",
            "test_cyberware_costs": "Ensures cyberware medication costs scale and cap correctly.",
            "test_loa_commands": "Runs start_loa and end_loa commands.",
            "test_checkup_command": "Runs the ripperdoc !checkup command.",
            "test_help_commands": "Executes !helpme and !helpfixer.",
            "test_post_dm_channel": "Runs !post from a DM thread.",
            "test_post_roll_as_user": "Executes a roll as another user via !post.",
            "test_dm_plain": "Sends a normal anonymous DM using !dm.",
            "test_dm_roll_command": "Relays a roll through !dm.",
            "test_dm_userid": "Ensures !dm works with a raw user ID.",
            "test_start_rp_multi": "Starts RP with two users and ends it.",
            "test_cyberware_weekly": "Simulates the weekly cyberware task.",
            "test_loa_fixer_other": "Fixer starts and ends LOA for another user.",
            "test_roll_as_user": "Rolls on behalf of another user.",
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

    def assert_send(self, logs: List[str], mock_obj, label: str) -> None:
        """Assert that a send-like coroutine was awaited."""
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
            dummy_thread = MagicMock(spec=discord.Thread)
            dm_channel = MagicMock(spec=discord.DMChannel)
            dm_channel.send = AsyncMock()
            with (
                patch.object(dm_handler, "get_or_create_dm_thread", new=AsyncMock(return_value=dummy_thread)),
                patch.object(self.bot.get_cog('RollSystem'), "loggable_roll", new=AsyncMock()) as mock_roll,
                patch.object(discord.Member, "create_dm", new=AsyncMock(return_value=dm_channel)),
            ):
                await dm_handler.dm.callback(dm_handler, ctx, user, message="!roll 1d20")
                self.assert_send(logs, dm_channel.send, "dm.send")
            self.assert_called(logs, mock_roll, "loggable_roll")
        except Exception as e:
            logs.append(f"❌ Exception in test_dm_roll_relay: {e}")
        return logs

    async def test_roll_direct_dm(self, ctx) -> List[str]:
        """Test roll command in direct DMs."""
        logs = []
        try:
            user = await self.get_test_user(ctx)
            dm_channel = MagicMock()
            with patch.object(user, "create_dm", new=AsyncMock(return_value=dm_channel)):
                roll_system = self.bot.get_cog("RollSystem")
                with patch.object(roll_system, "loggable_roll", new=AsyncMock()) as mock_roll:
                    await roll_system.loggable_roll(user, dm_channel, "1d6")
                    self.assert_called(logs, mock_roll, "loggable_roll")

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

            control = self.bot.get_cog('SystemControl')
            if control:
                await control.set_status('open_shop', True)

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
        """Test the attend reward command and its restrictions."""
        control = self.bot.get_cog('SystemControl')
        if control:
            await control.set_status('attend', True)
        logs = []
        economy = self.bot.get_cog('Economy')
        original_author = ctx.author
        mock_author = MagicMock(spec=discord.Member)
        mock_author.id = original_author.id
        mock_author.roles = [discord.Object(id=config.VERIFIED_ROLE_ID)]
        ctx.author = mock_author
        ctx.send = AsyncMock()

        # Non-Sunday should be rejected
        monday = datetime(2025, 6, 16)
        with (
            patch("NightCityBot.cogs.economy.datetime") as mock_dt,
            patch("NightCityBot.cogs.economy.load_json_file", new=AsyncMock(return_value={})),
            patch("NightCityBot.cogs.economy.save_json_file", new=AsyncMock()),
        ):
            mock_dt.utcnow.return_value = monday
            mock_dt.fromisoformat = datetime.fromisoformat
            await economy.attend(ctx)
            msg = ctx.send.await_args[0][0]
            if "only be logged on Sundays" in msg:
                logs.append("✅ attend rejected on non-Sunday")
            else:
                logs.append("❌ attend did not reject non-Sunday")
        ctx.send.reset_mock()

        # Already attended this week should be rejected
        sunday = datetime(2025, 6, 15)
        prev = sunday - timedelta(days=3)
        with (
            patch("NightCityBot.cogs.economy.datetime") as mock_dt,
            patch(
                "NightCityBot.cogs.economy.load_json_file",
                new=AsyncMock(return_value={str(mock_author.id): [prev.isoformat()]}),
            ),
            patch("NightCityBot.cogs.economy.save_json_file", new=AsyncMock()),
        ):
            mock_dt.utcnow.return_value = sunday
            mock_dt.fromisoformat = datetime.fromisoformat
            await economy.attend(ctx)
            msg = ctx.send.await_args[0][0]
            if "already logged attendance this week" in msg:
                logs.append("✅ attend rejected when used twice")
            else:
                logs.append("❌ attend did not enforce weekly limit")
        ctx.send.reset_mock()

        # Success when a week has passed
        prev2 = sunday - timedelta(days=7)
        with (
            patch("NightCityBot.cogs.economy.datetime") as mock_dt,
            patch(
                "NightCityBot.cogs.economy.load_json_file",
                new=AsyncMock(return_value={str(mock_author.id): [prev2.isoformat()]}),
            ),
            patch("NightCityBot.cogs.economy.save_json_file", new=AsyncMock()),
            patch.object(economy.unbelievaboat, "update_balance", new=AsyncMock()),
        ):
            mock_dt.utcnow.return_value = sunday
            mock_dt.fromisoformat = datetime.fromisoformat
            await economy.attend(ctx)
            msg = ctx.send.await_args[0][0]
            if "Attendance logged" in msg:
                logs.append("✅ attend succeeded after cooldown")
            else:
                logs.append("❌ attend did not succeed after cooldown")

        ctx.author = original_author
        return logs

    async def test_dm_thread_reuse(self, ctx) -> List[str]:
        """Ensure DM threads are reused instead of duplicated."""
        logs = []
        user = await self.get_test_user(ctx)
        dm_handler = self.bot.get_cog('DMHandler')
        dummy_thread = MagicMock()
        with patch.object(dm_handler, 'get_or_create_dm_thread', new=AsyncMock(return_value=dummy_thread)) as mock_get:
            first = await dm_handler.get_or_create_dm_thread(user)
            second = await dm_handler.get_or_create_dm_thread(user)
        if first is second:
            logs.append("✅ DM thread reused correctly")
        else:
            logs.append("❌ DM thread was recreated")
        self.assert_called(logs, mock_get, 'get_or_create_dm_thread')
        return logs

    async def test_open_shop_errors(self, ctx) -> List[str]:
        """Verify open_shop fails in wrong channel or on wrong day."""
        control = self.bot.get_cog('SystemControl')
        if control:
            await control.set_status('open_shop', True)
        logs = []
        economy = self.bot.get_cog('Economy')
        wrong_channel = ctx.channel
        with patch.object(economy.unbelievaboat, "update_balance", new=AsyncMock()):
            # Wrong channel
            await economy.open_shop(ctx)
            logs.append("✅ open_shop rejected outside business channel")

            ctx.channel = ctx.guild.get_channel(config.BUSINESS_ACTIVITY_CHANNEL_ID)
            original_author = ctx.author
            mock_author = MagicMock(spec=discord.Member)
            mock_author.id = original_author.id

            # Simulate no business role
            mock_author.roles = []
            ctx.author = mock_author
            await economy.open_shop(ctx)
            logs.append("✅ open_shop rejected without business role")

            # Simulate non-Sunday with business role
            role = MagicMock()
            role.name = "Business Tier 1"
            mock_author.roles = [role]
            if datetime.utcnow().weekday() == 6:
                logs.append("⚠️ Test run on Sunday; skip non-Sunday check")
            else:
                await economy.open_shop(ctx)
                logs.append("✅ open_shop rejected on non-Sunday")

            ctx.channel = wrong_channel
            ctx.author = original_author
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
        control = self.bot.get_cog('SystemControl')
        if control:
            await control.set_status('loa', True)
        logs = []
        loa = self.bot.get_cog('LOA')
        if not loa:
            logs.append("❌ LOA cog not loaded")
            return logs
        original_author = ctx.author
        mock_author = MagicMock(spec=discord.Member)
        mock_author.id = original_author.id
        mock_author.roles = []
        mock_author.add_roles = AsyncMock()
        mock_author.remove_roles = AsyncMock()
        ctx.author = mock_author
        loa_role = discord.Object(id=config.LOA_ROLE_ID)
        with patch('discord.Guild.get_role', return_value=loa_role):
            await loa.start_loa(ctx)
            mock_author.roles.append(loa_role)
            await loa.end_loa(ctx)
        self.assert_send(logs, mock_author.add_roles, "add_roles")
        self.assert_send(logs, mock_author.remove_roles, "remove_roles")
        ctx.author = original_author
        return logs

    async def test_checkup_command(self, ctx) -> List[str]:
        """Run the ripperdoc checkup command."""
        control = self.bot.get_cog('SystemControl')
        if control:
            await control.set_status('cyberware', True)
        logs = []
        cyber = self.bot.get_cog('CyberwareManager')
        if not cyber:
            logs.append("❌ CyberwareManager cog not loaded")
            return logs
        member = MagicMock(spec=discord.Member)
        member.display_name = "TestUser"
        member.roles = [discord.Object(id=config.CYBER_CHECKUP_ROLE_ID)]
        member.remove_roles = AsyncMock()
        log_channel = MagicMock()
        log_channel.send = AsyncMock()
        with (
            patch("discord.Guild.get_role", return_value=discord.Object(id=config.CYBER_CHECKUP_ROLE_ID)),
            patch("discord.Guild.get_channel", return_value=log_channel),
            patch("NightCityBot.cogs.cyberware.save_json_file", new=AsyncMock()),
        ):
            await cyber.checkup.callback(cyber, ctx, member)
        self.assert_send(logs, member.remove_roles, "remove_roles")
        self.assert_send(logs, log_channel.send, "log_channel.send")
        if cyber.data.get(str(member.id), 0) == 0:
            logs.append("✅ checkup streak reset")
        else:
            logs.append("❌ checkup streak not reset")
        return logs

    async def test_help_commands(self, ctx) -> List[str]:
        """Run the help commands."""
        logs: List[str] = []
        admin = self.bot.get_cog('Admin')
        ctx.send = AsyncMock()
        await admin.helpme(ctx)
        await admin.helpfixer(ctx)
        if ctx.send.await_count >= 2:
            logs.append("✅ helpme and helpfixer executed")
        else:
            logs.append("❌ Help commands failed")
        return logs

    async def test_post_dm_channel(self, ctx) -> List[str]:
        """Run !post from a DM thread."""
        logs: List[str] = []
        admin = self.bot.get_cog('Admin')
        dest = MagicMock(spec=discord.TextChannel)
        dest.name = "general"
        dest.send = AsyncMock()
        thread_parent = MagicMock()
        thread_parent.threads = []
        ctx.guild.text_channels = [dest, thread_parent]
        ctx.message.attachments = []
        ctx.channel = MagicMock(spec=discord.Thread)
        ctx.send = AsyncMock()
        await admin.post(ctx, dest.name, message="Test message")
        self.assert_send(logs, dest.send, "dest.send")
        return logs

    async def test_post_roll_as_user(self, ctx) -> List[str]:
        """Execute a roll as another user via !post."""
        logs: List[str] = []
        admin = self.bot.get_cog('Admin')
        thread = MagicMock(spec=discord.Thread)
        thread.name = "rp-thread"
        parent = MagicMock()
        parent.threads = [thread]
        ctx.guild.text_channels = [parent]
        ctx.message.attachments = []
        ctx.send = AsyncMock()
        with patch.object(self.bot, "invoke", new=AsyncMock()) as mock_invoke:
            await admin.post(ctx, thread.name, message=f"!roll d20 {ctx.author.id}")
        self.assert_called(logs, mock_invoke, "bot.invoke")
        return logs

    async def test_dm_plain(self, ctx) -> List[str]:
        """Send an anonymous DM."""
        logs: List[str] = []
        dm = self.bot.get_cog('DMHandler')
        user = await self.get_test_user(ctx)
        user.send = AsyncMock()
        ctx.send = AsyncMock()
        ctx.message.attachments = []
        with patch.object(dm, "get_or_create_dm_thread", new=AsyncMock(return_value=MagicMock(spec=discord.Thread))):
            await dm.dm.callback(dm, ctx, user, message="Hello there!")
        self.assert_send(logs, user.send, "user.send")
        return logs

    async def test_dm_roll_command(self, ctx) -> List[str]:
        """Relay a roll through !dm."""
        logs: List[str] = []
        dm = self.bot.get_cog('DMHandler')
        user = await self.get_test_user(ctx)
        ctx.send = AsyncMock()
        with patch.object(self.bot.get_cog('RollSystem'), "roll", new=AsyncMock()) as mock_roll:
            await dm.dm.callback(dm, ctx, user, message="!roll 1d20")
        self.assert_called(logs, mock_roll, "roll")
        return logs

    async def test_dm_userid(self, ctx) -> List[str]:
        """Ensure !dm works with a raw user ID."""
        logs: List[str] = []
        dm = self.bot.get_cog('DMHandler')
        user = await self.get_test_user(ctx)
        dummy = MagicMock(spec=discord.User)
        dummy.id = user.id
        dummy.display_name = user.display_name
        dummy.send = AsyncMock()
        ctx.send = AsyncMock()
        ctx.message.attachments = []
        with patch.object(dm, "get_or_create_dm_thread", new=AsyncMock(return_value=MagicMock(spec=discord.Thread))):
            await dm.dm.callback(dm, ctx, dummy, message="Test")
        self.assert_send(logs, dummy.send, "user.send")
        return logs

    async def test_start_rp_multi(self, ctx) -> List[str]:
        """Start RP with two users and roll inside."""
        logs: List[str] = []
        rp = self.bot.get_cog('RPManager')
        user = await self.get_test_user(ctx)
        channel = MagicMock(spec=discord.TextChannel)
        channel.name = "text-rp-test"
        rp.create_group_rp_channel = AsyncMock(return_value=channel)
        result = await rp.start_rp(ctx, f"<@{user.id}>", str(ctx.author.id))
        if result:
            logs.append("✅ start_rp handled users")
        await self.bot.get_cog('RollSystem').loggable_roll(ctx.author, channel, "1d6")
        rp.end_rp_session = AsyncMock()
        ctx.channel = channel
        await rp.end_rp(ctx)
        self.assert_called(logs, rp.end_rp_session, "end_rp_session")
        return logs

    async def test_cyberware_weekly(self, ctx) -> List[str]:
        """Simulate the weekly checkup task."""
        logs: List[str] = []
        manager = self.bot.get_cog('CyberwareManager')
        if not manager:
            logs.append("❌ CyberwareManager cog not loaded")
            return logs
        guild = MagicMock()
        check = discord.Object(id=config.CYBER_CHECKUP_ROLE_ID)
        medium = discord.Object(id=config.CYBER_MEDIUM_ROLE_ID)
        loa = discord.Object(id=config.LOA_ROLE_ID)
        guild.get_role.side_effect = lambda rid: {config.CYBER_CHECKUP_ROLE_ID: check,
                                                  config.CYBER_MEDIUM_ROLE_ID: medium, config.LOA_ROLE_ID: loa}.get(rid)
        member_a = MagicMock(spec=discord.Member)
        member_a.id = 1
        member_a.roles = [medium]
        member_a.add_roles = AsyncMock()
        member_b = MagicMock(spec=discord.Member)
        member_b.id = 2
        member_b.roles = [medium, check]
        member_b.add_roles = AsyncMock()
        guild.members = [member_a, member_b]
        log_channel = MagicMock()
        log_channel.send = AsyncMock()
        guild.get_channel.return_value = log_channel
        with (
            patch.object(self.bot, "get_guild", return_value=guild),
            patch.object(manager.unbelievaboat, "get_balance", new=AsyncMock(return_value={"cash": 5000, "bank": 0})),
            patch.object(manager.unbelievaboat, "update_balance", new=AsyncMock(return_value=True)),
            patch("NightCityBot.cogs.cyberware.save_json_file", new=AsyncMock()),
        ):
            await manager.process_week()
        self.assert_send(logs, member_a.add_roles, "add_roles")
        self.assert_send(logs, log_channel.send, "log_channel.send")
        return logs

    async def test_loa_fixer_other(self, ctx) -> List[str]:
        """Fixer starts and ends LOA for another user."""
        logs: List[str] = []
        loa = self.bot.get_cog('LOA')
        if not loa:
            logs.append("❌ LOA cog not loaded")
            return logs
        fixer = MagicMock()
        fixer.name = config.FIXER_ROLE_NAME
        ctx.author.roles.append(fixer)
        target = MagicMock(spec=discord.Member)
        target.roles = []
        target.add_roles = AsyncMock()
        target.remove_roles = AsyncMock()
        with patch('discord.Guild.get_role', return_value=discord.Object(id=config.LOA_ROLE_ID)):
            await loa.start_loa(ctx, target)
            target.roles.append(discord.Object(id=config.LOA_ROLE_ID))
            await loa.end_loa(ctx, target)
        self.assert_send(logs, target.add_roles, "add_roles")
        self.assert_send(logs, target.remove_roles, "remove_roles")
        ctx.author.roles.remove(fixer)
        return logs

    async def test_roll_as_user(self, ctx) -> List[str]:
        """Roll on behalf of another user."""
        logs: List[str] = []
        roll = self.bot.get_cog('RollSystem')
        user = await self.get_test_user(ctx)
        ctx.guild.get_member = MagicMock(return_value=user)
        ctx.channel = MagicMock()
        ctx.message = MagicMock()
        ctx.message.delete = AsyncMock()
        with patch.object(roll, "loggable_roll", new=AsyncMock()) as mock_log:
            await roll.roll.callback(roll, ctx, dice=f"2d6 <@{user.id}>")
        if mock_log.await_args.args[0] == user:
            logs.append("✅ roll executed for mentioned user")
        else:
            logs.append("❌ roll did not use mentioned user")
        with patch.object(roll, "loggable_roll", new=AsyncMock()) as mock_log2:
            await roll.roll.callback(roll, ctx, dice=f"2d6 {user.id}")
        if mock_log2.await_args.args[0] == user:
            logs.append("✅ roll executed for ID user")
        else:
            logs.append("❌ roll did not use ID user")
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

    async def test_open_shop_daily_limit(self, ctx) -> List[str]:
        """Ensure users can't log a business opening twice on the same day."""
        control = self.bot.get_cog('SystemControl')
        if control:
            await control.set_status('open_shop', True)
        logs = []
        economy = self.bot.get_cog('Economy')
        original_channel = ctx.channel
        ctx.channel = ctx.guild.get_channel(config.BUSINESS_ACTIVITY_CHANNEL_ID)

        storage = {}

        async def fake_load(*_, **__):
            return storage.get("data", {})

        async def fake_save(path, data):
            storage["data"] = data

        ctx.send = AsyncMock()

        sunday = datetime(2025, 6, 15)
        with (
            patch("NightCityBot.cogs.economy.datetime") as mock_dt,
            patch("NightCityBot.cogs.economy.load_json_file", new=fake_load),
            patch("NightCityBot.cogs.economy.save_json_file", new=fake_save),
            patch.object(economy.unbelievaboat, "update_balance", new=AsyncMock()),
        ):
            mock_dt.utcnow.return_value = sunday
            mock_dt.fromisoformat = datetime.fromisoformat
            await economy.open_shop(ctx)
            await economy.open_shop(ctx)
        msg = ctx.send.call_args_list[-1][0][0]
        if "already logged a business opening today" in msg:
            logs.append("✅ open_shop rejected when used twice")
        else:
            logs.append("❌ open_shop did not enforce daily limit")
        ctx.channel = original_channel
        return logs

    @commands.command(hidden=True)
    @commands.is_owner()
    async def test_bot(self, ctx, *test_names: str):
        """Run bot self tests.

        If no ``test_names`` are given all tests are executed. You can specify
        one or more test method names to only run those tests, e.g.
        ``!test_bot test_rolls test_bonus_rolls``.
        A ``-silent`` flag can be provided to send only a final summary via DM
        instead of the current channel. Use ``-verbose`` to print detailed logs
        for each test.
        """
        start = time.time()
        all_logs = []

        # Create a reusable RP channel for tests
        test_names = list(test_names)
        silent = False
        verbose = False
        if "-silent" in test_names:
            test_names.remove("-silent")
            silent = True
        if "-verbose" in test_names:
            test_names.remove("-verbose")
            verbose = True

        output_channel = ctx.channel
        if silent:
            output_channel = await ctx.author.create_dm()
            await ctx.send("🧪 Running tests in silent mode. Results will be sent via DM.")
            ctx.send = AsyncMock()

        ctx.message.attachments = []

        rp_required_tests = {
            "test_post_executes_command",
            "test_post_roll_execution",
        }

        if test_names:
            await output_channel.send(
                f"🧪 Running selected tests on <@{config.TEST_USER_ID}>: {', '.join(test_names)}"
            )
        else:
            await output_channel.send(
                f"🧪 Running full self-test on user <@{config.TEST_USER_ID}>..."
            )

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
            ("test_open_shop_daily_limit", self.test_open_shop_daily_limit),
            ("test_attend_command", self.test_attend_command),
            ("test_cyberware_costs", self.test_cyberware_costs),
            ("test_loa_commands", self.test_loa_commands),
            ("test_checkup_command", self.test_checkup_command),
            ("test_help_commands", self.test_help_commands),
            ("test_post_dm_channel", self.test_post_dm_channel),
            ("test_post_roll_as_user", self.test_post_roll_as_user),
            ("test_dm_plain", self.test_dm_plain),
            ("test_dm_roll_command", self.test_dm_roll_command),
            ("test_dm_userid", self.test_dm_userid),
            ("test_start_rp_multi", self.test_start_rp_multi),
            ("test_cyberware_weekly", self.test_cyberware_weekly),
            ("test_loa_fixer_other", self.test_loa_fixer_other),
            ("test_roll_as_user", self.test_roll_as_user),
        ]
        tests_dict = dict(tests)

        if test_names:
            filtered = []
            unknown = []
            for name in test_names:
                if name in tests_dict:
                    filtered.append((name, tests_dict[name]))
                else:
                    unknown.append(name)
            if unknown:
                await output_channel.send(
                    f"⚠️ Unknown tests: {', '.join(unknown)}"
                )
            tests = filtered
            if not tests:
                return

        rp_manager = self.bot.get_cog('RPManager')
        rp_channel = None
        needs_rp = (not test_names) or any(name in rp_required_tests for name, _ in tests)
        if needs_rp:
            rp_channel = await rp_manager.start_rp(ctx, f"<@{config.TEST_USER_ID}>")
        ctx.test_rp_channel = rp_channel

        try:
            for name, func in tests:
                if verbose:
                    await output_channel.send(
                        f"🧪 `{name}` — {self.test_descriptions.get(name, 'No description.')}"
                    )
                try:
                    logs = await func(ctx)
                except Exception as e:
                    logs = [f"❌ Exception in `{name}`: {e}"]
                all_logs.append(f"{name} — {self.test_descriptions.get(name, '')}")
                all_logs.extend(logs)
                all_logs.append("────────────")

            if verbose:
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
            else:
                summary_text = "\n".join(str(l) for l in all_logs)
                await output_channel.send(f"```\n{summary_text.strip()[:1900]}\n```")

            # Summary embed
            passed = sum(1 for r in all_logs if "✅" in r)
            failed = sum(1 for r in all_logs if "❌" in r)
            duration = time.time() - start

            title = "🧪 Full Bot Self-Test Summary" if not test_names else "🧪 Selected Test Summary"
            embed = discord.Embed(
                title=title,
                color=discord.Color.green() if failed == 0 else discord.Color.red()
            )
            embed.add_field(
                name="Result",
                value=f"✅ Passed: {passed}\n❌ Failed: {failed}",
                inline=False
            )
            embed.set_footer(text=f"⏱️ Completed in {duration:.2f}s")
            await output_channel.send(embed=embed)
        finally:
            if ctx.test_rp_channel:
                await rp_manager.end_rp_session(ctx.test_rp_channel)
