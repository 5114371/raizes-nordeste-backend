# Raizes do Nordeste - Back-end

API REST para a rede de lanchonetes Raizes do Nordeste, suportando multiplos
canais de atendimento (APP, TOTEM, BALCAO, PICKUP, WEB), integracao desacoplada
com gateway de pagamento e conformidade LGPD.

## Stack

- Python 3.11+
- FastAPI 0.110+
- PostgreSQL 16
- Redis 7 (cache)
- SQLAlchemy 2.0 + Alembic (ORM e migrations)
- Docker (opcional)

## Requisitos

- Python 3.11 ou superior
- PostgreSQL 16
- Redis 7
- Docker 24+ (opcional, mas recomendado)

## Configuracao

1. Clone o repositorio:
```bash
git clone https://github.com/5114371/raizes-nordeste-backend.git
cd raizes-nordeste-backend
```

2. Crie o ambiente virtual e instale as dependencias:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Copie o `.env.example` para `.env` e ajuste as credenciais:
```bash
cp .env.example .env
```

4. Crie o banco e rode as migrations:
```bash
createdb raizes_db
alembic upgrade head
```

5. Rode o seed para popular dados de teste:
```bash
python scripts/seed.py
```

6. Inicie a API:
```bash
uvicorn main:app --reload --port 8000
```

## Documentacao

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Testes

### Testes automatizados (pytest)
```bash
pytest -v
```

### Colecao Postman
Importe o arquivo `collections/raizes-nordeste.postman_collection.json` no Postman/Insomnia.

Ou rode via Newman:
```bash
newman run collections/raizes-nordeste.postman_collection.json
```

A colecao tem 15 cenarios de teste (9 positivos + 6 negativos) organizados em 5 pastas:
1. Auth (T01, T02)
2. Pedidos (T05-T09)
3. Pagamento (T10-T13)
4. Autorizacao (T03, T04)
5. LGPD/Auditoria (T14, T15)

## Executar via Docker

```bash
docker-compose up --build
```

Sobe:
- API: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Estrutura do projeto

```
raizes-nordeste-backend/
|-- domain/              # entidades, enums, regras de negocio
|-- application/         # services (casos de uso)
|-- infrastructure/      # banco, config, excecoes
|-- api/                 # routers, schemas, auth, errors
|-- tests/               # testes pytest
|-- migrations/          # Alembic
|-- collections/         # colecao Postman (.json)
|-- scripts/             # seed.py
|-- .env.example
|-- Dockerfile
|-- docker-compose.yml
|-- main.py
|-- README.md
`-- requirements.txt
```

## Credenciais de teste (seed)

| Perfil    | Email                | Senha      |
|-----------|----------------------|------------|
| ADMIN     | admin@teste.com      | Senha@123  |
| GERENTE   | gerente@teste.com    | Senha@123  |
| ATENDENTE | atendente@teste.com  | Senha@123  |
| COZINHA   | cozinha@teste.com    | Senha@123  |
| CLIENTE   | cliente@teste.com    | Senha@123  |

## canalPedido (multicanalidade)

O campo `canalPedido` e obrigatorio em todo pedido e aceita 5 valores:

- `APP` - aplicativo oficial
- `TOTEM` - totens de autoatendimento
- `BALCAO` - balcao humano
- `PICKUP` - retirada rapida
- `WEB` - site web

Filtro de pedidos por canal:
```
GET /api/v1/pedidos?canalPedido=TOTEM
```

## Padrao de erro

Todos os erros seguem o formato:
```json
{
  "error": "CODIGO_DO_ERRO",
  "message": "mensagem legivel",
  "details": [],
  "timestamp": "2026-10-29T12:00:00Z",
  "path": "/rota",
  "requestId": "uuid"
}
```

## Licenca

Uso academico - Projeto Multidisciplinar UNINTER 2026.
