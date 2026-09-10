import pytest

from src.domain.agent_gateway import AgentGateway


class FakeAgentGateway:
    async def send(self, agent: str, message: str) -> str:
        return f"fake:{agent}:{message}"


@pytest.mark.asyncio
async def test_fake_agent_gateway():
    gateway: AgentGateway = FakeAgentGateway()

    response = await gateway.send(
        "abrir_conta",
        "Quero abrir uma conta"
    )

    assert response == "fake:abrir_conta:Quero abrir uma conta"
