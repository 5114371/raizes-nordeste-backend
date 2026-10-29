"""Excecoes de dominio usadas pelo service e capturadas pelo handler."""


class EstoqueInsuficiente(Exception):
    def __init__(self, produto_id):
        self.produto_id = produto_id
        super().__init__(f"estoque insuficiente para produto {produto_id}")


class ConflitoEstado(Exception):
    def __init__(self, mensagem):
        super().__init__(mensagem)
