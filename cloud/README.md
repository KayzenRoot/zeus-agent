# Zeus Cloud — Clerk + Stripe (test mode)

Este diretório guarda apenas configuração **não secreta**. Chaves ficam no `.env` local do owner
(`%LOCALAPPDATA%\hermes\.env` no Windows) e nunca são commitadas.

## Estado atual

- **Clerk**: app `Zeus`, B2B com Organizations, e-mail + telefone (SMS) habilitados, redirect
  nativo `zeus://auth/callback`.
- **Stripe**: 4 produtos/preços BRL em test mode, trial de **2 dias**, Checkout Sessions criadas
  pelo serviço. Os Payment Links foram removidos do catálogo; a compra sempre passa pelo checkout
  autenticado.
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
| `GET /api/readiness` | pública | checagens booleanas de configuração, sem segredos |
| `GET /api/plans` | pública | catálogo de `cloud/plans.json` |
| `POST /api/checkout` | Bearer Clerk JWT | `{ "plan": "monthly" }` → `{ "url", "id" }` |
| `GET /api/entitlement` | Bearer Clerk JWT | plano, status, fim do período e features |
| `POST /api/entitlement/token` | Bearer Clerk JWT | `{ "device_id": "..." }` → token Ed25519 de 7 dias |
| `POST /api/device/authorize` | Bearer Clerk JWT | gera código de ativação de 10 min para o dispositivo |
| `POST /api/device/exchange` | código de uso único | troca código + `device_id` pelo token assinado |
| `POST /api/device/check` | token Ed25519 | revalida dispositivo/assinatura e informa `active`/`revoked`/`inactive`; não exige Clerk |
| `POST /api/billing/portal` | Bearer Clerk JWT | abre o Customer Portal do Stripe (cancelar/trocar plano) |
| `GET /api/devices` | Bearer Clerk JWT | lista dispositivos e status de revogação |
| `POST /api/devices/{device_id}/revoke` | Bearer Clerk JWT | revoga um dispositivo |
| `GET /api/audit?limit=50` | Bearer Clerk JWT | eventos de ativação/revogação/portal/checkout |
| `GET /api/audit/export?format=csv\|json` | Bearer Clerk JWT | exporta a auditoria |
| `GET /api/identity` | Bearer Clerk JWT | usuário + `org_id`/`org_role` do Clerk |
| `POST /api/stripe/webhook` | assinatura Stripe | `checkout.session.completed` e `customer.subscription.*` |

O entitlement só fica ativo com status `active`/`trialing` **e** período não expirado.
`checkout.session.completed` grava `pending`; a ativação usa o objeto autoritativo de
`customer.subscription.*`, sem buscar a assinatura por um ID recebido no webhook. O runtime
offline vai aplicar uma janela de tolerância própria (próxima camada).

O token de `POST /api/entitlement/token` é assinado com **Ed25519**, tem `iss=zeus-cloud`, `sub`,
`plan`, `features`, `seats`, `device_id` e validade de 7 dias (`ZEUS_ENTITLEMENT_TTL_DAYS`). A
chave pública fica em [`entitlement_public_key.pem`](entitlement_public_key.pem); a privada só no
`.env`. O runtime valida assinatura, `device_id` e `exp` antes de liberar o app.

Para ativar um dispositivo, o site autenticado chama `/api/device/authorize` (código de 10 min,
uso único, vinculado ao `device_id`) e entrega o código ao app via `zeus://auth/callback` ou
digitação. O app troca em `/api/device/exchange` e grava o token em
`<HERMES_HOME>/zeus-entitlement.json` com permissão 0600.

