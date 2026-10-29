"""Testes automatizados - cobrem os cenarios principais do roteiro."""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def auth_headers(perfil="CLIENTE"):
    """Pega token JWT via login (assume que o seed ja rodou)."""
    resp = client.post("/api/v1/auth/login", json={
        "email": f"{perfil.lower()}@teste.com",
        "senha": "Senha@123",
    })
    if resp.status_code != 200:
        pytest.skip(f"sem usuario {perfil} no seed")
    token = resp.json()["accessToken"]
    return {"Authorization": f"Bearer {token}"}


def test_criar_pedido_com_estoque():
    """T05 - criar pedido valido retorna 201."""
    resp = client.post("/api/v1/pedidos", json={
        "canalPedido": "TOTEM",
        "clienteId": "10",
        "unidadeId": "2",
        "itens": [{"produtoId": "101", "quantidade": 2}],
        "formaPagamento": "MOCK",
    }, headers=auth_headers("CLIENTE"))
    assert resp.status_code == 201
    body = resp.json()
    assert body["canalPedido"] == "TOTEM"
    assert body["status"] == "aguardando_pagamento"
    assert body["total"] > 0


def test_criar_pedido_sem_canal_pedido():
    """T08 - pedido sem canalPedido retorna 422."""
    resp = client.post("/api/v1/pedidos", json={
        "clienteId": "10",
        "unidadeId": "2",
        "itens": [{"produtoId": "101", "quantidade": 2}],
    }, headers=auth_headers("CLIENTE"))
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"] == "VALIDACAO_FALHOU"


def test_listar_sem_token():
    """T02 - listar sem token retorna 401."""
    resp = client.get("/api/v1/pedidos")
    assert resp.status_code == 401


def test_filtro_por_canal():
    """T09 - filtro canalPedido so traz pedidos daquele canal."""
    resp = client.get(
        "/api/v1/pedidos?canalPedido=TOTEM",
        headers=auth_headers("GERENTE"),
    )
    assert resp.status_code == 200
    for p in resp.json():
        assert p["canalPedido"] == "TOTEM"
