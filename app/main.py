from contextlib import asynccontextmanager
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import cache
from app.auth import autenticar, criar_token, usuario_atual
from app.config import settings
from app.database import Base, engine, get_db
from app.models import AlertaEstoque, Produto
from app.schemas import (
    AlertaOut,
    PaginaProdutos,
    ProdutoCreate,
    ProdutoOut,
    ProdutoUpdate,
    Token,
)
from app.tasks import enfileirar_verificacao


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)  # simplificação;
    yield


app = FastAPI(title="API de Produtos e Estoque", lifespan=lifespan)


# Auth
@app.post("/auth/token", response_model=Token, tags=["auth"])
def login(form: OAuth2PasswordRequestForm = Depends()):
    if not autenticar(form.username, form.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuário ou senha inválidos")
    return Token(access_token=criar_token(form.username))


# Rotas protegidas
protegido = [Depends(usuario_atual)]


def buscar_ou_404(db: Session, produto_id: int) -> Produto:
    produto = db.get(Produto, produto_id)
    if produto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Produto não encontrado")
    return produto


# CRUD
@app.post("/produtos", response_model=ProdutoOut, status_code=201, dependencies=protegido)
def criar_produto(payload: ProdutoCreate, db: Session = Depends(get_db)):
    produto = Produto(**payload.model_dump())
    db.add(produto)
    db.commit()
    db.refresh(produto)
    enfileirar_verificacao(produto)
    return produto


@app.get("/produtos", response_model=PaginaProdutos, dependencies=protegido)
def listar_produtos(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    nome: str | None = Query(None, description="Busca parcial, sem diferenciar maiúsculas"),
    preco_min: Decimal | None = Query(None, ge=0),
    preco_max: Decimal | None = Query(None, ge=0),
    estoque_baixo: bool = Query(False, description="Somente abaixo do estoque mínimo"),
):
    filtros = []
    if nome:
        filtros.append(Produto.nome.ilike(f"%{nome}%"))
    if preco_min is not None:
        filtros.append(Produto.preco >= preco_min)
    if preco_max is not None:
        filtros.append(Produto.preco <= preco_max)
    if estoque_baixo:
        filtros.append(Produto.quantidade_em_estoque < settings.estoque_minimo)

    total = db.scalar(select(func.count()).select_from(Produto).where(*filtros))
    items = db.scalars(
        select(Produto)
        .where(*filtros)
        .order_by(Produto.id)
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return PaginaProdutos(items=items, total=total, page=page, size=size)


@app.get("/produtos/{produto_id}", response_model=ProdutoOut, dependencies=protegido)
def obter_produto(produto_id: int, response: Response, db: Session = Depends(get_db)):
    chave = cache.chave_produto(produto_id)
    em_cache = cache.get(chave)
    if em_cache:
        response.headers["X-Cache"] = "HIT"
        return ProdutoOut.model_validate_json(em_cache)

    produto = ProdutoOut.model_validate(buscar_ou_404(db, produto_id))
    cache.set(chave, produto.model_dump_json())
    response.headers["X-Cache"] = "MISS"
    return produto


@app.patch("/produtos/{produto_id}", response_model=ProdutoOut, dependencies=protegido)
def atualizar_produto(produto_id: int, payload: ProdutoUpdate, db: Session = Depends(get_db)):
    produto = buscar_ou_404(db, produto_id)
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(produto, campo, valor)
    db.commit()
    db.refresh(produto)
    cache.invalidar(cache.chave_produto(produto_id)) 
    enfileirar_verificacao(produto)
    return produto


@app.delete("/produtos/{produto_id}", status_code=204, dependencies=protegido)
def remover_produto(produto_id: int, db: Session = Depends(get_db)):
    db.delete(buscar_ou_404(db, produto_id))
    db.commit()
    cache.invalidar(cache.chave_produto(produto_id))


# Alertas
@app.get("/alertas", response_model=list[AlertaOut], dependencies=protegido)
def listar_alertas(db: Session = Depends(get_db)):
    return db.scalars(select(AlertaEstoque).order_by(AlertaEstoque.id.desc()).limit(50)).all()
