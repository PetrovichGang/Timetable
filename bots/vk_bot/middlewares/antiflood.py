from vkbottle_types.events import GroupEventType
from vkbottle import BaseMiddleware, CtxStorage
from vkbottle.bot import Message
from loguru import logger
import time

LAST_CALL = 'called_at'
RATE_LIMIT = 'rate_limit'
RESULT = 'result'
EXCEEDED_COUNT = 'exceeded'
DELTA = 'delta'
dummy_db = CtxStorage()


class AntiFloodMiddleware(BaseMiddleware):
    def __init__(self):
        logger.debug("Middleware 'AntiFlood' loaded")

    async def pre(self, message: Message):
        try:
            await throttle("antiflood", user_id=message.from_id, chat_id=message.chat_id)

        except Throttled as t:
            if t.exceeded_count <= 2:
                logger.debug(t)
                await message.answer(f"@id{message.peer_id} Перестань спамить")
            return False

        return True


class RawMessageAntiFloodMiddleware(BaseMiddleware):
    def __init__(self):
        logger.debug("Middleware 'RawMessageAntiFlood' loaded")

    async def pre(self, event: GroupEventType):
        if event.type == "message_event":
            user_id, chat_id = event.object.user_id, event.object.peer_id - 2_000_000_000
            try:
                await throttle("antiflood", user_id=user_id, chat_id=chat_id)

            except Throttled as t:
                if t.exceeded_count <= 2:
                    logger.debug(t)
                return False

            return True
        return True


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
