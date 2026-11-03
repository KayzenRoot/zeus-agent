# ZEUS-ENTERPRISE-003 — Entitlement e seats por Organization

**Data:** 2026-11-03
**Escopo:** terceira camada do #51; SSO/IdP segue owner-gated no Clerk.
**Status:** implementado e verificado localmente; sem aprovação independente.

## Entregue

- `entitlements.org_id`, `devices.org_id` e `audit_events.org_id` (migração automática para DBs
  existentes).
- Checkout com `org_id` grava `zeus_org_id` na Checkout Session **e** na assinatura; webhooks
  propagam a Organization para o entitlement.
- `get_for_identity(user, org)`: membro de Organization usa o entitlement da Organization.
- Seats e dispositivos contados por Organization; `org:admin`/`org:owner` podem revogar e abrir o
  portal; membros comuns não podem iniciar checkout, abrir portal ou revogar.
- Auditoria e export usam o escopo da Organization quando presente.
- Landing continua exibindo seats em uso; a API `/api/entitlement` inclui `scope`
  (`user`/`organization`).

## Verificação

- `tests/cloud/test_cloud_service.py` — **40/40 PASS**, incluindo checkout com `zeus_org_id`,
  entitlement compartilhado entre owner e member, seat scope, revogação restrita ao admin e
  bloqueio de checkout/portal para member.
- `python scripts/check` — 12/12.

## Residual

1. SSO/SAML/OIDC: owner configura o Identity Provider no Clerk; o código já consome
   `org_id`/`org_role`.
2. Papéis finos (ex.: `org:billing`) e convite/remoção de membros ficam no Clerk.
3. Live mode/domínio/deploy seguem owner-gated.
