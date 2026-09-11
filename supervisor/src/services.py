import logging
import uuid

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from typing import TypedDict, Annotated
from operator import add

from ag_ui.core import (
    EventType,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent
)
from pydantic import BaseModel
from src.domain.agent_routing_strategy import AgentRoutingStrategy
from src.infrastructure.dependencies import (
    get_agent_gateway,
    get_agent_routing_strategy,
)
from src.domain.agent_gateway import AgentGateway
from src.application.supervisor_service import SupervisorService

logger = logging.getLogger(__name__)

agent_gateway: AgentGateway = get_agent_gateway()
routing_strategy: AgentRoutingStrategy = get_agent_routing_strategy()

supervisor_service = SupervisorService(
    agent_gateway=agent_gateway,
    routing_strategy=routing_strategy,
)

# -----------------------------
# STATE DO LANGGRAPH
# -----------------------------


class State(TypedDict):
    query: str
    responses: Annotated[list[str], add]

# -----------------------------
# EVENTO PARA STATE UPDATE
# -----------------------------


class StateUpdateEvent(BaseModel):
    type: str = "STATE_UPDATE"
    state: dict

# -----------------------------
# ROUTER
# -----------------------------


async def no_de_roteamento(state: State):
    query = state.get("query", "")

    classifications = await supervisor_service.route(query)

    return [
        Send(
            c["agent"],
            {"query": c["query"]}
        )
        for c in classifications
    ]

# -----------------------------
# NODE CARTAO
# -----------------------------


async def cartao_credito_node(state: State):
    query = state.get("query", "")

    resposta = await supervisor_service.execute_agent(
        "cartao_credito",
        query
    )

    return {"responses": [resposta]}

# -----------------------------
# NODE ABRIR CONTA
# -----------------------------


async def abrir_conta_node(state: State):
    query = state.get("query", "")

    resposta = await supervisor_service.execute_agent(
        "abrir_conta",
        query
    )

    return {"responses": [resposta]}

# -----------------------------
# BUILD DO GRAFO
# -----------------------------
builder = StateGraph(State)
builder.add_node("cartao_credito", cartao_credito_node)
builder.add_node("abrir_conta", abrir_conta_node)
builder.add_conditional_edges(START, no_de_roteamento)
builder.add_edge("cartao_credito", END)
builder.add_edge("abrir_conta", END)
graph = builder.compile()

# -----------------------------
# EXECUTOR DO SUPERVISOR (NORMAL)
# -----------------------------


async def executar_supervisor(texto_usuario: str):
    input_state: State = {"query": texto_usuario, "responses": []}
    result = await graph.ainvoke(input_state)
    return "\n\n".join(result["responses"])

# -----------------------------
# EXECUTOR DO SUPERVISOR (STREAMING COM STATE)
# -----------------------------


async def executar_supervisor_stream(input_data):
    """
    Retorna eventos para AG-UI, incluindo state compartilhado.
    """
    messages = input_data.messages
    if not messages:
        user_message = ""
    else:
        user_message = messages[-1].content

    assistant_id = str(uuid.uuid4())

    # Início da mensagem do assistant
    yield TextMessageStartEvent(
        type=EventType.TEXT_MESSAGE_START,
        message_id=assistant_id,
        role="assistant"
    )

    # Mensagem inicial
    yield TextMessageContentEvent(
        type=EventType.TEXT_MESSAGE_CONTENT,
        message_id=assistant_id,
        delta="Analisando sua solicitação...\n\n"
    )

    # Estado inicial
    state = {"user_query": user_message, "responses": []}
    yield StateUpdateEvent(state=state)

    # Classificação de agentes
    classifications = await supervisor_service.route(
        user_message
    )
    agentes = [c["agent"] for c in classifications]
    yield TextMessageContentEvent(
        type=EventType.TEXT_MESSAGE_CONTENT,
        message_id=assistant_id,
        delta=f"Agentes selecionados: {', '.join(agentes)}\n\n"
    )

    # Atualiza state
    state["agents"] = agentes
    yield StateUpdateEvent(state=state)

    respostas = []
    for c in classifications:
        agent_name = c["agent"]

        yield TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=assistant_id,
            delta=f"Chamando agente: {agent_name}...\n"
        )

        resposta = await supervisor_service.execute_agent(
            agent_name,
            c["query"]
        )
        respostas.append(resposta)

        yield TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=assistant_id,
            delta=f"{agent_name} respondeu\n\n"
        )

        # Atualiza state após cada agente
        state["responses"].append({agent_name: resposta})
        yield StateUpdateEvent(state=state)

    resposta_final = "\n\n".join(respostas)

    yield TextMessageContentEvent(
        type=EventType.TEXT_MESSAGE_CONTENT,
        message_id=assistant_id,
        delta=f"Resultado final:\n\n{resposta_final}"
    )

    # Fim da mensagem
    yield TextMessageEndEvent(
        type=EventType.TEXT_MESSAGE_END,
        message_id=assistant_id
    )