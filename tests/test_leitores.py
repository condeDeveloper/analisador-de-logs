import pytest

from logs import leitores
from logs.evento import Evento, gravidade, normalizar_nivel
from logs.leitores import LeitorDeAcesso, LeitorDeSyslog, LeitorDeTexto, LeitorEstruturado
from logs.leitores.texto import extrair_chave_valor
from tests import exemplos


class TestAcesso:
    def test_le_os_campos_da_requisicao(self):
        evento = LeitorDeAcesso().ler(exemplos.ACESSO[0], 1)

        assert evento.valor("ip") == "192.168.0.10"
        assert evento.valor("metodo") == "GET"
        assert evento.valor("rota") == "/api/pedidos"
        assert evento.valor("status") == 200
        assert evento.valor("bytes") == 1234
        assert evento.valor("duracao_ms") == 42.0

    def test_le_a_data_com_fuso(self):
        evento = LeitorDeAcesso().ler(exemplos.ACESSO[0], 1)

        assert evento.momento.hour == 10
        assert evento.momento.utcoffset().total_seconds() == -3 * 3600

    def test_le_o_usuario_quando_existe(self):
        assert LeitorDeAcesso().ler(exemplos.ACESSO[1], 1).valor("usuario") == "maria"

    def test_ignora_o_usuario_ausente(self):
        assert LeitorDeAcesso().ler(exemplos.ACESSO[0], 1).valor("usuario") is None

    @pytest.mark.parametrize(
        "linha, nivel",
        [(exemplos.ACESSO[0], "INFO"), (exemplos.ACESSO[2], "AVISO"), (exemplos.ACESSO[3], "ERRO")],
    )
    def test_o_status_define_a_gravidade(self, linha, nivel):
        assert LeitorDeAcesso().ler(linha, 1).nivel == nivel

    def test_recusa_linha_de_outro_formato(self):
        assert LeitorDeAcesso().reconhece("qualquer coisa") is False
        assert LeitorDeAcesso().ler("qualquer coisa", 1) is None


class TestTexto:
    def test_le_data_nivel_origem_e_mensagem(self):
        evento = LeitorDeTexto().ler(exemplos.TEXTO[2], 3)

        assert evento.nivel == "ERRO"
        assert evento.origem == "br.com.conde.Banco"
        assert evento.mensagem.startswith("falha na conexão")
        assert evento.momento.minute == 0

    def test_puxa_os_pares_chave_valor_da_mensagem(self):
        evento = LeitorDeTexto().ler(exemplos.TEXTO[2], 3)

        assert evento.valor("status") == 500
        assert evento.valor("duracao_ms") == 1204

    def test_converte_numero_com_ponto(self):
        assert extrair_chave_valor("valor=19.90")["valor"] == pytest.approx(19.9)

    def test_texto_entre_aspas_no_par(self):
        assert extrair_chave_valor('nome="Maria Souza"')["nome"] == "Maria Souza"

    def test_valor_nao_numerico_fica_texto(self):
        assert extrair_chave_valor("sku=ABC")["sku"] == "ABC"


class TestEstruturado:
    def test_le_json(self):
        evento = LeitorEstruturado().ler(exemplos.JSON[1], 2)

        assert evento.nivel == "ERRO"
        assert evento.mensagem == "timeout"
        assert evento.valor("duracao_ms") == 5000

    def test_reconhece_apelidos_de_chave(self):
        evento = LeitorEstruturado().ler('{"ts": 1758456000, "lvl": "warn", "msg": "oi"}', 1)

        assert evento.nivel == "AVISO"
        assert evento.mensagem == "oi"
        assert evento.momento is not None

    def test_milissegundos_viram_data(self):
        evento = LeitorEstruturado().ler('{"ts": 1758456000000, "msg": "x"}', 1)

        assert evento.momento.year >= 2025

    def test_json_invalido_devolve_nada(self):
        assert LeitorEstruturado().ler("{quebrado", 1) is None

    def test_json_que_nao_e_objeto_devolve_nada(self):
        assert LeitorEstruturado().ler("[1, 2]", 1) is None


