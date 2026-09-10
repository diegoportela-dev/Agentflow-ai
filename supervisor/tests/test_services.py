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
