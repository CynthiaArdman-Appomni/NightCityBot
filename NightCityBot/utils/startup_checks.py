import discord
from pathlib import Path
from typing import Iterable
import logging

logger = logging.getLogger(__name__)

import config
from .helpers import load_json_file, save_json_file
from NightCityBot.services.unbelievaboat import UnbelievaBoatAPI

# Role and channel identifiers to verify
ROLE_ID_FIELDS: Iterable[str] = [
    "FIXER_ROLE_ID",
    "TRAUMA_TEAM_ROLE_ID",
    "VERIFIED_ROLE_ID",
    "NPC_ROLE_ID",
    "CYBER_CHECKUP_ROLE_ID",
    "CYBER_MEDIUM_ROLE_ID",
    "CYBER_HIGH_ROLE_ID",
    "CYBER_EXTREME_ROLE_ID",
    "LOA_ROLE_ID",
    "RIPPERDOC_ROLE_ID",
]

CHANNEL_ID_FIELDS: Iterable[str] = [
    "DM_INBOX_CHANNEL_ID",
    "BUSINESS_ACTIVITY_CHANNEL_ID",
    "RENT_LOG_CHANNEL_ID",
    "EVICTION_CHANNEL_ID",
    "TRAUMA_FORUM_CHANNEL_ID",
    "TRAUMA_NOTIFICATIONS_CHANNEL_ID",
    "AUDIT_LOG_CHANNEL_ID",
    "GROUP_AUDIT_LOG_CHANNEL_ID",
]

# Additional config values that should not be empty
REQUIRED_FIELDS: Iterable[str] = [
    "AUDIT_LOG_CHANNEL_ID",
    "GROUP_AUDIT_LOG_CHANNEL_ID",
    "FIXER_ROLE_NAME",
    "FIXER_ROLE_ID",
    "DM_INBOX_CHANNEL_ID",
    "GUILD_ID",
    "TEST_USER_ID",
    "REPORT_USER_ID",
    "BUSINESS_ACTIVITY_CHANNEL_ID",
    "ATTENDANCE_CHANNEL_ID",
    "RENT_LOG_CHANNEL_ID",
    "EVICTION_CHANNEL_ID",
    "TRAUMA_TEAM_ROLE_ID",
    "TRAUMA_FORUM_CHANNEL_ID",
    "TRAUMA_NOTIFICATIONS_CHANNEL_ID",
    "VERIFIED_ROLE_ID",
    "APPROVED_ROLE_ID",
    "NPC_ROLE_ID",
    "THREAD_MAP_FILE",
    "OPEN_LOG_FILE",
    "LAST_RENT_FILE",
    "LAST_PAYMENT_FILE",
    "BALANCE_BACKUP_DIR",
    "CHARACTER_BACKUP_DIR",
    "RENT_AUDIT_DIR",
    "ATTEND_LOG_FILE",
    "CYBERWARE_LOG_FILE",
    "CYBERWARE_WEEKLY_FILE",
    "SYSTEM_STATUS_FILE",
    "CYBER_CHECKUP_ROLE_ID",
    "CYBER_MEDIUM_ROLE_ID",
    "CYBER_HIGH_ROLE_ID",
    "CYBER_EXTREME_ROLE_ID",
    "LOA_ROLE_ID",
    "RIPPERDOC_ROLE_ID",
    "RIPPERDOC_LOG_CHANNEL_ID",
    "TIMEZONE",
    "RP_IC_CATEGORY_ID",
    "CHARACTER_SHEETS_CHANNEL_ID",
    "RETIRED_SHEETS_CHANNEL_ID",
    "NPC_SHEETS_CHANNEL_ID",
]

LOG_FILES = [
    config.THREAD_MAP_FILE,
    config.OPEN_LOG_FILE,
    config.ATTEND_LOG_FILE,
    config.CYBERWARE_LOG_FILE,
]

async def verify_config(bot: discord.Client) -> None:
    guild = bot.get_guild(config.GUILD_ID)
    if not guild:
        logger.warning("\u26a0\ufe0f Guild with ID %s not found.", config.GUILD_ID)
        return

    issues = False
    # Ensure required config values are populated
    for field in REQUIRED_FIELDS:
        val = getattr(config, field, None)
        logger.info("Checking value %s: %s", field, val)
        if val in (None, "", 0):
            logger.warning("\u26a0\ufe0f Missing value for %s", field)
            issues = True
    for field in ROLE_ID_FIELDS:
        role_id = getattr(config, field, 0)
        logger.info("Checking role %s: %s", field, role_id)
        if role_id and guild.get_role(role_id) is None:
            logger.warning("\u26a0\ufe0f Missing role for %s: %s", field, role_id)
            issues = True

    # Check that configured channels exist
    for field in CHANNEL_ID_FIELDS:
        ch_id = getattr(config, field, 0)
        logger.info("Checking channel %s: %s", field, ch_id)
        if ch_id and guild.get_channel(ch_id) is None:
            logger.warning("\u26a0\ufe0f Missing channel for %s: %s", field, ch_id)
            issues = True

    # Check bot permissions
    required_perms = [
        "send_messages",
        "manage_messages",
        "manage_channels",
        "manage_roles",
        "attach_files",
        "embed_links",
    ]
    me = guild.me
    for perm in required_perms:
        logger.info("Checking permission: %s", perm)
        if not getattr(me.guild_permissions, perm, False):
            logger.warning("\u26a0\ufe0f Bot missing permission: %s", perm)
            issues = True

    if not issues:
        logger.info("\u2705 Configuration verified with no issues.")

async def cleanup_logs(bot: discord.Client) -> None:
    guild = bot.get_guild(config.GUILD_ID)
    if not guild:
        return

    member_ids = {str(m.id) for m in guild.members}

    for file_path in LOG_FILES:
        path = Path(file_path)
        if not path.exists():
            continue
        data = await load_json_file(path, default={})
        cleaned = {uid: val for uid, val in data.items() if uid in member_ids}
        if cleaned != data:
            await save_json_file(path, cleaned)
            logger.info("\u2705 Cleaned orphaned entries from %s", path.name)

async def check_unbelievaboat(bot: discord.Client) -> None:
    """Verify we can reach the UnbelievaBoat API."""
    token = getattr(config, "UNBELIEVABOAT_API_TOKEN", None)
    if not token:
        logger.warning("\u26a0\ufe0f UNBELIEVABOAT_API_TOKEN not configured.")
        return
    api = UnbelievaBoatAPI(token)
    try:
        logger.info("Checking UnbelievaBoat connection...")
        result = await api.get_balance(getattr(config, "TEST_USER_ID", 0))
        if result is not None:
            logger.info("\u2705 Connected to UnbelievaBoat successfully.")
        else:
            logger.warning("\u26a0\ufe0f Failed to fetch balance from UnbelievaBoat.")
    finally:
        await api.close()

async def perform_startup_checks(bot: discord.Client) -> None:
    await bot.wait_until_ready()
    await verify_config(bot)
    await check_unbelievaboat(bot)
    await cleanup_logs(bot)
    admin = bot.get_cog('Admin')
    if admin:
        await admin.log_audit(bot.user, "✅ Bot successfully started.")
    logger.info("\u2705 Bot successfully started and ready.")

