import pytest

from src.application.supervisor_graph import build_supervisor_graph


class FakeSupervisorService:
    async def route(
        self,
        query: str,
        thread_id: str,
    ) -> list[dict]:
        return [
            {
                "agent": "abrir_conta",
                "query": query,
            }
        ]

    async def execute_agent(
        self,
        agent: str,
        query: str,
        thread_id: str,
    ) -> str:
        return f"resposta-{agent}"


@pytest.mark.asyncio
async def test_supervisor_graph_routes_and_executes_agent():
    graph = build_supervisor_graph(
        FakeSupervisorService()
    )

    result = await graph.ainvoke(
        {
            "query": "Quero abrir uma conta",
            "thread_id": "test-thread-1",
            "responses": [],
        }
    )

    assert result["responses"] == [
        "resposta-abrir_conta"
    ]


@pytest.mark.asyncio
async def test_supervisor_graph_routes_to_support():
    class FakeSupervisorService:
        async def route(
            self,
            query: str,
            thread_id: str,
        ) -> list[dict]:
            return [
                {
                    "agent": "suporte_cliente",
                    "query": query,
                }
            ]

        async def execute_agent(
            self,
            agent: str,
            query: str,
            thread_id: str,
        ) -> str:
            return f"resposta-{agent}"

    graph = build_supervisor_graph(
        FakeSupervisorService()
    )

    result = await graph.ainvoke(
        {
            "query": "Quero falar com o suporte",
            "thread_id": "test-thread-2",
            "responses": [],
        }
    )

    assert result["responses"] == [
        "resposta-suporte_cliente"
    ]