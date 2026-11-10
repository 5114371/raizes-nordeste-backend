"""Webhook do gateway de pagamento.

Esse endpoint e chamado pelo gateway externo - nao precisa de JWT,
valida por HMAC no service. Nenhum dado de cartao passa por aqui.

O endpoint de solicitar pagamento exige JWT + perfil CLIENTE e
verifica se o usuario e dono do pedido via email (Cliente.email ==
Usuario.email). Cria o registro de Pagamento com status "pendente" -
o callback do gateway atualiza esse registro com o resultado.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from infrastructure.database import get_db
from application.pagamento_service import pagamento_service
from api.auth import require_perfil
from domain.enums import PerfilUsuario, StatusPedido
from domain.models import Usuario, Pedido, Pagamento, Cliente
from api.errors import erro_padrao
import uuid

router = APIRouter(prefix="/api/v1/pagamentos", tags=["pagamentos"])


@router.post("/callback")
async def callback_pagamento(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    try:
        return await pagamento_service.registrar_callback(db, payload, request)
    except ValueError as e:
        msg = str(e)
        codigo = ("ASSINATURA_INVALIDA" if "assinatura" in msg else
                  "TRANSACAO_NAO_ENCONTRADA" if "transacao" in msg else
                  "PEDIDO_NAO_ENCONTRADO" if "pedido" in msg else "STATUS_INVALIDO")
        raise HTTPException(status_code=400, detail=erro_padrao(
            codigo, msg, [], "/api/v1/pagamentos/callback"
        ))


@router.post("/{pedido_id}/pagamento")
def solicitar_pagamento(pedido_id: str,
                        db: Session = Depends(get_db),
                        user: Usuario = Depends(require_perfil(PerfilUsuario.CLIENTE))):
    """Solicita pagamento ao gateway mock - retorna transacaoId.
    So o CLIENTE dono do pedido pode solicitar.
    Cria o registro de Pagamento com status "pendente" - o callback
    do gateway atualiza esse registro com o resultado (aprovado/recusado)."""
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail=erro_padrao(
            "NAO_ENCONTRADO", "Pedido nao encontrado.", [],
            f"/api/v1/pagamentos/{pedido_id}/pagamento"
        ))
    # verifica se o usuario e dono do pedido via email (Cliente.email == Usuario.email)
    cliente = db.query(Cliente).filter(Cliente.email == user.email).first()
    if user.perfil != PerfilUsuario.ADMIN and (
            not cliente or pedido.cliente_id != cliente.id):
        raise HTTPException(status_code=403, detail=erro_padrao(
            "SEM_PERMISSAO", "So pode pagar pedidos proprios.", [],
            f"/api/v1/pagamentos/{pedido_id}/pagamento"
        ))
    # verifica se o pedido esta aguardando pagamento
    if pedido.status != StatusPedido.AGUARDANDO_PAGAMENTO:
        raise HTTPException(status_code=409, detail=erro_padrao(
            "CONFLITO_ESTADO", "Pedido nao esta aguardando pagamento.", [],
            f"/api/v1/pagamentos/{pedido_id}/pagamento"
        ))
    # cria o registro de Pagamento com status "pendente"
    # o callback do gateway vai atualizar esse registro
    transacao_id = f"txn_{uuid.uuid4().hex[:12]}"
    db.add(Pagamento(
        pedido_id=pedido_id,
        transacao_id=transacao_id,
        status="pendente",
    ))
    db.commit()
    return {"transacaoId": transacao_id, "status": "pendente", "pedidoId": pedido_id}