class TestSyslog:
    def test_le_maquina_processo_e_pid(self):
        evento = LeitorDeSyslog(ano=2026).ler(exemplos.SYSLOG[0], 1)

        assert evento.valor("maquina") == "servidor"
        assert evento.origem == "sshd"
        assert evento.valor("pid") == 1234
        assert evento.momento.year == 2026

    def test_processo_sem_pid(self):
        evento = LeitorDeSyslog(ano=2026).ler("Sep 21 10:00:00 maq servico: mensagem", 1)

        assert evento.valor("pid") is None


class TestDeteccao:
    @pytest.mark.parametrize(
        "linhas, esperado",
        [
            (exemplos.ACESSO, "acesso"),
            (exemplos.TEXTO, "texto"),
            (exemplos.JSON, "json"),
            (exemplos.SYSLOG, "syslog"),
        ],
    )
    def test_detecta_o_formato(self, linhas, esperado):
        assert leitores.detectar(linhas).nome == esperado

    def test_arquivo_vazio_nao_detecta_nada(self):
        assert leitores.detectar([]) is None
        assert leitores.detectar(["", "   "]) is None

    def test_formato_desconhecido_nao_detecta(self):
        assert leitores.detectar(["!!!", "???"]) is None

    def test_busca_leitor_pelo_nome(self):
        assert leitores.por_nome("json").nome == "json"

    def test_nome_invalido_reclama(self):
        with pytest.raises(ValueError):
            leitores.por_nome("inventado")

    def test_lista_os_nomes(self):
        assert "acesso" in leitores.nomes()


class TestLeitura:
    def test_le_uma_linha_de_cada_formato_no_mesmo_arquivo(self):
        eventos = list(leitores.ler(exemplos.MISTURADO))

        assert len(eventos) == 6
        assert {evento.origem for evento in eventos} >= {"acesso", "json"}

    def test_linha_nao_reconhecida_vira_evento_cru(self):
        eventos = list(leitores.ler(["!!! nada a ver"]))

        assert eventos[0].mensagem == "!!! nada a ver"
        assert eventos[0].nivel == "INFO"

    def test_linhas_em_branco_somem(self):
        assert list(leitores.ler(["", "   ", exemplos.TEXTO[0]])) != []
        assert len(list(leitores.ler(["", "   "]))) == 0

    def test_numera_as_linhas(self):
        eventos = list(leitores.ler(exemplos.TEXTO))

        assert [evento.numero for evento in eventos] == [1, 2, 3, 4, 5]

    def test_leitor_forcado_e_usado_para_tudo(self):
        eventos = list(leitores.ler(exemplos.MISTURADO, leitores.por_nome("json")))

        assert sum(1 for evento in eventos if evento.origem == "json") == 1


class TestEvento:
    def test_normaliza_o_nivel(self):
        assert normalizar_nivel("warn") == "AVISO"
        assert normalizar_nivel("FATAL") == "CRITICO"
        assert normalizar_nivel(None) == "INFO"
        assert normalizar_nivel("inventado") == "INFO"

    def test_gravidade_ordena_os_niveis(self):
        assert gravidade("ERRO") > gravidade("AVISO") > gravidade("INFO")

    def test_reconhece_o_que_e_problema(self):
        assert Evento(bruto="", nivel="ERRO").eh_problema is True
        assert Evento(bruto="", nivel="AVISO").eh_problema is False

    def test_valor_busca_nos_embutidos_e_nos_campos(self):
        evento = Evento(bruto="x", nivel="INFO", campos={"status": 200})

        assert evento.valor("nivel") == "INFO"
        assert evento.valor("status") == 200
        assert evento.valor("inexistente") is None

    def test_com_acrescenta_campos_sem_alterar_o_original(self):
        original = Evento(bruto="x", campos={"a": 1})
        copia = original.com(b=2)

        assert copia.valor("a") == 1
        assert copia.valor("b") == 2
        assert original.valor("b") is None

    def test_se_descreve_em_uma_linha(self):
        assert "ERRO" in str(Evento(bruto="", nivel="ERRO", mensagem="caiu"))
