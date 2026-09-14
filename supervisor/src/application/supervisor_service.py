import logging

from src.domain.agent_gateway import AgentGateway
from src.domain.agent_routing_strategy import AgentRoutingStrategy

logger = logging.getLogger(__name__)


class SupervisorService:
    def __init__(
        self,
        agent_gateway: AgentGateway,
        routing_strategy: AgentRoutingStrategy,
    ):
        self.agent_gateway = agent_gateway
        self.routing_strategy = routing_strategy

    async def route(
        self,
        query: str,
        thread_id: str,
    ) -> list[dict]:
        classifications = await self.routing_strategy.route(
            query=query,
            thread_id=thread_id,
        )

        logger.info(
            "Classificação: %s",
            classifications,
        )

        return classifications

    async def execute_agent(
        self,
        agent: str,
        query: str,
        thread_id: str,
    ) -> str:
        logger.info(
            "Executando agente %s",
            agent,
        )

        return await self.agent_gateway.send(
            agent=agent,
            message=query,
            thread_id=thread_id,
        )
