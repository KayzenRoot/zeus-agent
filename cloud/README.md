# Zeus Cloud — configuração dos provedores

Este diretório guarda apenas configuração **não secreta**. Chaves ficam no `.env` local do
owner (`%LOCALAPPDATA%\hermes\.env` no Windows) e nunca são commitadas.

## Estado atual (test mode)

- **Clerk**: app `Zeus`, B2B com Organizations, e-mail + telefone (SMS) habilitados, redirect
  nativo `zeus://auth/callback`.
- **Stripe**: 4 produtos/preços BRL em test mode, trial de **2 dias**, Payment Links ativos.
- IDs, Price IDs e links em [`plans.json`](plans.json).

## Variáveis de ambiente

```dotenv
CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
CLERK_APP_ID=app_...
CLERK_INSTANCE_ID=ins_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_MODE=test
STRIPE_PRICE_MONTHLY=price_...
STRIPE_PRICE_QUARTERLY=price_...
STRIPE_PRICE_SEMIANNUAL=price_...
STRIPE_PRICE_ANNUAL=price_...
```

Nunca coloque `CLERK_SECRET_KEY` ou `STRIPE_SECRET_KEY` no cliente/desktop. O desktop deve falar
com o Zeus Cloud, que guarda a chave e emite o entitlement.

## Landing comercial (test mode)

A landing está em `cloud/site/index.html`, com os quatro planos, trial de 2 dias, botões de
Checkout Stripe e entrada via Clerk Account Portal. Para visualizar:

```bash
python -m http.server 9120 --directory cloud/site
# http://127.0.0.1:9120/
```

Ela é estática de propósito: não guarda segredo nem libera o app. O gate de assinatura continua
sendo responsabilidade do serviço `zeus-cloud` (próxima camada).

## Próxima camada (issue #34/#35)

O serviço `zeus-cloud` (a criar) precisa de:

1. `POST /api/checkout` — valida o JWT do Clerk, abre Checkout Session Stripe para o Price ID do
   plano com `trial_period_days=2`.
2. `POST /api/stripe/webhook` — verifica a assinatura Stripe e grava assinatura/entitlement.
3. `GET /api/entitlement` — devolve `plan`, `features`, `exp`, `device_id` para o runtime.
4. Portal do cliente e cancelamento.
5. Migrar de test mode para live com os mesmos quatro preços (revisão do owner).

Até o gate existir, os Payment Links servem para testar a compra; eles **não** liberam o app.
