from src.agents import classifique_intencao_do_usuario
from src.domain.agent_routing_strategy import AgentRoutingStrategy


class LLMRoutingStrategy(AgentRoutingStrategy):
    async def route(self, query: str) -> list[dict]:
        return await classifique_intencao_do_usuario(query)
