# ZEUS-HEAL-002 — Propostas persistentes e sinais do runtime

**Data:** 2026-11-03
**Escopo:** segunda camada do #50; aprovação nativa no desktop fica para a camada seguinte.
**Status:** implementado e verificado localmente; sem aprovação independente.

## Entregue

- Sinais read-only em `state.db`: `stuck-turn` (admission `started`/`unknown` sem atividade por
  15 min), `stuck-worker` (`registered`/`running` sem atividade por 15 min) e
  `tool-failures-repeated` (mesma ferramenta com falha dura ≥ 3 vezes em 30 min). Nenhum desses
  sinais propõe correção automática.
- `hermes_cli/heal_store.py`: propostas em `<HERMES_HOME>/heal-proposals/<id>.json` (0600),
  TTL de 10 min, ID hexadecimal validado contra path traversal, rollback documentado e auditoria
  append-only em `logs/heal-audit.jsonl` (0600).
- CLI: `zeus heal propose|proposals|show|approve|reject`; `approve` exige TTY + palavra exata
  `APPROVE`, re-diagnostica antes de executar e marca `stale` se a ação saiu do plano.
- Cadeia de auditoria: `proposal.created` (motivo + códigos dos sinais), `proposal.approved`,
  `proposal.rejected`, `proposal.expired`, `proposal.stale`, `proposal.executed` (resultado e
  rollback). Falha de execução fecha como `failed`.
- `apply` mantém o caminho direto com TTY + `APPROVE` e agora registra o rollback.
- Documentação em `website/docs/reference/cli-commands.md` § `hermes heal`.

## Verificação

- `tests/test_zeus_heal.py` + `tests/test_zeus_heal_store.py` — **20/20 PASS**.
- `python scripts/check` — **12/12 OK** (footguns Windows e BLE001 corrigidos).
- Smoke real em `HERMES_HOME` temporário: `propose` criou proposta, `show` exibiu motivo/rollback,
  `reject` encerrou sem executar e o audit registrou os dois eventos.
- `heal status --json` no home real: gateway ativo, 60.1 GB livres, entitlement annual ativo,
  nenhum finding.

## Residual

1. Aprovação nativa no desktop (watcher/diálogo/IPC) e distribuição de skills ficam para a
   próxima camada; o CLI já é o backend determinístico.
2. Apenas `restart-gateway` é executável; qualquer ação destrutiva/rede/credencial/deploy exige
   desenho próprio e continua fora de escopo.
3. Nenhuma alteração de prompt, toolsets ou cache de contexto foi feita.
