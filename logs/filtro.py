"""Uma linguagem de filtro pequena, para peneirar eventos.

    status >= 500 e rota ~ "/api"
    nivel = ERRO ou nivel = CRITICO
    nao (agente ~ bot)

Existe porque a alternativa é `grep` encadeado: fácil de escrever, impossível
de ler depois, e sem noção nenhuma de que `status` é número.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from .evento import Evento, gravidade

_SIMBOLOS = ("!=", ">=", "<=", "!~", "=", ">", "<", "~")
_TOKENS = re.compile(
    r'\s*(?:(?P<texto>"[^"]*"|\'[^\']*\')'
    r"|(?P<simbolo>!=|>=|<=|!~|=|>|<|~|\(|\))"
    r"|(?P<palavra>[^\s()=<>!~]+))"
)


class ErroDeFiltro(ValueError):
    """O filtro não pôde ser lido."""


@dataclass(frozen=True, slots=True)
class Filtro:
    """Um filtro compilado."""

    texto: str
    teste: Callable[[Evento], bool]

    def __call__(self, evento: Evento) -> bool:
        return self.teste(evento)

    def aplicar(self, eventos):
        """Percorre os eventos devolvendo só os que passam."""
        return (evento for evento in eventos if self.teste(evento))

    def __str__(self) -> str:
        return self.texto


def compilar(expressao: str | None) -> Filtro:
    """Lê a expressão e devolve o filtro pronto."""
    if expressao is None or not expressao.strip():
        return Filtro("", lambda _: True)

    tokens = _separar(expressao)
    analisador = _Analisador(expressao, tokens)
    teste = analisador.ou()

    if not analisador.acabou():
        raise ErroDeFiltro(f"Sobrou {analisador.atual()!r} no fim do filtro.")

    return Filtro(expressao.strip(), teste)


def _separar(expressao: str) -> list[str]:
    tokens: list[str] = []
    posicao = 0

    while posicao < len(expressao):
        casou = _TOKENS.match(expressao, posicao)

        if casou is None or casou.end() == posicao:
            resto = expressao[posicao:].strip()
            if not resto:
                break
            raise ErroDeFiltro(f"Não entendi {resto!r}.")

        posicao = casou.end()
        tokens.append(casou.group("texto") or casou.group("simbolo") or casou.group("palavra"))

    return tokens


class _Analisador:
    def __init__(self, expressao: str, tokens: list[str]) -> None:
        self.expressao = expressao
        self.tokens = tokens
        self.i = 0

    def acabou(self) -> bool:
        return self.i >= len(self.tokens)

    def atual(self) -> str:
        return self.tokens[self.i]

    def aceitar(self, *quais: str) -> bool:
        if not self.acabou() and self.atual().lower() in quais:
            self.i += 1
            return True
        return False

    def ou(self) -> Callable[[Evento], bool]:
        esquerda = self.e()

        while self.aceitar("ou", "or", "||"):
            direita = self.e()
            esquerda = _ou(esquerda, direita)

        return esquerda

    def e(self) -> Callable[[Evento], bool]:
        esquerda = self.negacao()

        while self.aceitar("e", "and", "&&"):
            direita = self.negacao()
            esquerda = _e(esquerda, direita)

        return esquerda

    def negacao(self) -> Callable[[Evento], bool]:
        if self.aceitar("nao", "não", "not", "!"):
            dentro = self.negacao()
            return lambda evento: not dentro(evento)

        return self.termo()

    def termo(self) -> Callable[[Evento], bool]:
        if self.acabou():
            raise ErroDeFiltro("O filtro termina onde deveria haver uma condição.")

        if self.aceitar("("):
            dentro = self.ou()
            if not self.aceitar(")"):
                raise ErroDeFiltro("Faltou fechar o parêntese.")
            return dentro

        campo = self.tokens[self.i]
        self.i += 1

        if self.acabou() or self.atual() not in _SIMBOLOS:
            # Uma palavra solta procura no texto inteiro da linha, que é o que
            # se espera de quem digitou só "timeout".
            alvo = _limpar(campo).casefold()
            return lambda evento: alvo in evento.bruto.casefold()

        operador = self.tokens[self.i]
        self.i += 1

        if self.acabou():
            raise ErroDeFiltro(f"Faltou o valor depois de {operador!r}.")

        valor = _limpar(self.tokens[self.i])
        self.i += 1

        return _comparacao(campo, operador, valor)


def _limpar(token: str) -> str:
    if len(token) >= 2 and token[0] in "\"'" and token[-1] == token[0]:
        return token[1:-1]
    return token


def _e(esquerda, direita):
    return lambda evento: esquerda(evento) and direita(evento)


def _ou(esquerda, direita):
    return lambda evento: esquerda(evento) or direita(evento)


def _comparacao(campo: str, operador: str, alvo: str) -> Callable[[Evento], bool]:
    def testar(evento: Evento) -> bool:
        atual = evento.valor(campo)

        if operador == "~":
            return alvo.casefold() in _texto(atual).casefold()
        if operador == "!~":
            return alvo.casefold() not in _texto(atual).casefold()

        ordem = _ordenar(campo, atual, alvo)

        if ordem is None:
            # Campo ausente nunca satisfaz comparação, mas satisfaz "diferente
            # de" — é o mesmo critério do SQL para nulo e evita que uma linha
            # sem o campo apareça em `status >= 500`.
            return operador == "!="

        return {
            "=": ordem == 0,
            "!=": ordem != 0,
            ">": ordem > 0,
            ">=": ordem >= 0,
            "<": ordem < 0,
            "<=": ordem <= 0,
        }[operador]

    return testar


def _texto(valor: object) -> str:
    if valor is None:
        return ""
    if isinstance(valor, datetime):
        return valor.isoformat()
    return str(valor)


def _ordenar(campo: str, atual: object, alvo: str) -> int | None:
    if atual is None:
        return None

    # O nível é comparado pela gravidade, não pelo alfabeto: "nivel >= AVISO"
    # precisa pegar ERRO, que vem antes de AVISO em ordem alfabética.
    if campo == "nivel":
        return _sinal(gravidade(str(atual)), gravidade(alvo.strip().upper()))

    if isinstance(atual, bool):
        return _sinal(int(atual), int(alvo.strip().lower() in ("1", "true", "sim", "verdadeiro")))

    if isinstance(atual, (int, float)):
        try:
            return _sinal(float(atual), float(alvo.replace(",", ".")))
        except ValueError:
            return None

    if isinstance(atual, datetime):
        try:
            return _sinal(atual.timestamp(), datetime.fromisoformat(alvo).timestamp())
        except ValueError:
            return None

    return _sinal(str(atual).casefold(), alvo.casefold())


def _sinal(a, b) -> int:
    return (a > b) - (a < b)
