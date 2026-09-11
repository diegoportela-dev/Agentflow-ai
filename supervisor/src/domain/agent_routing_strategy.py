from typing import Protocol


class AgentRoutingStrategy(Protocol):
    async def route(self, query: str) -> list[dict]:
        ...
