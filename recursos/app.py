import json
import os
import random
from typing import Any, Dict, Optional

from fastmcp import Context, FastMCP
from fastmcp.prompts import Message
from starlette.requests import Request
from starlette.responses import JSONResponse


mcp = FastMCP("ContaService")

DB_FILE = "/app/db.json"


# -------------------------
# DB
# -------------------------


def load_db() -> Dict[str, Any]:
    if not os.path.exists(DB_FILE):
        return {
            "contas": {},
            "cartoes": {},
        }

    try:
        with open(DB_FILE, "r") as file:
            return json.load(file)
    except Exception:
        return {
            "contas": {},
            "cartoes": {},
        }


def save_db():
    try:
        with open(DB_FILE, "w") as file:
            json.dump(
                {
                    "contas": contas_mdbank,
                    "cartoes": cartoes_mdbank,
                },
                file,
                indent=2,
            )
    except Exception as error:
        print("Erro ao salvar DB:", error)


db = load_db()

contas_mdbank = db.get("contas", {})
cartoes_mdbank = db.get("cartoes", {})


# -------------------------
# CATÁLOGO DE CARTÕES
# Fonte oficial de dados
# -------------------------


CARTOES_DISPONIVEIS = {
    "platinum": {
        "nome": "Platinum",
        "descricao": "Cartão premium do MDBank.",
        "beneficios": [
            "Limite de crédito mais alto",
            "Programa de recompensas premium",
            "Atendimento prioritário",
        ],
    },
    "gold": {
        "nome": "Gold",
        "descricao": "Cartão intermediário do MDBank.",
        "beneficios": [
            "Limite de crédito elevado",
            "Programa de recompensas",
            "Condições diferenciadas para clientes elegíveis",
        ],
    },
    "silver": {
        "nome": "Silver",
        "descricao": (
            "Cartão para clientes que buscam "
            "uma opção simples e acessível."
        ),
        "beneficios": [
            "Limite de crédito moderado",
            "Programa de recompensas básico",
            "Sem benefícios premium",
        ],
    },
    "mdzao": {
        "nome": "Mdzao",
        "descricao": "Cartão de entrada do MDBank.",
        "beneficios": [
            "Limite de crédito inicial",
            "Sem anuidade",
            "Programa de recompensas simplificado",
        ],
    },
}


print("PID:", os.getpid())


# -------------------------
# UTILS
# -------------------------


def extract_resource_data(
    resource_result,
) -> Optional[Dict[str, Any]]:
    if not resource_result:
        return None

    try:
        if not resource_result.contents:
            return None

        raw = resource_result.contents[0].content

        if isinstance(raw, str):
            return json.loads(raw)

        return raw

    except Exception as error:
        print(
            "Erro extract_resource_data:",
            error,
        )

        return None


# -------------------------
# RESOURCES
# -------------------------


@mcp.resource("conta://{cpf}")
async def obter_conta(cpf: str):
    cpf = cpf.strip()

    data = contas_mdbank.get(
        cpf,
        {
            "erro": "Conta não encontrada",
        },
    )

    return json.dumps(data)


@mcp.resource("cartao://{cpf}")
async def obter_cartao(cpf: str):
    cpf = cpf.strip()

    data = cartoes_mdbank.get(
        cpf,
        {
            "erro": "Cartão não encontrado",
        },
    )

    return json.dumps(data)


# -------------------------
# PROMPTS
# -------------------------


@mcp.prompt
def abrir_conta_prompt(
    nome: str,
    cpf: str,
):
    return [
        Message(
            "O cliente deseja abrir conta."
        ),
        Message(
            f"Nome: {nome} | CPF: {cpf}"
        ),
        Message(
            (
                "Verifique se já existe conta "
                "antes de criar."
            ),
            role="assistant",
        ),
    ]


@mcp.prompt
def solicitar_cartao_prompt(
    cpf: str,
    tipo: str,
):
    return [
        Message(
            f"Cliente quer cartão {tipo}"
        ),
        Message(
            f"CPF: {cpf}"
        ),
        Message(
            (
                "Verifique se possui conta "
                "antes de emitir cartão."
            ),
            role="assistant",
        ),
    ]


# -------------------------
# TOOLS - CATÁLOGO
# -------------------------


@mcp.tool(
    description=(
        "Lista os tipos de cartão de crédito "
        "disponíveis no MDBank e seus benefícios"
    ),
    annotations={
        "tags": [
            "cartao",
            "credito",
            "beneficios",
            "tipos",
        ],
        "examples": [
            "quais cartões existem?",
            "quais os benefícios dos cartões?",
            "quais os tipos de cartão?",
            "benefícios do gold",
            "benefícios do platinum",
        ],
    },
)
async def listar_cartoes_disponiveis():
    return {
        "cartoes": list(
            CARTOES_DISPONIVEIS.values()
        )
    }


