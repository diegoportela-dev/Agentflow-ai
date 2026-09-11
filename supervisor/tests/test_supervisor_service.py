import pytest

from src.application.supervisor_service import SupervisorService


class FakeAgentGateway:
    async def send(self, agent: str, message: str) -> str:
        return f"resposta-{agent}-{message}"


class FakeRoutingStrategy:
    async def route(self, query: str) -> list[dict]:
        return [
            {
                "agent": "abrir_conta",
                "query": query,
            }
        ]


@pytest.mark.asyncio
async def test_route():
    service = SupervisorService(
        agent_gateway=FakeAgentGateway(),
        routing_strategy=FakeRoutingStrategy(),
    )

    result = await service.route(
        "Quero abrir uma conta"
    )

    assert result == [
        {
            "agent": "abrir_conta",
            "query": "Quero abrir uma conta",
        }
    ]


@pytest.mark.asyncio
async def test_execute_agent():
    service = SupervisorService(
        agent_gateway=FakeAgentGateway(),
        routing_strategy=FakeRoutingStrategy(),
    )

    result = await service.execute_agent(
        "cartao_credito",
        "Quero um cartão"
    )

    assert result == (
        "resposta-cartao_credito-Quero um cartão"
    )
