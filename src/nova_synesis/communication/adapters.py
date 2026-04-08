from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx
import websockets

from nova_synesis.domain.models import ProtocolType


class CommunicationAdapter:
    def __init__(
        self,
        protocol: ProtocolType,
        endpoint: str,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.protocol = protocol
        self.endpoint = endpoint
        self.config = config or {}

    async def send(self, message: Any) -> Any:
        raise NotImplementedError

    async def receive(self) -> Any:
        raise NotImplementedError

    async def close(self) -> None:
        return None


class RestCommunicationAdapter(CommunicationAdapter):
    def __init__(self, endpoint: str, config: dict[str, Any] | None = None) -> None:
        super().__init__(ProtocolType.REST, endpoint, config)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers=self.config.get("headers"),
                timeout=float(self.config.get("timeout_s", 10.0)),
            )
        return self._client

    async def send(self, message: Any) -> Any:
        payload = message if isinstance(message, dict) else {"message": message}
        url = payload.get("url", self.endpoint)
        method = str(payload.get("method", self.config.get("method", "POST"))).upper()
        client = await self._get_client()
        response = await client.request(
            method,
            url,
            json=payload.get("json", payload if method != "GET" else None),
            params=payload.get("params"),
            headers=payload.get("headers"),
            data=payload.get("data"),
        )
        response.raise_for_status()
        try:
            body = response.json()
        except ValueError:
            body = response.text
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": body,
        }

    async def receive(self) -> Any:
        client = await self._get_client()
        receive_url = self.config.get("receive_url", self.endpoint)
        response = await client.get(receive_url, params=self.config.get("receive_params"))
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            return response.text

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


class WebSocketCommunicationAdapter(CommunicationAdapter):
    def __init__(self, endpoint: str, config: dict[str, Any] | None = None) -> None:
        super().__init__(ProtocolType.WEBSOCKET, endpoint, config)
        self._connection: Any = None
        self._connect_lock = asyncio.Lock()

    async def _get_connection(self) -> Any:
        if self._connection is None:
            async with self._connect_lock:
                if self._connection is None:
                    self._connection = await websockets.connect(
                        self.endpoint,
                        open_timeout=float(self.config.get("timeout_s", 10.0)),
                        max_size=int(self.config.get("max_message_bytes", 1_048_576)),
                    )
        return self._connection

    async def send(self, message: Any) -> Any:
        connection = await self._get_connection()
        encoded = (
            message
            if isinstance(message, (str, bytes))
            else json.dumps(message, default=str)
        )
        await connection.send(encoded)
        return {"sent": True, "endpoint": self.endpoint}

    async def receive(self) -> Any:
        connection = await self._get_connection()
        payload = await connection.recv()
        if isinstance(payload, bytes):
            return payload
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return payload

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()
            self._connection = None


class MessageQueueCommunicationAdapter(CommunicationAdapter):
    _queues: dict[str, asyncio.Queue[Any]] = {}
    _registry_lock = asyncio.Lock()

    def __init__(self, endpoint: str, config: dict[str, Any] | None = None) -> None:
        super().__init__(ProtocolType.MESSAGE_QUEUE, endpoint, config)

    async def _get_queue(self, endpoint: str | None = None) -> asyncio.Queue[Any]:
        resolved_endpoint = endpoint or self.endpoint
        async with self._registry_lock:
            queue = self._queues.get(resolved_endpoint)
            if queue is None:
                queue = asyncio.Queue(maxsize=int(self.config.get("maxsize", 0)))
                self._queues[resolved_endpoint] = queue
            return queue

    async def send(self, message: Any) -> Any:
        target_endpoint = None
        if isinstance(message, dict):
            target_endpoint = message.get("target_endpoint")
        target_endpoint = target_endpoint or self.config.get("target_endpoint") or self.endpoint
        queue = await self._get_queue(target_endpoint)
        await queue.put(message)
        return {"queued": True, "endpoint": target_endpoint, "queue_size": queue.qsize()}

    async def receive(self) -> Any:
        queue = await self._get_queue(self.endpoint)
        timeout_s = self.config.get("receive_timeout_s")
        if timeout_s is None:
            return await queue.get()
        return await asyncio.wait_for(queue.get(), timeout=float(timeout_s))


class CommunicationAdapterFactory:
    @staticmethod
    def create(
        protocol: ProtocolType,
        endpoint: str,
        config: dict[str, Any] | None = None,
    ) -> CommunicationAdapter:
        if protocol == ProtocolType.REST:
            return RestCommunicationAdapter(endpoint, config)
        if protocol == ProtocolType.WEBSOCKET:
            return WebSocketCommunicationAdapter(endpoint, config)
        if protocol == ProtocolType.MESSAGE_QUEUE:
            return MessageQueueCommunicationAdapter(endpoint, config)
        raise ValueError(f"Unsupported protocol '{protocol}'")
