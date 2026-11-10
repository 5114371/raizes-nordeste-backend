"""Router de clientes - consentimento LGPD.

Quando o cliente revoga o consentimento a gente anonimiza:
- CPF e email do Cliente
- Email do Usuario (credenciais) - troca por anonimo-<id>@anonimizado.invalid
mas mantem o historico de pedidos para relatorio da matriz.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from infrastructure.database import get_db
from api.auth import get_current_user
from domain.models import Cliente, Auditoria, ConsentimentoLGPD, Usuario
from domain.enums import PerfilUsuario
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
            "NAO_ENCONTRADO", "Cliente nao encontrado.", [],
            "/api/v1/clientes/consentimento"
        ))
    # so o proprio cliente (via email) ou ADMIN pode alterar consentimento
    if user.perfil == PerfilUsuario.CLIENTE and cliente.email != user.email:
        raise HTTPException(status_code=403, detail=erro_padrao(
            "SEM_PERMISSAO", "So pode alterar proprio consentimento.", [],
            "/api/v1/clientes/consentimento"
        ))

    # busca o Usuario ANTES de zerar o email do Cliente
    usuario = db.query(Usuario).filter(Usuario.email == cliente.email).first()

    cliente.consentimento_lgpd = payload.aceito
    cliente.data_consentimento = datetime.utcnow()

    if not payload.aceito:
        # anonimiza Usuario (email e NOT NULL e unico: troca por valor anonimo)
        if usuario:
            usuario.email = f"anonimo-{usuario.id}@anonimizado.invalid"
        # anonimiza Cliente
        cliente.email = None
        cliente.cpf = None
        cliente.pontos = 0

    db.add(ConsentimentoLGPD(
        cliente_id=payload.clienteId,
        aceito=payload.aceito,
        finalidade=payload.finalidade,
    ))
    db.flush()
    db.add(Auditoria(
        usuario_id=str(user.id),
        acao="CONSENTIMENTO_LGPD_ALTERADO",
        recurso=f"cliente:{payload.clienteId}:aceito={payload.aceito}",
    ))
    db.commit()
    return {"ok": True, "consentimento": payload.aceito}
