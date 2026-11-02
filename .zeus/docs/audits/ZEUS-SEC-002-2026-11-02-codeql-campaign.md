# ZEUS-SEC-002 | CodeQL campaign — inventário e decisões por lote

**Data:** 2026-11-02 · **Baseline:** 908 alertas abertos · **Estado:** **733 abertos**
**Regra:** nenhuma demissão em massa sem motivo por classe; hardenings reais onde o alerta era
código de produção.

## 1. Resultado

| Ação | Alertas | Motivo |
|---|---|---|
| Hardenings de código | ~9 fechados pelo rescan | ver §3 |
| Dismiss `used in tests` | **148** | localização em `tests/` — código não distribuído, sem caminho de produção (inclui 1 `bad-code-sanitization` em `update-marker.test.ts`) |
| Dismiss `won't fix` (TLS) | **11** | `verify=False` só com `ssl_verify: false` explícito do usuário; padrão = trust store do SO; warning de inseguro |
| Dismiss `won't fix` (ECB) | **2** | AES-128-ECB exigido pelo protocolo Tencent iLink para mídia |
| Dismiss `false positive` | **5** | 3 transcripts de delegação (`_redact` não modelado) + 2 `bad-code-sanitization` do desktop (todo valor é `JSON.stringify`) |
| **Total reduzido** | **175** | 908 → 733 |

## 2. Verificação

```bash
gh api --paginate "repos/KayzenRoot/zeus-agent/code-scanning/alerts?state=open&per_page=100" \
  --jq '.[] | "\(.rule.id)\t\(.most_recent_instance.location.path)"' | sort | uniq -c | sort -rn
```

Contagem por severidade/regra e confirmação de `state=dismissed` por amostra foram executadas
após cada lote (a chamada de PATCH não é evidência sozinha).

## 3. Hardenings reais no período

| Commit | Correção |
|---|---|
| `21c17640d1` | 10 sites de URL-substring → host/path matching (Azure/MiniMax auth, beta 1M, Gemini native/OpenAI-compat, StepFun, Ollama); 10 testes anti-spoofing |
| `950fb0a6c4` | ReDoS: corpo temperado na chave privada; grupos possessivos no quoter FTS5; testes com limite de tempo |
| `a9d9209db4` | A2A audit redige o resumo antes de gravar; teste garante token/e-mail ausentes |

## 4. O que permanece (733)

| Regra | Abertos | Por que não demitir em bloco |
|---|---|---|
| `py/path-injection` | 311 | a maioria é ferramenta de arquivo/CLI que **deve** aceitar caminho do usuário; exige revisão por alerta para separar taint real de prompt |
| `py/log-injection` | 229 | log forjado por newline; mitigação central mudaria formato de logs; revisar por sink |
| `js/insecure-temporary-file` / `js/file-system-race` | 26+26 | maioria em `evals/`, `scripts/` e harnesses; runtime revisado (relaunch-waiter é leitura de log, não criação) |
| `py/clear-text-storage-sensitive-data` | 18 | estado local user-scoped (cron output, relatórios); A2A já corrigido |
| `py/overly-permissive-file` | 17 | lock 0644 / log 0660 / chmod 0666 apenas para unlink no Windows — intencionais |
| Demais | ~130 | classes pequenas (stack-trace, bad-code-sanitization, file-access-to-http), por alerta |

## 5. Limites

Estas decisões são **triagem advisory**; a fonte de verdade continua sendo o código, os testes e
os gates do CI. Alertas demitidos podem ser reabertos pelo owner ou por um rescan que os
reintroduza. Nenhuma demissão autoriza release/distribuição (seguem NO-GO em #4/#20).
