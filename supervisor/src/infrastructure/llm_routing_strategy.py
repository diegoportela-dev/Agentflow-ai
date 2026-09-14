from src.agents import classifique_intencao_do_usuario
from src.domain.agent_routing_strategy import AgentRoutingStrategy


class LLMRoutingStrategy(AgentRoutingStrategy):

    async def route(
        self,
        query: str,
        thread_id: str,
    ) -> list[dict]:
        return await classifique_intencao_do_usuario(
            query=query,
            thread_id=thread_id,
        )