"""Service de pedido - regras de negocio do fluxo critico.

Lock pessimista no estoque pra evitar condition race quando dois
pedidos chegam ao mesmo tempo no mesmo produto.

A camada Application NAO importa FastAPI - levanta excecoes de dominio
(UnidadeNaoEncontrada, ProdutoNaoEncontrado, StatusInvalido) e o router
converte em HTTP com o formato padronizado.
"""
from decimal import Decimal
from sqlalchemy.orm import Session
from domain.models import Pedido, ItemPedido, EstoqueLocal, Auditoria, Produto, Unidade, Cliente
from domain.enums import StatusPedido, CanalPedido
from infrastructure.exceptions import EstoqueInsuficiente, UnidadeNaoEncontrada, ProdutoNaoEncontrado, StatusInvalido


class PedidoService:

    def criar(self, db: Session, payload, usuario_id: str) -> Pedido:
        # valida se a unidade existe (excecao de dominio -> router converte em 404)
        unidade = db.query(Unidade).filter(Unidade.id == payload.unidadeId).first()
        if not unidade:
            raise UnidadeNaoEncontrada(payload.unidadeId)

        total = Decimal("0.00")
        itens_models = []

        for item in payload.itens:
            # valida se o produto existe (excecao de dominio -> router converte em 404)
            produto = db.query(Produto).filter(Produto.id == item.produtoId).first()
            if not produto:
                raise ProdutoNaoEncontrado(item.produtoId)

            # lock pessimista pra n ter race condition no estoque
            estoque = db.query(EstoqueLocal).filter_by(
                unidade_id=payload.unidadeId,
                produto_id=item.produtoId
            ).with_for_update().first()

            if not estoque:
                raise EstoqueInsuficiente(item.produtoId)
            if estoque.quantidade < item.quantidade:
                raise EstoqueInsuficiente(item.produtoId)

            preco = Decimal(produto.preco_base)
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
        # flush para obter pedido.id antes de criar a Auditoria
        db.flush()

        # auditoria - agora pedido.id ja tem valor
        db.add(Auditoria(
            usuario_id=usuario_id,
            acao="CRIAR_PEDIDO",
            recurso=f"pedido:{pedido.id}",
        ))

        db.commit()
        db.refresh(pedido)
        return pedido

    def listar(self, db: Session, canal: CanalPedido = None, status: str = None,
               page: int = 1, limit: int = 10, user=None):
        q = db.query(Pedido)
        # cliente so ve pedidos proprios (via email do Usuario -> Cliente)
        if user and user.perfil and user.perfil.value == "CLIENTE":
            cliente = db.query(Cliente).filter(Cliente.email == user.email).first()
            if cliente:
                q = q.filter(Pedido.cliente_id == cliente.id)
            else:
                q = q.filter(Pedido.cliente_id == None)
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
        # valida status (excecao de dominio -> router converte em 422)
        try:
            novo = StatusPedido(novo_status)
        except ValueError:
            raise StatusInvalido(novo_status)
        pedido.status = novo
        db.flush()
        db.add(Auditoria(
            usuario_id=usuario_id,
            acao="STATUS_ALTERADO",
            recurso=f"pedido:{pedido_id}:novo={novo_status}",
        ))
        db.commit()
        db.refresh(pedido)
        return pedido


pedido_service = PedidoService()
