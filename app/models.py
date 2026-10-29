from datetime import datetime
from decimal import Decimal
from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Produto(Base):
    __tablename__ = "produtos"
    __table_args__ = (
        CheckConstraint("preco >= 0", name="ck_preco_nao_negativo"),
        CheckConstraint("quantidade_em_estoque >= 0", name="ck_estoque_nao_negativo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), index=True)
    preco: Mapped[Decimal] = mapped_column(Numeric(12, 2)) 
    quantidade_em_estoque: Mapped[int] = mapped_column(default=0)
    data_criacao: Mapped[datetime] = mapped_column(server_default=func.now())
    data_atualizacao: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )


class AlertaEstoque(Base):

    __tablename__ = "alertas_estoque"

    id: Mapped[int] = mapped_column(primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id", ondelete="CASCADE"))
    quantidade: Mapped[int]
    mensagem: Mapped[str] = mapped_column(String(255))
    data_criacao: Mapped[datetime] = mapped_column(server_default=func.now())
