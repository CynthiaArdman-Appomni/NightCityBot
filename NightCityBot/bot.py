import os

# Allow debug logging of the startup sequence when the VERBOSE environment
# variable is truthy.  Missing definitions previously caused a NameError when
# ``vprint`` was called before ``VERBOSE`` existed.
VERBOSE = os.getenv("VERBOSE", "").lower() in {"1", "true", "yes"}


def vprint(*args, **kwargs):
    """Conditionally print when ``VERBOSE`` is enabled."""
    if VERBOSE:
        print(*args, **kwargs)

vprint("✅ os imported")

vprint("🔥 BOT.PY: Starting imports...")


vprint("🔥 BOT.PY: Starting imports...")
import discord
vprint("✅ discord imported")
from discord.ext import commands
vprint("✅ discord.ext.commands imported")
import sys
vprint("✅ sys imported")
import logging
vprint("✅ logging imported")

vprint("🔍 Setting up Python path...")
# Ensure the package root is on the path when executed as a script
package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
vprint(f"📁 Package root: {package_root}")
if package_root not in sys.path:
    sys.path.insert(0, package_root)
    vprint("✅ Package root added to sys.path")

vprint("🔍 Importing config...")
import config
vprint("✅ config imported")

vprint("🔍 Importing utils...")
from NightCityBot.utils.permissions import is_fixer
vprint("✅ permissions imported")

vprint("🔍 Importing cogs...")
from NightCityBot.cogs.dm_handling import DMHandler
vprint("✅ DMHandler imported")
from NightCityBot.cogs.economy import Economy
vprint("✅ Economy imported")
from NightCityBot.cogs.rp_manager import RPManager
vprint("✅ RPManager imported")
from NightCityBot.cogs.roll_system import RollSystem
vprint("✅ RollSystem imported")
from NightCityBot.cogs.admin import Admin
vprint("✅ Admin imported")
from NightCityBot.cogs.test_suite import TestSuite
vprint("✅ TestSuite imported")
from NightCityBot.cogs.cyberware import CyberwareManager
vprint("✅ CyberwareManager imported")
from NightCityBot.cogs.loa import LOA
vprint("✅ LOA imported")
from NightCityBot.cogs.system_control import SystemControl
vprint("✅ SystemControl imported")
from NightCityBot.cogs.role_buttons import RoleButtons
vprint("✅ RoleButtons imported")
from NightCityBot.cogs.trauma_team import TraumaTeam
vprint("✅ TraumaTeam imported")

vprint("🔍 Importing startup checks...")
from NightCityBot.utils.startup_checks import perform_startup_checks
vprint("✅ startup_checks imported")

vprint("🔍 Importing Flask...")
from flask import Flask
vprint("✅ Flask imported")
from threading import Thread
vprint("✅ Thread imported")

vprint("🎉 ALL IMPORTS COMPLETED SUCCESSFULLY!")



class NightCityBot(commands.Bot):
    """Discord bot wrapper for NCRP."""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        intents.members = True
        intents.dm_messages = True

        super().__init__(
            command_prefix="!",
            help_command=None,
            intents=intents
        )

    async def setup_hook(self):
        # Load all cogs
        await self.add_cog(DMHandler(self))
        await self.add_cog(SystemControl(self))
        await self.add_cog(Economy(self))
        await self.add_cog(RPManager(self))
        await self.add_cog(RollSystem(self))
        await self.add_cog(CyberwareManager(self))
        await self.add_cog(LOA(self))
        await self.add_cog(RoleButtons(self))
        await self.add_cog(TraumaTeam(self))
        await self.add_cog(Admin(self))
        await self.add_cog(TestSuite(self))
        # Verify configuration and clean up logs after all cogs are loaded
        self.loop.create_task(perform_startup_checks(self))

    async def on_message(self, message: discord.Message):
        if message.author == self.user or message.author.bot:
            return
        dm_handler = self.get_cog('DMHandler')
        if dm_handler and isinstance(message.channel, discord.Thread):
            if message.channel.id in getattr(dm_handler, 'dm_threads', {}).values():
                # Let DMHandler process without invoking commands to avoid duplicates
                return

        if isinstance(message.channel, discord.TextChannel) and message.channel.name.startswith("text-rp-"):
            # RPManager handles command invocation for text RP channels
            return

        await self.process_commands(message)

    async def on_ready(self):
        logger.info("%s is running!", self.user.name)
        admin = self.get_cog('Admin')
        if admin:
            await admin.log_audit(self.user, "✅ Bot started and ready.")


app = Flask('')


@app.route('/')
def home():
    return "Bot is alive Version 1.2!"


def run_flask():
    app.run(host='0.0.0.0', port=5000)


def keep_alive():
    t = Thread(target=run_flask)
    t.start()


def main():
    # Add startup logging if it hasn't been configured already
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    logger.debug("🚀 Starting NightCityBot initialization...")
    logger.info("Starting NightCityBot...")
    
    # Check token
    logger.debug(f"🔑 Checking for Discord token...")
    if not config.TOKEN:
        logger.debug("❌ No Discord token found! Please set TOKEN in Secrets.")
        logger.error("❌ No Discord token found! Please set TOKEN in Secrets.")
        return
    
    logger.debug("✅ Token found!")
    logger.info("✅ Token found, connecting to Discord...")
    
    # Initialize bot
    logger.debug("🤖 Creating bot instance...")
    try:
        bot = NightCityBot()
        logger.debug("✅ Bot instance created successfully")
    except Exception as e:
        logger.debug(f"❌ Failed to create bot instance: {e}")
        logger.error(f"❌ Failed to create bot instance: {e}")
        return
    
    # Start keep-alive server
    logger.debug("🌐 Starting keep-alive server...")
    try:
        keep_alive()
        logger.debug("✅ Keep-alive server started")
    except Exception as e:
        logger.debug(f"❌ Failed to start keep-alive server: {e}")
        logger.error(f"❌ Failed to start keep-alive server: {e}")
    
    # Connect to Discord
    logger.debug("🔗 Connecting to Discord...")
    try:
        bot.run(config.TOKEN)
    except discord.LoginFailure:
        logger.debug("❌ Invalid Discord token!")
        logger.error("❌ Invalid Discord token!")
    except Exception as e:
        logger.debug(f"❌ Bot startup failed: {e}")
        logger.error(f"❌ Bot startup failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
