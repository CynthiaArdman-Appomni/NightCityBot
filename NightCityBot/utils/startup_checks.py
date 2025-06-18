import discord
from pathlib import Path
from typing import Iterable

import config
from .helpers import load_json_file, save_json_file

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

    issues = False
    for field in ROLE_ID_FIELDS:
        role_id = getattr(config, field, 0)
        if role_id and guild.get_role(role_id) is None:
            print(f"⚠️ Missing role for {field}: {role_id}")
            issues = True

    # Check that configured channels exist
    for field in CHANNEL_ID_FIELDS:
        ch_id = getattr(config, field, 0)
        if ch_id and guild.get_channel(ch_id) is None:
            print(f"⚠️ Missing channel for {field}: {ch_id}")
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
        if not getattr(me.guild_permissions, perm, False):
            print(f"⚠️ Bot missing permission: {perm}")
            issues = True

    if not issues:
        print("✅ Configuration verified with no issues.")

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

async def perform_startup_checks(bot: discord.Client) -> None:
    await verify_config(bot)
    await cleanup_logs(bot)
