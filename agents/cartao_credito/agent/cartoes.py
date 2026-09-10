from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import InMemorySaver
import os

load_dotenv()

_llm = init_chat_model(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.3,
)

client = MultiServerMCPClient(
    {
        "conta": {
            "transport": "http",
            "url": "http://recursos:8000/mcp_gateway",
        }
    }
)

memory = InMemorySaver()

agent = None


async def build_cartao_agent():
    tools = await client.get_tools()

    agent_cartoes = create_agent(
        _llm,
        tools=tools,
        system_prompt=(
            "Você é especialista em cartões do MDBank.\n\n"

            "Tipos disponíveis: platinum, gold, silver, mdzao.\n\n"

            "==============================\n"
            "REGRAS OBRIGATÓRIAS (CRÍTICO)\n"
            "==============================\n"
            "1. Você DEVE obrigatoriamente chamar a tool consultar_conta\n"
            "2. Você NÃO pode responder sem verificar no sistema\n"
            "3. Você NÃO pode assumir se o cliente tem conta\n\n"

            "==============================\n"
            "FLUXO\n"
            "==============================\n"

            "PASSO 1: \n"
            "-> Identificar CPF (usar memória se já tiver)\n"
            "-> Se não tiver CPF, pedir ao cliente\n\n"

            "PASSO 2: \n"
            "-> Chamar consultar_conta\n\n"

            "PASSO 3:\n"
            "-> Se existe = False:\n"
            "    - Informar que não possui conta\n"
            "    - Oferecer abrir conta\n"
            "    - NÃO solicitar cartão\n\n"

            "-> Se existe = True\n"
            "- Se existe = True:\n"
            "  - Verificar se o cliente informou o tipo do cartão.\n"
            "  - Se não informou, perguntar qual deseja: platinum, gold, silver ou mdzao.\n"
            "  - Encerrar a resposta e aguardar a escolha.\n"
            "  - Somente após o cliente escolher, chamar solicitar_cartao.\n"

            "Nunca escolha um tipo automaticamente.\n\n"

            "==============================\n"
            "REGRAS GERAIS\n"
            "==============================\n"
            "- Sempre use tools\n"
            "- Nunca invente dados\n"
            "- Use memória para recuperar CPF\n"
            "- Nunca pule etapas\n\n"

            "==============================\n"
            "ERROS\n"
            "==============================\n"
            "- Use mensagem da tool\n"
            "- Explique claramente\n"
        ),
        checkpointer=memory
    )

    return agent_cartoes

async def run_agent(mensagem: str, thread_id: str = "1"):
    global agent

    if not agent:
        agent = await build_cartao_agent()

    resultado = await agent.ainvoke(
        {
            "messages": [
                HumanMessage(content=mensagem)
            ]
        },
        {
            "configurable": {
                "thread_id": thread_id
            }
        }
    )

    return resultado["messages"][-1].content
