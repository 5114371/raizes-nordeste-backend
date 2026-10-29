"""Router de fidelidade - saldo de pontos."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from infrastructure.database import get_db
from api.auth import require_perfil
from domain.enums import PerfilUsuario
from domain.models import Cliente, Usuario
from api.errors import erro_padrao

router = APIRouter(prefix="/api/v1/fidelidade", tags=["fidelidade"])


@router.get("/{cliente_id}/saldo")
def saldo_fidelidade(cliente_id: str,
                    db: Session = Depends(get_db),
                    user: Usuario = Depends(require_perfil(PerfilUsuario.CLIENTE, PerfilUsuario.ADMIN))):
    c = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not c:
        raise HTTPException(status_code=404, detail=erro_padrao(
            "NAO_ENCONTRADO", "Cliente nao encontrado.", [], f"/api/v1/fidelidade/{cliente_id}/saldo"
        ))
    return {"clienteId": str(c.id), "pontos": c.pontos, "consentimento": c.consentimento_lgpd}
