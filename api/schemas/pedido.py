"""Schema Pydantic para criacao/consulta de pedidos.

canalPedido tem que vir no payload sempre - se nao vier o Pydantic
ja devolve 422 automaticamente.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from domain.enums import CanalPedido, StatusPedido


class ItemPedidoCreate(BaseModel):
    produtoId: str = Field(..., description="UUID do produto")
    quantidade: int = Field(..., gt=0, description="quantidade maior que zero")


class ItemPedidoOut(BaseModel):
    produtoId: str
    quantidade: int
    precoUnitario: float

    class Config:
        from_attributes = True


class PedidoCreate(BaseModel):
    canalPedido: CanalPedido
    clienteId: str
    unidadeId: str
    itens: List[ItemPedidoCreate] = Field(..., min_items=1)
    formaPagamento: str = "MOCK"


class PedidoOut(BaseModel):
    pedidoId: str = Field(alias="id")
    canalPedido: CanalPedido
    status: StatusPedido
    total: float
    itens: List[ItemPedidoOut] = []
    createdAt: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True
