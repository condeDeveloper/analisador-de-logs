"""Percentis e resumo numérico.

O que interessa em latência não é a média — ela esconde a cauda. Um serviço com
média de 80 ms e p99 de 4 s tem um por cento dos usuários esperando quatro
segundos, e a média não conta isso.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


def percentil(valores, p: float) -> float:
    """Percentil por interpolação linear, como o do NumPy.

    Interpolar em vez de pegar o vizinho mais próximo evita o degrau feio em
    amostra pequena, onde o p95 de vinte valores saltaria de um para o outro.
    """
    if not 0 <= p <= 100:
        raise ValueError("O percentil vai de 0 a 100.")

    ordenados = sorted(float(valor) for valor in valores)

    if not ordenados:
        raise ValueError("Não dá para calcular percentil de nada.")

    if len(ordenados) == 1:
        return ordenados[0]

    posicao = (len(ordenados) - 1) * (p / 100)
    baixo = math.floor(posicao)
    alto = math.ceil(posicao)

    if baixo == alto:
        return ordenados[baixo]

    peso = posicao - baixo
    return ordenados[baixo] * (1 - peso) + ordenados[alto] * peso


@dataclass(frozen=True, slots=True)
class Resumo:
    """O resumo numérico de uma série."""

    quantidade: int
    minimo: float
    maximo: float
    media: float
    mediana: float
    p90: float
    p95: float
    p99: float
    desvio: float

    @staticmethod
    def de(valores) -> "Resumo | None":
        """Resume a série, ou devolve None se ela estiver vazia."""
        numeros = [float(valor) for valor in valores if isinstance(valor, (int, float)) and not isinstance(valor, bool)]

        if not numeros:
            return None

        media = math.fsum(numeros) / len(numeros)
        variancia = math.fsum((valor - media) ** 2 for valor in numeros) / len(numeros)

        return Resumo(
            quantidade=len(numeros),
            minimo=min(numeros),
            maximo=max(numeros),
            media=media,
            mediana=percentil(numeros, 50),
            p90=percentil(numeros, 90),
            p95=percentil(numeros, 95),
            p99=percentil(numeros, 99),
            desvio=math.sqrt(variancia),
        )

    def linha(self, unidade: str = "") -> str:
        """Uma linha legível com os números que importam."""
        def f(valor: float) -> str:
            return f"{valor:,.1f}{unidade}".replace(",", "_").replace(".", ",").replace("_", ".")

        return (
            f"n={self.quantidade}  min={f(self.minimo)}  mediana={f(self.mediana)}  "
            f"média={f(self.media)}  p95={f(self.p95)}  p99={f(self.p99)}  máx={f(self.maximo)}"
        )


def taxa(parte: int, total: int) -> float:
    """Percentual de uma parte sobre o total, tolerando total zero."""
    return 0.0 if total <= 0 else parte * 100 / total
