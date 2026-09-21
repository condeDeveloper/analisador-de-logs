"""Leitor de log em JSON por linha, o formato que aplicação moderna cospe."""

from __future__ import annotations

import json
from datetime import datetime

from ..evento import Evento, normalizar_nivel

_CHAVES_DE_MOMENTO = ("momento", "timestamp", "time", "@timestamp", "ts", "data")
_CHAVES_DE_NIVEL = ("nivel", "level", "severity", "lvl")
_CHAVES_DE_MENSAGEM = ("mensagem", "message", "msg", "texto")


class LeitorEstruturado:
    """Lê uma linha de JSON."""

    nome = "json"

    def reconhece(self, linha: str) -> bool:
        limpa = linha.strip()
        return limpa.startswith("{") and limpa.endswith("}")

    def ler(self, linha: str, numero: int) -> Evento | None:
        try:
            dados = json.loads(linha)
        except (json.JSONDecodeError, TypeError):
            return None

        if not isinstance(dados, dict):
            return None

        momento = _primeiro(dados, _CHAVES_DE_MOMENTO)
        nivel = _primeiro(dados, _CHAVES_DE_NIVEL)
        mensagem = _primeiro(dados, _CHAVES_DE_MENSAGEM)

        usados = set(_CHAVES_DE_MOMENTO) | set(_CHAVES_DE_NIVEL) | set(_CHAVES_DE_MENSAGEM)
        campos = {chave: valor for chave, valor in dados.items() if chave not in usados}

        return Evento(
            bruto=linha.rstrip("\n"),
            numero=numero,
            momento=_momento(momento),
            nivel=normalizar_nivel(str(nivel) if nivel is not None else None),
            mensagem=str(mensagem) if mensagem is not None else "",
            origem="json",
            campos=campos,
        )


def _primeiro(dados: dict, chaves: tuple[str, ...]) -> object:
    for chave in chaves:
        if chave in dados:
            return dados[chave]
    return None


def _momento(valor: object) -> datetime | None:
    if valor is None:
        return None

    if isinstance(valor, (int, float)):
        # Número grande demais para ser segundo é milissegundo; é o chute que
        # todo mundo faz, e acerta para qualquer data depois de 1973.
        segundos = valor / 1000 if valor > 1e11 else valor
        try:
            return datetime.fromtimestamp(segundos)
        except (OverflowError, OSError, ValueError):
            return None

    texto = str(valor).strip().replace("Z", "+00:00")

    try:
        return datetime.fromisoformat(texto)
    except ValueError:
        return None
