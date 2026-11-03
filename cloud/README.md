# Zeus Cloud — Clerk + Stripe (test mode)

Este diretório guarda apenas configuração **não secreta**. Chaves ficam no `.env` local do owner
(`%LOCALAPPDATA%\hermes\.env` no Windows) e nunca são commitadas.

## Estado atual

- **Clerk**: app `Zeus`, B2B com Organizations, e-mail + telefone (SMS) habilitados, redirect
  nativo `zeus://auth/callback`.
- **Stripe**: 4 produtos/preços BRL em test mode, trial de **2 dias**, Checkout Sessions criadas
  pelo serviço (os Payment Links continuam no `plans.json` apenas como catálogo).
- **Serviço `zeus-cloud`**: FastAPI em `cloud/service/`, com checkout autenticado, webhook Stripe
  assinado e entitlement em SQLite.
- **Landing**: `cloud/site/index.html` usa Clerk no navegador e chama o serviço; a compra fica
  vinculada ao `sub` do Clerk, então o webhook consegue liberar o usuário correto.

## Rodar localmente

```bash
# terminal 1 — serviço (127.0.0.1:9121); carrega o .env do HERMES_HOME
python -m cloud.service

# terminal 2 — landing (127.0.0.1:9120)
python -m http.server 9120 --directory cloud/site
```

Abra <http://127.0.0.1:9120>. O botão de assinatura abre o login Clerk; depois do login, o
serviço cria a Checkout Session e redireciona para o Stripe em test mode.

O endereço do serviço usado pela landing fica no `<meta name="zeus-cloud-api">`; em produção,
troque por `https://api.<domínio>`.

## API

| Rota | Auth | Função |
|---|---|---|
| `GET /health` | pública | status e modo (`test`/`live`) |
| `GET /api/plans` | pública | catálogo de `cloud/plans.json` |
| `POST /api/checkout` | Bearer Clerk JWT | `{ "plan": "monthly" }` → `{ "url", "id" }` |
| `GET /api/entitlement` | Bearer Clerk JWT | plano, status, fim do período e features |
| `POST /api/stripe/webhook` | assinatura Stripe | `checkout.session.completed` e `customer.subscription.*` |

O entitlement só fica ativo com status `active`/`trialing` **e** período não expirado.
`checkout.session.completed` grava `pending`; a ativação usa o objeto autoritativo de
`customer.subscription.*`, sem buscar a assinatura por um ID recebido no webhook. O runtime
offline vai aplicar uma janela de tolerância própria (próxima camada).

## Variáveis de ambiente

```dotenv
CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
CLERK_APP_ID=app_...
CLERK_INSTANCE_ID=ins_...
CLERK_FRONTEND_API=adequate-viper-3823.clerk.accounts.dev
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_MODE=test
STRIPE_PRICE_MONTHLY=price_...
STRIPE_PRICE_QUARTERLY=price_...
STRIPE_PRICE_SEMIANNUAL=price_...
STRIPE_PRICE_ANNUAL=price_...
```

Opcionais: `ZEUS_CLOUD_DB` (default `~/.zeus-cloud/entitlements.db`), `ZEUS_CLOUD_PORT` (default
`9121`), `ZEUS_CLOUD_ALLOWED_ORIGINS`, `ZEUS_CLOUD_SUCCESS_URL`, `ZEUS_CLOUD_CANCEL_URL`.

Nunca coloque `CLERK_SECRET_KEY` ou `STRIPE_SECRET_KEY` no cliente/desktop. O desktop fala com o
Zeus Cloud, que guarda a chave e emite o entitlement.

### Webhook local

Com o Stripe CLI instalado:

```bash
stripe listen --forward-to 127.0.0.1:9121/api/stripe/webhook
# copie o whsec_... exibido para STRIPE_WEBHOOK_SECRET
```

A verificação HMAC usa tolerância de 300 s e comparação em tempo constante. Sem o segredo
configurado, o endpoint responde 400 e não grava nada.

### Desenvolvimento sem Clerk

Apenas em ambiente local, `ZEUS_CLOUD_DEV_AUTH=1` aceita `Authorization: Bearer dev:<user_id>`.
Isso não substitui o Clerk em produção e não deve ser habilitado em deploy.

## Segurança

- Chave `sk_live_` é recusada na inicialização até `ZEUS_CLOUD_ALLOW_LIVE=1`, que só deve ser
  definido após o go-live aprovado pelo owner.
- O serviço não devolve segredos; `/api/plans` só expõe catálogo e chave publicável.
- O desktop nunca recebe `CLERK_SECRET_KEY`/`STRIPE_SECRET_KEY`.

## Testes

```bash
scripts/run_tests.sh tests/cloud/test_cloud_service.py
```

Cobrem autenticação, criação de checkout, assinatura de webhook (válida/inválida/expirada),
trial, cancelamento, expiração de período, checkout não pago, checkout pending até o evento de
assinatura e a trava de live mode.

## Pendências antes do release

1. Gate de assinatura no runtime (desktop/CLI) com grace offline assinado.
2. Portal do cliente/cancelamento e troca de plano.
3. Migrar para live mode com os mesmos quatro preços (revisão do owner) e domínio público.
4. Publicar termos/privacidade e configurar o endpoint de webhook no dashboard Stripe.
