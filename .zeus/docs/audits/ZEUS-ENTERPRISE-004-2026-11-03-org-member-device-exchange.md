# ZEUS-ENTERPRISE-004 — Ativação de member de Organization

**Data:** 2026-11-03
**Escopo:** correção de bug no fluxo de device code para membros de uma Organization Clerk.
**Status:** implementado e verificado localmente; sem aprovação independente.

## Sintoma

`POST /api/device/authorize` de um `org:member` emitia o código, mas
`POST /api/device/exchange` respondia **403 no active subscription**: o exchange buscava o
entitlement por `user_id` do member, enquanto a assinatura pertence à Organization. O owner
funcionava porque o `user_id` do entitlement era o próprio owner.

## Correção

- `device_codes.org_id` (migração automática `_ensure_column` em DBs existentes).
- `/api/device/authorize` grava a Organization no código.
- `/api/device/exchange` resolve o entitlement por `get_for_identity(user_id, org_id)` e audita no
  escopo da Organization.
- Nenhuma mudança no token: `sub` continua o titular do entitlement, `device_id` continua vinculante.

## Verificação

- `tests/cloud/test_cloud_service.py` — **45/45 PASS**.
- Novo contrato: member autoriza + troca o código e recebe token com o plano da Organization;
  dispositivo revogado não troca código novo.
- `python scripts/check` — **12/12 OK**.

## Residual

1. Seats continuam contados por dispositivo ativo; seats por membro/console administrativo e
   revogação online dentro de um ciclo seguem abertos no #51.
2. SSO/SAML/OIDC depende do IdP do owner no Clerk.
3. Live mode/domínio/deploy seguem owner-gated; nada disso foi executado.
