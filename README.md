# NightCityBot

NightCityBot is a Discord bot built with `discord.py` that provides roleplay utilities, economy management and automated moderation tools for a Cyberpunk themed server.  The bot is organised using *cogs* – modular components that group related commands and background tasks.

This document gives an overview of the major modules and how they work.

## Requirements

* Python 3.11+
* The packages listed in `requirements.txt`
* A Discord bot token and configuration values in `config.py`

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Running the bot

Execute the entry point script:

```bash
python -m NightCityBot.bot
```

A small Flask server is also started to keep the bot alive on certain hosting platforms.

## Cogs

### DMHandler
*File: `NightCityBot/cogs/dm_handling.py`*

Handles anonymous DMs from Fixers to players and maintains a logging thread for each user in the channel defined by `DM_INBOX_CHANNEL_ID`.

Key features:

* `!dm @user <message>` – send an anonymous DM and log the conversation in a private thread.
* Automatic relay of commands such as `!roll` or `!start_rp` when used from a DM logging thread.
* Creates/loads the mapping of users to logging threads using `thread_map.json`.

### Economy
*File: `NightCityBot/cogs/economy.py`*

Manages the in‑game economy and rent collection. It integrates with the [UnbelievaBoat](https://unbelievaboat.com/) economy API.

Main commands:

* `!open_shop` – record a business opening on Sundays and instantly grant passive income based on the business tier.
* `!attend` – weekly attendance reward for verified players.
* `!due` – estimate upcoming rent, baseline fees and this week's cyberware medication cost.
* `!collect_rent` / `!simulate_rent` – perform (or simulate) monthly rent collection across all members. Handles housing rent, business rent, baseline cost and Trauma Team subscriptions.
* `!collect_housing`, `!collect_business`, `!collect_trauma` – manual per‑member processing.

The cog stores logs in JSON files such as `business_open_log.json` and `attendance_log.json` and consults `NightCityBot/utils/constants.py` for role costs.

### CyberwareManager
*File: `NightCityBot/cogs/cyberware.py`*

Implements weekly check‑up reminders and medication costs for players with cyberware. A background task runs every Saturday:

1. Gives the `CYBER_CHECKUP_ROLE_ID` role each week.
2. If the role is kept the following week, deducts a cost based on the cyberware level (medium/high/extreme).

Commands:

* `!simulate_cyberware` – simulate the weekly process or calculate the cost for a particular user/week.
* `!checkup @user` – ripperdoc command to remove the check‑up role once an in‑character examination is done.
* `!weeks_without_checkup @user` – display the current streak.

All data is stored in `cyberware_log.json`.

### RPManager
*File: `NightCityBot/cogs/rp_manager.py`*

Provides tools for creating private RP text channels and archiving them when complete.

* `!start_rp @users` – creates a locked text channel named using `utils.helpers.build_channel_name`.
* `!end_rp` – archives the channel contents to a thread in `GROUP_AUDIT_LOG_CHANNEL_ID` and then deletes the channel.
* Commands typed inside `text-rp-*` channels are intercepted and passed back to the bot for processing (allowing `!roll` and other commands inside RP sessions).

### RollSystem
*File: `NightCityBot/cogs/roll_system.py`*

Simple dice rolling logic supporting `XdY+Z` syntax. Rolls can be used in any channel or DM.

Highlights:

* Applies a netrunner bonus based on the user's roles.
* Logs DM rolls back to the user's logging thread for record keeping.
* Supports rolling on behalf of another user when invoked via `!post` or `!dm`.

### LOA
*File: `NightCityBot/cogs/loa.py`*

Manages Leave‑of‑Absence status.

* `!start_loa` and `!end_loa` – players can toggle their own LOA, while Fixers can specify another member.
* When on LOA, baseline costs, housing rent and Trauma Team payments are skipped by other cogs.

### SystemControl
*File: `NightCityBot/cogs/system_control.py`*

A small cog that allows administrators to enable or disable major subsystems at runtime. States are persisted in `system_status.json`.

Commands:

* `!enable_system <name>` / `!disable_system <name>`
* `!system_status` – show current on/off flags.

### Admin
*File: `NightCityBot/cogs/admin.py`*

Offers helper commands for staff and global error handling.

* `!post <channel> <message>` – post a message or run a command in another channel/thread. Frequently used in conjunction with `!roll` or `!start_rp`.
* `!helpme` and `!helpfixer` – display help embeds for regular users and Fixers respectively.
* Logs actions to `AUDIT_LOG_CHANNEL_ID` via `log_audit`.

### TestSuite
*File: `NightCityBot/cogs/test_suite.py`*

Exposes the internal test suite directly through Discord commands.

* `!test_bot [tests]` – run selected self‑tests. Without arguments it runs the entire suite defined in `NightCityBot/tests`.
* `!test__bot [pattern]` – execute the pytest based tests. Mainly used by the repository maintainers.

## Services

The `services` package contains integrations used by the cogs:

* **UnbelievaBoatAPI** (`services/unbelievaboat.py`) – minimal wrapper around the UnbelievaBoat REST API for fetching and updating user balances. The wrapper includes basic retry logic for resilience against temporary failures.
* **TraumaTeamService** (`services/trauma_team.py`) – helper for processing Trauma Team subscription payments and posting into the configured forum channel.

## Startup checks

On initialisation the bot runs `perform_startup_checks` which verifies that all configured roles and channels exist, confirms the bot has the permissions it needs, and cleans up orphaned entries from the JSON log files. This helps catch configuration issues early and keeps data files tidy.

## Utilities

Utility helpers reside in `NightCityBot/utils`:

* `helpers.py` – asynchronous JSON helpers and the `build_channel_name` function.
* `permissions.py` – custom checks such as `is_fixer` and `is_ripperdoc`.
* `constants.py` – economy related constants and command filters.

## Data files

Several JSON files store runtime data:

* `thread_map.json` – mapping of user IDs to DM log thread IDs.
* `business_open_log.json` – timestamps of each user's `!open_shop` usage.
* `attendance_log.json` – records weekly attendance.
* `cyberware_log.json` – weeks since last check‑up for each user.
* `system_status.json` – persisted enable/disable flags for subsystems.

These files are loaded on startup via `utils.helpers.load_json_file`.

## Testing

A comprehensive suite of automated tests lives in `NightCityBot/tests`.  They can be executed with:

```bash
pytest
```

Alternatively, run `!test_bot` inside Discord to perform many of the same checks without leaving the chat.

