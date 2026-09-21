"""Leitor do log de acesso do Apache e do nginx (formato *combined*).

É o formato mais comum que existe em servidor web, e o mais chato de quebrar
com `split`: o caminho tem espaço dentro das aspas, e a data tem espaço dentro
dos colchetes. Por isso aqui é expressão regular, e não separação por espaço.
"""

from __future__ import annotations

import re
from datetime import datetime

from ..evento import Evento

_LINHA = re.compile(
    r'^(?P<ip>\S+) \S+ (?P<usuario>\S+) '
    r'\[(?P<momento>[^\]]+)\] '
    r'"(?P<metodo>[A-Z]+) (?P<rota>[^"\s]*)(?: (?P<protocolo>[^"]*))?" '
    r'(?P<status>\d{3}) (?P<bytes>\d+|-)'
    r'(?: "(?P<referencia>[^"]*)" "(?P<agente>[^"]*)")?'
    r'(?: (?P<duracao>\d+(?:\.\d+)?))?'
)

_FORMATO_DE_DATA = "%d/%b/%Y:%H:%M:%S %z"

_MESES = {
    "Jan": "Jan", "Feb": "Feb", "Mar": "Mar", "Apr": "Apr", "May": "May", "Jun": "Jun",
    "Jul": "Jul", "Aug": "Aug", "Sep": "Sep", "Oct": "Oct", "Nov": "Nov", "Dec": "Dec",
}


class LeitorDeAcesso:
    """Lê o *combined log format*."""

    nome = "acesso"

    def reconhece(self, linha: str) -> bool:
        return _LINHA.match(linha.strip()) is not None

    def ler(self, linha: str, numero: int) -> Evento | None:
        casou = _LINHA.match(linha.strip())
        if casou is None:
            return None

        dados = casou.groupdict()
        status = int(dados["status"])

        campos: dict[str, object] = {
            "ip": dados["ip"],
            "metodo": dados["metodo"],
            "rota": dados["rota"],
            "status": status,
            "bytes": int(dados["bytes"]) if dados["bytes"] != "-" else 0,
        }

        if dados.get("usuario") and dados["usuario"] != "-":
            campos["usuario"] = dados["usuario"]
        if dados.get("agente"):
            campos["agente"] = dados["agente"]
        if dados.get("referencia") and dados["referencia"] != "-":
            campos["referencia"] = dados["referencia"]
        if dados.get("duracao"):
            campos["duracao_ms"] = float(dados["duracao"])

        return Evento(
            bruto=linha.rstrip("\n"),
            numero=numero,
            momento=_momento(dados["momento"]),
            nivel=_nivel(status),
            mensagem=f'{dados["metodo"]} {dados["rota"]} {status}',
            origem="acesso",
            campos=campos,
        )


def _nivel(status: int) -> str:
    """O status HTTP já diz a gravidade; traduzir isso evita filtro por faixa."""
    if status >= 500:
        return "ERRO"
    if status >= 400:
        return "AVISO"
    return "INFO"


def _momento(texto: str) -> datetime | None:
    try:
        return datetime.strptime(texto, _FORMATO_DE_DATA)
    except ValueError:
        return None
