"""Analisador de logs em Python puro.

    >>> from logs import analisar
    >>> eventos = analisar([
    ...     '2026-09-21 10:00:00 INFO pedido criado id=1',
    ...     '2026-09-21 10:00:01 ERRO banco fora do ar status=500',
    ... ])
    >>> len(eventos)
    2
    >>> eventos[1].nivel
    'ERRO'
    >>> eventos[1].valor("status")
    500
"""

from __future__ import annotations

from pathlib import Path

from . import agregacao, estatistica, filtro, leitores, relatorio
from .estatistica import Resumo, percentil
from .evento import NIVEIS, Evento
from .filtro import ErroDeFiltro, Filtro, compilar
from .leitores import Leitor, detectar

__version__ = "1.0.0"


def analisar(linhas, formato: str | None = None, onde: str | None = None) -> list[Evento]:
    """Lê as linhas e devolve os eventos, opcionalmente peneirados.

    Sem formato informado, ele é detectado pelas primeiras linhas.
    """
    materializadas = list(linhas)
    leitor = leitores.por_nome(formato) if formato else detectar(materializadas)
    eventos = list(leitores.ler(materializadas, leitor))

    if onde:
        eventos = list(compilar(onde).aplicar(eventos))

    return eventos


def analisar_arquivo(
    caminho: str | Path,
    formato: str | None = None,
    onde: str | None = None,
    codificacao: str = "utf-8",
) -> list[Evento]:
    """O mesmo, lendo de um arquivo."""
    conteudo = Path(caminho).read_text(encoding=codificacao, errors="replace")
    return analisar(conteudo.splitlines(), formato, onde)


__all__ = [
    "ErroDeFiltro",
    "Evento",
    "Filtro",
    "Leitor",
    "NIVEIS",
    "Resumo",
    "agregacao",
    "analisar",
    "analisar_arquivo",
    "compilar",
    "detectar",
    "estatistica",
    "filtro",
    "leitores",
    "percentil",
    "relatorio",
]
