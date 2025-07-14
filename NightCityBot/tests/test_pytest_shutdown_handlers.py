import asyncio
import signal
from unittest.mock import patch

from NightCityBot.bot import register_shutdown, NightCityBot

class DummyBot(NightCityBot):
    def __init__(self):
        super().__init__()
        self.loop = asyncio.new_event_loop()


def test_register_shutdown():
    bot = DummyBot()
    def dummy_task(coro):
        coro.close()
        return None

    with patch('signal.signal') as sig_patch, \
         patch.object(bot.loop, 'create_task', side_effect=dummy_task) as create_task:
        register_shutdown(bot)
        assert sig_patch.call_count == 2
        signals = {call.args[0] for call in sig_patch.call_args_list}
        assert signal.SIGINT in signals and signal.SIGTERM in signals
        handler = sig_patch.call_args_list[0].args[1]
        handler(signal.SIGTERM, None)
        create_task.assert_called()
