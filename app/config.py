from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/estoque"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "troque-esta-chave-em-producao"
    jwt_algoritmo: str = "HS256"
    jwt_expira_minutos: int = 60

    # Usuário de demonstração
    usuario_demo: str = "admin"
    senha_demo: str = "admin123"

    cache_ttl_segundos: int = 60
    estoque_minimo: int = 10


settings = Settings()
