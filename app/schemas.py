from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def validar_nome(nome: str) -> str:
    nome = nome.strip()
    if not nome:
        raise ValueError("nome não pode ser vazio")
    try:
        float(nome.replace(",", "."))
    except ValueError:
        return nome
    raise ValueError("nome não pode ser numérico")


class ProdutoCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    preco: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    quantidade_em_estoque: int = Field(ge=0)

    _nome = field_validator("nome")(validar_nome)


class ProdutoUpdate(BaseModel):

    nome: str | None = Field(default=None, min_length=1, max_length=120)
    preco: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    quantidade_em_estoque: int | None = Field(default=None, ge=0)

    @field_validator("nome", "preco", "quantidade_em_estoque", mode="before")
    @classmethod
    def nao_nulo(cls, v):
        if v is None:
            raise ValueError("campo não pode ser nulo")
        return v

    @field_validator("nome")
    @classmethod
    def nome_valido(cls, v: str) -> str:
        return validar_nome(v)


class ProdutoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    preco: Decimal
    quantidade_em_estoque: int
    data_criacao: datetime
    data_atualizacao: datetime


class PaginaProdutos(BaseModel):
    items: list[ProdutoOut]
    total: int
    page: int
    size: int


class AlertaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    produto_id: int
    quantidade: int
    mensagem: str
    data_criacao: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
