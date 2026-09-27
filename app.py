from datetime import date

from flask import redirect
from flask_cors import CORS
from flask_openapi3 import Info, OpenAPI, Tag

from logger import logger
from model import Session
from model import estoque
from model.catalogo import busca_tipo
from model.evento_estoque import COMPRA, EventoEstoque
from model.exemplos import recria_banco_com_exemplos
from schemas import *

info = Info(title="UAI - Acabou? Não mais.", version="2.0.0")
app = OpenAPI(__name__, info=info)
CORS(app)

# Recria o banco com os dados de demonstração a cada inicialização
recria_banco_com_exemplos()

# Tags da documentação OpenAPI
home_tag = Tag(name="Documentação", description="Acesso à documentação interativa da API (Swagger UI)")
catalogo_tag = Tag(name="Catálogo", description="Consulta dos tipos de produto suportados pelo UAI")
despensa_tag = Tag(name="Despensa", description="Saldo por tipo, previsão de término e nível de enchimento")
item_tag = Tag(name="Compra", description="Registro, consulta e remoção de compras")
taxa_tag = Tag(name="Consumo", description="Taxa de consumo por tipo e conferência de saldo")


@app.get('/', tags=[home_tag])
def home():
    """Redireciona para /openapi, página da documentação interativa da API (Swagger UI).
    """
    return redirect('/openapi')


@app.get('/tipos-produtos', tags=[catalogo_tag],
         responses={"200": ListagemTiposSchema})
def get_tipos_produtos():
    """Lista os tipos de produto suportados pelo UAI

    Retorna, para cada tipo, a unidade e as sugestões de descrição e
    quantidade usadas para pré-preencher o cadastro de uma compra.
    """
    logger.debug("Coletando tipos de produto do catálogo")
    return apresenta_tipos(), 200


@app.get('/despensa', tags=[despensa_tag],
         responses={"200": DespensaSchema})
def get_despensa():
    """Lista a despensa, com um registro por tipo

    Retorna, para cada tipo já registrado, o saldo acumulado, o nível de
    enchimento sobre o consumo mensal, a data prevista de término, os dias
    restantes, a taxa vigente e se o tipo está pedindo conferência.
    """
    logger.debug("Coletando a despensa por tipo")
    with Session() as session:
        situacoes = [estoque.situacao_do_tipo(session, tipo)
                     for tipo in estoque.tipos_no_livro(session)]
        situacoes.sort(key=lambda s: s["dias_restantes"])
        return apresenta_despensa(situacoes), 200


@app.post('/item', tags=[item_tag],
          responses={"200": SituacaoTipoSchema, "400": ErrorSchema})
def add_item(body: ItemSchema):
    """Registra uma compra e soma ao saldo do tipo

    O tipo deve existir no catálogo, a quantidade comprada deve ser maior
    que zero e a data de compra não pode ser futura. A taxa aplicada é a
    vigente do tipo — a definida pela pessoa quando existir, ou a padrão do
    catálogo — sem necessidade de informá-la.
    """
    tipo_catalogo = busca_tipo(body.tipo)
    if not tipo_catalogo:
        error_msg = "Tipo de produto não encontrado no catálogo"
        logger.warning(f"Erro ao registrar compra do tipo '{body.tipo}', {error_msg}")
        return {"mensagem": error_msg}, 400

    if body.quantidade_comprada <= 0:
        error_msg = "Quantidade comprada deve ser maior que zero :/"
        logger.warning(f"Erro ao registrar compra do tipo '{body.tipo}', {error_msg}")
        return {"mensagem": error_msg}, 400

    data_compra = body.data_compra or date.today()
    if data_compra > date.today():
        error_msg = "Data de compra não pode ser futura"
        logger.warning(f"Erro ao registrar compra do tipo '{body.tipo}', {error_msg}")
        return {"mensagem": error_msg}, 400

    with Session() as session:
        estoque.registrar_compra(
            session,
            tipo=tipo_catalogo["tipo"],
            unidade=tipo_catalogo["unidade"],
            quantidade=body.quantidade_comprada,
            data_compra=data_compra,
            descricao=body.descricao,
        )
        session.commit()

        logger.debug(f"Compra registrada para '{tipo_catalogo['tipo']}'")
        return apresenta_situacao(estoque.situacao_do_tipo(session, tipo_catalogo["tipo"])), 200


@app.get('/itens', tags=[item_tag],
         responses={"200": ListagemComprasSchema})
def get_itens(query: ItensQuerySchema):
    """Lista as compras registradas de um tipo

    Usada para corrigir um registro equivocado: traz os identificadores que
    a rota de remoção espera.
    """
    logger.debug(f"Coletando compras do tipo '{query.tipo}'")
    with Session() as session:
        compras = (session.query(EventoEstoque)
                   .filter(EventoEstoque.tipo == query.tipo,
                           EventoEstoque.especie == COMPRA)
                   .order_by(EventoEstoque.data.desc(), EventoEstoque.id.desc())
                   .all())
        return apresenta_compras(compras), 200


@app.put('/item/<int:item_id>', tags=[item_tag],
         responses={"200": SituacaoTipoSchema, "400": ErrorSchema, "404": ErrorSchema})
