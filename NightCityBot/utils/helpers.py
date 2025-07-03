from typing import Optional, List
import re
from datetime import datetime
from zoneinfo import ZoneInfo
import config
from pathlib import Path
import json
import aiofiles
import logging

logger = logging.getLogger(__name__)


def build_channel_name(usernames, max_length=100):
    """Builds a Discord channel name for a group RP."""
    full_name = "text-rp-" + "-".join(f"{name}-{uid}" for name, uid in usernames)
    if len(full_name) <= max_length:
        return re.sub(r"[^a-z0-9\-]", "", full_name.lower())

    simple_name = "text-rp-" + "-".join(name for name, _ in usernames)
    if len(simple_name) > max_length:
        simple_name = simple_name[:max_length]

    return re.sub(r"[^a-z0-9\-]", "", simple_name.lower())


def safe_filename(name: str) -> str:
    """Return a filesystem-safe version of ``name``."""
    cleaned = re.sub(r"[\\/*?:\"<>|]", "", name).strip()
    return cleaned or "unnamed"


async def load_json_file(file_path: Path | str, default=None):
    """Safely load a JSON file with fallback to default value.

    `file_path` can be either a :class:`pathlib.Path` or a string path.
    """
    path = Path(file_path)
    try:
        if path.exists():
            async with aiofiles.open(path, "r") as f:
                content = await f.read()
                if not content.strip():
                    return default if default is not None else {}
                return json.loads(content)
    except json.JSONDecodeError as e:
        # File had invalid JSON; treat as empty and log without traceback
        logger.error("Invalid JSON in %s: %s", path.name, e)
    except Exception as e:
        logger.exception("Error loading %s: %s", path.name, e)
    return default if default is not None else {}


async def save_json_file(file_path: Path | str, data):
    """Safely save data to a JSON file."""
    path = Path(file_path)
    try:
        async with aiofiles.open(path, "w") as f:
            await f.write(json.dumps(data, indent=2))
        return True
    except Exception as e:
        logger.exception("Error saving %s: %s", path.name, e)
        return False


async def append_json_file(file_path: Path | str, item) -> bool:
    """Append an item to a JSON list file."""
    path = Path(file_path)
    entries = await load_json_file(path, default=[])
    if not isinstance(entries, list):
        entries = []
    entries.append(item)
    return await save_json_file(path, entries)


def get_tz_now() -> datetime:
    """Return current time in the configured timezone."""
    tz = ZoneInfo(getattr(config, "TIMEZONE", "UTC"))
    return datetime.now(tz)


def parse_dice(dice_str: str) -> tuple[int, int, int] | None:
    """Parse a dice string like '2d6+1'.

    Returns a tuple of (number of dice, sides, modifier) or ``None`` if invalid.
    """
    m = re.fullmatch(r"(?:(\d*)d)?(\d+)([+-]\d+)?", dice_str.replace(" ", ""))
    if not m:
        return None
    n_dice, sides, mod = m.groups()
    n_dice = int(n_dice) if n_dice else 1
    sides = int(sides)
    mod = int(mod) if mod else 0
    return n_dice, sides, mod
