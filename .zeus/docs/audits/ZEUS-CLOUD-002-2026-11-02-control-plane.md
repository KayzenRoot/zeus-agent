# ZEUS-CLOUD-002 — Control plane de checkout e entitlement

**Data:** 2026-11-02
**Escopo:** serviço `zeus-cloud` local, test mode. Nenhuma cobrança real, deploy ou publicação.
**Status:** implementado e verificado localmente; sem aprovação independente.

## Entregue

- **Serviço FastAPI** em `cloud/service/`:
  - `GET /health` e `GET /api/plans` públicos;
  - `POST /api/checkout` autenticado por Clerk JWT, cria Checkout Session no Price ID do plano
    com trial de 2 dias e identidade (`client_reference_id`, metadata da sessão e da assinatura);
  - `GET /api/entitlement` devolve plano/status/fim do período/features, com acesso apenas para
    `active`/`trialing` e período não expirado;
  - `POST /api/stripe/webhook` verifica HMAC `t=...,v1=...` (tolerância 300 s, comparação em tempo
    constante) e processa `checkout.session.completed` e `customer.subscription.*`.
- **Persistência SQLite** de entitlement por `user_id` do Clerk, com busca por subscription id para
  eventos que chegam sem metadata.
- **Trava de live mode:** chave `sk_live_` recusada na inicialização até `ZEUS_CLOUD_ALLOW_LIVE=1`,
  que exige go-live aprovado pelo owner; `dev:` auth é recusado com chave live mesmo após o opt-in.
- **Fail-closed:** checkout não pago ou fora de `mode=subscription` não concede acesso; o
  `checkout.session.completed` grava `pending` e a ativação vem do objeto autoritativo de
  `customer.subscription.*` (sem fetch por ID de webhook, eliminando o sink de SSRF parcial).
- **Landing autenticada:** os botões dos quatro planos chamam o serviço com o token da sessão Clerk;
  Payment Links deixaram de ser o caminho de compra porque não carregam a identidade do usuário.
  Modal Clerk validado no Chrome existente; `afterSignInUrl` depreciado corrigido para
  `fallbackRedirectUrl`.

## Evidência local

- `scripts/run_tests.sh tests/cloud/test_cloud_service.py` — **15/15 PASS** (auth, checkout,
  identidade na assinatura, assinatura de webhook válida/inválida/expirada, trial, cancelamento,
  expiração de período, fallback por subscription, ordem invertida sem downgrade, checkout não
  pago e trava de dev auth/live mode).
- `python scripts/check` — **12/12 ok** (ruff + code health incluídos).
- Smoke HTTP real em `127.0.0.1:9129`: `/health` → `{"ok":true,...,"mode":"test"}`;
  `/api/plans` → catálogo; `/api/entitlement` sem token → 401; com dev auth → inativo.
- Chrome já aberto (PID do processo existente, sem abrir outra janela): landing recarregada com o
  HTML novo, listener presente (`getEventListeners(...).click.length === 1`), clique dispara o
  modal “Sign in to Zeus” do Clerk e nenhum aviso de depreciação permanece no console.
- Segredos não transcritos em código, logs, testes ou neste documento.

## Limitações e gates seguintes

1. O runtime (desktop/CLI) ainda não consulta o entitlement nem aplica grace offline; isso é o
   próximo incremento e bloqueia o release comercial.
2. Portal do cliente, troca de plano e cancelamento ainda não existem.
3. Webhook local ainda depende de `stripe listen` ou de endpoint público; não há deploy.
4. Migração para live mode, domínio público, termos/privacidade e revisão independente continuam
   owner-gated.
