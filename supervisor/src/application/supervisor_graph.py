from operator import add
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from src.application.supervisor_service import SupervisorService


class State(TypedDict):
    query: str
    responses: Annotated[list[str], add]


def build_supervisor_graph(
    supervisor_service: SupervisorService,
):
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

    async def cartao_credito_node(state: State):
        query = state.get("query", "")

        resposta = await supervisor_service.execute_agent(
            "cartao_credito",
            query
        )

        return {
            "responses": [resposta]
        }

    async def abrir_conta_node(state: State):
        query = state.get("query", "")

        resposta = await supervisor_service.execute_agent(
            "abrir_conta",
            query
        )

        return {
            "responses": [resposta]
        }

    builder = StateGraph(State)

    builder.add_node(
        "cartao_credito",
        cartao_credito_node
    )

    builder.add_node(
        "abrir_conta",
        abrir_conta_node
    )

    builder.add_conditional_edges(
        START,
        no_de_roteamento
    )

    builder.add_edge(
        "cartao_credito",
        END
    )

    builder.add_edge(
        "abrir_conta",
        END
    )

    return builder.compile()
