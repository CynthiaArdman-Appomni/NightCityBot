import discord
from pathlib import Path
from typing import Iterable

import config
from .helpers import load_json_file, save_json_file
from NightCityBot.services.unbelievaboat import UnbelievaBoatAPI

# Role and channel identifiers to verify
ROLE_ID_FIELDS: Iterable[str] = [
    "FIXER_ROLE_ID",
    "TRAUMA_TEAM_ROLE_ID",
    "VERIFIED_ROLE_ID",
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
    "AUDIT_LOG_CHANNEL_ID",
    "GROUP_AUDIT_LOG_CHANNEL_ID",
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
        print(f"⚠️ Guild with ID {config.GUILD_ID} not found.")
        return

    # Check that configured roles exist
    for field in ROLE_ID_FIELDS:
        role_id = getattr(config, field, 0)
        print(f"Checking role {field}: {role_id}")
        if role_id and guild.get_role(role_id) is None:
            print(f"⚠️ Missing role for {field}: {role_id}")

    # Check that configured channels exist
    for field in CHANNEL_ID_FIELDS:
        ch_id = getattr(config, field, 0)
        print(f"Checking channel {field}: {ch_id}")
        if ch_id and guild.get_channel(ch_id) is None:
            print(f"⚠️ Missing channel for {field}: {ch_id}")

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
        print(f"Checking permission: {perm}")
        if not getattr(me.guild_permissions, perm, False):
            print(f"⚠️ Bot missing permission: {perm}")

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
            print(f"✅ Cleaned orphaned entries from {path.name}")

async def check_unbelievaboat(bot: discord.Client) -> None:
    """Verify we can reach the UnbelievaBoat API."""
    token = getattr(config, "UNBELIEVABOAT_API_TOKEN", None)
    if not token:
        print("⚠️ UNBELIEVABOAT_API_TOKEN not configured.")
        return
    api = UnbelievaBoatAPI(token)
    try:
        print("Checking UnbelievaBoat connection...")
        result = await api.get_balance(getattr(config, "TEST_USER_ID", 0))
        if result is not None:
            print("✅ Connected to UnbelievaBoat successfully.")
        else:
            print("⚠️ Failed to fetch balance from UnbelievaBoat.")
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
    print("✅ Bot successfully started and ready.")

