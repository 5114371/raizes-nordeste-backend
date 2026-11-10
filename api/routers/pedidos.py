"""Router de pedidos - fluxo critico da API.

Traduz excecoes de dominio (camada Application) em respostas HTTP
com o formato padronizado (camada API).
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from api.schemas.pedido import PedidoCreate, PedidoOut
from application.pedido_service import pedido_service
from infrastructure.database import get_db
from api.auth import get_current_user, require_perfil
from domain.enums import CanalPedido, PerfilUsuario
from domain.models import Usuario, Pedido, Cliente
from infrastructure.exceptions import (EstoqueInsuficiente, UnidadeNaoEncontrada,
                                       ProdutoNaoEncontrado, StatusInvalido)
from api.errors import erro_padrao

router = APIRouter(prefix="/api/v1/pedidos", tags=["pedidos"])


@router.post("", response_model=PedidoOut, status_code=201)
def criar_pedido(payload: PedidoCreate,
                db: Session = Depends(get_db),
                user: Usuario = Depends(require_perfil(PerfilUsuario.CLIENTE))):
    try:
        return pedido_service.criar(db, payload, str(user.id))
    except UnidadeNaoEncontrada:
        raise HTTPException(status_code=404, detail=erro_padrao(
            "NAO_ENCONTRADO", "Unidade nao encontrada.", [], "/api/v1/pedidos"))
    except ProdutoNaoEncontrado as e:
        raise HTTPException(status_code=404, detail=erro_padrao(
            "NAO_ENCONTRADO", f"Produto {e.produto_id} nao encontrado.", [],
            "/api/v1/pedidos"))
    except EstoqueInsuficiente as e:
        raise HTTPException(status_code=409, detail=erro_padrao(
            "ESTOQUE_INSUFICIENTE",
            "Nao ha quantidade suficiente para um ou mais itens.",
            [{"field": "itens", "issue": f"produto {e.produto_id} sem estoque"}],
            "/api/v1/pedidos"
        ))


@router.get("", response_model=List[PedidoOut])
def listar_pedidos(
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
    canalPedido: CanalPedido = Query(None),
    status: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    """Lista pedidos - cliente so ve proprios; admin/gerente ve todos."""
    return pedido_service.listar(db, canal=canalPedido, status=status,
                                 page=page, limit=limit, user=user)


@router.get("/{pedido_id}", response_model=PedidoOut)
def consultar_pedido(pedido_id: str,
                     db: Session = Depends(get_db),
                     user: Usuario = Depends(get_current_user)):
    p = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not p:
        raise HTTPException(status_code=404, detail=erro_padrao(
            "NAO_ENCONTRADO", "Pedido nao encontrado.", [],
            f"/api/v1/pedidos/{pedido_id}"
        ))
    # cliente so ve pedidos proprios (via email)
    if user.perfil == PerfilUsuario.CLIENTE:
        cliente = db.query(Cliente).filter(Cliente.id == p.cliente_id).first()
        if not cliente or cliente.email != user.email:
            raise HTTPException(status_code=403, detail=erro_padrao(
                "SEM_PERMISSAO", "So pode consultar pedidos proprios.", [],
                f"/api/v1/pedidos/{pedido_id}"
            ))
    return p


@router.patch("/{pedido_id}/status")
def atualizar_status(pedido_id: str,
                     novo_status: str,
                     db: Session = Depends(get_db),
                     user: Usuario = Depends(require_perfil(
                         PerfilUsuario.ATENDENTE, PerfilUsuario.COZINHA, PerfilUsuario.ADMIN
                     ))):
    try:
        p = pedido_service.atualizar_status(db, pedido_id, novo_status, str(user.id))
    except StatusInvalido as e:
        raise HTTPException(status_code=422, detail=erro_padrao(
            "VALIDACAO_FALHOU", "Status invalido.",
            [{"field": "novo_status", "issue": f"valor '{e.valor}' nao existe"}],
            f"/api/v1/pedidos/{pedido_id}/status"))
    if not p:
        raise HTTPException(status_code=404, detail=erro_padrao(
            "NAO_ENCONTRADO", "Pedido nao encontrado.", [],
            f"/api/v1/pedidos/{pedido_id}"
        ))
    return {"ok": True, "status": novo_status}
