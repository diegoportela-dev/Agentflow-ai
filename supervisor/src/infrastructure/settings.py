import os


class Settings:
    def __init__(self):
        self.cartao_credito_agent_url = os.getenv(
            "CARTAO_CREDITO_AGENT_URL",
            "http://cartao_credito_agent:8000",
        )

        self.abrir_conta_agent_url = os.getenv(
            "ABRIR_CONTA_AGENT_URL",
            "http://abrir_conta_agent:8000",
        )

        self.suporte_cliente_agent_url = os.getenv(
            "SUPORTE_CLIENTE_AGENT_URL",
            "http://suporte_cliente_agent:8000",
        )


settings = Settings()
