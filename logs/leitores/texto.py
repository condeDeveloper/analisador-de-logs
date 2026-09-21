"""Leitor do log de aplicação em texto, do tipo ``2026-09-21 10:00:00 ERRO msg``.

Cobre também o syslog clássico e o formato com o nível entre colchetes, que são
as três variações que aparecem em quase todo serviço.
"""

from __future__ import annotations

import re
from datetime import datetime

from ..evento import Evento, normalizar_nivel

_NIVEL = r"(?:TRACE|DEBUG|INFO|INFORMATION|NOTICE|WARN|WARNING|AVISO|ERROR|ERRO|ERR|SEVERE|FATAL|CRITICAL|CRITICO|ALERT|EMERG)"

_DATADO = re.compile(
    r"^(?P<momento>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?)"
    r"\s+\[?(?P<nivel>" + _NIVEL + r")\]?"
    r"(?:\s+\[?(?P<origem>[\w.$-]+)\]?)?"
    r"\s+(?P<mensagem>.*)$",
    re.IGNORECASE,
)

_SYSLOG = re.compile(
    r"^(?P<momento>[A-Z][a-z]{2}\s+\d{1,2} \d{2}:\d{2}:\d{2})\s+"
    r"(?P<maquina>\S+)\s+(?P<origem>[^\s:\[]+)(?:\[(?P<pid>\d+)\])?:\s+(?P<mensagem>.*)$"
)

_CHAVE_VALOR = re.compile(r"(\w+)=(\"[^\"]*\"|\S+)")


class LeitorDeTexto:
    """Lê log de aplicação com data no começo da linha."""

    nome = "texto"

    def reconhece(self, linha: str) -> bool:
        return _DATADO.match(linha.strip()) is not None

    def ler(self, linha: str, numero: int) -> Evento | None:
        casou = _DATADO.match(linha.strip())
        if casou is None:
            return None

        dados = casou.groupdict()
        mensagem = dados["mensagem"].strip()

        return Evento(
            bruto=linha.rstrip("\n"),
            numero=numero,
            momento=_momento_iso(dados["momento"]),
            nivel=normalizar_nivel(dados["nivel"]),
            mensagem=mensagem,
            origem=(dados.get("origem") or "").strip(),
            campos=extrair_chave_valor(mensagem),
        )


class LeitorDeSyslog:
    """Lê o syslog clássico, com mês abreviado em inglês e sem ano."""

    nome = "syslog"

    def __init__(self, ano: int | None = None) -> None:
        # O syslog não grava o ano; sem um informado, vale o ano corrente, que
        # é o que o próprio `journalctl` assume.
        self.ano = ano or datetime.now().year

    def reconhece(self, linha: str) -> bool:
        return _SYSLOG.match(linha.strip()) is not None

    def ler(self, linha: str, numero: int) -> Evento | None:
        casou = _SYSLOG.match(linha.strip())
        if casou is None:
            return None

        dados = casou.groupdict()
        mensagem = dados["mensagem"].strip()

        campos: dict[str, object] = {"maquina": dados["maquina"]}
        if dados.get("pid"):
            campos["pid"] = int(dados["pid"])
        campos.update(extrair_chave_valor(mensagem))

        return Evento(
            bruto=linha.rstrip("\n"),
            numero=numero,
            momento=_momento_syslog(dados["momento"], self.ano),
            nivel=_nivel_pela_mensagem(mensagem),
            mensagem=mensagem,
            origem=dados["origem"],
            campos=campos,
        )


def extrair_chave_valor(mensagem: str) -> dict[str, object]:
    """Pesca pares ``chave=valor`` soltos no meio da mensagem.

    Muito log é meio estruturado: texto livre com ``status=500 duracao_ms=1204``
    no fim. Puxar esses pares deixa o filtro trabalhar com eles.
    """
    campos: dict[str, object] = {}

    for chave, bruto in _CHAVE_VALOR.findall(mensagem):
        valor = bruto.strip('"')
        campos[chave] = _converter(valor)

    return campos


def _converter(valor: str) -> object:
    try:
        return int(valor)
    except ValueError:
        pass

    try:
        return float(valor)
    except ValueError:
        return valor


def _nivel_pela_mensagem(mensagem: str) -> str:
    achado = re.search(_NIVEL, mensagem, re.IGNORECASE)
    return normalizar_nivel(achado.group(0)) if achado else "INFO"


def _momento_iso(texto: str) -> datetime | None:
    limpo = texto.strip().replace(",", ".").replace("Z", "+00:00")

    try:
        return datetime.fromisoformat(limpo)
    except ValueError:
        return None


def _momento_syslog(texto: str, ano: int) -> datetime | None:
    try:
        return datetime.strptime(f"{ano} {' '.join(texto.split())}", "%Y %b %d %H:%M:%S")
    except ValueError:
        return None
