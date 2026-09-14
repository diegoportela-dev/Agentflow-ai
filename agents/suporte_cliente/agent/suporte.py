import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import ChatOpenAI


load_dotenv()


SYSTEM_PROMPT = """
Você é um agente de suporte ao cliente do MDBank.

Sua responsabilidade é ajudar clientes com dúvidas gerais sobre o banco,
serviços oferecidos, canais de atendimento e orientações básicas.

Você NÃO deve executar ações de abertura de conta ou emissão de cartão.
Quando identificar que o usuário deseja abrir uma conta ou solicitar
um cartão de crédito, oriente que a solicitação será direcionada ao
agente especializado.

Responda de forma clara, objetiva e cordial.
"""


def create_support_agent():
    model = ChatOpenAI(
        model=os.getenv(
            "OPENAI_MODEL",
            "gpt-4o-mini",
        ),
        temperature=0,
    )

    return create_agent(
        model=model,
        tools=[],
        system_prompt=SYSTEM_PROMPT,
    )


agent = create_support_agent()


async def run_agent(
    message: str,
    thread_id: str,
):
    global agent

    if not agent:
        agent = await build_support_agent()

    resultado = await agent.ainvoke(
        {
            "messages": [
                HumanMessage(content=message)
            ]
        },
        {
            "configurable": {
                "thread_id": thread_id
            }
        }
    )

    return resultado["messages"][-1].content