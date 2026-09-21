from datetime import datetime, timedelta

from logs import analisar, relatorio
from logs.evento import Evento
from tests import exemplos


def test_relatorio_de_nada():
    assert relatorio.montar([]) == "Nenhum evento."


def test_o_resumo_conta_eventos_e_erros():
    texto = relatorio.montar(analisar(exemplos.ACESSO))

    assert "eventos          5" in texto
    assert "erros            2" in texto
    assert "40.0%" in texto


def test_mostra_o_periodo():
    texto = relatorio.montar(analisar(exemplos.ACESSO))

    assert "período" in texto
    assert "21/09/2026" in texto


def test_lista_os_niveis_presentes():
    texto = relatorio.montar(analisar(exemplos.ACESSO))

    assert "ERRO" in texto
    assert "AVISO" in texto
    assert "CRITICO" not in texto


def test_lista_as_rotas_mais_frequentes():
    texto = relatorio.montar(analisar(exemplos.ACESSO))

    assert "/api/relatorio" in texto


def test_mostra_a_latencia_quando_ha_duracao():
    texto = relatorio.montar(analisar(exemplos.ACESSO))

    assert "Latência" in texto
    assert "p99" in texto


def test_omite_a_latencia_quando_nao_ha_duracao():
    eventos = [Evento(bruto="x", mensagem="sem duração")]

    assert "Latência" not in relatorio.montar(eventos)


def test_mostra_as_mensagens_de_erro_mais_comuns():
    texto = relatorio.montar(analisar(exemplos.TEXTO))

    assert "Mensagens de erro mais comuns" in texto
    assert "falha na conexão" in texto


def test_desenha_a_serie_temporal():
    momentos = [datetime(2026, 9, 21, 10, minuto) for minuto in range(6)]
    eventos = [Evento(bruto="x", momento=momento) for momento in momentos]

    texto = relatorio.montar(eventos, intervalo=timedelta(minutes=1))

    assert "Volume por 1min" in texto


def test_aponta_os_picos():
    momentos = [datetime(2026, 9, 21, 10, 0)] * 50 + [datetime(2026, 9, 21, 10, m) for m in range(1, 6)]
    eventos = [Evento(bruto="x", momento=momento) for momento in momentos]

    texto = relatorio.montar(eventos, intervalo=timedelta(minutes=1))

    assert "picos" in texto


def test_a_barra_e_proporcional():
    assert len(relatorio.barra(10, 10, 20)) == 20
    assert len(relatorio.barra(5, 10, 20)) == 10
    assert relatorio.barra(0, 10) == ""
    assert relatorio.barra(1, 0) == ""


def test_valor_pequeno_ainda_desenha_um_bloco():
    assert relatorio.barra(1, 1000, 10) == "█"


def test_a_faixa_desenha_um_bloco_por_janela():
    serie = [(datetime(2026, 9, 21, 10, minuto), minuto) for minuto in range(5)]

    assert len(relatorio.faixa(serie)) == 5


def test_faixa_de_serie_vazia():
    assert relatorio.faixa([]) == ""


def test_faixa_toda_zerada():
    serie = [(datetime(2026, 9, 21, 10, minuto), 0) for minuto in range(3)]

    assert relatorio.faixa(serie) == "▁▁▁"
