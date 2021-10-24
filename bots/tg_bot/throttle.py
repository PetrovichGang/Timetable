from aiogram.dispatcher import middlewares, handler
from aiogram.utils.exceptions import Throttled
from bots.common.strings import strings
from aiogram import types, Dispatcher
import asyncio


class ThrottlingMiddleware(middlewares.BaseMiddleware):
    def __init__(self, dispatcher: Dispatcher):
        self.dispatcher = dispatcher
        super(ThrottlingMiddleware, self).__init__()

    # noinspection PyUnusedLocal
    async def on_process_message(self, message: types.Message, data: dict):
        try:
            await self.dispatcher.throttle("throttle", rate=10)  # сброс состояния через x сек.
        except Throttled as t:
            if t.exceeded_count == 20:  # кол-во сообщений за x сек.
                await message.answer(strings.error.throttle)
            if t.exceeded_count >= 20:
                await asyncio.sleep(10)
                raise handler.CancelHandler()
