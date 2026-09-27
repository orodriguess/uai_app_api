from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field

from model.catalogo import CATALOGO_TIPOS
from model.evento_estoque import EventoEstoque


class TipoProdutoSchema(BaseModel):
    """ Define como um tipo de produto do catálogo é representado.
    """
    tipo: str = "Café"
    unidade: str = "g"
    descricao_sugerida: str = "Cafezim é bão dimais, sô"
    quantidade_sugerida: float = 500


class ListagemTiposSchema(BaseModel):
    """ Define como a listagem de tipos de produto será retornada.
    """
    tipos: List[TipoProdutoSchema]


def apresenta_tipos():
    """ Retorna a representação do catálogo de tipos suportados.
    """
    return {"tipos": [
        {
            "tipo": t["tipo"],
            "unidade": t["unidade"],
            "descricao_sugerida": t["descricao_sugerida"],
            "quantidade_sugerida": t["quantidade_sugerida"],
        }
        for t in CATALOGO_TIPOS
    ]}


class ItemSchema(BaseModel):
    """ Define como uma nova compra deve ser representada.
    """
    tipo: str = Field(..., json_schema_extra={"example": "Café"})
    quantidade_comprada: float = Field(..., json_schema_extra={"example": 500})
    data_compra: Optional[date] = None
    descricao: Optional[str] = Field(None, json_schema_extra={"example": "Cafezim é bão dimais, sô"})


class CompraEdicaoSchema(BaseModel):
    """ Define os dados corrigíveis de uma compra já registrada.
    """
    quantidade_comprada: float = Field(..., json_schema_extra={"example": 5})
    data_compra: date
    descricao: Optional[str] = Field(None, json_schema_extra={"example": "Arroz branco tipo 1"})


class ItemPathSchema(BaseModel):
    """ Define a estrutura do identificador de uma compra registrada.
    """
    item_id: int = Field(..., description="Identificador da compra")


class TipoPathSchema(BaseModel):
    """ Define a estrutura do nome do tipo usado nas rotas por tipo.
    """
    tipo: str = Field(..., description="Nome do tipo de produto")


class ItensQuerySchema(BaseModel):
    """ Define o filtro usado para listar as compras de um tipo.
    """
    tipo: str = Field(..., description="Nome do tipo de produto")


class SituacaoTipoSchema(BaseModel):
    """ Define como a situação de um tipo na despensa é retornada.
    """
    tipo: str = "Arroz"
    descricao: Optional[str] = None
    saldo: float = 3.5
    unidade: str = "kg"
    nivel: float = 0.7
    data_prevista: date
    dias_restantes: int = 23
    consumo_mensal: float = 4.5
    taxa_quantidade: float = 0.15
    taxa_periodo_dias: int = 1
    pendente_conferencia: bool = False


class DespensaSchema(BaseModel):
    """ Define como a despensa, um registro por tipo, será retornada.
    """
    tipos: List[SituacaoTipoSchema]


class CompraViewSchema(BaseModel):
    """ Define como uma compra registrada é retornada.
    """
    id: int = 1
    tipo: str = "Arroz"
    quantidade_comprada: float = 5
    unidade: str = "kg"
    data_compra: date
    descricao: Optional[str] = None


class ListagemComprasSchema(BaseModel):
    """ Define como a listagem de compras de um tipo será retornada.
    """
    itens: List[CompraViewSchema]


class TaxaSchema(BaseModel):
    """ Define a taxa de consumo de um tipo, na forma em que a pessoa informa.
    """
    tipo: str = Field(..., json_schema_extra={"example": "Arroz"})
    quantidade: float = Field(..., json_schema_extra={"example": 1})
    periodo_dias: int = Field(..., json_schema_extra={"example": 7}, description="1 (dia), 7 (semana) ou 30 (mês)")


class TaxasLoteSchema(BaseModel):
    """ Define o lote de taxas enviado pela edição em lote.
    """
    taxas: List[TaxaSchema]


class ConferenciaSchema(BaseModel):
    """ Define a quantidade realmente disponível informada na conferência.
    """
    quantidade: float = Field(..., json_schema_extra={"example": 0.5})


class ItemDelSchema(BaseModel):
    """ Define como deve ser a estrutura do dado retornado após uma
        requisição de remoção.
    """
    mensagem: str
    id: int


def apresenta_situacao(situacao: dict):
    """ Retorna a representação da situação de um tipo na despensa.
    """
    return {
        "tipo": situacao["tipo"],
        "descricao": situacao["descricao"],
        "saldo": round(situacao["saldo"], 3),
        "unidade": situacao["unidade"],
        "nivel": round(situacao["nivel"], 4),
        "data_prevista": situacao["data_prevista"].isoformat(),
        "dias_restantes": situacao["dias_restantes"],
        "consumo_mensal": round(situacao["consumo_mensal"], 3),
        "taxa_quantidade": round(situacao["taxa_quantidade"], 4),
        "taxa_periodo_dias": situacao["taxa_periodo_dias"],
        "pendente_conferencia": situacao["pendente_conferencia"],
    }


def apresenta_despensa(situacoes: List[dict]):
    """ Retorna a representação da despensa inteira.
    """
    return {"tipos": [apresenta_situacao(s) for s in situacoes]}


def apresenta_compra(evento: EventoEstoque):
    """ Retorna a representação de uma compra registrada.
    """
    return {
        "id": evento.id,
        "tipo": evento.tipo,
        "quantidade_comprada": evento.quantidade,
        "unidade": evento.unidade,
        "data_compra": evento.data.isoformat(),
        "descricao": evento.descricao,
    }


def apresenta_compras(eventos: List[EventoEstoque]):
    """ Retorna a representação de uma listagem de compras.
    """
    return {"itens": [apresenta_compra(evento) for evento in eventos]}