@mcp.tool(
    description=(
        "Consulta detalhes e benefícios "
        "de um tipo específico de cartão "
        "do MDBank"
    ),
    annotations={
        "tags": [
            "cartao",
            "credito",
            "beneficios",
            "consulta",
        ],
        "examples": [
            "benefícios do gold",
            "como funciona o platinum?",
            "me fale sobre o silver",
            "quero saber sobre o mdzao",
        ],
    },
)
async def consultar_tipo_cartao(
    tipo: str,
):
    tipo_normalizado = (
        tipo
        .strip()
        .lower()
    )

    cartao = CARTOES_DISPONIVEIS.get(
        tipo_normalizado
    )

    if not cartao:
        return {
            "status": "erro",
            "mensagem": (
                "Tipo de cartão não encontrado"
            ),
        }

    return {
        "status": "ok",
        "cartao": cartao,
    }


# -------------------------
# TOOLS - CLIENTE
# -------------------------


@mcp.tool(
    description=(
        "Consulta se um cliente possui "
        "conta bancária a partir do CPF"
    ),
    annotations={
        "tags": [
            "conta",
            "banco",
            "consulta",
            "cpf",
        ],
        "examples": [
            "consultar conta cpf 123",
            "ver se tenho conta",
            "checar conta existente",
            "buscar conta pelo cpf",
            "cliente possui conta?",
        ],
    },
)
async def consultar_conta(
    cpf: str,
    ctx: Context,
):
    resource = await ctx.read_resource(
        f"conta://{cpf}"
    )

    data = extract_resource_data(
        resource
    )

    if not data or "erro" in data:
        return {
            "existe": False,
        }

    return {
        "existe": True,
        "conta": data,
    }


@mcp.tool(
    description=(
        "Consulta se o cliente possui "
        "cartão de crédito"
    ),
    annotations={
        "tags": [
            "cartao",
            "credito",
            "consulta",
        ],
        "examples": [
            "consultar cartao cpf 123",
            "ver cartao do cliente",
            "checar cartao existente",
            "cliente tem cartao?",
        ],
    },
)
async def consultar_cartao(
    cpf: str,
    ctx: Context,
):
    resource = await ctx.read_resource(
        f"cartao://{cpf}"
    )

    data = extract_resource_data(
        resource
    )

    if not data or "erro" in data:
        return {
            "existe": False,
        }

    return {
        "existe": True,
        "cartao": data,
    }


# -------------------------
# TOOLS - CONTA
# -------------------------


@mcp.tool(
    description=(
        "Cria uma conta bancária "
        "ou retorna uma existente"
    ),
    annotations={
        "tags": [
            "conta",
            "criar",
            "banco",
        ],
        "examples": [
            "abrir conta para joao cpf 123",
            "criar conta nova",
            "cadastrar conta",
            "quero abrir uma conta",
            "criar conta com cpf",
        ],
    },
)
async def criar_ou_buscar_conta(
    nome: str,
    cpf: str,
    ctx: Context,
):
    cpf = cpf.strip()

    await ctx.info(
        f"[Conta] Processando CPF {cpf}"
    )

    resource = await ctx.read_resource(
        f"conta://{cpf}"
    )

    data = extract_resource_data(
        resource
    )

    if data and "erro" not in data:
        return {
            "status": "existente",
            "conta": data,
        }

    numero_conta = random.randint(
        10000,
        99999,
    )

    conta = {
        "nome": nome,
        "numero": numero_conta,
        "saldo": 0.0,
    }

    contas_mdbank[cpf] = conta

    save_db()

    return {
        "status": "criada",
        "conta": conta,
    }


# -------------------------
# TOOLS - CARTÃO
# -------------------------


