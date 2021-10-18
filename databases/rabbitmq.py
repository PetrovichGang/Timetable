from config import RABBITMQ_ENABLE, RABBITMQ_URL, RABBITMQ_PORT
from typing import List, Callable, Dict, Union, Optional
from pydantic import BaseModel, Field
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

    text: str = Field(alias="text")
    images_url: Optional[List[str]] = Field(alias="images_url")


class Consumer:
    def __init__(self, exchange_name: str, routing_keys: List[RoutingKey], prefetch_count: int = 1, url: str = RABBITMQ_URL, port: int = RABBITMQ_PORT, loop: asyncio.AbstractEventLoop = None):
        self.url = url
        self.port = port
        self.exchange_name = exchange_name
        self.prefetch_count = prefetch_count
        self.loop: asyncio.AbstractEventLoop = loop
        self.routing_keys = routing_keys

        if not all(isinstance(rout, RoutingKey) for rout in self.routing_keys):
            raise ValueError(f"Invalid routing keys")

        self.connection: aio_pika.Connection
        self.exchange: aio_pika.Exchange
        self.channel: aio_pika.Channel
        self.queues: Dict[str, aio_pika.Queue] = {}

    async def start(self) -> bool:
        if not RABBITMQ_ENABLE:
            logger.info(f"RabbitMQ is disabled, set RABBITMQ_ENABLE to True on .env")
            return False

        try:
            if self.loop:
                self.connection = await aio_pika.connect(self.url, loop=self.loop, port=self.port)
            else:
                self.loop = asyncio.get_event_loop()
                self.connection = await aio_pika.connect(self.url, loop=self.loop, port=self.port)
            logger.info(f"RabbitMQ Consumer: The connection is established")

            self.channel = await self.connection.channel()

            for rout in self.routing_keys:
                await self.add_queue(rout)

        except ConnectionError as ex:
            logger.error(f"RabbitMQ Consumer: Connection Error: {ex}")
            return False
        return True

    async def add_queue(self, routing_key: RoutingKey, durable=True):
        try:
            queue = await self.channel.declare_queue(name=routing_key.key, durable=durable)
            await queue.bind(self.exchange_name, routing_key=routing_key.key)
            await queue.consume(routing_key.func)

            self.queues[routing_key.key] = queue
            logger.info(f"RabbitMQ Consumer: Queue {routing_key.key} bind")
        except (aio_pika.exceptions.ChannelNotFoundEntity, aio_pika.exceptions.ChannelInvalidStateError) as ex:
            logger.error(f"RabbitMQ Consumer: {ex}")

    async def close(self):
        try:
            await self.connection.close()
            logger.info(f"RabbitMQ Consumer: Connection close")
        except AttributeError as ex:
            logger.error(f"RabbitMQ Consumer: {ex}")


class Producer:
    def __init__(self, exchange_name: str, url: str = RABBITMQ_URL, port: int = RABBITMQ_PORT, loop: asyncio.AbstractEventLoop = None):
        self.url = url
        self.port = port
        self.exchange_name = exchange_name
        self.loop: asyncio.AbstractEventLoop = loop

        self.connection: aio_pika.Connection
        self.channel: aio_pika.Channel
        self.exchange: aio_pika.Exchange

    async def start(self) -> bool:
        if not RABBITMQ_ENABLE:
            logger.info(f"RabbitMQ is disabled, set RABBITMQ_ENABLE to True on .env")
            return False

        try:
            if self.loop:
                self.connection = await aio_pika.connect(self.url, loop=self.loop, port=self.port)
            else:
                self.loop = asyncio.get_event_loop()
                self.connection = await aio_pika.connect(self.url, loop=self.loop, port=self.port)
            logger.info(f"RabbitMQ Producer: The connection is established")

            channel = await self.connection.channel()
            self.exchange = await channel.declare_exchange(self.exchange_name, aio_pika.ExchangeType.DIRECT)
        except ConnectionError as ex:
            logger.error(f"RabbitMQ Producer: Connection Error {ex}")
            return False
        return True

    async def close(self):
        try:
            await self.connection.close()
            logger.info(f"RabbitMQ Producer: Connection close")
        except AttributeError as ex:
            logger.error(f"RabbitMQ Producer: {ex}")

    async def send_message(self, message: Union[str, bytes], routing_key: str):
        try:
            message = message if isinstance(message, bytes) else message.encode()
            message = aio_pika.Message(body=message)
            await self.exchange.publish(message, routing_key=routing_key)
            logger.debug(
                f"RabbitMQ Producer: Exchange: '{self.exchange_name}' Routing key: '{routing_key}' Message body: {message.body}")
        except AttributeError as ex:
            logger.error(f"RabbitMQ Producer: {ex}")
