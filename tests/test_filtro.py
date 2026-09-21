import pytest

from logs import analisar
from logs.evento import Evento
from logs.filtro import ErroDeFiltro, compilar
from tests import exemplos


@pytest.fixture()
def eventos():
    return analisar(exemplos.ACESSO)


def filtrar(eventos, expressao):
    return list(compilar(expressao).aplicar(eventos))


def test_filtro_vazio_deixa_tudo_passar(eventos):
    assert len(filtrar(eventos, "")) == len(eventos)
    assert len(filtrar(eventos, None)) == len(eventos)


def test_igualdade_em_texto(eventos):
    assert len(filtrar(eventos, "metodo = GET")) == 4


def test_comparacao_numerica(eventos):
    assert len(filtrar(eventos, "status >= 500")) == 2
    assert len(filtrar(eventos, "status < 300")) == 2


def test_a_comparacao_numerica_nao_e_alfabetica(eventos):
    # Se comparasse como texto, "404" seria maior que "1234".
    assert len(filtrar(eventos, "bytes > 100")) == 1


def test_diferente(eventos):
    assert len(filtrar(eventos, "status != 500")) == 3


def test_contem(eventos):
    assert len(filtrar(eventos, "rota ~ relatorio")) == 2


def test_nao_contem(eventos):
    assert len(filtrar(eventos, "rota !~ relatorio")) == 3


def test_contem_ignora_a_caixa(eventos):
    assert len(filtrar(eventos, "agente ~ MOZILLA")) == 3


def test_e_junta_as_condicoes(eventos):
    assert len(filtrar(eventos, "status >= 500 e rota ~ relatorio")) == 2


def test_ou_soma_as_condicoes(eventos):
    assert len(filtrar(eventos, "status = 404 ou status = 500")) == 3


def test_nao_inverte(eventos):
    assert len(filtrar(eventos, "nao status = 500")) == 3


def test_parenteses_mudam_a_ordem(eventos):
    com = filtrar(eventos, "(status = 404 ou status = 500) e metodo = GET")
    sem = filtrar(eventos, "status = 404 ou status = 500 e metodo = GET")

    assert len(com) == 3
    assert len(sem) == 3


def test_palavra_solta_procura_na_linha_inteira(eventos):
    assert len(filtrar(eventos, "bot")) == 1


def test_texto_entre_aspas_permite_espaco(eventos):
    assert len(filtrar(eventos, 'agente ~ "Mozilla/5.0"')) == 3


def test_o_nivel_e_comparado_por_gravidade(eventos):
    # Por ordem alfabética "ERRO" viria antes de "INFO"; o que vale é a escala.
    assert len(filtrar(eventos, "nivel >= AVISO")) == 3


def test_campo_ausente_nao_satisfaz_comparacao(eventos):
    assert filtrar(eventos, "inexistente >= 1") == []


def test_campo_ausente_satisfaz_diferente(eventos):
    assert len(filtrar(eventos, "inexistente != 1")) == len(eventos)


def test_filtra_por_momento():
    eventos = analisar(exemplos.TEXTO)

    assert len(filtrar(eventos, "momento >= 2026-09-21T10:00:02")) == 3


def test_filtra_por_mensagem():
    eventos = analisar(exemplos.TEXTO)

    assert len(filtrar(eventos, 'mensagem ~ "falha na conexão"')) == 2


def test_aceita_operadores_em_ingles(eventos):
    assert len(filtrar(eventos, "status = 500 and metodo = GET")) == 2
    assert len(filtrar(eventos, "status = 404 or status = 500")) == 3


def test_o_filtro_se_descreve_de_volta():
    assert str(compilar("status >= 500")) == "status >= 500"


def test_o_filtro_e_chamavel_direto():
    filtro = compilar("nivel = ERRO")

    assert filtro(Evento(bruto="", nivel="ERRO")) is True
    assert filtro(Evento(bruto="", nivel="INFO")) is False


@pytest.mark.parametrize("expressao", ["status >=", "(status = 1", "status = 1 e", "nao"])
def test_filtro_malformado_reclama(expressao):
    with pytest.raises(ErroDeFiltro):
        compilar(expressao)


def test_uma_conjuncao_sozinha_vale_como_busca_de_texto(eventos):
    # "e" sem nada em volta não é operador pendurado: é palavra solta, e
    # palavra solta procura na linha inteira.
    assert len(filtrar(eventos, "e")) == len(eventos)


def test_o_booleano_e_comparado_como_verdadeiro_ou_falso():
    eventos = [Evento(bruto="", campos={"ativo": True}), Evento(bruto="", campos={"ativo": False})]

    assert len(filtrar(eventos, "ativo = true")) == 1
    assert len(filtrar(eventos, "ativo = false")) == 1
