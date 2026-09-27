from datetime import date, timedelta
from typing import Optional

from model.catalogo import busca_tipo
from model.evento_estoque import (ALTERACAO_TAXA, COMPRA, CONFERENCIA,
                                  EventoEstoque)
from model.taxa_consumo import TaxaConsumo

# Duração de um mês de consumo, base do nível de enchimento.
DIAS_NO_MES = 30

# Fração do consumo mensal abaixo da qual o tipo passa a pedir conferência.
LIMITE_CONFERENCIA = 0.2

# Períodos aceitos para a taxa de consumo: dia, semana ou mês. A recalibração
# automática também grava em um deles (ver `registrar_conferencia`).
PERIODOS_VALIDOS = (1, 7, 30)


def eventos_do_tipo(session, tipo: str) -> list:
    """Eventos do livro de um tipo, em ordem cronológica."""
    return (session.query(EventoEstoque)
            .filter(EventoEstoque.tipo == tipo)
            .order_by(EventoEstoque.data, EventoEstoque.id)
            .all())


def tipos_no_livro(session) -> list:
    """Tipos que já tiveram ao menos um evento registrado."""
    registros = (session.query(EventoEstoque.tipo)
                 .distinct()
                 .order_by(EventoEstoque.tipo)
                 .all())
    return [registro[0] for registro in registros]


def taxa_do_tipo(session, tipo: str) -> Optional[TaxaConsumo]:
    """Taxa pessoal registrada para o tipo, quando existir."""
    return session.query(TaxaConsumo).filter(TaxaConsumo.tipo == tipo).first()


def consumo_padrao(tipo: str) -> tuple:
    """Consumo de partida do tipo, vindo do catálogo: (quantidade, período em dias)."""
    tipo_catalogo = busca_tipo(tipo)
    return tipo_catalogo["consumo_padrao"] if tipo_catalogo else (0.0, 1)


def taxa_diaria_padrao(tipo: str) -> float:
    """Taxa diária de partida do tipo, derivada do consumo padrão do catálogo."""
    quantidade, periodo_dias = consumo_padrao(tipo)
    return quantidade / periodo_dias


def taxa_diaria_vigente(session, tipo: str) -> float:
    """Taxa diária em vigor: a definida pela pessoa ou o padrão do catálogo."""
    taxa = taxa_do_tipo(session, tipo)
    if taxa:
        return taxa.taxa_diaria()
    return taxa_diaria_padrao(tipo)


def reapurar(session, tipo: str) -> None:
    """Reescreve os campos derivados de todo o livro do tipo.

    Percorre os eventos em ordem cronológica, descontando o consumo entre
    eventos consecutivos com piso em zero a cada trecho, de modo que dias
    sem estoque não sejam descontados da compra seguinte.

    O livro é reapurado por inteiro a cada escrita, pois compras
    retroativas e remoções alteram eventos intermediários.
    """
    saldo = 0.0
    taxa = taxa_diaria_padrao(tipo)
    anterior = None

    for evento in eventos_do_tipo(session, tipo):
        if anterior is not None:
            dias = (evento.data - anterior.data).days
            saldo = max(0.0, saldo - taxa * dias)

        if evento.especie == COMPRA:
            saldo = saldo + (evento.quantidade or 0.0)
            evento.taxa_diaria_vigente = taxa
        elif evento.especie == CONFERENCIA:
            saldo = evento.quantidade or 0.0
            taxa = evento.taxa_diaria_vigente
        elif evento.especie == ALTERACAO_TAXA:
            taxa = evento.taxa_diaria_vigente

        evento.saldo_resultante = saldo
        anterior = evento


def saldo_corrente(session, tipo: str, referencia: Optional[date] = None) -> float:
    """Saldo de hoje: o saldo congelado no último evento, menos o consumo desde ele."""
    referencia = referencia or date.today()
    eventos = eventos_do_tipo(session, tipo)
    if not eventos:
        return 0.0

    ultimo = eventos[-1]
    dias = max(0, (referencia - ultimo.data).days)
    return max(0.0, ultimo.saldo_resultante - ultimo.taxa_diaria_vigente * dias)


def pendente_conferencia(session, tipo: str, saldo: Optional[float] = None,
                         referencia: Optional[date] = None) -> bool:
    """Indica se o tipo pede conferência de saldo.

    A conferência é pedida quando o saldo está no limite ou abaixo dele e,
    desde a última conferência, algum evento elevou o saldo acima desse
    limite. Isso evita pedir nova conferência logo após uma já registrada.
    """
    taxa = taxa_diaria_vigente(session, tipo)
    consumo_mensal = taxa * DIAS_NO_MES
    if consumo_mensal <= 0:
        return False

    eventos = eventos_do_tipo(session, tipo)
    if not eventos:
        return False

    if saldo is None:
        saldo = saldo_corrente(session, tipo, referencia)

    limite = LIMITE_CONFERENCIA * consumo_mensal
    if saldo > limite:
        return False

    indice_conferencia = None
    for indice, evento in enumerate(eventos):
        if evento.especie == CONFERENCIA:
            indice_conferencia = indice

    if indice_conferencia is None:
        return True

    posteriores = eventos[indice_conferencia + 1:]
    return any(evento.saldo_resultante > limite for evento in posteriores)


