"""Service de pagamento - integra desacoplada com gateway mock.

Idempotencia: o callback busca o Pagamento pela transacao_id.
Se o status ja for "aprovado" ou "recusado", responde "ja processado".
Se for "pendente", atualiza o registro com o resultado.

O metodo e async porque precisa ler o corpo da requisicao
(await request.body()) para validar a assinatura HMAC.
"""
from sqlalchemy.orm import Session
from domain.models import Pagamento, Pedido, Auditoria, EstoqueLocal
from domain.enums import StatusPedido
from datetime import datetime
import hmac, hashlib
from infrastructure.config import settings


class PagamentoService:

    async def registrar_callback(self, db: Session, payload: dict, request) -> dict:
        # valida assinatura HMAC do gateway
        assinatura = request.headers.get("X-Signature", "")
        corpo = await request.body()
        esperada = hmac.new(
            settings.gateway_secret.encode(), corpo, hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(assinatura, esperada):
            raise ValueError("assinatura_hmac_invalida")

        transacao_id = payload.get("transacaoId") or payload.get("transacao_id")
        status = payload.get("status")

        if status not in ("aprovado", "recusado"):
            raise ValueError("status_invalido")

        # busca o pagamento pela transacao_id (foi criado em solicitar_pagamento)
        pagamento = db.query(Pagamento).filter_by(transacao_id=transacao_id).first()
        if not pagamento:
            raise ValueError("transacao_nao_encontrada")

        # idempotencia: so ignora se o pagamento ja saiu de "pendente"
        if pagamento.status != "pendente":
            return {"ok": True, "msg": "ja processado"}

        pedido = db.query(Pedido).filter(Pedido.id == pagamento.pedido_id).first()
        if not pedido:
            raise ValueError("pedido_nao_encontrado")

        if status == "aprovado":
            pedido.status = StatusPedido.EM_PRODUCAO
            acao = "PAGAMENTO_APROVADO"
        else:
            pedido.status = StatusPedido.CANCELADO
            # devolve o estoque que tinha sido debitado na criacao do pedido
            for item in pedido.itens:
                est = db.query(EstoqueLocal).filter_by(
                    unidade_id=pedido.unidade_id,
                    produto_id=item.produto_id,
                ).with_for_update().first()
                if est:
                    est.quantidade += item.quantidade
            acao = "PAGAMENTO_RECUSADO"

        # atualiza o pagamento pendente com o resultado (nao duplica)
        pagamento.status = status
        pagamento.forma_pagamento = payload.get("formaPagamento", "MOCK")
        pagamento.processado_em = datetime.utcnow()

        db.add(Auditoria(
            usuario_id=None,
            acao=acao,
            recurso=f"pedido:{pedido.id}",
            ip_origem=request.client.host if request.client else None,
        ))
        db.commit()
        return {"ok": True}


pagamento_service = PagamentoService()
