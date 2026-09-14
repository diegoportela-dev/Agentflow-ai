import uuid

from ag_ui.core import (
    EventType,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
)
from pydantic import BaseModel

from src.application.supervisor_service import SupervisorService


class StateUpdateEvent(BaseModel):
    type: str = "STATE_UPDATE"
    state: dict


async def stream_supervisor_response(
    input_data,
    supervisor_service: SupervisorService,
):
    messages = input_data.messages

    if not messages:
        user_message = ""
    else:
        user_message = messages[-1].content

    assistant_id = str(uuid.uuid4())

    yield TextMessageStartEvent(
        type=EventType.TEXT_MESSAGE_START,
        message_id=assistant_id,
        role="assistant",
    )

    yield TextMessageContentEvent(
        type=EventType.TEXT_MESSAGE_CONTENT,
        message_id=assistant_id,
        delta="Analisando sua solicitação...\n\n",
    )

    state = {
        "user_query": user_message,
        "responses": [],
    }

    yield StateUpdateEvent(
        state=state
    )

    classifications = await supervisor_service.route(
        query=user_message,
        thread_id=input_data.thread_id,
    )

    agentes = [
        classification["agent"]
        for classification in classifications
    ]

    yield TextMessageContentEvent(
        type=EventType.TEXT_MESSAGE_CONTENT,
        message_id=assistant_id,
        delta=f"Agentes selecionados: {', '.join(agentes)}\n\n",
    )

    state["agents"] = agentes

    yield StateUpdateEvent(
        state=state
    )

    respostas = []

    for classification in classifications:
        agent_name = classification["agent"]
        query = classification["query"]

        yield TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=assistant_id,
            delta=f"Chamando agente: {agent_name}...\n",
        )

        resposta = await supervisor_service.execute_agent(
            agent=agent_name,
            query=query,
            thread_id=input_data.thread_id,
        )

        respostas.append(resposta)

        yield TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=assistant_id,
            delta=f"{agent_name} respondeu\n\n",
        )

        state["responses"].append(
            {
                agent_name: resposta
            }
        )

        yield StateUpdateEvent(
            state=state
        )

    resposta_final = "\n\n".join(respostas)

    yield TextMessageContentEvent(
        type=EventType.TEXT_MESSAGE_CONTENT,
        message_id=assistant_id,
        delta=f"Resultado final:\n\n{resposta_final}",
    )

    yield TextMessageEndEvent(
        type=EventType.TEXT_MESSAGE_END,
        message_id=assistant_id,
    )
