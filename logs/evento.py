"""O evento: uma linha de log já interpretada.

Todo leitor devolve a mesma coisa, independente do formato que leu. É isso que
permite filtrar, agregar e relatar sem que o resto do programa precise saber se
a origem era Apache, JSON ou syslog.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

#: Níveis conhecidos, do menos para o mais grave.
NIVEIS = ("DEBUG", "INFO", "AVISO", "ERRO", "CRITICO")

_APELIDOS = {
    "TRACE": "DEBUG",
    "DEBUG": "DEBUG",
    "INFO": "INFO",
    "INFORMATION": "INFO",
    "NOTICE": "INFO",
    "WARN": "AVISO",
    "WARNING": "AVISO",
    "AVISO": "AVISO",
    "ERROR": "ERRO",
    "ERRO": "ERRO",
    "ERR": "ERRO",
    "SEVERE": "ERRO",
    "FATAL": "CRITICO",
    "CRITICAL": "CRITICO",
    "CRITICO": "CRITICO",
    "ALERT": "CRITICO",
    "EMERG": "CRITICO",
}


def normalizar_nivel(bruto: str | None) -> str:
    """Traduz o nível para o vocabulário único, em português."""
    if not bruto:
        return "INFO"
    return _APELIDOS.get(bruto.strip().upper(), "INFO")


def gravidade(nivel: str) -> int:
    """Posição do nível na escala, para comparar um com o outro."""
    try:
        return NIVEIS.index(nivel)
    except ValueError:
        return NIVEIS.index("INFO")


@dataclass(frozen=True, slots=True)
class Evento:
    """Uma linha de log interpretada."""

    bruto: str
    numero: int = 0
    momento: datetime | None = None
    nivel: str = "INFO"
    mensagem: str = ""
    origem: str = ""
    campos: dict[str, object] = field(default_factory=dict)

    @property
    def eh_problema(self) -> bool:
        """Indica se o evento é erro ou pior."""
        return gravidade(self.nivel) >= gravidade("ERRO")

    def valor(self, campo: str) -> object:
        """Lê um campo pelo nome, caia ele nos fixos ou no dicionário."""
        embutidos = {
            "nivel": self.nivel,
            "mensagem": self.mensagem,
            "momento": self.momento,
            "origem": self.origem,
            "numero": self.numero,
            "bruto": self.bruto,
        }

        if campo in embutidos:
            return embutidos[campo]

        return self.campos.get(campo)

    def com(self, **extras: object) -> "Evento":
        """Devolve uma cópia com campos adicionais."""
        return Evento(
            bruto=self.bruto,
            numero=self.numero,
            momento=self.momento,
            nivel=self.nivel,
            mensagem=self.mensagem,
            origem=self.origem,
            campos={**self.campos, **extras},
        )

    def __str__(self) -> str:
        carimbo = self.momento.isoformat(sep=" ", timespec="seconds") if self.momento else "?"
        return f"{carimbo} {self.nivel} {self.mensagem}".strip()
