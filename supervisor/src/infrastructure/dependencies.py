from src.domain.agent_gateway import AgentGateway
from src.domain.agent_routing_strategy import AgentRoutingStrategy
from src.infrastructure.a2a_agent_gateway import A2AAgentGateway
from src.infrastructure.llm_routing_strategy import LLMRoutingStrategy
from src.infrastructure.settings import settings


def get_agent_gateway() -> AgentGateway:
    agents = {
        "cartao_credito": settings.cartao_credito_agent_url,
        "abrir_conta": settings.abrir_conta_agent_url,
        "suporte_cliente": settings.suporte_cliente_agent_url,
    }

    return A2AAgentGateway(agents)


def get_agent_routing_strategy() -> AgentRoutingStrategy:
    return LLMRoutingStrategy()