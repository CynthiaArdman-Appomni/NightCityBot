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

AUDIT_LOG_CHANNEL_ID = 1341160960924319804
GROUP_AUDIT_LOG_CHANNEL_ID = 1366880900599517214
FIXER_ROLE_NAME = "Fixer"
FIXER_ROLE_ID = 1379437060389339156
DM_INBOX_CHANNEL_ID = 1366880900599517214
GUILD_ID = 1320924574761746473
TEST_USER_ID = 286338318076084226
BUSINESS_ACTIVITY_CHANNEL_ID = 1341160960924319804
ATTENDANCE_CHANNEL_ID = 1341160960924319804
RENT_LOG_CHANNEL_ID = 1379615621167321189
EVICTION_CHANNEL_ID = 1379611043843539004
TRAUMA_TEAM_ROLE_ID = 1380341033124102254
TRAUMA_FORUM_CHANNEL_ID = 1366880900599517214
VERIFIED_ROLE_ID = 1383584459386912913
THREAD_MAP_FILE = "thread_map.json"
OPEN_LOG_FILE = "business_open_log.json"
LAST_RENT_FILE = "last_rent.json"
BALANCE_BACKUP_DIR = "backups"
RENT_AUDIT_DIR = "rent_audits"
ATTEND_LOG_FILE = "attendance_log.json"
CYBERWARE_LOG_FILE = "cyberware_log.json"
SYSTEM_STATUS_FILE = "system_status.json"
CYBER_CHECKUP_ROLE_ID = 1383584111054295193
CYBER_MEDIUM_ROLE_ID = 1383583965192917123
CYBER_HIGH_ROLE_ID = 1383584039763443773
CYBER_EXTREME_ROLE_ID = 1383584070843502602
LOA_ROLE_ID = 1383584185893130421
RIPPERDOC_ROLE_ID = 1383584931594375218
TIMEZONE = "UTC"
RP_IC_CATEGORY_ID = 1348605939527192576
