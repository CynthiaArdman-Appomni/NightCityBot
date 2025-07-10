print("🔥 BOT.PY: Starting imports...")

import discord

print("✅ discord imported")
from discord.ext import commands

print("✅ discord.ext.commands imported")
import os

print("✅ os imported")
import sys

print("✅ sys imported")
import logging

print("✅ logging imported")

print("🔍 Setting up Python path...")
# Ensure the package root is on the path when executed as a script
package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(f"📁 Package root: {package_root}")
if package_root not in sys.path:
    sys.path.insert(0, package_root)
    print("✅ Package root added to sys.path")

print("🔍 Importing config...")
import config

print("✅ config imported")

print("🔍 Importing utils...")
from NightCityBot.utils.permissions import is_fixer

print("✅ permissions imported")

print("🔍 Importing cogs...")
from NightCityBot.cogs.dm_handling import DMHandler

print("✅ DMHandler imported")
from NightCityBot.cogs.economy import Economy

print("✅ Economy imported")
from NightCityBot.cogs.rp_manager import RPManager

print("✅ RPManager imported")
from NightCityBot.cogs.roll_system import RollSystem

print("✅ RollSystem imported")
from NightCityBot.cogs.admin import Admin

print("✅ Admin imported")
from NightCityBot.cogs.test_suite import TestSuite

print("✅ TestSuite imported")
from NightCityBot.cogs.cyberware import CyberwareManager

print("✅ CyberwareManager imported")
from NightCityBot.cogs.loa import LOA

print("✅ LOA imported")
from NightCityBot.cogs.character_manager import CharacterManager

print("✅ CharacterManager imported")
from NightCityBot.cogs.system_control import SystemControl

print("✅ SystemControl imported")
from NightCityBot.cogs.role_buttons import RoleButtons

print("✅ RoleButtons imported")
from NightCityBot.cogs.trauma_team import TraumaTeam

print("✅ TraumaTeam imported")

print("🔍 Importing startup checks...")
from NightCityBot.utils.startup_checks import perform_startup_checks

print("✅ startup_checks imported")

print("🔍 Importing Flask...")
from flask import Flask

print("✅ Flask imported")
from threading import Thread

print("✅ Thread imported")

print("🎉 ALL IMPORTS COMPLETED SUCCESSFULLY!")

logger = logging.getLogger(__name__)


class NightCityBot(commands.Bot):
    """Discord bot wrapper for NCRP."""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        intents.members = True
        intents.dm_messages = True

        super().__init__(command_prefix="!", help_command=None, intents=intents)

    async def setup_hook(self):
        # Load all cogs
        await self.add_cog(DMHandler(self))
        await self.add_cog(SystemControl(self))
        await self.add_cog(Economy(self))
        await self.add_cog(RPManager(self))
        await self.add_cog(RollSystem(self))
        await self.add_cog(CyberwareManager(self))
        await self.add_cog(LOA(self))
        await self.add_cog(CharacterManager(self))
        await self.add_cog(RoleButtons(self))
        await self.add_cog(TraumaTeam(self))
        await self.add_cog(Admin(self))
        await self.add_cog(TestSuite(self))
        # Verify configuration and clean up logs after all cogs are loaded
        self.loop.create_task(perform_startup_checks(self))

    async def on_message(self, message: discord.Message):
        if message.author == self.user or message.author.bot:
            return
        dm_handler = self.get_cog("DMHandler")
        if dm_handler and isinstance(message.channel, discord.Thread):
            if message.channel.id in getattr(dm_handler, "dm_threads", {}).values():
                # Let DMHandler process without invoking commands to avoid duplicates
                return

        if isinstance(
            message.channel, discord.TextChannel
        ) and message.channel.name.startswith("text-rp-"):
            # RPManager handles command invocation for text RP channels
            return

        await self.process_commands(message)

    async def on_ready(self):
        logger.info("%s is running!", self.user.name)
        admin = self.get_cog("Admin")
        if admin:
            await admin.log_audit(self.user, "✅ Bot started and ready.")


app = Flask("")


@app.route("/")
def home():
    return "Bot is alive Version 1.2!"


def run_flask():
    app.run(host="0.0.0.0", port=5000)


def keep_alive():
    t = Thread(target=run_flask)
    t.start()


def main():
    # Add startup logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    print("🚀 Starting NightCityBot initialization...")
    logger.info("Starting NightCityBot...")

    # Check token
    print(f"🔑 Checking for Discord token...")
    if not config.TOKEN:
        print("❌ No Discord token found! Please set TOKEN in Secrets.")
        logger.error("❌ No Discord token found! Please set TOKEN in Secrets.")
        return

    print("✅ Token found!")
    logger.info("✅ Token found, connecting to Discord...")

    # Initialize bot
    print("🤖 Creating bot instance...")
    try:
        bot = NightCityBot()
        print("✅ Bot instance created successfully")
    except Exception as e:
        print(f"❌ Failed to create bot instance: {e}")
        logger.error(f"❌ Failed to create bot instance: {e}")
        return

    # Start keep-alive server
    print("🌐 Starting keep-alive server...")
    try:
        keep_alive()
        print("✅ Keep-alive server started")
    except Exception as e:
        print(f"❌ Failed to start keep-alive server: {e}")
        logger.error(f"❌ Failed to start keep-alive server: {e}")

    # Connect to Discord
    print("🔗 Connecting to Discord...")
    try:
        bot.run(config.TOKEN)
    except discord.LoginFailure:
        print("❌ Invalid Discord token!")
        logger.error("❌ Invalid Discord token!")
    except Exception as e:
        print(f"❌ Bot startup failed: {e}")
        logger.error(f"❌ Bot startup failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
