from src.domain.agent_gateway import AgentGateway
from src.domain.agent_routing_strategy import AgentRoutingStrategy
from src.infrastructure.a2a_agent_gateway import A2AAgentGateway
from src.infrastructure.llm_routing_strategy import LLMRoutingStrategy


AGENTS = {
    "cartao_credito": "http://cartao_credito_agent:8000",
    "abrir_conta": "http://abrir_conta_agent:8000",
}


def get_agent_gateway() -> AgentGateway:
    return A2AAgentGateway(AGENTS)


def get_agent_routing_strategy() -> AgentRoutingStrategy:
    return LLMRoutingStrategy()