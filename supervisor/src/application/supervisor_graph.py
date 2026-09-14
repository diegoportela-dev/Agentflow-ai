from operator import add
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from src.application.supervisor_service import SupervisorService


class State(TypedDict):
    query: str
    thread_id: str
    responses: Annotated[list[str], add]


def build_supervisor_graph(
    supervisor_service: SupervisorService,
):
    async def no_de_roteamento(state: State):
        query = state.get("query", "")
        thread_id = state.get("thread_id", "")

        classifications = await supervisor_service.route(
            query=query,
            thread_id=thread_id,
        )

        return [
            Send(
                classification["agent"],
                {
                    "query": classification["query"],
                    "thread_id": thread_id,
                    "responses": [],
                },
            )
            for classification in classifications
        ]

    async def cartao_credito_node(state: State):
        query = state.get("query", "")
        thread_id = state.get("thread_id", "")

        resposta = await supervisor_service.execute_agent(
            agent="cartao_credito",
            query=query,
            thread_id=thread_id,
        )

        return {
            "responses": [resposta]
        }

    async def abrir_conta_node(state: State):
        query = state.get("query", "")
        thread_id = state.get("thread_id", "")

        resposta = await supervisor_service.execute_agent(
            agent="abrir_conta",
            query=query,
            thread_id=thread_id,
        )

        return {
            "responses": [resposta]
        }

    async def suporte_cliente_node(state: State):
        query = state.get("query", "")
        thread_id = state.get("thread_id", "")

        resposta = await supervisor_service.execute_agent(
            agent="suporte_cliente",
            query=query,
            thread_id=thread_id,
        )

        return {
            "responses": [resposta]
        }

    builder = StateGraph(State)

    builder.add_node(
        "cartao_credito",
        cartao_credito_node,
    )

    builder.add_node(
        "abrir_conta",
        abrir_conta_node,
    )

    builder.add_node(
        "suporte_cliente",
        suporte_cliente_node,
    )

    builder.add_conditional_edges(
        START,
        no_de_roteamento,
    )

    builder.add_edge(
        "cartao_credito",
        END,
    )

    builder.add_edge(
        "abrir_conta",
        END,
    )

    builder.add_edge(
        "suporte_cliente",
        END,
    )

    return builder.compile()