def edit_item(path: ItemPathSchema, body: CompraEdicaoSchema):
    """Corrige a quantidade, a data ou a descrição de uma compra registrada

    Aplica as mesmas validações do cadastro. O tipo não é alterável: uma
    compra do tipo errado deve ser removida e registrada de novo. O livro do
    tipo é reapurado após a correção.
    """
    with Session() as session:
        compra = (session.query(EventoEstoque)
                  .filter(EventoEstoque.id == path.item_id,
                          EventoEstoque.especie == COMPRA)
                  .first())

        if not compra:
            error_msg = "Compra não encontrada na base :/"
            logger.warning(f"Erro ao corrigir compra #{path.item_id}, {error_msg}")
            return {"mensagem": error_msg}, 404

        if body.quantidade_comprada <= 0:
            error_msg = "Quantidade comprada deve ser maior que zero :/"
            logger.warning(f"Erro ao corrigir compra #{path.item_id}, {error_msg}")
            return {"mensagem": error_msg}, 400

        if body.data_compra > date.today():
            error_msg = "Data de compra não pode ser futura"
            logger.warning(f"Erro ao corrigir compra #{path.item_id}, {error_msg}")
            return {"mensagem": error_msg}, 400

        compra.quantidade = body.quantidade_comprada
        compra.data = body.data_compra
        compra.descricao = body.descricao or None
        session.flush()
        estoque.reapurar(session, compra.tipo)
        session.commit()

        logger.debug(f"Compra corrigida #{path.item_id}")
        return apresenta_situacao(estoque.situacao_do_tipo(session, compra.tipo)), 200


@app.delete('/item/<int:item_id>', tags=[item_tag],
            responses={"200": ItemDelSchema, "404": ErrorSchema})
def del_item(path: ItemPathSchema):
    """Remove uma compra registrada por engano

    O livro do tipo é reapurado após a remoção, de modo que o saldo passa a
    desconsiderar a quantidade removida.
    """
    with Session() as session:
        compra = (session.query(EventoEstoque)
                  .filter(EventoEstoque.id == path.item_id,
                          EventoEstoque.especie == COMPRA)
                  .first())

        if not compra:
            error_msg = "Compra não encontrada na base :/"
            logger.warning(f"Erro ao remover compra #{path.item_id}, {error_msg}")
            return {"mensagem": error_msg}, 404

        tipo = compra.tipo
        session.delete(compra)
        session.flush()
        estoque.reapurar(session, tipo)
        session.commit()

        logger.debug(f"Compra removida #{path.item_id}")
        return {"mensagem": "Compra removida", "id": path.item_id}, 200


@app.put('/taxas', tags=[taxa_tag],
         responses={"200": DespensaSchema, "400": ErrorSchema})
def put_taxas(body: TaxasLoteSchema):
    """Altera a taxa de consumo de vários tipos de uma vez

    A quantidade deve ser maior que zero e o período deve ser de 1, 7 ou 30
    dias. Um único valor inválido rejeita o lote inteiro. Só é registrado
    evento de alteração para os tipos cuja taxa efetivamente mudou, e a taxa
    nova incide apenas sobre o estoque restante.
    """
    with Session() as session:
        for taxa in body.taxas:
            if not busca_tipo(taxa.tipo):
                error_msg = f"Tipo de produto '{taxa.tipo}' não encontrado no catálogo"
                logger.warning(f"Erro ao alterar taxas, {error_msg}")
                return {"mensagem": error_msg}, 400
            if taxa.quantidade <= 0:
                error_msg = f"Quantidade de consumo de '{taxa.tipo}' deve ser maior que zero :/"
                logger.warning(f"Erro ao alterar taxas, {error_msg}")
                return {"mensagem": error_msg}, 400
            if taxa.periodo_dias not in estoque.PERIODOS_VALIDOS:
                error_msg = f"Período de consumo de '{taxa.tipo}' deve ser de 1, 7 ou 30 dias"
                logger.warning(f"Erro ao alterar taxas, {error_msg}")
                return {"mensagem": error_msg}, 400

        alterados = []
        for taxa in body.taxas:
            if _taxa_mudou(session, taxa):
                estoque.registrar_alteracao_taxa(session, taxa.tipo,
                                                 taxa.quantidade, taxa.periodo_dias)
                alterados.append(taxa.tipo)

        session.commit()
        logger.debug(f"Taxas alteradas: {alterados}")

        situacoes = [estoque.situacao_do_tipo(session, tipo) for tipo in alterados]
        return apresenta_despensa(situacoes), 200


def _taxa_mudou(session, taxa) -> bool:
    """Indica se a taxa enviada difere da vigente para aquele tipo."""
    registrada = estoque.taxa_do_tipo(session, taxa.tipo)
    if registrada:
        return (registrada.quantidade != taxa.quantidade
                or registrada.periodo_dias != taxa.periodo_dias)

    return (taxa.quantidade, taxa.periodo_dias) != estoque.consumo_padrao(taxa.tipo)


@app.post('/tipo/<tipo>/conferencia', tags=[taxa_tag],
          responses={"200": SituacaoTipoSchema, "400": ErrorSchema, "404": ErrorSchema})
def add_conferencia(path: TipoPathSchema, body: ConferenciaSchema):
    """Registra a quantidade realmente disponível de um tipo

    A conferência substitui o saldo apurado pela quantidade informada e
    recalibra a taxa a partir do consumo real observado desde o evento
    anterior. Quando não há consumo observável — nenhum dia decorrido, ou
    saldo maior que o previsto — a taxa vigente é preservada.
    """
    if not busca_tipo(path.tipo):
        error_msg = "Tipo de produto não encontrado no catálogo"
        logger.warning(f"Erro ao conferir '{path.tipo}', {error_msg}")
        return {"mensagem": error_msg}, 404

    if body.quantidade < 0:
        error_msg = "Quantidade disponível não pode ser negativa :/"
        logger.warning(f"Erro ao conferir '{path.tipo}', {error_msg}")
        return {"mensagem": error_msg}, 400

    with Session() as session:
        estoque.registrar_conferencia(session, path.tipo, body.quantidade)
        session.commit()

        logger.debug(f"Conferência registrada para '{path.tipo}'")
        return apresenta_situacao(estoque.situacao_do_tipo(session, path.tipo)), 200