O runtime consulta `POST /api/device/check` antes de liberar um turno, com timeout de 2 s e cache
local de 300 s (60 s quando a nuvem está indisponível). Resposta `active: false` bloqueia o turno
mesmo com o token ainda dentro da validade; falha de rede preserva a janela offline de 7 dias.
Ativação bem-sucedida limpa o cache.

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
ZEUS_ENTITLEMENT_PRIVATE_KEY_B64=...   # 32 bytes Ed25519 em base64; nunca commitar
ZEUS_ENTITLEMENT_TTL_DAYS=7
```

Opcionais: `ZEUS_CLOUD_DB` (default `~/.zeus-cloud/entitlements.db`), `ZEUS_CLOUD_PORT` (default
`9121`), `ZEUS_CLOUD_ALLOWED_ORIGINS`, `ZEUS_CLOUD_SUCCESS_URL`, `ZEUS_CLOUD_CANCEL_URL`,
`ZEUS_CLOUD_PORTAL_RETURN_URL`.

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
- `ZEUS_DEV_UNLOCK=1` libera o runtime local sem token; nunca usar em produção.
- `hermes entitlement status`, `hermes entitlement device-id` e `hermes entitlement activate <code>`
  inspecionam/ativam o dispositivo pelo CLI.
- O serviço não devolve segredos; `/api/plans` só expõe catálogo e chave publicável.
- O desktop nunca recebe `CLERK_SECRET_KEY`/`STRIPE_SECRET_KEY`.

## Testes

```bash
scripts/run_tests.sh tests/cloud/test_cloud_service.py
```

Cobrem autenticação, criação de checkout, assinatura de webhook (válida/inválida/expirada),
trial, cancelamento, expiração de período, checkout não pago, checkout pending até o evento de
assinatura, ativação por device code, portal do cliente, seats, listagem/revogação de
dispositivos, auditoria/export e a trava de live mode.

## Organizations

Quando o JWT do Clerk traz `org_id`, o checkout grava a Organization na sessão/assinatura e o
entitlement passa a valer para os membros dessa Organization. Seats e dispositivos são contados
por Organization; `org:admin`/`org:owner` podem revogar dispositivos e abrir o portal. Membros
podem ativar dispositivos dentro dos seats; o device code carrega a Organization e o exchange
resolve o entitlement da Organization. SSO/SAML/OIDC exige configurar o IdP no Clerk.

## Pendências antes do release

1. SSO/SAML/OIDC e seats por Organization: requerem o IdP do owner configurado no Clerk; o
   contexto `org_id`/`org_role` já chega em `/api/identity`.
2. Domínio público, DNS/TLS, webhook público em `https://api.<domínio>/api/stripe/webhook` e
   deploy do serviço/landing — **owner-gated** até a compra do domínio.
3. Live mode com os mesmos quatro preços, revisão do owner e `ZEUS_CLOUD_ALLOW_LIVE=1` apenas no
   go-live aprovado.
4. Revisão jurídica dos termos/privacidade e preenchimento dos dados do controlador.
5. Release assinada (MSIX/DMG/publisher) — issue #4.

## Checklist de produção (#52)

O que já está pronto e testado sem domínio nem live mode:

- [x] Checkout autenticado por Clerk (e-mail/telefone) com 2 dias de trial.
- [x] Quatro planos BRL em test mode; compra nunca usa Payment Link público.
- [x] Webhook Stripe assinado (HMAC, tolerância de 300 s, comparação constante).
- [x] Entitlement Ed25519 vinculado ao dispositivo, com assinatura verificada no runtime.
- [x] Seats e escopo por usuário/Organization; portal, dispositivos e auditoria.
- [x] `GET /api/readiness` valida Stripe, webhook, Clerk, chave de assinatura, quatro preços e DB
      sem devolver segredos; responde `{"ready": false, "checks": {...}}` se faltar configuração.
- [x] Termos de uso e Política de Privacidade em `cloud/site/terms.html` e
      `cloud/site/privacy.html`, linkados no rodapé da landing.
- [x] Landing sem referências visuais ao Hermes; atribuição MIT no README/termos.

Antes do go-live, o owner precisa fornecer/executar:

- [ ] Comprar o domínio e definir `api.<domínio>`/`<domínio>`.
- [ ] Criar os quatro preços **live** no Stripe e configurar o webhook público.
- [ ] Preencher `RAZÃO SOCIAL`, `CNPJ`, endereço, e-mail de suporte, DPO e foro nos documentos
      legais; revisão jurídica.
- [ ] Definir `ZEUS_CLOUD_ALLOW_LIVE=1` somente na janela de go-live aprovada.
- [ ] Deploy do serviço/landing com TLS e backup do SQLite.
- [ ] Confirmar `GET /api/readiness` → `ready: true`, `mode: "live"` no ambiente final.

Enquanto o domínio não for comprado, o serviço permanece em `127.0.0.1:9121`, test mode, sem
deploy público e sem cobrança real. Nada nesta etapa autoriza gastos ou operações financeiras.
