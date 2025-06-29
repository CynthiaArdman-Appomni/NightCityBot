from typing import List
from unittest.mock import AsyncMock, patch
import discord
import NightCityBot

async def run(suite, ctx) -> List[str]:
    """Ensure long plain messages are split automatically."""
    logs: List[str] = []
    send_mock = AsyncMock()
    with patch('NightCityBot.orig_send', new=send_mock):
        await discord.abc.Messageable.send(object(), 'A' * 5000)
    try:
        send_mock.assert_awaited()
        calls = send_mock.await_args_list
        if len(calls) >= 3 and all(len(c.args[1]) <= 1900 for c in calls):
            logs.append('✅ chunks used')
        else:
            logs.append('❌ not chunked')
    except Exception as e:
        logs.append(f'❌ exception {e}')
    return logs
