# API de Produtos e Estoque (Questão 6)

FastAPI + PostgreSQL + Redis + RQ, com autenticação JWT.

## Como rodar

```bash
docker compose up --build
```

- API: http://localhost:8000 (documentação em http://localhost:8000/docs)
- Usuário de demonstração: `admin` / `admin123`

No Swagger (`/docs`), clique em **Authorize**, informe usuário e senha, e todas as rotas passam a enviar o token.

### Sem Docker

Com Postgres e Redis rodando localmente:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
rq worker estoque
```

## Endpoints

| Método | Rota             | Descrição                                         |
| ------ | ---------------- | ------------------------------------------------- |
| POST   | `/auth/token`    | Login (form `username`/`password`), devolve o JWT |
| POST   | `/produtos`      | Cria produto                                      |
| GET    | `/produtos`      | Lista com paginação e filtros                     |
| GET    | `/produtos/{id}` | Detalhe (**com cache Redis**)                     |
| PATCH  | `/produtos/{id}` | Atualização parcial                               |
| DELETE | `/produtos/{id}` | Remove                                            |
| GET    | `/alertas`       | Alertas de estoque baixo gerados pelo worker      |

Filtros da listagem: `?page=1&size=20&nome=caneta&preco_min=1&preco_max=10&estoque_baixo=true`
(`estoque_baixo` = quantidade abaixo de 10, configurável em `ESTOQUE_MINIMO`).

### Validação (Pydantic)

- `preco` e `quantidade_em_estoque` com `ge=0`; `preco` como `Decimal` com 2 casas.
- `nome` não pode ser nulo, vazio ou numérico (`"123"`, `"12,5"` são rejeitados). Valores não-texto como `123` já são recusados pelo Pydantic v2, que não converte int em str.
- No `PATCH`, os campos são opcionais, mas não aceitam `null`.
- As regras de preço e estoque não negativos também existem como `CHECK` no banco, protegendo contra escritas que não passem pela API.

### Autenticação JWT

Login via OAuth2 password flow em `/auth/token`; token HS256 com expiração de 60 min. Todas as rotas de produto exigem `Authorization: Bearer <token>`.
Simplificação: usuário único vindo de configuração. Em produção haveria uma tabela de usuários com senha em bcrypt/argon2 e a chave secreta viria de um cofre.

## Uso de IA

Usei o Claude como assistente de desenvolvimento nesta prova:

- Geração da estrutura inicial do projeto;
- Redação deste README;
- Auxílio no desenvolvimento de um teste ponta a ponta com PostgreSQL, Redis e worker reais, para confirmar autenticação, validações, filtros, cache (HIT/MISS e invalidação) e geração de alertas.

Os demais desenvolvimentos são de minha responsabilidade. Assim como:

- Revisão do código e das decisões técnicas (escolha do ORM, estratégia de invalidação do cache, uso do RQ);
- Validação final da execução no meu ambiente.
- Não aceitei o código sem verificação: cada requisito foi testado em execução real, não apenas lido.
