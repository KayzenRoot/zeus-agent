# ZEUS-HEAL-004 — Revisão de skills geradas pelo agente

**Data:** 2026-11-03
**Escopo:** camada final do #50; usa o gate existente `skills.write_approval`, sem alterar prompts,
toolsets ou cache.
**Status:** implementado e verificado localmente; sem aprovação independente.

## Entregue

- `hermes skills review list [--json]`: lista writes de skill staged em
  `<HERMES_HOME>/pending/skills/` (id, ação, resumo, origem, timestamp), sem expor payloads.
- `hermes skills review diff <id>`: imprime o diff/content exato que o approve aplicaria.
- `hermes skills review approve <id>`: exige TTY + palavra exata `APPROVE`; aplica via
  `apply_skill_pending` e mantém o código de saída correto no roteador `hermes skills`.
- `hermes skills review reject <id>`: descarta sem escrever no skill.
- O gate `skills.write_approval` foi ativado na configuração local do owner
  (`C:\Users\csn19\AppData\Local\hermes\config.yaml` → `skills.write_approval: true`). Reverter:
  `zeus config set skills.write_approval false`.
- Documentação em `website/docs/reference/cli-commands.md` § `hermes skills`.

## Verificação

- `tests/hermes_cli/test_skills_review.py` — **8/8 PASS** (list, diff, TTY, palavra exata,
  aprovação, rejeição, JSON, roteamento/exit code).
- `python scripts/check` — **12/12 OK**.
- E2E em `HERMES_HOME` temporário: `skill_manage(create)` com gate on retornou `staged: true`,
  nenhum `SKILL.md` foi instalado; `skills review approve` em PTY recebeu `APPROVE`, saiu 0 e o
  skill apareceu no diretório — **installedBefore=false, installedAfter=true**.
- O caminho de chat já existente (`/skills pending|diff|approve|reject`) continua atendendo o
  desktop/TUI/gateway.

## Residual

1. A distribuição de skills entre agentes/subagentes do orquestrador mestre não foi alterada
   nesta camada; o curator e o `skill_manage` seguem sendo o mecanismo de aprendizado.
2. Aprovar/rejeitar pelo chat do desktop usa o handler compartilhado; não há botão dedicado no
   renderer.
3. O gate é uma configuração do owner, não um novo default upstream: instalações existentes
   continuam com o comportamento anterior até ativarem `skills.write_approval`.
