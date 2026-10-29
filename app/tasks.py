import logging
from redis import Redis
from rq import Queue
from app.config import settings
from app.database import SessionLocal
from app.models import AlertaEstoque, Produto

log = logging.getLogger(__name__)
fila = Queue("estoque", connection=Redis.from_url(settings.redis_url))

def verificar_estoque_baixo(produto_id: int) -> str:
    with SessionLocal() as db:
        produto = db.get(Produto, produto_id)
        if produto is None or produto.quantidade_em_estoque >= settings.estoque_minimo:
            return "sem alerta"

        mensagem = (
            f"Estoque baixo: '{produto.nome}' com {produto.quantidade_em_estoque} unidade(s) "
            f"(mínimo {settings.estoque_minimo})"
        )
        db.add(
            AlertaEstoque(
                produto_id=produto.id,
                quantidade=produto.quantidade_em_estoque,
                mensagem=mensagem,
            )
        )
        db.commit()
        log.warning(mensagem)
        return mensagem


def enfileirar_verificacao(produto: Produto) -> None:
    if produto.quantidade_em_estoque < settings.estoque_minimo:
        try:
            fila.enqueue(verificar_estoque_baixo, produto.id)
        except Exception:
            log.exception("Não foi possível enfileirar a verificação de estoque")
