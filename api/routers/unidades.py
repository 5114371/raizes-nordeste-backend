"""Router de unidades e cardapio."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from infrastructure.database import get_db
from api.auth import get_current_user
from domain.models import Unidade, Produto, EstoqueLocal

router = APIRouter(prefix="/api/v1", tags=["unidades"])


@router.get("/unidades")
def listar_unidades(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Unidade).all()


@router.get("/unidades/{unidade_id}/cardapio")
def cardapio(unidade_id: str, db: Session = Depends(get_db),
             user=Depends(get_current_user)):
    # so mostra produtos que tem estoque > 0 na unidade
    itens = db.query(Produto, EstoqueLocal).join(
        EstoqueLocal, EstoqueLocal.produto_id == Produto.id
    ).filter(
        EstoqueLocal.unidade_id == unidade_id,
        EstoqueLocal.quantidade > 0,
    ).all()
    return [
        {
            "produtoId": str(p.id), "nome": p.nome,
            "preco": float(p.preco_base), "categoria": p.categoria,
            "sazonal": p.sazonal,
        }
        for p, e in itens
    ]
