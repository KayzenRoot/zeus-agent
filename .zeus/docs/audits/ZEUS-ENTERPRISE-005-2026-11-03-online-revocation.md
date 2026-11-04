# ZEUS-ENTERPRISE-005 — Revogação online do entitlement

**Data:** 2026-11-03
**Escopo:** propagação de revogação em um ciclo online, sem remover a janela offline de 7 dias.
**Status:** implementado e verificado localmente; sem aprovação independente.

## Entregue

- `POST /api/device/check` no cloud: verifica a assinatura Ed25519 do token, o `device_id`, o
  registro/revogação do dispositivo e o status do entitlement. Retorna somente
  `active`/`reason`/`plan`/`seats`, sem segredos e sem exigir Clerk.
- Runtime `zeus_entitlement.require_entitlement()`: consulta o endpoint com timeout de **2 s**
  antes de liberar o turno, com cache local 0600 em `zeus-entitlement-check.json`.
  - cache positivo/negativo: 300 s; falha de rede: 60 s de tolerância e mantém o token válido.
  - resposta `active: false` bloqueia mesmo com token não expirado.
  - `ZEUS_DEV_UNLOCK=1` continua bypassando a checagem; ativação limpa o cache.
- `_post_json` ganhou timeout configurável; erros de rede/JSON não derrubam o turno.
- `cloud/README.md` documenta a rota, o cache e a janela offline.

## Verificação

- `tests/cloud/test_cloud_service.py` — **48/48 PASS** (check ativo, revogado, token inválido,
  assinatura cancelada).
- `tests/test_zeus_entitlement.py` — **11/11 PASS** (revogação + cache, offline grace, cache
  positivo, dev unlock, gate tipado).
- `python scripts/check` — **12/12 OK**.

## Residual

1. Um atacante que bloqueie a rede mantém a janela offline até `exp`; o token continua limitado a
   7 dias e vinculado ao dispositivo.
2. Seats por membro/console administrativo, convite/remoção e SSO/SAML/OIDC seguem abertos no #51.
3. O endpoint público não tem rate limit próprio nesta camada; token válido é o requisito.
4. Nenhuma mudança de prompt, toolsets ou cache de contexto; live mode/domínio/deploy seguem
   owner-gated.
