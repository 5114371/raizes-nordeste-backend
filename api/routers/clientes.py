"""Router de clientes - consentimento LGPD.

Quando o cliente revoga o consentimento a gente anonimiza cpf e email
mas mantem o historico de pedidos pra relatorio da matriz.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from infrastructure.database import get_db
from api.auth import get_current_user
from domain.models import Cliente, Auditoria, ConsentimentoLGPD
from api.errors import erro_padrao

router = APIRouter(prefix="/api/v1/clientes", tags=["clientes"])


class ConsentimentoDTO(BaseModel):
    clienteId: str
    aceito: bool
    finalidade: str = "fidelizacao e execucao de contrato"


@router.post("/consentimento")
def registrar_consentimento(payload: ConsentimentoDTO,
                            db: Session = Depends(get_db),
                            user=Depends(get_current_user)):
    cliente = db.query(Cliente).filter(Cliente.id == payload.clienteId).first()
    if not cliente:
        raise HTTPException(status_code=404, detail=erro_padrao(
            "NAO_ENCONTRADO", "Cliente nao encontrado.", [], "/api/v1/clientes/consentimento"
        ))

    cliente.consentimento_lgpd = payload.aceito
    cliente.data_consentimento = datetime.utcnow()

    if not payload.aceito:
        # anonimiza - preserva historico mas sem dados pessoais
        cliente.email = None
        cliente.cpf = None
        cliente.pontos = 0

    db.add(ConsentimentoLGPD(
        cliente_id=payload.clienteId,
        aceito=payload.aceito,
        finalidade=payload.finalidade,
    ))
    db.add(Auditoria(
        usuario_id=str(user.id),
        acao="CONSENTIMENTO_LGPD_ALTERADO",
        recurso=f"cliente:{payload.clienteId}:aceito={payload.aceito}",
    ))
    db.commit()
    return {"ok": True, "consentimento": payload.aceito}
