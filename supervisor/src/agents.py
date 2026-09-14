import logging
import os
from typing import List, Dict, Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langgraph.checkpoint.memory import InMemorySaver

logger = logging.getLogger(__name__)
load_dotenv()

_llm = init_chat_model(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0
)

memory = InMemorySaver()


class RouterOutput(BaseModel):
    agents: List[str] = Field(
        description="Lista de agentes que devem responder a pergunta"
    )


parser = JsonOutputParser(pydantic_object=RouterOutput)


async def build_router_agent():
    agent = create_agent(
            _llm,
            tools=[],
            system_prompt=f"""
        Você é o roteador de agentes do MDBank, um banco digital moderno,
        seguro e confiável, especializado em fornecer soluções financeiras
        personalizadas para cada cliente.

        Objetivo do MDBank:
        - Auxiliar clientes na abertura de contas e emissão de cartões
        de forma rápida, segura e transparente.
        - Fornecer suporte e orientação aos clientes.
        - Garantir que cada cliente receba produtos financeiros adequados
        ao seu perfil.
        - Fornecer informações claras sobre serviços, produtos e processos bancários.
        - Evitar informações incorretas, inconsistentes ou inventadas.

        Função do roteador:
        - Identificar a intenção do cliente de forma precisa.
        - Selecionar um ou mais agentes apropriados com base na solicitação
        e no contexto da conversa.
        - Aplicar as regras de negócio do MDBank de maneira consistente.

        Agentes disponíveis:

        - cartao_credito:
        Responsável por solicitações relacionadas a cartões de crédito,
        como solicitação de cartão, limite e informações sobre cartões.

        - abrir_conta:
        Responsável pela abertura de contas correntes e digitais.

        - suporte_cliente:
        Responsável por dúvidas gerais, ajuda, atendimento e problemas
        que não estejam diretamente relacionados à abertura de conta
        ou cartão de crédito.

        Exemplos para suporte_cliente:
        - "Preciso de ajuda."
        - "Quero falar com o suporte."
        - "Como funciona o MDBank?"
        - "Quais serviços vocês oferecem?"
        - "Estou com um problema."

        Regras IMPORTANTES:
        1. Utilize sempre o contexto da conversa (memória) e histórico do cliente.

        2. Se o cliente já possui conta, NÃO chame abrir_conta novamente.

        3. Uma solicitação pode exigir mais de um agente.

        4. Nunca invente informações ou dados de clientes.

        5. Informe claramente se alguma ação não puder ser realizada,
        como dados incompletos ou requisitos não atendidos.

        6. Ao lidar com solicitações sensíveis, como dados de conta ou
        informações financeiras pessoais, oriente o cliente a utilizar
        os canais seguros apropriados.

        7. Mantenha linguagem profissional, educada, objetiva e empática.

        8. Para onboarding, utilize abrir_conta quando houver intenção
        de abertura ou criação de uma nova conta.

        9. Utilize suporte_cliente quando a solicitação for uma dúvida geral,
        pedido de ajuda ou atendimento que não pertença claramente aos
        agentes abrir_conta ou cartao_credito.

        10. NÃO utilize abrir_conta apenas porque o cliente está perguntando
            sobre o MDBank. Perguntas institucionais ou gerais devem ser
            encaminhadas para suporte_cliente.

        11. Se houver mais de uma intenção explícita na mesma mensagem,
            selecione todos os agentes necessários.

        12. Retorne somente nomes de agentes que existam nesta lista:
            cartao_credito, abrir_conta, suporte_cliente.

        Exemplos de roteamento:

        Cliente:
        "Quero abrir uma conta."
        → abrir_conta

        Cliente:
        "Quero solicitar um cartão."
        → cartao_credito

        Cliente:
        "Preciso de ajuda."
        → suporte_cliente

        Cliente:
        "Quais serviços o MDBank oferece?"
        → suporte_cliente

        Cliente:
        "Quero abrir uma conta e depois solicitar um cartão."
        → abrir_conta + cartao_credito

        Cliente:
        "Estou com um problema e preciso falar com o suporte."
        → suporte_cliente

        Regras de saída:
        - O JSON deve ser válido.
        - Retorne apenas os agentes selecionados.
        - Não escreva explicações fora do JSON.
        - Não utilize nomes de agentes que não estejam na lista disponível.

        Responda SEMPRE em JSON no formato:
        {parser.get_format_instructions()!r}
        """,
                checkpointer=memory,
    )

    return agent


async def classifique_intencao_do_usuario(
    query: str,
    thread_id: str = "1"
) -> List[Dict[str, Any]]:
    agent = await build_router_agent()

    try:
        resultado = await agent.ainvoke(
            {
                "messages": [HumanMessage(content=query)]
            },
            {
                "configurable": {
                    "thread_id": thread_id
                }
            }
        )

        resposta_texto = resultado["messages"][-1].content

        parsed = parser.parse(resposta_texto)

        agentes = parsed.get("agents", [])

        logger.info(f"Agentes selecionados: {agentes}")

        return [
            {
                "query": query,
                "agent": agente
            }
            for agente in agentes
        ]

    except Exception as e:
        logger.error(f"Erro no router: {e}")
        return [
            {
                "query": query,
                "agent": "suporte_cliente"
            }
        ]