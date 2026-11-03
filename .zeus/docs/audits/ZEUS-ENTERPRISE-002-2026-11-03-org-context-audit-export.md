# ZEUS-ENTERPRISE-002 — Organization context e export de auditoria

**Data:** 2026-11-03
**Escopo:** segunda camada da issue #51. SSO/SAML/OIDC permanece owner-gated no Clerk.
**Status:** implementado e verificado localmente; sem aprovação independente.

## Entregue

- `current_identity` no cloud: além do `sub`, extrai `org_id` e `org_role` do JWT Clerk, sem
  armazenar o token.
- `GET /api/identity`: devolve `user_id`, `org_id`, `org_role` para o cliente.
- `GET /api/audit/export?format=csv|json&limit=1..100`: exporta os eventos do usuário com
  `Content-Disposition`, sem incluir tokens/segredos.
- Landing: seção **Auditoria** com últimos 20 eventos e botões CSV/JSON; a seção Dispositivos já
  mostra seats em uso.

## Verificação

- `tests/cloud/test_cloud_service.py` — **38/38 PASS**, incluindo contexto de Organization via
  dependency override, export JSON/CSV e conteúdo.
- `python scripts/check` — 12/12.
- Landing JS validado com `new Function` (sintaxe).

## Limite / residual

1. **SSO/SAML/OIDC** exige configurar a conexão de Identity Provider no dashboard Clerk
   (owner-gated). O código já consome `org_id`/`org_role`.
2. Seats por **Organization** (compartilhados entre membros) ainda não são aplicados: o
   entitlement é por usuário; a próxima camada precisa mapear a Organization assinante e contar
   devices por `org_id`.
3. Export de auditoria é por usuário; agregação por Organization fica para a mesma camada.
4. Live mode/domínio/deploy seguem owner-gated.
