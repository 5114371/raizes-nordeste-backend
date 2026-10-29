"""Enums de dominio do projeto.

O canalPedido tem que ter 5 valores conforme o roteiro pede.
"""
import enum


class CanalPedido(str, enum.Enum):
    APP = "app"
    TOTEM = "totem"
    BALCAO = "balcao"
    PICKUP = "pickup"
    WEB = "web"


class StatusPedido(str, enum.Enum):
    RECEBIDO = "recebido"
    AGUARDANDO_PAGAMENTO = "aguardando_pagamento"
    EM_PRODUCAO = "em_producao"
    PRONTO = "pronto"
    ENTREGUE = "entregue"
    CANCELADO = "cancelado"


class PerfilUsuario(str, enum.Enum):
    ADMIN = "admin"
    GERENTE = "gerente"
    ATENDENTE = "atendente"
    COZINHA = "cozinha"
    CLIENTE = "cliente"
