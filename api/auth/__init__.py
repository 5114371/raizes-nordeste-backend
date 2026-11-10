"""Autenticacao JWT e controle de perfil por dependencia.

O require_perfil devolve uma dependencia que bloqueia se o usuario
nao tiver um dos perfis permitidos - assim a gente nao precisa repetir
o if/else em cada endpoint.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from infrastructure.database import get_db
from infrastructure.config import settings
from domain.models import Usuario
from domain.enums import PerfilUsuario
from typing import List

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=settings.bcrypt_cost)


def hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return pwd_context.verify(senha, senha_hash)


def criar_token(usuario: Usuario) -> str:
    payload = {
        "sub": str(usuario.id),
        "email": usuario.email,
        "perfil": usuario.perfil.value,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_user(token: str = Depends(oauth2_scheme),
                     db: Session = Depends(get_db)) -> Usuario:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": "NAO_AUTENTICADO", "message": "Token ausente ou invalido."},
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if not user_id:
            raise cred_exc
    except JWTError:
        raise cred_exc

    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not usuario:
        raise cred_exc
    return usuario


def require_perfil(*perfis: PerfilUsuario):
    """Devolve dependencia que valida se o usuario tem um dos perfis."""
    def dep(user: Usuario = Depends(get_current_user)) -> Usuario:
        if user.perfil not in perfis:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "SEM_PERMISSAO",
                    "message": f"Perfil {user.perfil.value} nao tem permissao para esta operacao.",
                }
            )
        return user
    return dep
