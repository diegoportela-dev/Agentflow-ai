import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

from agent.suporte import run_agent

logger = logging.getLogger("a2a")


class SuporteClienteExecutor(AgentExecutor):

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        logger.info(
            "agent.execute.suporte_cliente"
        )

        user_text = context.get_user_input()

        thread_id = self._get_thread_id(
            context
        )

        logger.info(
            "suporte_cliente thread_id=%s",
            thread_id,
        )

        response = await run_agent(
            message=user_text,
            thread_id=thread_id,
        )

        await event_queue.enqueue_event(
            new_agent_text_message(
                response
            )
        )

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        raise NotImplementedError(
            "Cancelamento não implementado."
        )

    @staticmethod
    def _get_thread_id(
        context: RequestContext,
    ) -> str:
        message = context.message

        if (
            message
            and message.metadata
            and message.metadata.get("thread_id")
        ):
            return str(
                message.metadata["thread_id"]
            )

        if context.context_id:
            return str(context.context_id)

        return "default"