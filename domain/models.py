"""Modelos SQLAlchemy do dominio.

Separei Usuario (autenticacao) de Cliente (dados de negocio) pra facilitar
a anonimizacao LGPD - assim quando o cliente revoga o consentimento a gente
so anonimiza cpf/email sem mexer nas credenciais.
"""
from sqlalchemy import Column, String, Integer, Numeric, Enum, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from infrastructure.database import Base
from domain.enums import CanalPedido, StatusPedido, PerfilUsuario


class Cliente(Base):
    __tablename__ = "cliente"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(120), nullable=False)
    cpf = Column(String(11), unique=True, index=True)
    email = Column(String(120))
    consentimento_lgpd = Column(Boolean, default=False)
    data_consentimento = Column(DateTime)
    pontos = Column(Integer, default=0)

    pedidos = relationship("Pedido", back_populates="cliente")


class Usuario(Base):
    __tablename__ = "usuario"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(120), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    perfil = Column(Enum(PerfilUsuario), nullable=False)
    unidade_id = Column(UUID(as_uuid=True), ForeignKey("unidade.id"))


class Unidade(Base):
    __tablename__ = "unidade"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(120), nullable=False)
    cidade = Column(String(80))
    estado = Column(String(2))
    tipo_cozinha = Column(String(20), default="completa")  # completa ou reduzida


class Produto(Base):
    __tablename__ = "produto"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(120), nullable=False)
    preco_base = Column(Numeric(10, 2), nullable=False)
    categoria = Column(String(60))
    sazonal = Column(Boolean, default=False)
    regiao = Column(String(60))


class EstoqueLocal(Base):
    __tablename__ = "estoque_local"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    unidade_id = Column(UUID(as_uuid=True), ForeignKey("unidade.id"), nullable=False)
    produto_id = Column(UUID(as_uuid=True), ForeignKey("produto.id"), nullable=False)
    quantidade = Column(Numeric(10, 2), default=0)


class Pedido(Base):
    __tablename__ = "pedido"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("cliente.id"))
    unidade_id = Column(UUID(as_uuid=True), ForeignKey("unidade.id"), nullable=False)
    canal_pedido = Column(Enum(CanalPedido), nullable=False)
    status = Column(Enum(StatusPedido), default=StatusPedido.AGUARDANDO_PAGAMENTO)
    total = Column(Numeric(10, 2), default=0)
    criado_em = Column(DateTime, default=datetime.utcnow)

    cliente = relationship("Cliente", back_populates="pedidos")
    itens = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")


class ItemPedido(Base):
    __tablename__ = "item_pedido"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pedido_id = Column(UUID(as_uuid=True), ForeignKey("pedido.id"), nullable=False)
    produto_id = Column(UUID(as_uuid=True), ForeignKey("produto.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Numeric(10, 2), nullable=False)

    pedido = relationship("Pedido", back_populates="itens")


class Pagamento(Base):
    __tablename__ = "pagamento"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pedido_id = Column(UUID(as_uuid=True), ForeignKey("pedido.id"), nullable=False)
    transacao_id = Column(String(100), unique=True, index=True)
    status = Column(String(20))  # aprovado / recusado / pendente
    forma_pagamento = Column(String(20), default="MOCK")
    processado_em = Column(DateTime, default=datetime.utcnow)


class Auditoria(Base):
    __tablename__ = "auditoria"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuario.id"))
    acao = Column(String(60), nullable=False)
    recurso = Column(String(200))
    ip_origem = Column(String(45))
    timestamp = Column(DateTime, default=datetime.utcnow)


class ConsentimentoLGPD(Base):
    __tablename__ = "consentimento_lgpd"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("cliente.id"), nullable=False)
    aceito = Column(Boolean, nullable=False)
    finalidade = Column(String(200))
    data_registro = Column(DateTime, default=datetime.utcnow)
