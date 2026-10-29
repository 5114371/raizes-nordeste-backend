"""Webhook do gateway de pagamento.

Esse endpoint e chamado pelo gateway externo - nao precisa de JWT,
valida por HMAC no service. Nenhum dado de cartao passa por aqui.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from infrastructure.database import get_db
from application.pagamento_service import pagamento_service
from api.errors import erro_padrao

router = APIRouter(prefix="/api/v1/pagamentos", tags=["pagamentos"])


@router.post("/callback")
async def callback_pagamento(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    try:
        return pagamento_service.registrar_callback(db, payload, request)
    except ValueError as e:
        msg = str(e)
        codigo = "ASSINATURA_INVALIDA" if "assinatura" in msg else \
                 "PEDIDO_NAO_ENCONTRADO" if "pedido" in msg else "STATUS_INVALIDO"
        raise HTTPException(status_code=400, detail=erro_padrao(
            codigo, msg, [], "/api/v1/pagamentos/callback"
        ))


@router.post("/{pedido_id}/pagamento")
def solicitar_pagamento(pedido_id: str, db: Session = Depends(get_db)):
    """Solicita pagamento ao gateway mock - retorna 202 com transacaoId."""
    from domain.models import Pedido, Pagamento
    import uuid
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail=erro_padrao(
            "NAO_ENCONTRADO", "Pedido nao encontrado.", [], f"/api/v1/pagamentos/{pedido_id}/pagamento"
        ))
    transacao_id = f"txn_{uuid.uuid4().hex[:12]}"
    db.add(Pagamento(
        pedido_id=pedido_id,
        transacao_id=transacao_id,
        status="pendente",
    ))
    db.commit()
    return {"transacaoId": transacao_id, "status": "pendente"}
