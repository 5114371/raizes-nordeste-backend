"""Excecoes de dominio usadas pelo service e capturadas pelo router.

A camada Application nao importa FastAPI - levanta excecoes de dominio
e o router (camada API) converte em HTTP com o formato padronizado.
"""


class EstoqueInsuficiente(Exception):
    def __init__(self, produto_id):
        self.produto_id = produto_id
        super().__init__(f"estoque insuficiente para produto {produto_id}")


class ConflitoEstado(Exception):
    def __init__(self, mensagem):
        super().__init__(mensagem)


class UnidadeNaoEncontrada(Exception):
    def __init__(self, unidade_id):
        self.unidade_id = unidade_id
        super().__init__(f"unidade {unidade_id} nao encontrada")


class ProdutoNaoEncontrado(Exception):
    def __init__(self, produto_id):
        self.produto_id = produto_id
        super().__init__(f"produto {produto_id} nao encontrado")


class StatusInvalido(Exception):
    def __init__(self, valor):
        self.valor = valor
        super().__init__(f"status '{valor}' invalido")
