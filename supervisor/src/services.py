import logging

from src.application.supervisor_graph import (
    State,
    build_supervisor_graph,
)
from src.application.supervisor_service import SupervisorService
from src.domain.agent_gateway import AgentGateway
from src.domain.agent_routing_strategy import AgentRoutingStrategy
from src.infrastructure.dependencies import (
    get_agent_gateway,
    get_agent_routing_strategy,
)
from src.presentation.agui_stream import (
    stream_supervisor_response,
)

logger = logging.getLogger(__name__)

agent_gateway: AgentGateway = get_agent_gateway()
routing_strategy: AgentRoutingStrategy = get_agent_routing_strategy()

supervisor_service = SupervisorService(
    agent_gateway=agent_gateway,
    routing_strategy=routing_strategy,
)

graph = build_supervisor_graph(
    supervisor_service
)


# -----------------------------
# EXECUTOR DO SUPERVISOR (NORMAL)
# -----------------------------


async def executar_supervisor(texto_usuario: str):
    input_state: State = {"query": texto_usuario, "responses": []}
    result = await graph.ainvoke(input_state)
    return "\n\n".join(result["responses"])

async def executar_supervisor_stream(input_data):
    async for event in stream_supervisor_response(
        input_data=input_data,
        supervisor_service=supervisor_service,
    ):
        yield event