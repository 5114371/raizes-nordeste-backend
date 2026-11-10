"""Router de autenticacao - login e refresh."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.schemas.auth import LoginRequest, TokenResponse
from api.auth import verificar_senha, criar_token, get_current_user
from infrastructure.database import get_db
from domain.models import Usuario
from api.errors import erro_padrao

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if not usuario or not verificar_senha(payload.senha, usuario.senha_hash):
        raise HTTPException(status_code=401, detail=erro_padrao(
            "CREDENCIAIS_INVALIDAS",
            "E-mail ou senha invalidos.",
            [],
            "/api/v1/auth/login",
        ))
    token = criar_token(usuario)
    return {
        "accessToken": token,
        "tokenType": "Bearer",
        "expiresIn": 3600,
        "user": {"id": str(usuario.id), "nome": usuario.email, "perfil": usuario.perfil.value},
    }


@router.post("/refresh")
def refresh(user: Usuario = Depends(get_current_user)):
    novo = criar_token(user)
    return {"accessToken": novo, "tokenType": "Bearer"}
