import inspect
from NightCityBot.cogs.loa import LOA
from NightCityBot.cogs.rp_manager import RPManager
from NightCityBot.cogs.economy import Economy
from NightCityBot.cogs.cyberware import CyberwareManager
from NightCityBot.cogs.system_control import SystemControl
from NightCityBot.cogs.test_suite import TestSuite
from NightCityBot.cogs.dm_handling import DMHandler
import discord
import pytest

@pytest.mark.parametrize("cls, method, aliases", [
    (LOA, "start_loa", ["startloa", "loa_start", "loastart"]),
    (LOA, "end_loa", ["endloa", "loa_end", "loaend"]),
    (RPManager, "start_rp", ["startrp", "rp_start", "rpstart"]),
    (RPManager, "end_rp", ["endrp", "rp_end", "rpend"]),
    (Economy, "open_shop", ["openshop", "os"]),
    (Economy, "collect_rent", ["collectrent"]),
    (Economy, "collect_housing", ["collecthousing"]),
    (Economy, "collect_business", ["collectbusiness"]),
    (Economy, "collect_trauma", ["collecttrauma"]),
    (CyberwareManager, "checkup", ["check-up", "check_up", "cu", "cup"]),
    (CyberwareManager, "weeks_without_checkup", ["weekswithoutcheckup", "wwocup", "wwc"]),
    (CyberwareManager, "give_checkup_role", ["givecheckuprole", "givecheckups", "cuall", "checkupall"]),
    (CyberwareManager, "collect_cyberware", ["collectcyberware"]),
    (SystemControl, "enable_system", ["enablesystem", "es", "systemenable"]),
    (SystemControl, "disable_system", ["disablesystem", "ds", "systemdisable"]),
    (SystemControl, "system_status", ["systemstatus"]),
    (TestSuite, "test_bot", ["testbot"]),
])
def test_aliases(cls, method, aliases):
    command = getattr(cls, method)
    assert hasattr(command, "aliases"), f"{method} missing aliases"
    for a in aliases:
        assert a in command.aliases
