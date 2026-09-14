from typing import Protocol


class AgentGateway(Protocol):
    async def send(
        self,
        agent: str,
        message: str,
        thread_id: str,
    ) -> str:
        ...