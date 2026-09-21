from datetime import datetime, timedelta

import pytest

from logs import agregacao, analisar
from logs.evento import Evento
from tests import exemplos


@pytest.fixture()
def acessos():
    return analisar(exemplos.ACESSO)


def test_conta_por_campo(acessos):
    contagem = agregacao.contar_por(acessos, "status")

    assert contagem["500"] == 2
    assert contagem["200"] == 1


def test_conta_ignora_quem_nao_tem_o_campo(acessos):
    assert sum(agregacao.contar_por(acessos, "usuario").values()) == 1


def test_agrupa_por_campo(acessos):
    grupos = agregacao.agrupar_por(acessos, "metodo")

    assert set(grupos) == {"GET", "POST"}
    assert len(grupos["GET"]) == 4


def test_pega_os_valores_numericos(acessos):
    valores = agregacao.valores_de(acessos, "duracao_ms")

    assert len(valores) == 5
    assert max(valores) == 3200


def test_valores_ignora_texto():
    eventos = [Evento(bruto="", campos={"x": 1}), Evento(bruto="", campos={"x": "a"})]

    assert agregacao.valores_de(eventos, "x") == [1.0]


def test_top_ordena_do_maior_para_o_menor(acessos):
    maiores = agregacao.top(agregacao.contar_por(acessos, "rota"))

    # /api/pedidos e /api/relatorio empatam em 2; o desempate alfabético põe
    # /api/pedidos na frente, e /api/pedidos/9, com 1, fica por último.
    assert maiores == [("/api/pedidos", 2), ("/api/relatorio", 2), ("/api/pedidos/9", 1)]


def test_top_desempata_em_ordem_alfabetica():
    eventos = [Evento(bruto="", campos={"x": nome}) for nome in ("zebra", "abelha")]

    assert agregacao.top(agregacao.contar_por(eventos, "x")) == [("abelha", 1), ("zebra", 1)]


def test_top_respeita_a_quantidade(acessos):
    assert len(agregacao.top(agregacao.contar_por(acessos, "rota"), 1)) == 1


def test_serie_temporal_agrupa_em_janelas(acessos):
    serie = agregacao.serie_temporal(acessos, timedelta(minutes=1))

    assert len(serie) == 2
    assert serie[0][1] == 3
    assert serie[1][1] == 2


def test_a_serie_preenche_as_janelas_vazias():
    momentos = [datetime(2026, 9, 21, 10, 0), datetime(2026, 9, 21, 10, 5)]
    eventos = [Evento(bruto="", momento=momento) for momento in momentos]

    serie = agregacao.serie_temporal(eventos, timedelta(minutes=1))

    assert len(serie) == 6
    assert [contagem for _, contagem in serie] == [1, 0, 0, 0, 0, 1]


def test_serie_de_eventos_sem_data_e_vazia():
    assert agregacao.serie_temporal([Evento(bruto="x")]) == []


def test_serie_com_intervalo_invalido_reclama(acessos):
    with pytest.raises(ValueError):
        agregacao.serie_temporal(acessos, timedelta(0))


def test_picos_acham_a_janela_fora_da_curva():
    serie = [(datetime(2026, 9, 21, 10, minuto), contagem)
             for minuto, contagem in enumerate([1, 1, 1, 1, 50])]

    encontrados = agregacao.picos(serie)

    assert len(encontrados) == 1
    assert encontrados[0][1] == 50


def test_serie_plana_nao_tem_pico():
    serie = [(datetime(2026, 9, 21, 10, minuto), 5) for minuto in range(5)]

    assert agregacao.picos(serie) == []


def test_serie_vazia_nao_tem_pico():
    assert agregacao.picos([]) == []
