"""O relatório de terminal.

A saída é feita para caber em um terminal comum e ser lida de cima para baixo:
primeiro o tamanho do problema, depois onde ele está.
"""

from __future__ import annotations

from datetime import timedelta

from . import agregacao
from .estatistica import Resumo, taxa
from .evento import NIVEIS, Evento

_BLOCOS = "▁▂▃▄▅▆▇█"


def barra(valor: int, maximo: int, largura: int = 24) -> str:
    """Uma barra horizontal proporcional ao valor."""
    if maximo <= 0 or valor <= 0:
        return ""
    return "█" * max(1, round(valor * largura / maximo))


def faixa(serie) -> str:
    """Um gráfico de uma linha só com a série temporal."""
    if not serie:
        return ""

    contagens = [contagem for _, contagem in serie]
    maximo = max(contagens)

    if maximo == 0:
        return _BLOCOS[0] * len(contagens)

    return "".join(_BLOCOS[min(len(_BLOCOS) - 1, round(c * (len(_BLOCOS) - 1) / maximo))] for c in contagens)


def montar(
    eventos: list[Evento],
    campo_de_duracao: str = "duracao_ms",
    quantidade: int = 5,
    intervalo: timedelta = timedelta(minutes=1),
) -> str:
    """Monta o relatório inteiro."""
    if not eventos:
        return "Nenhum evento."

    linhas: list[str] = []
    total = len(eventos)

    linhas.append(_titulo("Resumo"))
    linhas.append(f"  eventos          {total}")

    datados = [evento.momento for evento in eventos if evento.momento is not None]
    if datados:
        inicio, fim = min(datados), max(datados)
        linhas.append(f"  período          {inicio:%d/%m/%Y %H:%M:%S} até {fim:%d/%m/%Y %H:%M:%S}")
        linhas.append(f"  duração          {_duracao(fim - inicio)}")

    problemas = sum(1 for evento in eventos if evento.eh_problema)
    linhas.append(f"  erros            {problemas} ({taxa(problemas, total):.1f}%)")

    linhas.append("")
    linhas.append(_titulo("Por nível"))
    contagem_de_nivel = agregacao.contar_por(eventos, "nivel")
    maximo = max(contagem_de_nivel.values(), default=0)

    for nivel in NIVEIS:
        quantos = contagem_de_nivel.get(nivel, 0)
        if quantos:
            linhas.append(f"  {nivel:<9} {quantos:>7}  {barra(quantos, maximo)}")

    for campo, titulo in (("rota", "Rotas"), ("status", "Status"), ("origem", "Origens")):
        bloco = _bloco_de_contagem(eventos, campo, titulo, quantidade)
        if bloco:
            linhas.append("")
            linhas.extend(bloco)

    duracoes = agregacao.valores_de(eventos, campo_de_duracao)
    resumo = Resumo.de(duracoes)
    if resumo is not None:
        linhas.append("")
        linhas.append(_titulo(f"Latência ({campo_de_duracao})"))
        linhas.append(f"  {resumo.linha()}")

    serie = agregacao.serie_temporal(eventos, intervalo)
    if len(serie) > 1:
        linhas.append("")
        linhas.append(_titulo(f"Volume por {_duracao(intervalo)}"))
        linhas.append(f"  {faixa(serie)}")

        encontrados = agregacao.picos(serie)
        if encontrados:
            linhas.append("  picos:")
            for momento, contagem in encontrados[:quantidade]:
                linhas.append(f"    {momento:%d/%m %H:%M}  {contagem}")

    erros = [evento for evento in eventos if evento.eh_problema]
    if erros:
        linhas.append("")
        linhas.append(_titulo("Mensagens de erro mais comuns"))
        contagem = agregacao.contar_por(erros, "mensagem")
        for mensagem, quantos in agregacao.top(contagem, quantidade):
            linhas.append(f"  {quantos:>5}  {_cortar(mensagem, 70)}")

    return "\n".join(linhas)


def _bloco_de_contagem(eventos, campo: str, titulo: str, quantidade: int) -> list[str]:
    contagem = agregacao.contar_por(eventos, campo)

    if not contagem or len(contagem) == 1 and "" in contagem:
        return []

    maiores = agregacao.top(contagem, quantidade)
    maximo = maiores[0][1] if maiores else 0

    linhas = [_titulo(titulo)]
    for valor, quantos in maiores:
        if not valor:
            continue
        linhas.append(f"  {_cortar(valor, 32):<32} {quantos:>7}  {barra(quantos, maximo, 16)}")

    return linhas if len(linhas) > 1 else []


def _titulo(texto: str) -> str:
    return f"{texto}\n{'─' * len(texto)}"


def _cortar(texto: str, tamanho: int) -> str:
    return texto if len(texto) <= tamanho else texto[: tamanho - 1] + "…"


def _duracao(intervalo: timedelta) -> str:
    segundos = int(intervalo.total_seconds())

    if segundos < 60:
        return f"{segundos}s"
    if segundos < 3600:
        return f"{segundos // 60}min"
    if segundos < 86400:
        return f"{segundos // 3600}h{(segundos % 3600) // 60:02d}"

    return f"{segundos // 86400}d{(segundos % 86400) // 3600:02d}h"
