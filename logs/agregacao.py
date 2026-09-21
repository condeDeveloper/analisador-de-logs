"""Contagens, agrupamentos e série temporal."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta

from .evento import Evento


def contar_por(eventos, campo: str) -> Counter:
    """Conta quantos eventos há para cada valor de um campo."""
    contagem: Counter = Counter()

    for evento in eventos:
        valor = evento.valor(campo)
        if valor is not None:
            contagem[_chave(valor)] += 1

    return contagem


def agrupar_por(eventos, campo: str) -> dict[str, list[Evento]]:
    """Separa os eventos em listas, uma por valor do campo."""
    grupos: dict[str, list[Evento]] = defaultdict(list)

    for evento in eventos:
        valor = evento.valor(campo)
        if valor is not None:
            grupos[_chave(valor)].append(evento)

    return dict(grupos)


def valores_de(eventos, campo: str) -> list[float]:
    """Os valores numéricos de um campo, ignorando quem não é número."""
    numeros = []

    for evento in eventos:
        valor = evento.valor(campo)
        if isinstance(valor, (int, float)) and not isinstance(valor, bool):
            numeros.append(float(valor))

    return numeros


def top(contagem: Counter, quantidade: int = 10) -> list[tuple[str, int]]:
    """Os mais frequentes, com desempate alfabético para ficar estável."""
    return sorted(contagem.items(), key=lambda par: (-par[1], par[0]))[:quantidade]


def serie_temporal(eventos, intervalo: timedelta = timedelta(minutes=1)) -> list[tuple[datetime, int]]:
    """Agrupa os eventos em janelas de tempo iguais.

    Cada evento cai na janela que começa no múltiplo do intervalo abaixo dele,
    e as janelas vazias do meio entram com zero — sem isso, um gráfico de picos
    mentiria sobre o silêncio entre eles.
    """
    if intervalo <= timedelta(0):
        raise ValueError("O intervalo precisa ser positivo.")

    datados = [evento for evento in eventos if evento.momento is not None]

    if not datados:
        return []

    segundos = int(intervalo.total_seconds())
    inicio = min(evento.momento for evento in datados)
    fim = max(evento.momento for evento in datados)

    contagem: Counter = Counter()
    for evento in datados:
        contagem[_janela(evento.momento, inicio, segundos)] += 1

    serie = []
    atual = _janela(inicio, inicio, segundos)
    ultima = _janela(fim, inicio, segundos)

    while atual <= ultima:
        serie.append((atual, contagem.get(atual, 0)))
        atual += intervalo

    return serie


def picos(serie, limiar: float = 2.0) -> list[tuple[datetime, int]]:
    """Janelas muito acima da média da série.

    O critério é a média vezes o limiar; é grosseiro de propósito, porque a
    alternativa séria — desvio padrão em série com cauda longa — dispara em
    tudo quando o tráfego é irregular.
    """
    if not serie:
        return []

    contagens = [contagem for _, contagem in serie]
    media = sum(contagens) / len(contagens)

    if media <= 0:
        return []

    return [(momento, contagem) for momento, contagem in serie if contagem > media * limiar]


def _janela(momento: datetime, inicio: datetime, segundos: int) -> datetime:
    decorrido = int((momento - inicio).total_seconds())
    return inicio + timedelta(seconds=(decorrido // segundos) * segundos)


def _chave(valor: object) -> str:
    return valor.isoformat() if isinstance(valor, datetime) else str(valor)
