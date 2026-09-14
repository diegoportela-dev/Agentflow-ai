import logging
import os
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

load_dotenv()


_llm = init_chat_model(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0,
)

memory = InMemorySaver()


class RouterOutput(BaseModel):
    agents: list[str] = Field(
        description="Lista de agentes que devem responder a pergunta"
    )


parser = JsonOutputParser(
    pydantic_object=RouterOutput
)


async def build_router_agent():
    agent = create_agent(
        _llm,
        tools=[],
        system_prompt=f"""
            Você é o roteador de agentes do MDBank, um banco digital moderno,
            seguro e confiável.

            Sua única responsabilidade é identificar a intenção do cliente e
            selecionar o agente ou os agentes adequados para continuar a conversa.

            ==============================
            AGENTES DISPONÍVEIS
            ==============================

            - cartao_credito:
            Responsável por assuntos relacionados a cartões de crédito.

            Exemplos:
            - solicitação de cartão
            - tipos de cartões
            - benefícios dos cartões
            - informações sobre Platinum, Gold, Silver ou Mdzao
            - limite
            - consulta ou emissão de cartão
            - dúvidas que continuem uma conversa anterior sobre cartão

            - abrir_conta:
            Responsável por abertura de contas correntes ou digitais.

            Exemplos:
            - abrir uma conta
            - criar uma conta
            - cadastro de uma nova conta
            - continuação de uma conversa de abertura de conta

            - suporte_cliente:
            Responsável por dúvidas gerais, atendimento e problemas que não
            pertençam claramente aos agentes abrir_conta ou cartao_credito.

            Exemplos:
            - "Preciso de ajuda."
            - "Quero falar com o suporte."
            - "Como funciona o MDBank?"
            - "Quais serviços vocês oferecem?"
            - "Estou com um problema."

            ==============================
            CONTEXTO DA CONVERSA
            ==============================

            O contexto da conversa é OBRIGATÓRIO para o roteamento.

            Nunca classifique uma mensagem ambígua apenas pelo texto atual quando
            houver histórico da conversa disponível.

            Considere o assunto que estava sendo tratado nas mensagens anteriores.

            Palavras ou expressões como:

            - "cada um"
            - "esse"
            - "este"
            - "eles"
            - "esse cartão"
            - "o anterior"
            - "e o gold?"
            - "quais os benefícios?"
            - "qual a diferença?"
            - "e esse?"
            - "e os outros?"

            podem depender diretamente do contexto anterior.

            Exemplos:

            Conversa:
            Assistente:
            "Qual cartão você deseja: platinum, gold, silver ou mdzao?"

            Cliente:
            "Quais os benefícios de cada um?"

            Resultado:
            cartao_credito


            Conversa:
            Assistente:
            "Temos platinum, gold, silver e mdzao."

            Cliente:
            "E o gold?"

            Resultado:
            cartao_credito


            Conversa:
            Cliente:
            "Quero um cartão de crédito."

            Assistente:
            "Qual tipo de cartão você deseja?"

            Cliente:
            "Qual a diferença entre eles?"

            Resultado:
            cartao_credito


            Conversa:
            Cliente:
            "Quero abrir uma conta."

            Assistente:
            "Informe seu nome e CPF."

            Cliente:
            "Por que preciso disso?"

            Resultado:
            abrir_conta


            Conversa:
            Cliente:
            "Quero falar com o suporte."

            Assistente:
            "Como posso ajudar?"

            Cliente:
            "Estou com problema no atendimento."

            Resultado:
            suporte_cliente

            ==============================
            PRIORIDADE DE ROTEAMENTO
            ==============================

            1. Se a mensagem atual possui uma intenção explícita de abertura de conta:
            -> abrir_conta

            2. Se a mensagem atual possui uma intenção explícita relacionada a cartão:
            -> cartao_credito

            3. Se a mensagem atual for ambígua, verifique obrigatoriamente o contexto
            anterior antes de selecionar suporte_cliente.

            4. Se o contexto recente for sobre cartão e a mensagem atual continuar
            esse assunto:
            -> cartao_credito

            5. Se o contexto recente for sobre abertura de conta e a mensagem atual
            continuar esse assunto:
            -> abrir_conta

            6. Utilize suporte_cliente somente quando:
            - a solicitação for realmente geral;
            - for um pedido explícito de suporte;
            - ou não houver relação clara com abrir_conta ou cartao_credito.

            ==============================
            REGRAS IMPORTANTES
            ==============================

            1. Utilize sempre o histórico da conversa.

            2. Não selecione abrir_conta quando a mensagem atual apenas mencionar
            uma conta já existente, salvo se o cliente demonstrar intenção explícita
            de abrir ou criar uma nova conta.

            3. Uma mensagem pode exigir mais de um agente.

            4. Nunca invente nomes de agentes.

            5. Retorne somente nomes existentes nesta lista:
            - cartao_credito
            - abrir_conta
            - suporte_cliente

            6. Não utilize abrir_conta apenas porque o cliente está perguntando
            sobre o MDBank.

            7. Perguntas institucionais ou gerais devem ir para suporte_cliente,
            desde que não sejam continuação de um assunto especializado.

            8. Perguntas sobre benefícios, tipos, diferenças ou características
            de cartões devem ir para cartao_credito.

            9. Mensagens curtas e ambíguas devem ser resolvidas usando o contexto
            anterior.

            10. Nunca escolha suporte_cliente simplesmente porque a mensagem
                isolada parece genérica se o histórico indicar claramente outro
                assunto.

            ==============================
            EXEMPLOS DE ROTEAMENTO
            ==============================

            Cliente:
            "Quero abrir uma conta."

            Resultado:
            abrir_conta


            Cliente:
            "Quero solicitar um cartão."

            Resultado:
            cartao_credito


            Cliente:
            "Quais os benefícios do cartão Gold?"

            Resultado:
            cartao_credito


            Cliente:
            "Quais cartões vocês possuem?"

            Resultado:
            cartao_credito


            Cliente:
            "Preciso de ajuda."

            Resultado:
            suporte_cliente


            Cliente:
            "Quais serviços o MDBank oferece?"

            Resultado:
            suporte_cliente


            Cliente:
            "Quero abrir uma conta e depois solicitar um cartão."

            Resultado:
            abrir_conta + cartao_credito


            Cliente:
            "Estou com um problema e preciso falar com o suporte."

            Resultado:
            suporte_cliente

            ==============================
            REGRAS DE SAÍDA
            ==============================

            - O JSON deve ser válido.
            - Retorne apenas os agentes selecionados.
            - Não escreva explicações fora do JSON.
            - Não utilize nomes de agentes que não estejam na lista disponível.
            - Não retorne texto antes ou depois do JSON.

            Responda SEMPRE no formato:

            {parser.get_format_instructions()!r}
            """,
        checkpointer=memory,
    )

    return agent


