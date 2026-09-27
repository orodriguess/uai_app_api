from datetime import date, timedelta

from logger import logger
from model import Base, Session, engine
from model import estoque
from model.catalogo import busca_tipo
from model.evento_estoque import ALTERACAO_TAXA, COMPRA, CONFERENCIA

# Eventos de demonstração, em ordem cronológica. O primeiro campo indica
# quantos dias antes da inicialização o evento ocorreu, mantendo a mesma
# variedade de situações em qualquer data de execução.
#
# A ordem é relevante: a conferência calcula o consumo observado a partir do
# último evento registrado do tipo.
EVENTOS_EXEMPLO = [
    # (dias atrás, espécie, tipo, dados do evento)
    (40, COMPRA, "Detergente", {"quantidade": 500, "descricao": "Detergente líquido neutro"}),  # saldo zerado
    (20, COMPRA, "Papel higiênico", {"quantidade": 12, "descricao": "Papel higiênico folha dupla"}),
    (20, COMPRA, "Café", {"quantidade": 1000, "descricao": "Cafezim é bão dimais, sô"}),
    (12, COMPRA, "Pasta de dente", {"quantidade": 90, "descricao": "Colgate total 12"}),
    (12, ALTERACAO_TAXA, "Pasta de dente", {"quantidade": 30, "periodo_dias": 7}),  # taxa personalizada
    (10, COMPRA, "Arroz", {"quantidade": 5, "descricao": "Arroz branco tipo 1"}),
    (7, COMPRA, "Shampoo", {"quantidade": 350, "descricao": "Cabelos secos"}),
    (6, CONFERENCIA, "Café", {"quantidade": 720}),  # recalibra a taxa para 20 g/dia
    (5, COMPRA, "Goiabada", {"quantidade": 500, "descricao": "Goiabada cascão"}),
    (4, COMPRA, "Feijão", {"quantidade": 2000, "descricao": "Feijão preto"}),
    (3, COMPRA, "Ovo", {"quantidade": 30, "descricao": "Ovo de galinha caipira"}),
    (2, COMPRA, "Pão de queijo", {"quantidade": 30, "descricao": "Pão de queijo mineiro"}),
    (2, COMPRA, "Papel higiênico", {"quantidade": 12, "descricao": "Papel higiênico folha dupla"}),  # segunda compra do tipo
    (1, COMPRA, "Pão", {"quantidade": 10, "descricao": "Pão de sal quentim"}),  # pendente de conferência
]


def recria_banco_com_exemplos() -> None:
    """Apaga todas as tabelas, recria o esquema e carrega o livro de exemplo.

    Executada a cada inicialização da API.
    """
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    hoje = date.today()
    session = Session()

    for dias_atras, especie, tipo, dados in EVENTOS_EXEMPLO:
        data = hoje - timedelta(days=dias_atras)
        if especie == COMPRA:
            estoque.registrar_compra(session, tipo=tipo,
                                     unidade=busca_tipo(tipo)["unidade"],
                                     quantidade=dados["quantidade"],
                                     data_compra=data,
                                     descricao=dados["descricao"])
        elif especie == ALTERACAO_TAXA:
            estoque.registrar_alteracao_taxa(session, tipo, dados["quantidade"],
                                             dados["periodo_dias"], referencia=data)
        elif especie == CONFERENCIA:
            estoque.registrar_conferencia(session, tipo, dados["quantidade"],
                                          referencia=data)

    session.commit()
    session.close()
    logger.info(f"Banco recriado com {len(EVENTOS_EXEMPLO)} eventos de exemplo")
