from __future__ import annotations

import asyncio
import json
import math
import sqlite3
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nova_synesis.domain.models import MemoryType


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


@dataclass(slots=True)
class MemorySearchHit:
    key: str
    value: Any
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "score": self.score,
            "metadata": self.metadata,
        }


class MemorySystem(ABC):
    def __init__(
        self,
        memory_id: str,
        memory_type: MemoryType,
        backend: str,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.memory_id = memory_id
        self.type = memory_type
        self.backend = backend
        self.config = config or {}

    @abstractmethod
    async def store(self, key: str, value: Any) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def retrieve(self, key: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def search(self, query: Any, limit: int = 5) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def persist(self) -> None:
        raise NotImplementedError


class ShortTermMemorySystem(MemorySystem):
    def __init__(
        self,
        memory_id: str,
        backend: str = "memory",
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(memory_id, MemoryType.SHORT_TERM, backend, config)
        self._lock = asyncio.Lock()
        self._values: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._max_items = int(self.config.get("max_items", 512))
        if self.backend != "memory":
            self._load_from_disk()

    def _load_from_disk(self) -> None:
        path = Path(self.backend)
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            for key, entry in payload.items():
                self._values[key] = entry

    async def store(self, key: str, value: Any) -> dict[str, Any]:
        async with self._lock:
            self._values[key] = {"value": value, "stored_at": utcnow_iso()}
            self._values.move_to_end(key)
            while len(self._values) > self._max_items:
                self._values.popitem(last=False)
        return {"memory_id": self.memory_id, "key": key, "stored": True}

    async def retrieve(self, key: str) -> Any:
        async with self._lock:
            entry = self._values.get(key)
            if entry is None:
                return None
            self._values.move_to_end(key)
            return entry["value"]

    async def search(self, query: Any, limit: int = 5) -> list[dict[str, Any]]:
        async with self._lock:
            hits: list[MemorySearchHit] = []
            for key, entry in self._values.items():
                value = entry["value"]
                score = self._score_value(value, query)
                if score > 0:
                    hits.append(MemorySearchHit(key=key, value=value, score=score))
            ordered = sorted(hits, key=lambda hit: hit.score, reverse=True)[:limit]
            return [hit.as_dict() for hit in ordered]

    def _score_value(self, value: Any, query: Any) -> float:
        if isinstance(query, str):
            haystack = json.dumps(value, ensure_ascii=False)
            return 1.0 if query.lower() in haystack.lower() else 0.0
        embedding = self._extract_embedding(value)
        if isinstance(query, list) and embedding:
            return cosine_similarity(query, embedding)
        return 1.0 if value == query else 0.0

    @staticmethod
    def _extract_embedding(value: Any) -> list[float] | None:
        if isinstance(value, dict):
            embedding = value.get("embedding")
            if isinstance(embedding, list):
                return [float(component) for component in embedding]
        return None

    async def persist(self) -> None:
        if self.backend == "memory":
            return
        async with self._lock:
            path = Path(self.backend)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(self._values, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )


class LongTermMemorySystem(MemorySystem):
    def __init__(
        self,
        memory_id: str,
        backend: str,
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(memory_id, MemoryType.LONG_TERM, backend, config)
        Path(self.backend).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.backend, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._lock = asyncio.Lock()
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS long_term_memory (
                memory_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value_json TEXT NOT NULL,
                metadata_json TEXT,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (memory_id, key)
            )
            """
        )
        self._connection.commit()

    async def store(self, key: str, value: Any) -> dict[str, Any]:
        payload = value.get("value") if isinstance(value, dict) and "value" in value else value
        metadata = value.get("metadata", {}) if isinstance(value, dict) else {}
        async with self._lock:
            self._connection.execute(
                """
                INSERT INTO long_term_memory (memory_id, key, value_json, metadata_json, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(memory_id, key) DO UPDATE SET
                    value_json = excluded.value_json,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    self.memory_id,
                    key,
                    json.dumps(payload, ensure_ascii=False, default=str),
                    json.dumps(metadata, ensure_ascii=False, default=str),
                    utcnow_iso(),
                ),
            )
            self._connection.commit()
        return {"memory_id": self.memory_id, "key": key, "stored": True}

    async def retrieve(self, key: str) -> Any:
        async with self._lock:
            row = self._connection.execute(
                "SELECT value_json FROM long_term_memory WHERE memory_id = ? AND key = ?",
                (self.memory_id, key),
            ).fetchone()
        return json.loads(row["value_json"]) if row else None

    async def search(self, query: Any, limit: int = 5) -> list[dict[str, Any]]:
        async with self._lock:
            rows = self._connection.execute(
                "SELECT key, value_json, metadata_json FROM long_term_memory WHERE memory_id = ?",
                (self.memory_id,),
            ).fetchall()
        hits: list[MemorySearchHit] = []
        for row in rows:
            value = json.loads(row["value_json"])
            metadata = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
            score = 0.0
            if isinstance(query, str):
                score = 1.0 if query.lower() in json.dumps(value).lower() else 0.0
            elif value == query:
                score = 1.0
            elif isinstance(query, list) and isinstance(value, dict) and isinstance(value.get("embedding"), list):
                score = cosine_similarity(query, value["embedding"])
            if score > 0:
                hits.append(MemorySearchHit(key=row["key"], value=value, metadata=metadata, score=score))
        ordered = sorted(hits, key=lambda hit: hit.score, reverse=True)[:limit]
        return [hit.as_dict() for hit in ordered]

    async def persist(self) -> None:
        async with self._lock:
            self._connection.commit()


class VectorMemorySystem(MemorySystem):
    def __init__(
        self,
        memory_id: str,
        backend: str,
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(memory_id, MemoryType.VECTOR, backend, config)
        Path(self.backend).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.backend, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._lock = asyncio.Lock()
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS vector_memory (
                memory_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value_json TEXT NOT NULL,
                embedding_json TEXT NOT NULL,
                metadata_json TEXT,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (memory_id, key)
            )
            """
        )
        self._connection.commit()

    async def store(self, key: str, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict) or "embedding" not in value:
            raise ValueError("Vector memory expects a dict value containing an 'embedding' field")
        embedding = [float(component) for component in value["embedding"]]
        payload = value.get("value", value)
        metadata = value.get("metadata", {})
        async with self._lock:
            self._connection.execute(
                """
                INSERT INTO vector_memory (memory_id, key, value_json, embedding_json, metadata_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(memory_id, key) DO UPDATE SET
                    value_json = excluded.value_json,
                    embedding_json = excluded.embedding_json,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    self.memory_id,
                    key,
                    json.dumps(payload, ensure_ascii=False, default=str),
                    json.dumps(embedding),
                    json.dumps(metadata, ensure_ascii=False, default=str),
                    utcnow_iso(),
                ),
            )
            self._connection.commit()
        return {"memory_id": self.memory_id, "key": key, "stored": True}

    async def retrieve(self, key: str) -> Any:
        async with self._lock:
            row = self._connection.execute(
                "SELECT value_json, embedding_json, metadata_json FROM vector_memory WHERE memory_id = ? AND key = ?",
                (self.memory_id, key),
            ).fetchone()
        if row is None:
            return None
        return {
            "value": json.loads(row["value_json"]),
            "embedding": json.loads(row["embedding_json"]),
            "metadata": json.loads(row["metadata_json"]) if row["metadata_json"] else {},
        }

    async def search(self, query: Any, limit: int = 5) -> list[dict[str, Any]]:
        if not isinstance(query, list):
            raise ValueError("Vector memory search expects a vector query list")
        normalized_query = [float(component) for component in query]
        async with self._lock:
            rows = self._connection.execute(
                "SELECT key, value_json, embedding_json, metadata_json FROM vector_memory WHERE memory_id = ?",
                (self.memory_id,),
            ).fetchall()
        hits: list[MemorySearchHit] = []
        for row in rows:
            embedding = json.loads(row["embedding_json"])
            score = cosine_similarity(normalized_query, embedding)
            if score > 0:
                hits.append(
                    MemorySearchHit(
                        key=row["key"],
                        value=json.loads(row["value_json"]),
                        metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else {},
                        score=score,
                    )
                )
        ordered = sorted(hits, key=lambda hit: hit.score, reverse=True)[:limit]
        return [hit.as_dict() for hit in ordered]

    async def persist(self) -> None:
        async with self._lock:
            self._connection.commit()


class MemorySystemFactory:
    @staticmethod
    def create(
        memory_id: str,
        memory_type: MemoryType,
        backend: str,
        config: dict[str, Any] | None = None,
    ) -> MemorySystem:
        if memory_type == MemoryType.SHORT_TERM:
            return ShortTermMemorySystem(memory_id=memory_id, backend=backend, config=config)
        if memory_type == MemoryType.LONG_TERM:
            return LongTermMemorySystem(memory_id=memory_id, backend=backend, config=config)
        if memory_type == MemoryType.VECTOR:
            return VectorMemorySystem(memory_id=memory_id, backend=backend, config=config)
        raise ValueError(f"Unsupported memory type '{memory_type}'")


class MemoryManager:
    def __init__(self) -> None:
        self._systems: dict[str, MemorySystem] = {}

    def register(self, system: MemorySystem) -> MemorySystem:
        self._systems[system.memory_id] = system
        return system

    def get(self, memory_id: str) -> MemorySystem:
        if memory_id not in self._systems:
            raise KeyError(f"Unknown memory system '{memory_id}'")
        return self._systems[memory_id]

    def list(self) -> list[MemorySystem]:
        return list(self._systems.values())

    async def store(self, memory_id: str, key: str, value: Any) -> dict[str, Any]:
        return await self.get(memory_id).store(key, value)

    async def retrieve(self, memory_id: str, key: str) -> Any:
        return await self.get(memory_id).retrieve(key)

    async def search(self, memory_id: str, query: Any, limit: int = 5) -> list[dict[str, Any]]:
        return await self.get(memory_id).search(query, limit=limit)

    async def persist_all(self) -> None:
        for system in self._systems.values():
            await system.persist()