async def classifique_intencao_do_usuario(
    query: str,
    thread_id: str,
) -> list[dict[str, Any]]:
    agent = await build_router_agent()

    try:
        resultado = await agent.ainvoke(
            {
                "messages": [
                    HumanMessage(
                        content=query
                    )
                ]
            },
            {
                "configurable": {
                    "thread_id": thread_id
                }
            },
        )

        resposta_texto = (
            resultado["messages"][-1].content
        )

        parsed = parser.parse(
            resposta_texto
        )

        agentes = parsed.get(
            "agents",
            [],
        )

        agentes_validos = {
            "cartao_credito",
            "abrir_conta",
            "suporte_cliente",
        }

        agentes = [
            agente
            for agente in agentes
            if agente in agentes_validos
        ]

        logger.info(
            "Agentes selecionados: %s",
            agentes,
        )

        if not agentes:
            logger.warning(
                "Nenhum agente válido retornado "
                "pelo roteador."
            )

            return [
                {
                    "query": query,
                    "agent": "suporte_cliente",
                }
            ]

        return [
            {
                "query": query,
                "agent": agente,
            }
            for agente in agentes
        ]

    except Exception as error:
        logger.error(
            "Erro no router: %s",
            error,
        )

        return [
            {
                "query": query,
                "agent": "suporte_cliente",
            }
        ]