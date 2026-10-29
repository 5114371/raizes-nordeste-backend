"""Service de pedido - regras de negocio do fluxo critico.

Lock pessimista no estoque pra evitar condition race quando dois
pedidos chegam ao mesmo tempo no mesmo produto.
"""
from decimal import Decimal
from sqlalchemy.orm import Session
from domain.models import Pedido, ItemPedido, EstoqueLocal, Auditoria, Produto
from domain.enums import StatusPedido, CanalPedido
from infrastructure.exceptions import EstoqueInsuficiente


class PedidoService:

    def criar(self, db: Session, payload, usuario_id: str) -> Pedido:
        total = Decimal("0.00")
        itens_models = []

        for item in payload.itens:
            # lock pessimista pra n ter race condition no estoque
            estoque = db.query(EstoqueLocal).filter_by(
                unidade_id=payload.unidadeId,
                produto_id=item.produtoId
            ).with_for_update().first()

            if not estoque or estoque.quantidade < item.quantidade:
                raise EstoqueInsuficiente(item.produtoId)

            # pega o preco do produto pra nao confiar no que o cliente mandou
            produto = db.query(Produto).filter(Produto.id == item.produtoId).first()
            preco = Decimal(produto.preco_base) if produto else Decimal("0")
            subtotal = preco * item.quantidade
            total += subtotal

            itens_models.append(ItemPedido(
                produto_id=item.produtoId,
                quantidade=item.quantidade,
                preco_unitario=preco,
            ))
            estoque.quantidade -= item.quantidade

        pedido = Pedido(
            cliente_id=payload.clienteId,
            unidade_id=payload.unidadeId,
            canal_pedido=payload.canalPedido,
            status=StatusPedido.AGUARDANDO_PAGAMENTO,
            total=total,
            itens=itens_models,
        )
        db.add(pedido)

        # auditoria - toda criacao de pedido precisa ficar registrada
        db.add(Auditoria(
            usuario_id=usuario_id,
            acao="CRIAR_PEDIDO",
            recurso=f"pedido:{pedido.id}",
        ))

        db.commit()
        db.refresh(pedido)
        return pedido

    def listar(self, db: Session, canal: CanalPedido = None, status: str = None,
               page: int = 1, limit: int = 10):
        q = db.query(Pedido)
        if canal:
            q = q.filter(Pedido.canal_pedido == canal)
        if status:
            q = q.filter(Pedido.status == status)
        offset = (page - 1) * limit
        return q.offset(offset).limit(limit).all()

    def atualizar_status(self, db: Session, pedido_id: str, novo_status: str, usuario_id: str):
        pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
        if not pedido:
            return None
        pedido.status = StatusPedido(novo_status)
        db.add(Auditoria(
            usuario_id=usuario_id,
            acao="STATUS_ALTERADO",
            recurso=f"pedido:{pedido_id}:novo={novo_status}",
        ))
        db.commit()
        db.refresh(pedido)
        return pedido


pedido_service = PedidoService()
