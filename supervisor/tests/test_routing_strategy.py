import pytest

from src.domain.agent_routing_strategy import AgentRoutingStrategy


class FakeRoutingStrategy:
    async def route(self, query: str) -> list[dict]:
        return [
            {
                "agent": "abrir_conta",
                "query": query,
            }
        ]


@pytest.mark.asyncio
async def test_fake_routing_strategy():
    strategy: AgentRoutingStrategy = FakeRoutingStrategy()

    result = await strategy.route("Quero abrir uma conta")

    assert result == [
        {
            "agent": "abrir_conta",
            "query": "Quero abrir uma conta",
        }
    ]