def situacao_do_tipo(session, tipo: str, referencia: Optional[date] = None) -> dict:
    """Retrato atual de um tipo: saldo, nível do pote e previsão de término."""
    referencia = referencia or date.today()
    tipo_catalogo = busca_tipo(tipo)
    unidade = tipo_catalogo["unidade"] if tipo_catalogo else ""

    taxa_diaria = taxa_diaria_vigente(session, tipo)
    saldo = saldo_corrente(session, tipo, referencia)
    consumo_mensal = taxa_diaria * DIAS_NO_MES

    nivel = min(1.0, saldo / consumo_mensal) if consumo_mensal > 0 else 0.0
    dias_restantes = int(saldo / taxa_diaria) if taxa_diaria > 0 else 0

    taxa = taxa_do_tipo(session, tipo)
    quantidade_taxa, periodo_taxa = ((taxa.quantidade, taxa.periodo_dias) if taxa
                                     else consumo_padrao(tipo))

    return {
        "tipo": tipo,
        "descricao": descricao_mais_recente(session, tipo),
        "saldo": saldo,
        "unidade": unidade,
        "nivel": nivel,
        "data_prevista": referencia + timedelta(days=dias_restantes),
        "dias_restantes": dias_restantes,
        "consumo_mensal": consumo_mensal,
        "taxa_quantidade": quantidade_taxa,
        "taxa_periodo_dias": periodo_taxa,
        "pendente_conferencia": pendente_conferencia(session, tipo, saldo, referencia),
    }


def descricao_mais_recente(session, tipo: str) -> Optional[str]:
    """Descrição da compra mais recente do tipo, quando houver."""
    compra = (session.query(EventoEstoque)
              .filter(EventoEstoque.tipo == tipo,
                      EventoEstoque.especie == COMPRA,
                      EventoEstoque.descricao.isnot(None))
              .order_by(EventoEstoque.data.desc(), EventoEstoque.id.desc())
              .first())
    return compra.descricao if compra else None


def consumo_observado(session, tipo: str, quantidade_informada: float,
                      data_conferencia: date):
    """Consumo real entre o último evento e a conferência.

    Retorna o par (quantidade, dias) observado, ou None quando não há
    observação utilizável: nenhum dia decorrido, ou consumo nulo ou
    negativo (saldo informado maior que o previsto).
    """
    eventos = eventos_do_tipo(session, tipo)
    if not eventos:
        return None

    anterior = eventos[-1]
    dias = (data_conferencia - anterior.data).days
    consumido = anterior.saldo_resultante - quantidade_informada

    if dias <= 0 or consumido <= 0:
        return None

    return consumido, dias


def registrar_compra(session, tipo: str, unidade: str, quantidade: float,
                     data_compra: date, descricao: Optional[str]) -> EventoEstoque:
    """Registra a compra e reapura o livro do tipo."""
    evento = EventoEstoque(
        tipo=tipo,
        especie=COMPRA,
        data=data_compra,
        unidade=unidade,
        quantidade=quantidade,
        descricao=descricao,
    )
    session.add(evento)
    session.flush()
    reapurar(session, tipo)
    return evento


def registrar_alteracao_taxa(session, tipo: str, quantidade: float,
                             periodo_dias: int, referencia: Optional[date] = None) -> None:
    """Grava a nova taxa do tipo e registra o evento que congela o saldo.

    O saldo apurado até aqui fica congelado no evento, de modo que a taxa
    nova incide apenas sobre o estoque restante.
    """
    referencia = referencia or date.today()
    tipo_catalogo = busca_tipo(tipo)
    unidade = tipo_catalogo["unidade"] if tipo_catalogo else ""

    taxa = taxa_do_tipo(session, tipo)
    if taxa:
        taxa.quantidade = quantidade
        taxa.periodo_dias = periodo_dias
    else:
        session.add(TaxaConsumo(tipo=tipo, quantidade=quantidade,
                                periodo_dias=periodo_dias))

    evento = EventoEstoque(
        tipo=tipo,
        especie=ALTERACAO_TAXA,
        data=referencia,
        unidade=unidade,
        taxa_diaria_vigente=quantidade / periodo_dias,
    )
    session.add(evento)
    session.flush()
    reapurar(session, tipo)


def registrar_conferencia(session, tipo: str, quantidade_informada: float,
                          referencia: Optional[date] = None) -> None:
    """Registra a conferência, substituindo o saldo e recalibrando a taxa.

    Quando não há consumo observável — nenhum dia decorrido desde o evento
    anterior, ou saldo informado maior que o previsto — a taxa vigente é
    preservada e apenas o saldo é corrigido.
    """
    referencia = referencia or date.today()
    tipo_catalogo = busca_tipo(tipo)
    unidade = tipo_catalogo["unidade"] if tipo_catalogo else ""

    observado = consumo_observado(session, tipo, quantidade_informada, referencia)

    if observado:
        consumido, dias = observado
        taxa_diaria = consumido / dias

        # Converte a taxa observada para o período já utilizado pelo tipo.
        taxa = taxa_do_tipo(session, tipo)
        periodo = (taxa.periodo_dias if taxa and taxa.periodo_dias in PERIODOS_VALIDOS
                   else consumo_padrao(tipo)[1])
        quantidade = round(taxa_diaria * periodo, 3)

        if taxa:
            taxa.quantidade = quantidade
            taxa.periodo_dias = periodo
        else:
            session.add(TaxaConsumo(tipo=tipo, quantidade=quantidade,
                                    periodo_dias=periodo))
    else:
        taxa_diaria = taxa_diaria_vigente(session, tipo)

    evento = EventoEstoque(
        tipo=tipo,
        especie=CONFERENCIA,
        data=referencia,
        unidade=unidade,
        quantidade=quantidade_informada,
        taxa_diaria_vigente=taxa_diaria,
    )
    session.add(evento)
    session.flush()
    reapurar(session, tipo)
