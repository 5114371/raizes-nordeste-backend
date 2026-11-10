"""Router de auditoria - consulta de logs (so ADMIN)."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from infrastructure.database import get_db
from api.auth import require_perfil
from domain.enums import PerfilUsuario
from domain.models import Auditoria, Usuario
from api.errors import erro_padrao

router = APIRouter(prefix="/api/v1/auditoria", tags=["auditoria"])


@router.get("")
def consultar_auditoria(
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_perfil(PerfilUsuario.ADMIN)),
    recurso: str = Query(None),
    acao: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    q = db.query(Auditoria)
    if recurso:
        q = q.filter(Auditoria.recurso.ilike(f"%{recurso}%"))
    if acao:
        q = q.filter(Auditoria.acao == acao)
    offset = (page - 1) * limit
    rows = q.order_by(Auditoria.timestamp.desc()).offset(offset).limit(limit).all()
    return [
        {
            "id": str(r.id),
            "acao": r.acao,
            "recurso": r.recurso,
            "ip_origem": r.ip_origem,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        }
        for r in rows
    ]
