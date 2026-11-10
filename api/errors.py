"""Handler de erros padronizado - toda excecao vira JSON no mesmo formato.

Inclui handler para HTTPException (extrai dict de detail e poe na raiz),
para RequestValidationError (422 automatico do Pydantic) e para
excecoes nao tratadas (500).

O requestId e gerado a cada erro via uuid4 (nao por middleware).
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime, timezone
import uuid


def erro_padrao(codigo: str, mensagem: str, detalhes: list, path: str,
                request_id: str = None):
    return {
        "error": codigo,
        "message": mensagem,
        "details": detalhes,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "path": path,
        "requestId": request_id or str(uuid.uuid4()),
    }


async def validation_handler(request: Request, exc: RequestValidationError):
    """Handler para erros de validacao do Pydantic (422)."""
    detalhes = [{"field": ".".join(str(e["loc"][1:])), "issue": e["msg"]}
                for e in exc.errors()]
    return JSONResponse(status_code=422, content=erro_padrao(
        "VALIDACAO_FALHOU",
        "Dados de entrada invalidos.",
        detalhes,
        str(request.url.path),
    ))


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler para HTTPException - extrai o dict de detail e poe na raiz."""
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    else:
        return JSONResponse(status_code=exc.status_code, content=erro_padrao(
            "ERRO_HTTP",
            str(exc.detail),
            [],
            str(request.url.path),
        ))


async def generic_exception_handler(request: Request, exc: Exception):
    """Handler para qualquer excecao nao tratada (500)."""
    return JSONResponse(status_code=500, content=erro_padrao(
        "ERRO_INTERNO",
        "Erro interno do servidor.",
        [],
        str(request.url.path),
    ))
