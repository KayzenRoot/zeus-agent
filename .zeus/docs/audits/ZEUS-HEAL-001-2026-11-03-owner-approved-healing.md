# ZEUS-HEAL-001 — Auto-healing determinístico com aprovação do owner

**Data:** 2026-11-03
**Escopo:** primeira camada da issue #50. Sem correção silenciosa, sem LLM e sem ações destrutivas.
**Status:** implementado e verificado localmente; sem aprovação independente.

## Entregue

- `zeus heal status [--json]`: diagnostica gateway (running/stale), `state.db` (`quick_check`),
  espaço em disco e entitlement.
- `zeus heal plan [--json]`: lista somente ações propostas, todas com
  `requires_owner_approval: true`.
- `zeus heal apply <action>`:
  - recusa se a ação não está no plano atual;
  - recusa quando não há terminal interativo (um agente não consegue se autoaprovar);
  - exige a palavra `APPROVE` digitada pelo owner;
  - executa apenas `restart-gateway` nesta camada;
  - grava `logs/heal-audit.jsonl` (0600 no POSIX) com ação, resultado e exit code.
- Diagnósticos de corrupção de DB e disco baixo são **advisory**: não têm ação automática.

## Verificação

- `tests/test_zeus_heal.py` — **6/6 PASS**: proposta, recusa não-interativa, palavra errada,
  execução aprovada + auditoria, ação fora do plano e status.
- Smoke real no PC: `zeus heal status` → gateway running, disco 60.2 GB, entitlement active,
  nenhum problema; `heal plan` vazio; `heal apply` recusou sem ação aplicável.
- `python scripts/check` — 12/12.

## Limite e residual

- O "orquestrador mestre" e a distribuição de skills continuam no roadmap; esta camada é o
  mecanismo seguro de detecção/proposta/execução.
- Aprovação no desktop (IPC/UI) e outras ações (limpar lock órfão, rotacionar logs, reparar DB
  com backup) exigem uma próxima WO.
- Nenhuma ação de rede, financeira, credenciais ou deploy é executada.
