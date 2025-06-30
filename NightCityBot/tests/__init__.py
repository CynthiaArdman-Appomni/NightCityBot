from importlib import import_module
from typing import Callable, Dict

TEST_FUNCTIONS: Dict[str, Callable] = {}
TEST_DESCRIPTIONS: Dict[str, str] = {}

# List of test module names and descriptions
TEST_MODULES = {
    "test_dm_roll_relay": "Relays a roll to a user's DM forum thread using `!dm`.",
    "test_roll_direct_dm": "User runs `!roll` in a DM. Verifies result is DM'd and logged to DM thread.",
    "test_post_executes_command": "Sends a `!roll` command into a channel using `!post`.",
    "test_post_roll_execution": "Executes a roll via !post and checks result inside RP channel.",
    "test_rolls": "Runs `!roll` with valid and invalid input and checks result.",
    "test_bonus_rolls": "Checks that Netrunner bonuses are applied correctly.",
    "test_full_rent_commands": "Executes rent collection on a live user and verifies balance updates.",
    "test_passive_income_logic": "Applies passive income based on recent shop opens.",
    "test_trauma_payment": "Attempts to log a trauma plan subscription in the correct DM thread.",
    "test_rent_logging_sends": "Verifies that rent events are logged in #rent and #eviction-notices.",
    "test_open_shop_command": "Runs !open_shop in the correct channel.",
    "test_dm_thread_reuse": "Ensures DM logging reuses existing threads.",
    "test_open_shop_errors": "Checks open_shop failures for bad context.",
    "test_start_end_rp": "Creates and ends an RP session to verify logging.",
    "test_unknown_command": "Ensures unknown commands don't spam the audit log.",
    "test_ignore_unbelievaboat": "Ignores UnbelievaBoat economy commands.",
    "test_open_shop_daily_limit": "Ensures !open_shop can't run twice on the same Sunday.",
    "test_attend_command": "Runs !attend and verifies weekly/Sunday restrictions.",
    "test_cyberware_costs": "Ensures cyberware medication costs scale and cap correctly.",
    "test_loa_commands": "Runs start_loa and end_loa commands.",
    "test_checkup_command": "Runs the ripperdoc !checkup command.",
    "test_help_commands": "Executes !helpme and !helpfixer.",
    "test_post_dm_channel": "Runs !post from a DM thread.",
    "test_post_roll_as_user": "Executes a roll as another user via !post.",
    "test_dm_plain": "Sends a normal anonymous DM using !dm.",
    "test_dm_roll_command": "Relays a roll through !dm.",
    "test_dm_userid": "Ensures !dm works with a raw user ID.",
    "test_dm_thread_autolink": "Links DM threads from their name when missing.",
    "test_start_rp_multi": "Starts RP with two users and ends it.",
    "test_cyberware_weekly": "Simulates the weekly cyberware task.",
    "test_loa_fixer_other": "Fixer starts and ends LOA for another user.",
    "test_loa_id_check": "Handles LOA with distinct role instances sharing an ID.",
    "test_roll_as_user": "Rolls on behalf of another user.",
    "test_message_cleanup": "Ensures !dm and !post delete their commands.",
    "test_balance_backup": "Ensures collect_rent backs up balances before processing.",
    "test_backup_balance_command": "Runs !backup_balance for a single user.",
    "test_backup_balances_command": "Runs !backup_balances and saves a snapshot.",
    "test_restore_balance_command": "Restores a single user's balance from backup.",
    "test_restore_balance_latest": "Restores the latest entry from a user's backup log.",
    "test_restore_balance_label": "Restores a user's balance using a label.",
    "test_restore_balances_label": "Restores all users' balances using a label.",
    "test_test_bot_dm": "Runs test_bot in silent mode and checks DM output.",
    "test_open_shop_concurrency": "Runs open_shop concurrently to ensure locking.",
    "test_npc_button": "Assign NPC role via button.",
    "test_call_trauma": "Pings Trauma Team with the user's plan.",
    "test_list_deficits": "Reports members with insufficient funds.",
    "test_simulate_rent_cyberware": "Runs simulate_rent with the -cyberware flag.",
    "test_simulate_all": "Runs the combined simulate_all command.",

    "test_log_audit_chunks": "Ensures long audit entries are split across fields.",
    "test_helpfixer_chunks": "Ensures long help entries are split across fields.",
    "test_send_chunks": "Ensures long plain messages are chunked automatically.",
    "test_rent_baseline_non_tier": "Baseline living cost deducted for members without Tier roles.",
    "test_eviction_on_baseline_failure": "Eviction notices sent when baseline deduction fails.",
}

for name in TEST_MODULES:
    mod = import_module(f"NightCityBot.tests.{name}")
    TEST_FUNCTIONS[name] = mod.run
    TEST_DESCRIPTIONS[name] = TEST_MODULES[name]
