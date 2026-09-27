from sqlalchemy import Column, Float, Integer, String

from model import Base


class TaxaConsumo(Base):
    """Taxa de consumo pessoal de um tipo de produto.

    A taxa é armazenada como quantidade consumida ao longo de um período,
    preservando a forma em que foi informada. A taxa diária é derivada
    desses dois valores.
    """

    __tablename__ = 'taxa_consumo'

    id = Column("pk_taxa_consumo", Integer, primary_key=True)
    tipo = Column(String(80), unique=True, nullable=False)
    quantidade = Column(Float, nullable=False)
    periodo_dias = Column(Integer, nullable=False)

    def __init__(self, tipo: str, quantidade: float, periodo_dias: int):
        """
        Cria a taxa de consumo de um tipo

        Arguments:
            tipo: tipo do produto, conforme o catálogo interno.
            quantidade: quantidade consumida no período, na unidade do tipo.
            periodo_dias: período em dias ao longo do qual a quantidade é consumida.
        """
        self.tipo = tipo
        self.quantidade = quantidade
        self.periodo_dias = periodo_dias

    def taxa_diaria(self) -> float:
        """Consumo médio por dia, derivado da quantidade e do período."""
        return self.quantidade / self.periodo_dias
