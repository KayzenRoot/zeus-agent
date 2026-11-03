# ZEUS-ENTERPRISE-001 — Seats e auditoria

**Data:** 2026-11-03
**Escopo:** primeira camada da issue #51. SSO/Organizations no Clerk segue configuração externa.
**Status:** implementado e verificado localmente; sem aprovação independente.

## Entregue

- **Seats por plano**: `monthly/quarterly=5`, `semiannual=8`, `annual=10`.
  - `POST /api/device/authorize` recusa novo dispositivo com `409 seat limit reached` quando o
    usuário já tem `seats` dispositivos ativos.
  - Reautorizar um dispositivo existente não consome seat; dispositivo revogado não conta e não
    pode ser reautorizado.
  - `GET /api/entitlement` expõe `seats` do plano.
- **Auditoria** em SQLite (`audit_events`): ativação, troca de código, revogação, criação de
  checkout e abertura do portal.
  - `GET /api/audit?limit=1..100` lista os eventos do usuário autenticado; detalhes não incluem
    tokens/segredos.
- **Landing**: a seção Dispositivos mostra `N de S seats em uso` usando o entitlement.

## Verificação

- `tests/cloud/test_cloud_service.py` — **36/36 PASS**, incluindo limite de seats, reautorização,
  revogação liberando seat, seats no entitlement, auditoria e limite inválido.
- `python scripts/check` — 12/12.
- Nenhum segredo no código/testes.

## Residual

1. SSO/SAML/OIDC e papéis por Organization dependem da configuração do Clerk; o enforcement
   org-level (seats compartilhados por organização) fica para a próxima camada.
2. Export CSV/JSON e UI de auditoria no dashboard ainda não existem.
3. Live mode/domínio/deploy seguem owner-gated.
