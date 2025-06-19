import discord
from discord.ext import commands
import time
import asyncio
import sys
from pathlib import Path
import logging

# Ensure the project root is on the path for `import config` and utility modules
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
from typing import List, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import config

from NightCityBot import tests

logger = logging.getLogger(__name__)

class TestSuite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tests = tests.TEST_FUNCTIONS
        self.test_descriptions = tests.TEST_DESCRIPTIONS
        self.verbose = False

    @commands.command(name="list_tests")
    @commands.is_owner()
    async def list_tests(self, ctx):
        """List available self-tests and descriptions."""
        lines = [f"`{name}` - {desc}" for name, desc in self.test_descriptions.items()]
        current = ""
        for line in lines:
            if len(current) + len(line) + 1 > 1900:
                await ctx.send(f"```\n{current.strip()}\n```")
                current = line + "\n"
            else:
                current += line + "\n"
        if current:
            await ctx.send(f"```\n{current.strip()}\n```")

    def debug(self, logs: List[str], message: str) -> None:
        """Append a debug message when verbose output is enabled."""
        if self.verbose:
            logs.append(f"🔍 {message}")

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

    async def audit_log(self, ctx, message: str) -> None:
        """Send a message to the audit log channel via the Admin cog."""
        admin = self.bot.get_cog('Admin')
        if not admin:
            return
        for i in range(0, len(message), 900):
            await admin.log_audit(ctx.author, message[i : i + 900])

    @commands.command(hidden=True, aliases=["testbot"])
    @commands.is_owner()
    async def test_bot(self, ctx, *test_names: str):
        """Run bot self tests."""
        start = time.time()
        all_logs = []

        # Create a reusable RP channel for tests
        test_names = list(test_names)
        silent = False
        verbose = False
        dry_run = False
        if "-silent" in test_names:
            test_names.remove("-silent")
            silent = True
        if "-verbose" in test_names:
            test_names.remove("-verbose")
            verbose = True
        if "-dry" in test_names:
            test_names.remove("-dry")
            dry_run = True

        self.verbose = verbose
        ctx.verbose = verbose

        await self.audit_log(
            ctx,
            f"Started test_bot: {', '.join(test_names) if test_names else 'all tests'};"
            f" silent={silent}, verbose={verbose}, dry_run={dry_run}"
        )

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

        if dry_run:
            await output_channel.send(
                f"🧪 Dry run — would execute: {', '.join(test_names) if test_names else 'all tests'}"
            )
            await self.audit_log(
                ctx,
                f"Dry run — would execute: {', '.join(test_names) if test_names else 'all tests'}"
            )
            return

        tests = list(self.tests.items())
        tests_dict = self.tests

        expanded_names = []
        if test_names:
            selected = []
            unknown = []
            for pattern in test_names:
                matched = [
                    (n, tests_dict[n])
                    for n in tests_dict
                    if n == pattern or n.startswith(pattern)
                ]
                if matched:
                    selected.extend(matched)
                else:
                    unknown.append(pattern)
            if unknown:
                await output_channel.send(
                    f"⚠️ Unknown tests: {', '.join(unknown)}"
                )
            # deduplicate while preserving order
            seen = set()
            filtered = []
            for name, func in selected:
                if name not in seen:
                    seen.add(name)
                    filtered.append((name, func))
            tests = filtered
            expanded_names = [n for n, _ in filtered]
            if not tests:
                return

            await output_channel.send(
                f"🧪 Running selected tests on <@{config.TEST_USER_ID}>: {', '.join(expanded_names)}"
            )
            await self.audit_log(
                ctx,
                f"Running selected tests: {', '.join(expanded_names)}"
            )
        else:
            await output_channel.send(
                f"🧪 Running full self-test on user <@{config.TEST_USER_ID}>..."
            )
            await self.audit_log(ctx, "Running full self-test")

        rp_manager = self.bot.get_cog('RPManager')
        rp_channel = None
        ctx.initial_rp_channels = {
            ch.id for ch in ctx.guild.text_channels if ch.name.startswith("text-rp-")
        }
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
                await self.audit_log(
                    ctx,
                    f"Running test {name}: {self.test_descriptions.get(name, 'No description.')}"
                )
                try:
                    logs = await func(self, ctx)
                except Exception as e:
                    logs = [f"❌ Exception in `{name}`: {e}"]
                await self.audit_log(ctx, f"Results for {name}:\n" + "\n".join(str(l) for l in logs))
                all_logs.append(f"{name} — {self.test_descriptions.get(name, '')}")
                all_logs.extend(logs)
                all_logs.append("────────────")

            summary_text = "\n".join(str(l) for l in all_logs).strip()
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
                current_chunk = ""
                for line in summary_text.split("\n"):
                    if len(current_chunk) + len(line) + 1 > 1900:
                        await output_channel.send(f"```\n{current_chunk.strip()}\n```")
                        current_chunk = line
                    else:
                        current_chunk += line + "\n"
                if current_chunk:
                    await output_channel.send(f"```\n{current_chunk.strip()}\n```")
            await self.audit_log(ctx, summary_text)

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
            await self.audit_log(
                ctx,
                f"Summary: Passed {passed}, Failed {failed}, Duration {duration:.2f}s"
            )
        finally:
            if ctx.test_rp_channel:
                logger.debug("Cleaning up test RP channel %s", ctx.test_rp_channel)
                thread = await rp_manager.end_rp_session(ctx.test_rp_channel)
                if thread:
                    try:
                        await thread.delete(reason="Test cleanup")
                    except Exception:
                        logger.exception("Failed to delete log thread %s", thread)
            for ch in ctx.guild.text_channels:
                if (
                    ch.name.startswith("text-rp-")
                    and ch != ctx.test_rp_channel
                    and ch.id not in getattr(ctx, "initial_rp_channels", set())
                ):
                    try:
                        logger.debug("Cleaning residual RP channel %s", ch)
                        thread = await rp_manager.end_rp_session(ch)
                        if thread:
                            try:
                                await thread.delete(reason="Test cleanup")
                            except Exception:
                                logger.exception("Failed to delete log thread %s", thread)
                    except Exception:
                        logger.exception("Failed to clean RP channel %s", ch)

    @commands.command(hidden=True, name="test__bot")
    @commands.is_owner()
    async def test__bot(self, ctx, *patterns: str):
        """Run the self tests through PyTest."""
        import pytest
        await ctx.send("🧪 Running tests with PyTest...")
        args = ["-q", str(Path(__file__).resolve().parents[1] / "tests")]
        if patterns:
            args.extend(["-k", " or ".join(patterns)])
        result = await asyncio.to_thread(pytest.main, args)
        if result == 0:
            await ctx.send("✅ PyTest finished successfully.")
        else:
            await ctx.send(f"❌ PyTest exited with code {result}.")
