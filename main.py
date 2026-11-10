"""Ponto de entrada da API Raizes do Nordeste."""
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from infrastructure.config import settings
from infrastructure.database import Base, engine
from api.errors import (validation_handler, http_exception_handler,
                        generic_exception_handler)
from api.routers import auth, pedidos, pagamentos, unidades, clientes, auditoria, fidelidade

# cria tabelas em dev - em prod usar alembic
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="API REST para a rede de lanchonetes Raizes do Nordeste.",
)

# handlers globais de erro - todos devolvem JSON no formato padrao (raiz, nao "detail")
app.add_exception_handler(RequestValidationError, validation_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# registra os routers
app.include_router(auth.router)
app.include_router(pedidos.router)
app.include_router(pagamentos.router)
app.include_router(unidades.router)
app.include_router(clientes.router)
app.include_router(auditoria.router)
app.include_router(fidelidade.router)


@app.get("/")
def root():
    return {"status": "ok", "app": settings.app_name}


@app.get("/health")
def health():
    return {"status": "healthy"}
