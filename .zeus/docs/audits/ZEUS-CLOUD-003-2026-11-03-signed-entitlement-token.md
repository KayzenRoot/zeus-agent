# ZEUS-CLOUD-003 — Token de entitlement assinado (camada 1 do gate)

**Data:** 2026-11-03
**Escopo:** emissão de token Ed25519 device-bound no Zeus Cloud. O gate no runtime e a ativação
do desktop ainda não foram implementados. Nenhuma cobrança real, deploy ou live mode.
**Status:** implementado e verificado localmente; sem aprovação independente.

## Entregue

- `cloud/service/entitlements.py`: features/seats por plano, verificação de entitlement ativo e
  assinatura Ed25519 (`iss=zeus-cloud`, `sub`, `plan`, `features`, `seats`, `device_id`, `iat`,
  `exp`).
- `POST /api/entitlement/token`: exige Bearer Clerk e `device_id` (8–128 chars), devolve 403 sem
  assinatura ativa e 503 se a chave de assinatura não estiver configurada.
- `ZEUS_ENTITLEMENT_PRIVATE_KEY_B64` (32 bytes raw em base64, só no `.env`) e
  `ZEUS_ENTITLEMENT_TTL_DAYS` (default 7). Chave pública em
  `cloud/entitlement_public_key.pem` — material público, versionável.
- TTL inválido/negativo falha fechado; o token não é emitido sem chave válida.

## Evidência local

- `scripts/run_tests.sh tests/cloud/test_cloud_service.py` — **20/20 PASS**, incluindo:
  token verificável com a chave pública, `device_id`, plano anual/seats/features, expiração de
  7 dias, 403 sem assinatura, 422 sem device id, 503 sem chave e validade da chave pública
  versionada.
- `python scripts/check` — **12/12 ok**.
- Par de chaves de **test mode** gerado localmente; a privada foi anexada ao `.env` do home e
  não aparece em código, logs, testes ou neste documento.
- Smoke real em `127.0.0.1:9130` com a chave do `.env`: `POST /api/entitlement/token` respondeu
  **200**, plano `annual`, 10 seats e token de 388 chars; o token foi verificado com a chave
  pública versionada (`iss=zeus-cloud`, `sub=smoke_user`, `device_id`, TTL de 7 dias).

## Residual

1. Runtime desktop/CLI ainda não valida o token nem aplica grace offline.
2. Ativação do desktop (deep link `zeus://`) e armazenamento local 0600 ainda não existem.
3. Rotação de chave (`kid`), denylist/revogação online e reconciliação periódica ficam para a
   camada 2/3.