@mcp.tool(
    description=(
        "Solicita emissão de cartão "
        "de crédito para um cliente"
    ),
    annotations={
        "tags": [
            "cartao",
            "credito",
            "emitir",
        ],
        "examples": [
            "quero um cartao",
            "solicitar cartao",
            "emitir cartao de credito",
            "gerar cartao platinum",
            "criar cartao para cpf 123",
        ],
    },
)
async def solicitar_cartao(
    cpf: str,
    tipo: str,
    ctx: Context,
):
    cpf = cpf.strip()

    tipo = (
        tipo
        .strip()
        .lower()
    )

    await ctx.info(
        f"[Cartão] Solicitação para CPF {cpf}"
    )

    # -------------------------
    # Valida tipo do cartão
    # -------------------------

    if tipo not in CARTOES_DISPONIVEIS:
        return {
            "status": "erro",
            "mensagem": (
                "Tipo de cartão inválido. "
                "Opções disponíveis: "
                "platinum, gold, silver ou mdzao."
            ),
        }

    # -------------------------
    # Verifica conta
    # -------------------------

    resource = await ctx.read_resource(
        f"conta://{cpf}"
    )

    conta = extract_resource_data(
        resource
    )

    if not conta or "erro" in conta:
        return {
            "status": "erro",
            "mensagem": (
                "Cliente não possui conta"
            ),
        }

    # -------------------------
    # Verifica cartão existente
    # -------------------------

    resource_cartao = await ctx.read_resource(
        f"cartao://{cpf}"
    )

    cartao_existente = (
        extract_resource_data(
            resource_cartao
        )
    )

    if (
        cartao_existente
        and "erro" not in cartao_existente
    ):
        return {
            "status": "existente",
            "cartao": cartao_existente,
        }

    # -------------------------
    # Criação do cartão
    # -------------------------

    numero_cartao = random.randint(
        100000,
        999999,
    )

    cartao = {
        "numero": numero_cartao,
        "tipo": tipo,
        "limite": random.randint(
            1000,
            5000,
        ),
    }

    cartoes_mdbank[cpf] = cartao

    save_db()

    return {
        "status": "criado",
        "cartao": cartao,
    }


# -------------------------
# TOOLS - PROMPTS
# -------------------------


@mcp.tool(
    description=(
        "Gera um prompt para "
        "abertura de conta"
    ),
    annotations={
        "tags": [
            "prompt",
            "conta",
        ],
        "examples": [
            (
                "gerar prompt de "
                "abertura de conta"
            ),
            (
                "criar mensagem "
                "para abrir conta"
            ),
        ],
    },
)
async def gerar_prompt_abertura(
    nome: str,
    cpf: str,
    ctx: Context,
):
    prompt = await ctx.get_prompt(
        "abrir_conta_prompt",
        {
            "nome": nome,
            "cpf": cpf,
        },
    )

    return [
        message.content
        for message in prompt.messages
    ]


# -------------------------
# /tools
# -------------------------


@mcp.custom_route(
    "/tools",
    methods=["GET"],
)
async def list_tools(
    request: Request,
) -> JSONResponse:
    try:
        result = await mcp.list_tools()

        schema_map = {
            "listar_cartoes_disponiveis": {
                "type": "object",
                "properties": {},
                "required": [],
            },

            "consultar_tipo_cartao": {
                "type": "object",
                "properties": {
                    "tipo": {
                        "type": "string",
                        "description": (
                            "Tipo do cartão: "
                            "platinum, gold, "
                            "silver ou mdzao"
                        ),
                    },
                },
                "required": [
                    "tipo",
                ],
            },

            "consultar_conta": {
                "type": "object",
                "properties": {
                    "cpf": {
                        "type": "string",
                        "description": (
                            "CPF do cliente"
                        ),
                    },
                },
                "required": [
                    "cpf",
                ],
            },

            "consultar_cartao": {
                "type": "object",
                "properties": {
                    "cpf": {
                        "type": "string",
                    },
                },
                "required": [
                    "cpf",
                ],
            },

            "criar_ou_buscar_conta": {
                "type": "object",
                "properties": {
                    "nome": {
                        "type": "string",
                    },
                    "cpf": {
                        "type": "string",
                    },
                },
                "required": [
                    "nome",
                    "cpf",
                ],
            },

            "solicitar_cartao": {
                "type": "object",
                "properties": {
                    "cpf": {
                        "type": "string",
                    },
                    "tipo": {
                        "type": "string",
                        "description": (
                            "Tipo do cartão: "
                            "platinum, gold, "
                            "silver ou mdzao"
                        ),
                    },
                },
                "required": [
                    "cpf",
                    "tipo",
                ],
            },

            "gerar_prompt_abertura": {
                "type": "object",
                "properties": {
                    "nome": {
                        "type": "string",
                    },
                    "cpf": {
                        "type": "string",
                    },
                },
                "required": [
                    "nome",
                    "cpf",
                ],
            },
        }

        tools = []

        for tool in result:
            annotations = getattr(
                tool,
                "annotations",
                None,
            )

            tools.append(
                {
                    "name": tool.name,
                    "description": (
                        tool.description
                        or ""
                    ),
                    "inputSchema": (
                        schema_map.get(
                            tool.name,
                            {},
                        )
                    ),
                    "annotations": {
                        "tags": (
                            getattr(
                                annotations,
                                "tags",
                                [],
                            )
                            if annotations
                            else []
                        ),
                        "examples": (
                            getattr(
                                annotations,
                                "examples",
                                [],
                            )
                            if annotations
                            else []
                        ),
                    },
                }
            )

        return JSONResponse(
            tools
        )

    except Exception as error:
        print(
            "ERRO /tools:",
            error,
        )

        return JSONResponse(
            {
                "error": (
                    "failed to list tools"
                ),
                "details": str(
                    error
                ),
            },
            status_code=500,
        )