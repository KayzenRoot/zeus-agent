# ZEUS-CLOUD-006 — Gestão de dispositivos

**Data:** 2026-11-03
**Escopo:** registrar, listar e revogar máquinas ativadas. Test mode; sem deploy/live mode.
**Status:** implementado e verificado localmente; sem aprovação independente.

## Entregue

- Tabela `devices` (device_id, user_id, name, created_at, last_seen, revoked_at) no SQLite.
- `POST /api/device/authorize` registra/atualiza o dispositivo e recusa (409) um `device_id` já
  pertencente a outra conta.
- `GET /api/devices` lista os dispositivos do usuário com status de revogação.
- `POST /api/devices/{device_id}/revoke` revoga; um `device_id` revogado não recebe novo código
  válido nem token (`/api/device/exchange` e `/api/entitlement/token` retornam 403).
- Landing: seção **Dispositivos** com lista, “Atualizar” e botão “Revogar” autenticados por Clerk.

## Evidência local

- `scripts/run_tests.sh tests/cloud/test_cloud_service.py` — **28/28 PASS** (lista/revogação,
  device de outra conta 409, revogado sem exchange/token, device desconhecido 404).
- `python scripts/check` — 12/12.
- Nenhum segredo no código/testes.

## Residual

1. A revogação é aplicada quando o dispositivo fala com o cloud; o token offline continua válido
   até o `exp` (máximo 7 dias). O runtime online deve consultar a denylist em um próximo ciclo.
2. Nome do dispositivo ainda é opcional (a landing envia o campo quando disponível).
3. Live mode/domínio/deploy seguem owner-gated.
