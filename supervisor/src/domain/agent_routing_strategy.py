from typing import Protocol


class AgentRoutingStrategy(Protocol):

    async def route(
        self,
        query: str,
        thread_id: str,
    ) -> list[dict]:
        ...