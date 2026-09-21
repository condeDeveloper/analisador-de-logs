# analisador-de-logs

Lê arquivo de log, filtra com uma linguagem própria e resume no terminal.
Python puro, sem dependência nenhuma.

```bash
$ logs acesso.log -f "status >= 500"
```

```
Resumo
──────
  eventos          5
  período          21/09/2026 10:00:00 até 21/09/2026 10:01:02
  duração          1min
  erros            2 (40.0%)

Por nível
─────────
  INFO            2  ████████████████████████
  AVISO           1  ████████████
  ERRO            2  ████████████████████████

Rotas
─────
  /api/pedidos                           2  ████████████████
  /api/relatorio                         2  ████████████████

Latência (duracao_ms)
─────────────────────
  n=5  min=3,0  mediana=42,0  média=1.272,0  p95=3.156,0  p99=3.191,2  máx=3.200,0
```

## Por que existe

`grep | awk | sort | uniq -c | sort -rn` resolve — até a terceira vez que você
precisa escrever a mesma coisa, ou até precisar de um p95. O problema é que o
pipe não sabe que `status` é número: `grep "status=5"` pega 500 e 5, e
`sort` coloca "1234" antes de "404".

Aqui a linha vira um **evento tipado**, com data que é data e status que é
número, e daí em diante tudo funciona.

## Formatos que ele lê

| Formato | Exemplo |
| --- | --- |
| `acesso` | Apache e nginx *combined*: `10.0.0.1 - - [21/Sep/2026:10:00:00 -0300] "GET /api 200 1234 …` |
| `texto` | aplicação: `2026-09-21 10:00:02 ERROR br.com.Banco falha status=500 duracao_ms=1204` |
| `json` | uma linha de JSON, com apelidos de chave (`ts`/`timestamp`, `lvl`/`level`, `msg`/`message`) |
| `syslog` | `Sep 21 10:00:00 servidor sshd[1234]: Accepted publickey` |

O formato é detectado pelas primeiras linhas, e **arquivo com formatos
misturados continua funcionando** — cada linha é oferecida a todos os leitores.
Linha que ninguém reconhece não é descartada: vira evento com o texto cru, que
num log real costuma ser justamente a interessante.

Dos logs de texto e syslog ele ainda pesca pares `chave=valor` soltos no meio
da mensagem, então `duracao_ms=1204` vira um campo numérico de verdade.

## A linguagem de filtro

```bash
logs app.log -f "status >= 500 e rota ~ /api"
logs app.log -f 'nivel >= AVISO e nao (agente ~ bot)'
logs app.log -f "timeout"
```

| Operador | O que faz |
| --- | --- |
| `=` `!=` `>` `>=` `<` `<=` | comparação, respeitando o tipo do campo |
| `~` `!~` | contém / não contém, ignorando a caixa |
| `e` `ou` `nao` | composição (também aceita `and`, `or`, `not`) |
| `( )` | agrupamento |
| palavra solta | procura no texto inteiro da linha |

Dois detalhes que fazem diferença:

- **`nivel >= AVISO` compara por gravidade, não pelo alfabeto.** Pelo alfabeto,
  `ERRO` viria antes de `AVISO` e o filtro perderia justamente os erros.
- **Campo ausente nunca satisfaz uma comparação**, mas satisfaz `!=` — mesmo
  critério do SQL para nulo. Sem isso, uma linha sem `status` apareceria em
  `status >= 500`.

## Linha de comando

```bash
logs app.log                          # relatório completo
logs app.log -f "status >= 500"       # filtrando
logs app.log --listar                 # imprime os eventos em vez do relatório
logs app.log --top rota               # os valores mais frequentes de um campo
logs app.log --percentis duracao_ms   # só o resumo numérico
logs app.log --intervalo 300          # janela da série temporal, em segundos
cat app.log | logs                    # lê da entrada padrão
logs --formatos                       # lista os formatos conhecidos
```

## Como biblioteca

```python
from logs import analisar_arquivo, agregacao, relatorio
from logs.estatistica import Resumo

eventos = analisar_arquivo("acesso.log", onde="status >= 500")

print(relatorio.montar(eventos))
print(agregacao.top(agregacao.contar_por(eventos, "rota"), 5))
print(Resumo.de(agregacao.valores_de(eventos, "duracao_ms")).linha("ms"))
```

## Sobre os percentis

O percentil é calculado por **interpolação linear**, como o do NumPy. Vale
saber de um efeito que confunde muita gente: com exatamente 100 amostras e uma
única lenta, o p99 cai *entre* a penúltima e a última, e devolve um valor
intermediário — não os 5000 ms do outlier. Não é bug, é o que interpolação
significa, e é o motivo de p99 em amostra pequena enganar. Tem um teste
documentando exatamente esse caso.

## Estrutura

```
logs/evento.py            o evento tipado e a escala de níveis
logs/leitores/            um módulo por formato, mais a detecção automática
logs/filtro.py            tokenizador e descida recursiva da linguagem de filtro
logs/estatistica.py       percentis e resumo numérico
logs/agregacao.py         contagens, agrupamento, série temporal e picos
logs/relatorio.py         o relatório de terminal, com barras e sparkline
logs/__main__.py          a linha de comando
```

## Rodando

```bash
pip install -e ".[dev]"
pytest
```

129 testes, sem dependência de runtime. Python 3.10 ou mais novo.

## Limites conhecidos

- Carrega o arquivo inteiro na memória; não serve para log de gigabytes.
- Não acompanha arquivo em tempo real (`tail -f`).
- A detecção de picos usa média vezes um limiar, que é grosseiro de propósito:
  desvio padrão em série com cauda longa dispara em tudo.
- Sem cores na saída e sem exportação para CSV ou JSON.

## Licença

MIT.
