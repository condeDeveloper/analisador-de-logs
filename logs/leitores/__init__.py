"""Os leitores de formato, e a detecção automática entre eles."""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from ..evento import Evento
from .acesso import LeitorDeAcesso
from .base import Leitor, evento_cru
from .estruturado import LeitorEstruturado
from .texto import LeitorDeSyslog, LeitorDeTexto, extrair_chave_valor

#: Ordem em que os leitores são tentados na detecção automática.
PADRAO: tuple[Leitor, ...] = (
    LeitorEstruturado(),
    LeitorDeAcesso(),
    LeitorDeTexto(),
    LeitorDeSyslog(),
)


def por_nome(nome: str) -> Leitor:
    """Busca um leitor pelo nome, para quando o formato é conhecido."""
    for leitor in PADRAO:
        if leitor.nome == nome:
            return leitor

    conhecidos = ", ".join(leitor.nome for leitor in PADRAO)
    raise ValueError(f"Formato desconhecido: {nome!r}. Conhecidos: {conhecidos}.")


def nomes() -> list[str]:
    """Os nomes dos formatos conhecidos."""
    return [leitor.nome for leitor in PADRAO]


def detectar(linhas: Iterable[str], amostra: int = 20) -> Leitor | None:
    """Descobre o formato olhando as primeiras linhas.

    Vale o leitor que reconhecer mais linhas da amostra. Empate resolve pela
    ordem da lista, que vai do formato mais específico para o mais genérico.
    """
    vistas = [linha for _, linha in zip(range(amostra), linhas) if linha.strip()]

    if not vistas:
        return None

    melhor = None
    melhor_acertos = 0

    for leitor in PADRAO:
        acertos = sum(1 for linha in vistas if leitor.reconhece(linha))

        if acertos > melhor_acertos:
            melhor = leitor
            melhor_acertos = acertos

    return melhor


def ler(linhas: Iterable[str], leitor: Leitor | None = None) -> Iterator[Evento]:
    """Percorre as linhas devolvendo eventos.

    Sem um leitor informado, cada linha é oferecida a todos até alguém
    reconhecê-la — um arquivo com formatos misturados continua funcionando.
    """
    for numero, linha in enumerate(linhas, start=1):
        if not linha.strip():
            continue

        yield _ler_uma(linha, numero, leitor)


def _ler_uma(linha: str, numero: int, leitor: Leitor | None) -> Evento:
    if leitor is not None:
        return leitor.ler(linha, numero) or evento_cru(linha, numero)

    for candidato in PADRAO:
        if candidato.reconhece(linha):
            evento = candidato.ler(linha, numero)
            if evento is not None:
                return evento

    return evento_cru(linha, numero)


__all__ = [
    "PADRAO",
    "Leitor",
    "LeitorDeAcesso",
    "LeitorDeSyslog",
    "LeitorDeTexto",
    "LeitorEstruturado",
    "detectar",
    "evento_cru",
    "extrair_chave_valor",
    "ler",
    "nomes",
    "por_nome",
]
