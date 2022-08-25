from datetime import timedelta
import time

from vkbottle_types.events import GroupEventType
from vkbottle import BaseMiddleware, CtxStorage
from vkbottle.bot import Message
from loguru import logger

LAST_CALL = 'called_at'
RATE_LIMIT = 'rate_limit'
RESULT = 'result'
EXCEEDED_COUNT = 'exceeded'
DELTA = 'delta'
dummy_db = CtxStorage()


class BlockList:
    @staticmethod
    def check(chat_id) -> bool:
        if user := dummy_db.get(chat_id):
            if user["blocked_until"] > time.time():
                return True
            dummy_db.delete(chat_id)
        return False

    @staticmethod
    def add(chat_id):
        dummy_db.set(
            chat_id,
            {"blocked_until": time.time() + timedelta(seconds=3).total_seconds()}
        )


class AntiFloodMiddleware(BaseMiddleware[Message]):
    def __init__(self, *args, **kwargs):
        logger.debug("Middleware 'AntiFlood' loaded")
        super().__init__(*args, **kwargs)

    async def pre(self):
        if BlockList.check(self.event.peer_id):
            self.stop(f"@id{self.event.peer_id} временно заблокирован")
        try:
            await throttle("antiflood", user_id=self.event.from_id, chat_id=self.event.chat_id)

        except Throttled as t:
            if t.exceeded_count <= 2:
                logger.debug(t)
                await self.event.answer(f"@id{self.event.peer_id} Перестань спамить")
                BlockList.add(self.event.peer_id)
            self.stop(f"@id{self.event.peer_id} решил спамить")


class RawMessageAntiFloodMiddleware(BaseMiddleware[GroupEventType.MESSAGE_EVENT]):
    def __init__(self, *args, **kwargs):
        logger.debug("Middleware 'RawMessageAntiFlood' loaded")
        super().__init__(*args, **kwargs)

    async def pre(self):
        if self.event["type"] == "message_event":
            user_id, chat_id = self.event["object"]["user_id"], self.event["object"]["peer_id"] - 2_000_000_000
            if BlockList.check(chat_id):
                self.stop(f"@id{user_id} временно заблокирован")

            try:
                await throttle("antiflood", user_id=user_id, chat_id=chat_id)

            except Throttled as t:
                if t.exceeded_count <= 2:
                    logger.critical(t)
                    BlockList.add(chat_id)
                self.stop(f"@id{user_id} решил спамить")


async def throttle(key, *, rate=.3, user_id=None, chat_id=None) -> bool:
    """
    From AIOGRAM
    Execute throttling manager.
    Returns True if limit has not exceeded otherwise raises ThrottleError or returns False

    :param key: key in storage
    :param rate: limit (by default is equal to default rate limit)
    :param user_id: user id
    :param chat_id: chat id
    :return: bool
    """

    # Detect current time
    now = time.time()

    bucket = dummy_db.get(f"{chat_id}:{user_id}")

    # Fix bucket
    if bucket is None:
        bucket = {key: {}}
    if key not in bucket:
        bucket[key] = {}
    data = bucket[key]

    # Calculate
    called = data.get(LAST_CALL, now)
    delta = now - called
    result = delta >= rate or delta <= 0

    # Save results
    data[RESULT] = result
    data[RATE_LIMIT] = rate
    data[LAST_CALL] = now
    data[DELTA] = delta
    if not result:
        data[EXCEEDED_COUNT] += 1
    else:
        data[EXCEEDED_COUNT] = 1
    bucket[key].update(data)
    dummy_db.set(f"{chat_id}:{user_id}", bucket)

    if not result:
        # Raise if it is allowed
        raise Throttled(key=key, chat=chat_id, user=user_id, **data)
    return result


class Throttled(Exception):
    def __init__(self, **kwargs):
        self.key = kwargs.pop("antiflood", '<None>')
        self.called_at = kwargs.pop(LAST_CALL, time.time())
        self.rate = kwargs.pop(RATE_LIMIT, None)
        self.result = kwargs.pop(RESULT, False)
        self.exceeded_count = kwargs.pop(EXCEEDED_COUNT, 0)
        self.delta = kwargs.pop(DELTA, 0)
        self.user = kwargs.pop('user', None)
        self.chat = kwargs.pop('chat', None)

    def __str__(self):
        return f"Rate limit exceeded! (Peer_id: {self.user}, Limit: {self.rate} s, " \
            f"exceeded: {self.exceeded_count}, " \
            f"time delta: {round(self.delta, 3)} s)"
