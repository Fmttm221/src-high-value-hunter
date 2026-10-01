from abc import ABC, abstractmethod
from typing import Any


class Provider(ABC):
    name: str
    asset_types: list[str]
    requires_key: bool = False
    passive: bool = True

    @abstractmethod
    async def query(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def normalize(
        self,
        raw_items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        raise NotImplementedError
