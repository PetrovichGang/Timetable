from typing import List, Callable, Dict
from aio_pika import IncomingMessage
from pydantic import BaseModel
import aio_pika
import asyncio
import loguru

logger = loguru.logger


class RoutingKey(BaseModel):
    key: str
    func: Callable[[IncomingMessage], None]


class Consumer:
    def __init__(self, url: str, exchange_name: str, routing_keys: List[RoutingKey], prefetch_count: int = 1, loop: asyncio.AbstractEventLoop = None):
        self.url = url
        self.exchange_name = exchange_name
        self.prefetch_count = prefetch_count
        self.loop: asyncio.AbstractEventLoop = loop
        self.routing_keys = routing_keys

        if not all(isinstance(rout, RoutingKey) for rout in self.routing_keys):
            raise ValueError(f"Invalid routing keys")

        for rout in self.routing_keys:
            setattr(self, rout.key, rout.func)

        self.connection: aio_pika.Connection
        self.exchange: aio_pika.Exchange
        self.channel: aio_pika.Channel
        self.queues: Dict[str, aio_pika.Queue] = {}

    async def start(self) -> bool:
        try:
            if self.loop:
                self.connection = await aio_pika.connect(self.url, loop=self.loop)
            else:
                self.loop = asyncio.get_event_loop()
                self.connection = await aio_pika.connect(self.url, loop=self.loop)
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
    def __init__(self, url: str, exchange_name: str, loop: asyncio.AbstractEventLoop = None):
        self.url = url
        self.exchange_name = exchange_name
        self.loop: asyncio.AbstractEventLoop = loop

        self.connection: aio_pika.Connection
        self.channel: aio_pika.Channel
        self.exchange: aio_pika.Exchange

    async def start(self):
        try:
            if self.loop:
                self.connection = await aio_pika.connect(self.url, loop=self.loop)
            else:
                self.loop = asyncio.get_event_loop()
                self.connection = await aio_pika.connect(self.url, loop=self.loop)

            channel = await self.connection.channel()
            self.exchange = await channel.declare_exchange(self.exchange_name, aio_pika.ExchangeType.DIRECT)
        except ConnectionError as ex:
            logger.error(f"RabbitMQ Producer: Connection Error {ex}")

    async def close(self):
        try:
            await self.connection.close()
            logger.info(f"RabbitMQ Producer: Connection close")
        except AttributeError as ex:
            logger.error(f"RabbitMQ Producer: {ex}")

    async def send_message(self, message: str, routing_key: str):
        try:
            message = aio_pika.Message(body=message.encode())
            await self.exchange.publish(message, routing_key=routing_key)
            logger.debug(
                f"RabbitMQ Producer: Exchange: '{self.exchange_name}' Routing key: '{routing_key}' Message body: {message.body}")
        except AttributeError as ex:
            logger.error(f"RabbitMQ Producer: {ex}")


if __name__ == "__main__":
    async def main(loop):
        async def on_vk_message(message: IncomingMessage):
            logger.debug("VK: [x] %r" % message.body)
            await asyncio.sleep(0.1)

            if True:
                message.ack()
            else:
                message.nack()

        async def on_tg_message(message: IncomingMessage):
            logger.debug("TG: [x] %r" % message.body)
            await asyncio.sleep(0.1)

            if True:
                message.ack()
            else:
                message.nack()

        v = RoutingKey(key="VK", func=on_vk_message)
        t = RoutingKey(key="TG", func=on_tg_message)

        c = Consumer("amqp://user:user@192.168.1.160/", "Bots message", [v, t], loop=loop)
        status = await c.start()

    loop = asyncio.get_event_loop()
    connection = loop.run_until_complete(main(loop))

    loop.run_forever()