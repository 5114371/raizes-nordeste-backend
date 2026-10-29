"""Handler de erros padronizado - toda excecao vira JSON no mesmo formato."""
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime, timezone
import uuid


def erro_padrao(codigo: str, mensagem: str, detalhes: list, path: str, request_id: str = None):
    return {
        "error": codigo,
        "message": mensagem,
        "details": detalhes,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "path": path,
        "requestId": request_id or str(uuid.uuid4()),
    }


async def validation_handler(request: Request, exc: RequestValidationError):
    detalhes = [{"field": ".".join(str(e["loc"][1:])), "issue": e["msg"]} for e in exc.errors()]
    return JSONResponse(status_code=422, content=erro_padrao(
        "VALIDACAO_FALHOU",
        "Dados de entrada invalidos.",
        detalhes,
        str(request.url.path),
    ))
