"""Service de pagamento - integra desacoplada com gateway mock.

Idempotencia: se a transacao_id ja existe no banco, devolve 200
sem reprocessar - webhooks podem chegar duplicados.
"""
from sqlalchemy.orm import Session
from domain.models import Pagamento, Pedido, Auditoria, EstoqueLocal
from domain.enums import StatusPedido
import hmac
import hashlib
import os
from infrastructure.config import settings


class PagamentoService:

    def registrar_callback(self, db: Session, payload: dict, request) -> dict:
        # valida assinatura HMAC do gateway
        assinatura = request.headers.get("X-Signature", "")
        corpo = await request.body() if hasattr(request, "body") else b""
        esperada = hmac.new(
            settings.gateway_secret.encode(), corpo, hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(assinatura, esperada):
            raise ValueError("assinatura_hmac_invalida")

        transacao_id = payload.get("transacaoId") or payload.get("transacao_id")
        pedido_id = payload.get("pedidoId") or payload.get("pedido_id")
        status = payload.get("status")

        # idempotencia - nao processa de novo se ja tem a transacao
        ja_existe = db.query(Pagamento).filter_by(transacao_id=transacao_id).first()
        if ja_existe:
            return {"ok": True, "msg": "ja processado"}

        pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
        if not pedido:
            raise ValueError("pedido_nao_encontrado")

        if status == "aprovado":
            pedido.status = StatusPedido.EM_PRODUCAO
            acao = "PAGAMENTO_APROVADO"
        elif status == "recusado":
            pedido.status = StatusPedido.CANCELADO
            # devolve o estoque que tinha sido debitado
            for item in pedido.itens:
                est = db.query(EstoqueLocal).filter_by(
                    unidade_id=pedido.unidade_id,
                    produto_id=item.produto_id,
                ).first()
                if est:
                    est.quantidade += item.quantidade
            acao = "PAGAMENTO_RECUSADO"
        else:
            raise ValueError("status_invalido")

        db.add(Pagamento(
            pedido_id=pedido_id,
            transacao_id=transacao_id,
            status=status,
            forma_pagamento=payload.get("formaPagamento", "MOCK"),
        ))
        db.add(Auditoria(
            usuario_id=None,  # sistema / gateway
            acao=acao,
            recurso=f"pedido:{pedido_id}",
            ip_origem=request.client.host if request.client else None,
        ))
        db.commit()
        return {"ok": True}


pagamento_service = PagamentoService()
