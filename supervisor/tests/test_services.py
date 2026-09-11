import pytest

import src.services as services


class FakeAgentGateway:
    async def send(self, agent: str, message: str) -> str:
        return f"resposta-{agent}"


@pytest.mark.asyncio
async def test_cartao_credito_node(monkeypatch):
    fake_gateway = FakeAgentGateway()

    monkeypatch.setattr(
        services,
        "agent_gateway",
        fake_gateway
    )

    result = await services.cartao_credito_node(
        {"query": "Quero um cartão"}
    )

    assert result == {
        "responses": ["resposta-cartao_credito"]
    }


@pytest.mark.asyncio
async def test_abrir_conta_node(monkeypatch):
    fake_gateway = FakeAgentGateway()

    monkeypatch.setattr(
        services,
        "agent_gateway",
        fake_gateway
    )

    result = await services.abrir_conta_node(
        {"query": "Quero abrir uma conta"}
    )

    assert result == {
        "responses": ["resposta-abrir_conta"]
    }

@pytest.mark.asyncio
async def test_no_de_roteamento(monkeypatch):
    class FakeRoutingStrategy:
        async def route(self, query: str) -> list[dict]:
            return [
                {
                    "agent": "abrir_conta",
                    "query": query,
                }
            ]

    monkeypatch.setattr(
        services,
        "routing_strategy",
        FakeRoutingStrategy()
    )

    result = await services.no_de_roteamento(
        {
            "query": "Quero abrir uma conta",
            "responses": [],
        }
    )

    assert len(result) == 1
    assert result[0].node == "abrir_conta"
    assert result[0].arg == {
        "query": "Quero abrir uma conta"
    }
