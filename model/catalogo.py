from typing import Optional, TypedDict


class TipoCatalogo(TypedDict):
    tipo: str
    unidade: str
    consumo_padrao: tuple[float, int]
    descricao_sugerida: str
    quantidade_sugerida: float


# Catálogo fixo dos tipos suportados. O consumo padrão vale até que a pessoa
# informe o seu e é expresso como (quantidade na unidade do tipo, período em
# dias: 1, 7 ou 30). A taxa diária é sempre derivada desse par.
CATALOGO_TIPOS: list[TipoCatalogo] = [
    {"tipo": "Café", "unidade": "g", "consumo_padrao": (450, 30),
     "descricao_sugerida": "Cafezim é bão dimais, sô", "quantidade_sugerida": 500},
    {"tipo": "Pão", "unidade": "unidade", "consumo_padrao": (2, 1),
     "descricao_sugerida": "Pão de sal quentim", "quantidade_sugerida": 10},
    {"tipo": "Iogurte", "unidade": "unidade", "consumo_padrao": (1, 1),
     "descricao_sugerida": "Iogurte natural", "quantidade_sugerida": 6},
    {"tipo": "Ovo", "unidade": "unidade", "consumo_padrao": (2, 1),
     "descricao_sugerida": "Ovo de galinha", "quantidade_sugerida": 12},
    {"tipo": "Arroz", "unidade": "kg", "consumo_padrao": (1, 7),
     "descricao_sugerida": "Arroz branco tipo 1", "quantidade_sugerida": 5},
    {"tipo": "Feijão", "unidade": "g", "consumo_padrao": (100, 1),
     "descricao_sugerida": "Feijão preto", "quantidade_sugerida": 1000},
    {"tipo": "Carne vermelha", "unidade": "g", "consumo_padrao": (1000, 7),
     "descricao_sugerida": "Picanha", "quantidade_sugerida": 1000},
    {"tipo": "Frango", "unidade": "g", "consumo_padrao": (1000, 7),
     "descricao_sugerida": "Peito de frango", "quantidade_sugerida": 1000},
    {"tipo": "Frutas", "unidade": "unidade", "consumo_padrao": (2, 1),
     "descricao_sugerida": "Banana", "quantidade_sugerida": 7},
    {"tipo": "Granola", "unidade": "g", "consumo_padrao": (40, 1),
     "descricao_sugerida": "Granola tradicional", "quantidade_sugerida": 500},
    {"tipo": "Pão de queijo", "unidade": "unidade", "consumo_padrao": (3, 1),
     "descricao_sugerida": "Pão de queijo mineiro", "quantidade_sugerida": 20},
    {"tipo": "Goiabada", "unidade": "g", "consumo_padrao": (500, 30),
     "descricao_sugerida": "Goiabada cascão", "quantidade_sugerida": 500},
    {"tipo": "Pasta de dente", "unidade": "g", "consumo_padrao": (120, 30),
     "descricao_sugerida": "Colgate total 12", "quantidade_sugerida": 90},
    {"tipo": "Papel higiênico", "unidade": "unidade", "consumo_padrao": (3, 7),
     "descricao_sugerida": "Papel higiênico folha dupla", "quantidade_sugerida": 12},
    {"tipo": "Escova de dente", "unidade": "unidade", "consumo_padrao": (0.33, 30),
     "descricao_sugerida": "Escova de dente macia", "quantidade_sugerida": 1},
    {"tipo": "Fio dental", "unidade": "m", "consumo_padrao": (15, 30),
     "descricao_sugerida": "Sabor menta", "quantidade_sugerida": 50},
    {"tipo": "Shampoo", "unidade": "ml", "consumo_padrao": (300, 30),
     "descricao_sugerida": "Cabelos secos", "quantidade_sugerida": 350},
    {"tipo": "Sabonete", "unidade": "unidade", "consumo_padrao": (1, 7),
     "descricao_sugerida": "Sabonete em barra", "quantidade_sugerida": 6},
    {"tipo": "Detergente", "unidade": "ml", "consumo_padrao": (500, 30),
     "descricao_sugerida": "Detergente líquido neutro", "quantidade_sugerida": 500},
    {"tipo": "Sabão para roupas", "unidade": "ml", "consumo_padrao": (1000, 30),
     "descricao_sugerida": "Sabão líquido para roupas", "quantidade_sugerida": 1000},
    {"tipo": "Amaciante", "unidade": "ml", "consumo_padrao": (500, 30),
     "descricao_sugerida": "Amaciante concentrado", "quantidade_sugerida": 1000},
]


def busca_tipo(nome: str) -> Optional[TipoCatalogo]:
    """Busca um tipo do catálogo pelo nome exato."""
    for item in CATALOGO_TIPOS:
        if item["tipo"] == nome:
            return item
    return None
