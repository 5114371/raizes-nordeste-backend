"""Router de pedidos - fluxo critico da API."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from api.schemas.pedido import PedidoCreate, PedidoOut
from application.pedido_service import pedido_service
from infrastructure.database import get_db
from api.auth import get_current_user, require_perfil
from domain.enums import CanalPedido, PerfilUsuario
from domain.models import Usuario, Pedido
from infrastructure.exceptions import EstoqueInsuficiente
from api.errors import erro_padrao

router = APIRouter(prefix="/api/v1/pedidos", tags=["pedidos"])


@router.post("", response_model=PedidoOut, status_code=201)
def criar_pedido(payload: PedidoCreate,
                db: Session = Depends(get_db),
                user: Usuario = Depends(require_perfil(PerfilUsuario.CLIENTE))):
    try:
        return pedido_service.criar(db, payload, str(user.id))
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
    """Lista pedidos - da pra filtrar por canal e por status."""
    return pedido_service.listar(db, canal=canalPedido, status=status, page=page, limit=limit)


@router.get("/{pedido_id}", response_model=PedidoOut)
def consultar_pedido(pedido_id: str,
                     db: Session = Depends(get_db),
                     user: Usuario = Depends(get_current_user)):
    p = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not p:
        raise HTTPException(status_code=404, detail=erro_padrao(
            "NAO_ENCONTRADO", "Pedido nao encontrado.", [], f"/api/v1/pedidos/{pedido_id}"
        ))
    return p


@router.patch("/{pedido_id}/status")
def atualizar_status(pedido_id: str,
                     novo_status: str,
                     db: Session = Depends(get_db),
                     user: Usuario = Depends(require_perfil(
                         PerfilUsuario.ATENDENTE, PerfilUsuario.COZINHA
                     ))):
    p = pedido_service.atualizar_status(db, pedido_id, novo_status, str(user.id))
    if not p:
        raise HTTPException(status_code=404, detail=erro_padrao(
            "NAO_ENCONTRADO", "Pedido nao encontrado.", [], f"/api/v1/pedidos/{pedido_id}"
        ))
    return {"ok": True, "status": novo_status}
