from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from nova_synesis.domain.models import Resource, ResourceState, ResourceType


class ResourceManager:
    def __init__(self) -> None:
        self._resources: dict[int, Resource] = {}
        self._resources_by_type: dict[ResourceType, list[Resource]] = defaultdict(list)

    def register(self, resource: Resource) -> Resource:
        self._resources[resource.resource_id] = resource
        self._resources_by_type[resource.type].append(resource)
        return resource

    def get(self, resource_id: int) -> Resource:
        if resource_id not in self._resources:
            raise KeyError(f"Unknown resource '{resource_id}'")
        return self._resources[resource_id]

    def list(self) -> list[Resource]:
        return list(self._resources.values())

    def resolve_resources(
        self,
        resource_ids: Iterable[int] | None = None,
        resource_types: Iterable[ResourceType] | None = None,
    ) -> list[Resource]:
        resolved: list[Resource] = []
        seen: set[int] = set()
        for resource_id in resource_ids or []:
            resource = self.get(resource_id)
            if resource.resource_id not in seen:
                resolved.append(resource)
                seen.add(resource.resource_id)
        for resource_type in resource_types or []:
            for resource in self._resources_by_type.get(resource_type, []):
                if resource.resource_id not in seen:
                    resolved.append(resource)
                    seen.add(resource.resource_id)
        return resolved

    async def acquire_many(
        self,
        resources: list[Resource],
        timeout: float | None = None,
    ) -> list[Resource]:
        acquired: list[Resource] = []
        try:
            for resource in resources:
                if not await resource.acquire(timeout=timeout):
                    raise RuntimeError(f"Resource {resource.resource_id} could not be acquired")
                acquired.append(resource)
            return acquired
        except Exception:
            await self.release_many(acquired)
            raise

    async def release_many(self, resources: list[Resource]) -> None:
        for resource in reversed(resources):
            await resource.release()

    async def health_report(self) -> list[dict[str, object]]:
        report: list[dict[str, object]] = []
        for resource in self.list():
            healthy = await resource.health_check()
            report.append(
                {
                    "resource_id": resource.resource_id,
                    "type": resource.type.value,
                    "endpoint": resource.endpoint,
                    "healthy": healthy,
                    "state": resource.state.value,
                }
            )
        return report

    def find_fallback_resources(self, required_resources: list[Resource]) -> list[Resource]:
        replacements: list[Resource] = []
        used_ids = {resource.resource_id for resource in required_resources}
        for original in required_resources:
            replacement = next(
                (
                    candidate
                    for candidate in self._resources_by_type.get(original.type, [])
                    if candidate.resource_id not in used_ids
                    and candidate.state != ResourceState.DOWN
                ),
                None,
            )
            if replacement is not None:
                replacements.append(replacement)
                used_ids.add(replacement.resource_id)
            else:
                replacements.append(original)
        return replacements
