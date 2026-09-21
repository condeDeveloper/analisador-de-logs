"""Linha de comando do analisador."""

from __future__ import annotations

import argparse
import sys
from datetime import timedelta

from . import agregacao, analisar_arquivo, leitores, relatorio
from .estatistica import Resumo
from .filtro import ErroDeFiltro


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada do comando ``logs``."""
    analisador = argparse.ArgumentParser(
        prog="logs",
        description="Lê um arquivo de log, filtra e resume.",
    )
    analisador.add_argument("arquivo", nargs="?", help="arquivo de log; sem ele, lê da entrada padrão")
    analisador.add_argument("-f", "--filtro", help='condição, por exemplo: "status >= 500 e rota ~ /api"')
    analisador.add_argument("--formato", help=f"força o formato ({', '.join(leitores.nomes())})")
    analisador.add_argument("--top", metavar="CAMPO", help="mostra os valores mais frequentes de um campo")
    analisador.add_argument("--percentis", metavar="CAMPO", help="mostra o resumo numérico de um campo")
    analisador.add_argument("-n", "--quantidade", type=int, default=10, help="quantos itens listar (padrão: 10)")
    analisador.add_argument("--intervalo", type=int, default=60, help="janela da série temporal em segundos")
    analisador.add_argument("--listar", action="store_true", help="imprime os eventos em vez do relatório")
    analisador.add_argument("--formatos", action="store_true", help="lista os formatos conhecidos e sai")

    opcoes = analisador.parse_args(argv)
    _garantir_utf8()

    if opcoes.formatos:
        print("\n".join(leitores.nomes()))
        return 0

    try:
        eventos = _carregar(opcoes)
    except OSError as erro:
        print(f"Não consegui ler o arquivo: {erro}", file=sys.stderr)
        return 1
    except ErroDeFiltro as erro:
        print(f"Filtro inválido: {erro}", file=sys.stderr)
        return 2

    if opcoes.listar:
        for evento in eventos:
            print(evento)
        return 0

    if opcoes.top:
        contagem = agregacao.contar_por(eventos, opcoes.top)
        maximo = max(contagem.values(), default=0)

        for valor, quantos in agregacao.top(contagem, opcoes.quantidade):
            print(f"{quantos:>7}  {valor:<40} {relatorio.barra(quantos, maximo, 20)}")

        return 0

    if opcoes.percentis:
        resumo = Resumo.de(agregacao.valores_de(eventos, opcoes.percentis))

        if resumo is None:
            print(f"Nenhum valor numérico em {opcoes.percentis!r}.", file=sys.stderr)
            return 3

        print(resumo.linha())
        return 0

    print(relatorio.montar(
        eventos,
        quantidade=opcoes.quantidade,
        intervalo=timedelta(seconds=max(1, opcoes.intervalo)),
    ))

    return 0


def _garantir_utf8() -> None:
    """Evita que o relatório quebre no console do Windows.

    O terminal do Windows ainda sai em cp1252 quando a saída é redirecionada, e
    aí os blocos das barras derrubam o programa com UnicodeEncodeError. Trocar
    para UTF-8 resolve; quando não dá, o ``errors="replace"`` garante que no
    pior caso saia um caractere estranho em vez de um traceback.
    """
    for fluxo in (sys.stdout, sys.stderr):
        reconfigurar = getattr(fluxo, "reconfigure", None)

        if reconfigurar is None:
            continue

        try:
            reconfigurar(encoding="utf-8", errors="replace")
        except (ValueError, OSError):  # pragma: no cover - depende do terminal
            pass


def _carregar(opcoes):
    from . import analisar

    if opcoes.arquivo:
        return analisar_arquivo(opcoes.arquivo, opcoes.formato, opcoes.filtro)

    return analisar(sys.stdin.read().splitlines(), opcoes.formato, opcoes.filtro)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
