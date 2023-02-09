from config import RABBITMQ_ENABLE, RABBITMQ_URL, RABBITMQ_PORT
from typing import List, Callable, Union, Optional
from pydantic import BaseModel, Field, AnyHttpUrl
from aio_pika import IncomingMessage
import aio_pika
import asyncio
import loguru

logger = loguru.logger


class RoutingKey(BaseModel):
    key: str
    func: Callable[[IncomingMessage], None]


class Message(BaseModel):
    routing_key: str = Field(alias="routing_key")
    recipient_ids: List[int] = Field(alias="recipient_ids")

    lessons: List[dict]


class RabbitModel:
    def __init__(self, exchange_name: str, url: str = RABBITMQ_URL, port: int = RABBITMQ_PORT
                 , timeout: int = 5, limit_reconnects: int = 100, loop: asyncio.AbstractEventLoop = None):
        self.url = url
        self.port = port
        self.exchange_name = exchange_name
        self.timeout = timeout

        if loop is None: loop = asyncio.get_event_loop()
        self.loop: asyncio.AbstractEventLoop = loop
        self.limit_reconnects = limit_reconnects

        self.connection: aio_pika.Connection
        self.channel: aio_pika.Channel
        self.exchange: aio_pika.Exchange


class Consumer(RabbitModel):
    def __init__(self, exchange_name: str, routing_keys: List[RoutingKey], prefetch_count: int = 1,
                 url: str = RABBITMQ_URL, port: int = RABBITMQ_PORT, timeout: int = 5, limit_reconnects: int = 1000,
                 loop: asyncio.AbstractEventLoop = None):
        super(Consumer, self).__init__(exchange_name, url, port, timeout, limit_reconnects, loop)

        if not all(isinstance(rout, RoutingKey) for rout in routing_keys):
            raise ValueError(f"Invalid routing keys")

        self.routing_keys = routing_keys
        self.prefetch_count = prefetch_count
        self.__start_block = False

    async def start(self):
        if not RABBITMQ_ENABLE:
            logger.info(f"RabbitMQ is disabled, set RABBITMQ_ENABLE to True on .env")
            return

        if self.__start_block:
            return
        self.__start_block = True

        for i in range(self.limit_reconnects):
            try:
                self.connection = await aio_pika.connect_robust(self.url, loop=self.loop, port=self.port,
                                                                timeout=self.timeout)
                logger.info(f"RabbitMQ Consumer: The connection is established")

                self.channel = await self.connection.channel()

                for rout in self.routing_keys:
                    await self.add_queue(rout)
                break

            except ConnectionError as ex:
                logger.error(f"RabbitMQ Consumer: Connection Error: {ex}")

            except asyncio.exceptions.TimeoutError as ex:
                logger.error(f"RabbitMQ Producer: Connection Timeout {ex}")

            logger.info(f"RabbitMQ Consumer: [ {i} ] Trying to connect after 10 seconds")
            await asyncio.sleep(10)

    async def add_queue(self, routing_key: RoutingKey):
        try:
            queue = await self.channel.declare_queue(name=routing_key.key, auto_delete=True, timeout=self.timeout)
            await queue.bind(self.exchange_name, routing_key=routing_key.key)
            await queue.consume(routing_key.func)
            logger.info(f"RabbitMQ Consumer: Queue {routing_key.key} bind")

        except (aio_pika.exceptions.ChannelNotFoundEntity, aio_pika.exceptions.ChannelInvalidStateError) as ex:
            logger.error(f"RabbitMQ Consumer: {ex}")

    async def close(self):
        if not RABBITMQ_ENABLE:
            logger.info(f"RabbitMQ is disabled, set RABBITMQ_ENABLE to True on .env")
            return

        try:
            await self.connection.close()
            logger.info(f"RabbitMQ Consumer: Connection close")
        except AttributeError as ex:
            logger.error(f"RabbitMQ Consumer: {ex}")


class Producer(RabbitModel):
    def __init__(self, exchange_name: str, url: str = RABBITMQ_URL, port: int = RABBITMQ_PORT
                 , timeout: int = 5, limit_reconnects: int = 1000, loop: asyncio.AbstractEventLoop = None):
        super(Producer, self).__init__(exchange_name, url, port, timeout, limit_reconnects, loop)

        self.__start_block = False

    async def start(self):
        if not RABBITMQ_ENABLE:
            logger.info(f"RabbitMQ is disabled, set RABBITMQ_ENABLE to True on .env")
            return

        if self.__start_block:
            return
        self.__start_block = True

        for i in range(self.limit_reconnects):
            try:
                self.connection = await aio_pika.connect_robust(self.url, loop=self.loop, port=self.port,
                                                                timeout=self.timeout)
                logger.info(f"RabbitMQ Producer: The connection is established")

                channel = await self.connection.channel()
                self.exchange = await channel.declare_exchange(self.exchange_name, aio_pika.ExchangeType.DIRECT,
                                                               durable=True)
                break

            except ConnectionError as ex:
                logger.error(f"RabbitMQ Producer: Connection Error {ex}")

            except asyncio.exceptions.TimeoutError as ex:
                logger.error(f"RabbitMQ Producer: Connection Timeout {ex}")

            logger.info(f"RabbitMQ Producer: [ {i} ] Trying to connect after 10 seconds")
            await asyncio.sleep(10)

        self.__start_block = False

    async def close(self):
        if not RABBITMQ_ENABLE:
            logger.info(f"RabbitMQ is disabled, set RABBITMQ_ENABLE to True on .env")
            return

        try:
            await self.connection.close()
            logger.info(f"RabbitMQ Producer: Connection close")
        except AttributeError as ex:
            logger.error(f"RabbitMQ Producer: {ex}")

    async def send_message(self, message: Union[str, bytes], routing_key: str):
        if not RABBITMQ_ENABLE:
            logger.info(f"RabbitMQ is disabled, set RABBITMQ_ENABLE to True on .env")
            return

        try:
            message = message if isinstance(message, bytes) else message.encode()
            message = aio_pika.Message(body=message)
            await self.exchange.publish(message, routing_key=routing_key, timeout=self.timeout)
            logger.debug(
                f"RabbitMQ Producer: Exchange: '{self.exchange_name}' Routing key: '{routing_key}' Message body: {message.body}")
        except AttributeError as ex:
            logger.error(f"RabbitMQ Producer: {ex}")

        except asyncio.exceptions.TimeoutError as ex:
            logger.error(f"RabbitMQ Producer: Connection Timeout {ex}")
