import pytest

from logs import analisar, analisar_arquivo
from logs.__main__ import main
from tests import exemplos


@pytest.fixture()
def arquivo(tmp_path):
    caminho = tmp_path / "acesso.log"
    caminho.write_text("\n".join(exemplos.ACESSO), encoding="utf-8")
    return caminho


def test_analisar_detecta_o_formato_sozinho():
    eventos = analisar(exemplos.ACESSO)

    assert len(eventos) == 5
    assert eventos[0].origem == "acesso"


def test_analisar_aceita_filtro_direto():
    assert len(analisar(exemplos.ACESSO, onde="status >= 500")) == 2


def test_analisar_aceita_formato_forcado():
    assert len(analisar(exemplos.JSON, formato="json")) == 3


def test_analisar_arquivo(arquivo):
    assert len(analisar_arquivo(arquivo)) == 5


def test_relatorio_na_tela(arquivo, capsys):
    assert main([str(arquivo)]) == 0
    assert "Resumo" in capsys.readouterr().out


def test_filtro_pela_linha_de_comando(arquivo, capsys):
    assert main([str(arquivo), "-f", "status >= 500", "--listar"]) == 0

    saida = capsys.readouterr().out
    assert saida.count("\n") == 2


def test_top_de_um_campo(arquivo, capsys):
    assert main([str(arquivo), "--top", "rota"]) == 0
    assert "/api/relatorio" in capsys.readouterr().out


def test_percentis_de_um_campo(arquivo, capsys):
    assert main([str(arquivo), "--percentis", "duracao_ms"]) == 0
    assert "p95" in capsys.readouterr().out


def test_percentis_de_campo_sem_numero(arquivo, capsys):
    assert main([str(arquivo), "--percentis", "metodo"]) == 3
    assert "Nenhum valor" in capsys.readouterr().err


def test_lista_os_formatos(capsys):
    assert main(["--formatos"]) == 0
    assert "acesso" in capsys.readouterr().out


def test_arquivo_inexistente(tmp_path, capsys):
    assert main([str(tmp_path / "nao-existe.log")]) == 1
    assert "não consegui" in capsys.readouterr().err.lower()


def test_filtro_invalido(arquivo, capsys):
    assert main([str(arquivo), "-f", "status >="]) == 2
    assert "inválido" in capsys.readouterr().err.lower()


def test_le_da_entrada_padrao(monkeypatch, capsys):
    import io

    monkeypatch.setattr("sys.stdin", io.StringIO("\n".join(exemplos.TEXTO)))

    assert main([]) == 0
    assert "Resumo" in capsys.readouterr().out


def test_quantidade_limita_a_listagem(arquivo, capsys):
    assert main([str(arquivo), "--top", "rota", "-n", "1"]) == 0
    assert capsys.readouterr().out.count("\n") == 1
