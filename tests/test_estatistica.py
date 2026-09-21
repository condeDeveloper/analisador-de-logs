import pytest

from logs.estatistica import Resumo, percentil, taxa


def test_percentil_zero_e_cem_sao_as_pontas():
    valores = [1, 2, 3, 4, 5]

    assert percentil(valores, 0) == 1
    assert percentil(valores, 100) == 5


def test_mediana_de_quantidade_impar():
    assert percentil([1, 2, 3], 50) == 2


def test_mediana_de_quantidade_par_interpola():
    assert percentil([1, 2, 3, 4], 50) == 2.5


def test_interpola_entre_dois_valores():
    # Entre 10 e 20, o percentil 25 de dois pontos fica a um quarto do caminho.
    assert percentil([10, 20], 25) == 12.5


def test_um_valor_so():
    assert percentil([7], 95) == 7


def test_a_ordem_de_entrada_nao_importa():
    assert percentil([5, 1, 3], 50) == percentil([1, 3, 5], 50)


def test_percentil_de_nada_reclama():
    with pytest.raises(ValueError):
        percentil([], 50)


@pytest.mark.parametrize("p", [-1, 101])
def test_percentil_fora_da_faixa_reclama(p):
    with pytest.raises(ValueError):
        percentil([1, 2], p)


def test_resumo_traz_os_numeros_que_importam():
    resumo = Resumo.de(range(1, 101))

    assert resumo.quantidade == 100
    assert resumo.minimo == 1
    assert resumo.maximo == 100
    assert resumo.media == pytest.approx(50.5)
    assert resumo.mediana == pytest.approx(50.5)
    assert resumo.p95 == pytest.approx(95.05)
    assert resumo.p99 == pytest.approx(99.01)


def test_o_resumo_ignora_o_que_nao_e_numero():
    resumo = Resumo.de([1, "a", None, 3, True])

    assert resumo.quantidade == 2


def test_resumo_de_nada_devolve_nulo():
    assert Resumo.de([]) is None
    assert Resumo.de(["a", None]) is None


def test_o_desvio_de_valores_iguais_e_zero():
    assert Resumo.de([5, 5, 5]).desvio == 0


def test_a_media_esconde_a_cauda_e_o_p99_nao():
    # Dois por cento das requisições são lentas: a média mal se mexe, o p99
    # denuncia.
    resumo = Resumo.de([10] * 980 + [5000] * 20)

    assert resumo.media < 120
    assert resumo.p99 > 4000


def test_com_exatamente_um_por_cento_de_lentidao_o_p99_fica_na_fronteira():
    # Com uma única amostra lenta em cem, o p99 cai justamente entre a
    # penúltima e a última, e a interpolação devolve um valor intermediário.
    # Não é bug: é o que "percentil por interpolação" significa, e é por isso
    # que p99 de amostra pequena engana.
    resumo = Resumo.de([10] * 99 + [5000])

    assert resumo.p99 == pytest.approx(59.9)
    assert resumo.maximo == 5000


def test_a_linha_do_resumo_e_legivel():
    linha = Resumo.de([1, 2, 3]).linha("ms")

    assert "n=3" in linha
    assert "ms" in linha


def test_taxa():
    assert taxa(1, 4) == 25
    assert taxa(0, 0) == 0
    assert taxa(5, 0) == 0
