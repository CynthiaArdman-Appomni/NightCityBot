"""Bot configuration values.

Sensitive tokens such as ``TOKEN`` and ``UNBELIEVABOAT_API_TOKEN`` are loaded
from environment variables if available so they don't need to be hard coded.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Automatically load variables from a `.env` file located next to this
# config module so local development doesn't require exporting them.
load_dotenv(Path(__file__).with_name('.env'))

# Secrets can be provided via environment variables.  They default to ``None``
# so running the bot locally can still work if these values are assigned below
# or patched in tests.
TOKEN = os.getenv("TOKEN")
UNBELIEVABOAT_API_TOKEN = os.getenv("UNBELIEVABOAT_API_TOKEN")

AUDIT_LOG_CHANNEL_ID = 1349160856688267285
GROUP_AUDIT_LOG_CHANNEL_ID = 1379222007513874523
FIXER_ROLE_NAME = "Fixer"
FIXER_ROLE_ID = 1348633945545379911
DM_INBOX_CHANNEL_ID = 1379222007513874523
GUILD_ID = 1348601552083882108
TEST_USER_ID = 286338318076084226
BUSINESS_ACTIVITY_CHANNEL_ID = 1379941898772414464
ATTENDANCE_CHANNEL_ID = 1384001117125345280
RENT_LOG_CHANNEL_ID = 1379942591721902152
EVICTION_CHANNEL_ID = 1379942446829404321
TRAUMA_TEAM_ROLE_ID = 1348661300334563328
TRAUMA_FORUM_CHANNEL_ID = 1351070651313557545
VERIFIED_ROLE_ID = 1351048862323834952
THREAD_MAP_FILE = "thread_map.json"
OPEN_LOG_FILE = "business_open_log.json"
LAST_RENT_FILE = "last_rent.json"
BALANCE_BACKUP_DIR = "backups"
RENT_AUDIT_DIR = "rent_audits"
ATTEND_LOG_FILE = "attendance_log.json"
CYBERWARE_LOG_FILE = "cyberware_log.json"
SYSTEM_STATUS_FILE = "system_status.json"
CYBER_CHECKUP_ROLE_ID = 1383623743934300272
CYBER_MEDIUM_ROLE_ID = 1383623573939159240
CYBER_HIGH_ROLE_ID = 1383623624560345139
CYBER_EXTREME_ROLE_ID = 1383623702742302800
LOA_ROLE_ID = 1383623986843357324
RIPPERDOC_ROLE_ID = 1356028868103897156
TIMEZONE = "UTC"
RP_IC_CATEGORY_ID = 1348605939527192576
