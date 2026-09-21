"""Linhas de log de apoio aos testes, uma por formato."""

ACESSO = [
    '192.168.0.10 - - [21/Sep/2026:10:00:00 -0300] "GET /api/pedidos HTTP/1.1" 200 1234 "-" "curl/8.4" 42',
    '192.168.0.11 - maria [21/Sep/2026:10:00:05 -0300] "POST /api/pedidos HTTP/1.1" 201 87 "https://site" "Mozilla/5.0" 130',
    '10.0.0.3 - - [21/Sep/2026:10:00:07 -0300] "GET /api/pedidos/9 HTTP/1.1" 404 0 "-" "Mozilla/5.0" 8',
    '10.0.0.3 - - [21/Sep/2026:10:01:00 -0300] "GET /api/relatorio HTTP/1.1" 500 0 "-" "Mozilla/5.0" 3200',
    '10.0.0.4 - - [21/Sep/2026:10:01:02 -0300] "GET /api/relatorio HTTP/1.1" 500 0 "-" "bot/1.0" 2980',
]

TEXTO = [
    "2026-09-21 10:00:00 INFO  br.com.conde.Pedidos pedido criado id=1 valor=19.90",
    "2026-09-21 10:00:01 WARN  br.com.conde.Estoque estoque baixo sku=ABC restante=3",
    "2026-09-21 10:00:02 ERROR br.com.conde.Banco falha na conexão status=500 duracao_ms=1204",
    "2026-09-21 10:00:03 ERROR br.com.conde.Banco falha na conexão status=500 duracao_ms=980",
    "2026-09-21 10:05:00 INFO  br.com.conde.Pedidos pedido criado id=2 valor=49.90",
]

JSON = [
    '{"timestamp": "2026-09-21T10:00:00", "level": "info", "message": "subiu", "porta": 8080}',
    '{"timestamp": "2026-09-21T10:00:10", "level": "error", "message": "timeout", "duracao_ms": 5000}',
    '{"timestamp": "2026-09-21T10:00:20", "level": "warning", "message": "lento", "duracao_ms": 900}',
]

SYSLOG = [
    "Sep 21 10:00:00 servidor sshd[1234]: Accepted publickey for conde",
    "Sep 21 10:00:30 servidor cron[99]: erro ao rodar tarefa status=1",
]

MISTURADO = ACESSO[:2] + TEXTO[:2] + JSON[:1] + ["linha que não é de formato nenhum"]
