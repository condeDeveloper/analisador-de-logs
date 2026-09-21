"""O contrato de um leitor de formato de log."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..evento import Evento


@runtime_checkable
class Leitor(Protocol):
    """Sabe transformar uma linha de um formato específico em evento."""

    nome: str

    def reconhece(self, linha: str) -> bool:
        """Indica se a linha parece ser deste formato."""
        ...

    def ler(self, linha: str, numero: int) -> Evento | None:
        """Interpreta a linha, ou devolve None se não conseguir."""
        ...


def evento_cru(linha: str, numero: int) -> Evento:
    """O evento de quem não foi reconhecido por leitor nenhum.

    Guardar a linha crua em vez de descartá-la importa: em um arquivo de log
    real sempre há a linha estranha, e ela costuma ser justamente a
    interessante.
    """
    return Evento(bruto=linha, numero=numero, mensagem=linha.strip())
