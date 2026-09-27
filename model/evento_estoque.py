from datetime import date
from typing import Optional

from sqlalchemy import Column, Date, Float, Integer, String

from model import Base

# Espécies de evento que compõem o livro de um tipo.
COMPRA = 'compra'
ALTERACAO_TAXA = 'alteracao_taxa'
CONFERENCIA = 'conferencia'


class EventoEstoque(Base):
    """Um evento do livro de estoque de um tipo de produto.

    O saldo de um tipo é derivado da sequência de eventos. Cada evento
    armazena dois campos derivados, a taxa vigente a partir dele e o saldo
    resultante, recalculados a cada gravação (ver `model.estoque.reapurar`).

    Como o saldo fica congelado em cada evento, uma alteração de taxa afeta
    apenas o consumo posterior a ela.
    """

    __tablename__ = 'evento_estoque'

    id = Column("pk_evento_estoque", Integer, primary_key=True)
    tipo = Column(String(80), nullable=False, index=True)
    especie = Column(String(20), nullable=False)
    data = Column(Date, nullable=False)
    unidade = Column(String(20), nullable=False)

    # Compra: quantidade adquirida. Conferência: quantidade realmente disponível.
    # Alteração de taxa: não se aplica.
    quantidade = Column(Float, nullable=True)
    descricao = Column(String(200), nullable=True)

    # Campos derivados, reescritos pela reapuração do livro.
    taxa_diaria_vigente = Column(Float, nullable=False, default=0.0)
    saldo_resultante = Column(Float, nullable=False, default=0.0)

    def __init__(self, tipo: str, especie: str, data: date, unidade: str,
                 quantidade: Optional[float] = None,
                 descricao: Optional[str] = None,
                 taxa_diaria_vigente: float = 0.0):
        """
        Cria um evento do livro de estoque

        Arguments:
            tipo: tipo do produto, conforme o catálogo interno.
            especie: COMPRA, ALTERACAO_TAXA ou CONFERENCIA.
            data: data em que o evento ocorreu.
            unidade: unidade de medida do tipo (g, ml, unidade, etc).
            quantidade: comprada, na compra; disponível, na conferência.
            descricao: descrição opcional, usada apenas na compra.
            taxa_diaria_vigente: taxa estabelecida pelo evento, quando ele
                estabelece uma (alteração de taxa e conferência).
        """
        self.tipo = tipo
        self.especie = especie
        self.data = data
        self.unidade = unidade
        self.quantidade = quantidade
        self.descricao = descricao
        self.taxa_diaria_vigente = taxa_diaria_vigente
        self.saldo_resultante = 0.0
