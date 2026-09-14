import logging
import uuid

import httpx
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import Message, Part, Role, TextPart

from src.domain.agent_gateway import AgentGateway

logger = logging.getLogger(__name__)


class A2AAgentGateway(AgentGateway):
    def __init__(self, agents: dict[str, str]):
        self.agents = agents
        self.http_client = httpx.AsyncClient(timeout=30)
        self.client_cache = {}

    async def send(self, agent: str, message: str) -> str:
        agent_url = self.agents[agent]

        client = await self._get_client(agent_url)

        msg = Message(
            role=Role.user,
            message_id=str(uuid.uuid4()),
            parts=[
                Part(
                    root=TextPart(
                        text=message
                    )
                )
            ],
        )

        logger.info(
            "Enviando mensagem para agente %s",
            agent
        )

        async for event in client.send_message(msg):
            if isinstance(event, Message):
                for part in event.parts:
                    if part.root.kind == "text":
                        return part.root.text

        return "Sem resposta do agente."

    async def _get_client(self, agent_url: str):
        if agent_url in self.client_cache:
            return self.client_cache[agent_url]

        logger.info(
            "Descobrindo AgentCard em %s",
            agent_url
        )

        resolver = A2ACardResolver(
            httpx_client=self.http_client,
            base_url=agent_url,
        )

        agent_card = await resolver.get_agent_card()

        logger.info(
            "Agent encontrado: %s",
            agent_card.name
        )

        config = ClientConfig(
            httpx_client=self.http_client,
            streaming=False
        )

        factory = ClientFactory(config)

        client = factory.create(agent_card)

        self.client_cache[agent_url] = client

        return client