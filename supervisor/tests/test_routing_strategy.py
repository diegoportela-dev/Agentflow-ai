import pytest

from src.domain.agent_routing_strategy import AgentRoutingStrategy


class FakeRoutingStrategy:
    async def route(
        self,
        query: str,
        thread_id: str,
    ) -> list[dict]:
        return [
            {
                "agent": "abrir_conta",
                "query": query,
            }
        ]


class ContextAwareFakeRoutingStrategy:
    async def route(
        self,
        query: str,
        thread_id: str,
    ) -> list[dict]:
        query_normalizada = query.lower()

        if "benefícios de cada um" in query_normalizada:
            return [
                {
                    "agent": "cartao_credito",
                    "query": query,
                }
            ]

        return [
            {
                "agent": "suporte_cliente",
                "query": query,
            }
        ]


@pytest.mark.asyncio
async def test_fake_routing_strategy():
    strategy: AgentRoutingStrategy = FakeRoutingStrategy()

    result = await strategy.route(
        query="Quero abrir uma conta",
        thread_id="thread-1",
    )

    assert result == [
        {
            "agent": "abrir_conta",
            "query": "Quero abrir uma conta",
        }
    ]


@pytest.mark.asyncio
async def test_contextual_follow_up_routes_to_credit_card():
    strategy: AgentRoutingStrategy = (
        ContextAwareFakeRoutingStrategy()
    )

    query = "quais benefícios de cada um?"

    result = await strategy.route(
        query=query,
        thread_id="thread-cartao",
    )

    assert result == [
        {
            "agent": "cartao_credito",
            "query": query,
        }
    ]