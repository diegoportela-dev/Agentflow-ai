from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from starlette.responses import JSONResponse

from executor import SuporteClienteExecutor


# -----------------------
# Skill do agente
# -----------------------
skill = AgentSkill(
    id="suporte_cliente",
    name="Suporte ao Cliente MDBank",
    description=(
        "Ajuda clientes com dúvidas gerais sobre o MDBank, "
        "serviços, atendimento e orientações."
    ),
    tags=[
        "suporte",
        "atendimento",
        "ajuda",
        "duvidas",
        "mdbank",
        "servicos",
    ],
    examples=[
        "preciso de ajuda",
        "como funciona o MDBank?",
        "quais serviços vocês oferecem?",
        "quero falar com o suporte",
        "estou com um problema",
    ],
)


# -----------------------
# Agent Card
# -----------------------
agent_card = AgentCard(
    name="Agente de Suporte ao Cliente MDBank",
    description=(
        "Especialista em atendimento e dúvidas gerais "
        "sobre o MDBank."
    ),
    url="http://suporte_cliente_agent:8000/",
    default_input_modes=["text"],
    default_output_modes=["text"],
    skills=[skill],
    version="1.0.0",
    capabilities=AgentCapabilities(),
)


# -----------------------
# Request Handler
# -----------------------
handler = DefaultRequestHandler(
    agent_executor=SuporteClienteExecutor(),
    task_store=InMemoryTaskStore(),
)


# -----------------------
# A2A Application
# -----------------------
server = A2AStarletteApplication(
    http_handler=handler,
    agent_card=agent_card,
)

app = server.build()


# -----------------------
# Healthcheck
# -----------------------
async def health(request):
    return JSONResponse({"status": "ok"})


app.router.add_route(
    "/health",
    health,
    methods=["GET"],
)
