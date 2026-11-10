"""Seed de dados - roda uma vez para popular o banco em dev.

Cria 2 unidades, 5 produtos, estoque, e 5 usuarios (um de cada perfil).
"""
from infrastructure.database import SessionLocal, Base, engine
from domain.models import Unidade, Produto, EstoqueLocal, Usuario
from api.auth import hash_senha
from domain.enums import PerfilUsuario
import uuid

Base.metadata.create_all(bind=engine)

db = SessionLocal()

# unidades
u1 = Unidade(id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
             nome="Raizes Recife", cidade="Recife", estado="PE")
u2 = Unidade(id=uuid.UUID("00000000-0000-0000-0000-000000000003"),
             nome="Raizes Porto Ferreira", cidade="Porto Ferreira", estado="SP")

# produtos
produtos = [
    Produto(id=uuid.UUID("00000000-0000-0000-0000-000000000101"),
            nome="Cuscuz recheado", preco_base=12.50, categoria="cafe", sazonal=False),
    Produto(id=uuid.UUID("00000000-0000-0000-0000-000000000305"),
            nome="Bolo de macaxeira", preco_base=8.90, categoria="doce", sazonal=False),
]

# estoque
estoques = [
    EstoqueLocal(unidade_id=u1.id, produto_id=produtos[0].id, quantidade=20),
    EstoqueLocal(unidade_id=u1.id, produto_id=produtos[1].id, quantidade=1),
]

# usuarios - um de cada perfil
usuarios = [
    Usuario(email="admin@teste.com", senha_hash=hash_senha("Senha@123"), perfil=PerfilUsuario.ADMIN),
    Usuario(email="gerente@teste.com", senha_hash=hash_senha("Senha@123"), perfil=PerfilUsuario.GERENTE, unidade_id=u1.id),
    Usuario(email="atendente@teste.com", senha_hash=hash_senha("Senha@123"), perfil=PerfilUsuario.ATENDENTE, unidade_id=u1.id),
    Usuario(email="cozinha@teste.com", senha_hash=hash_senha("Senha@123"), perfil=PerfilUsuario.COZINHA, unidade_id=u1.id),
    Usuario(email="cliente@teste.com", senha_hash=hash_senha("Senha@123"), perfil=PerfilUsuario.CLIENTE),
]

for obj in [u1, u2] + produtos + estoques + usuarios:
    db.add(obj)
db.commit()
print("seed aplicado com sucesso")
