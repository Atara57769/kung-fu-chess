"""
NATS Client Wrapper for Microservice Event Bus Communication.
"""

import json
import logging
import os
import asyncio
from dataclasses import is_dataclass, asdict
from typing import Dict, Any, Callable, Awaitable, Optional, Union, Type
import nats
from nats.aio.client import Client as NATSClient
from nats.aio.msg import Msg
from shared.message_contracts.contracts import dict_to_dataclass

logger = logging.getLogger(__name__)

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")


def _to_json_dict(data: Any) -> Dict[str, Any]:
    """Helper converting DTO dataclass instances or dicts into JSON-serializable dictionaries."""
    if hasattr(data, "to_dict") and callable(getattr(data, "to_dict")):
        return data.to_dict()
    elif is_dataclass(data) and not isinstance(data, type):
        return asdict(data)
    elif isinstance(data, dict):
        return data
    elif hasattr(data, "__dict__"):
        return data.__dict__
    return data


class NatsBus:
    """Async wrapper around nats-py for DTO-based JSON pub/sub and request/reply messaging."""

    def __init__(self, url: str = NATS_URL) -> None:
        self.url = url
        self.nc: Optional[NATSClient] = None

    async def connect(self) -> NATSClient:
        """Establishes connection to NATS broker with reconnect retry handling."""
        if self.nc is None or not self.nc.is_connected:
            try:
                self.nc = await nats.connect(self.url, max_reconnect_attempts=10, reconnect_time_wait=1)
                logger.info("Connected to NATS server at %s", self.url)
            except Exception as e:
                logger.error("Failed to connect to NATS at %s: %s", self.url, e)
                raise
        return self.nc

    async def close(self) -> None:
        """Closes NATS connection safely."""
        if self.nc and not self.nc.is_closed:
            await self.nc.drain()
            await self.nc.close()
            self.nc = None

    async def publish(self, subject: str, data: Any) -> None:
        """Publishes DTO instance or JSON payload to NATS subject."""
        if self.nc is None or not self.nc.is_connected:
            await self.connect()
        dict_payload = _to_json_dict(data)
        payload = json.dumps(dict_payload).encode("utf-8")
        await self.nc.publish(subject, payload)

    async def request(self, subject: str, data: Any, timeout: float = 5.0) -> Dict[str, Any]:
        """Sends DTO instance or JSON payload to NATS subject and waits for JSON reply."""
        if self.nc is None or not self.nc.is_connected:
            await self.connect()
        dict_payload = _to_json_dict(data)
        payload = json.dumps(dict_payload).encode("utf-8")
        msg: Msg = await self.nc.request(subject, payload, timeout=timeout)
        return json.loads(msg.data.decode("utf-8"))

    async def subscribe(self, subject: str, cb: Callable[[Any, Optional[str]], Awaitable[Optional[Any]]], dto_class: Optional[Type] = None) -> Any:
        """Subscribes to NATS subject and invokes handler for received messages, converting payloads to DTO dataclasses when requested."""
        if self.nc is None or not self.nc.is_connected:
            await self.connect()

        async def msg_handler(msg: Msg) -> None:
            try:
                raw_data = json.loads(msg.data.decode("utf-8"))
                data = dict_to_dataclass(dto_class, raw_data) if dto_class else raw_data
                reply_to = msg.reply if msg.reply else None
                response = await cb(data, reply_to)
                if reply_to and response is not None:
                    resp_dict = _to_json_dict(response)
                    resp_bytes = json.dumps(resp_dict).encode("utf-8")
                    await self.nc.publish(reply_to, resp_bytes)
            except Exception as e:
                logger.exception("Error processing NATS message on subject %s: %s", subject, e)

        sub = await self.nc.subscribe(subject, cb=msg_handler)
        logger.info("Subscribed to NATS subject: %s", subject)
        return sub
