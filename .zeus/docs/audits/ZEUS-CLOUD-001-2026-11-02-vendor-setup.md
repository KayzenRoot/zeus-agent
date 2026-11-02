# ZEUS-CLOUD-001 | Configuração Clerk + Stripe (test mode)

**Data:** 2026-11-02 · **Escopo:** configuração dos provedores comerciais no Chrome do owner.
**Segredos:** não transcritos aqui; ficam no `.env` local do home real.

## Clerk

| Item | Valor |
|---|---|
| App | **Zeus** (`app_3LZQvceu62Q3uvSFc27zP0oekXj`) |
| Instância dev | `ins_3LZQvgwvGabslL3kb3dKiuQDAc6` |
| Frontend API | `adequate-viper-3823.clerk.accounts.dev` |
| Tipo | B2B — Organizations habilitado |
| Sign-in/sign-up | e-mail + telefone (SMS) habilitados; verificação de telefone no sign-up |
| Redirect nativo | `zeus://auth/callback` (allowlist de Native applications) |

Chaves de desenvolvimento copiadas para o `.env` local (`CLERK_PUBLISHABLE_KEY`,
`CLERK_SECRET_KEY`, `CLERK_APP_ID`, `CLERK_INSTANCE_ID`). A API Backend de instância retornou
403 para a chave de aplicação — configuração via dashboard.

## Stripe (test mode)

Conta **PromptApp** (`acct_1SrK3SRtfVHyZXkv`), chave de teste no `.env`
(`STRIPE_MODE=test`). Produtos/preços BRL criados pelo script idempotente
`scripts/zeus_cloud/stripe_setup.py`:

| Plano | Preço | Produto | Price | Payment Link |
|---|---|---|---|---|
| Mensal | R$ 990,00 | `prod_VYbHywAKtOdw8K` | `price_1UXU5LRtfVHyZXkvkSTUS7Jz` | `buy.stripe.com/test_9B67sN0JMaBJ24b1a68bS00` |
| Trimestral | R$ 2.670,00 | `prod_VYbHHpFhteuTQt` | `price_1UXU5NRtfVHyZXkvAFPIZD4q` | `buy.stripe.com/test_14A00l78a7px5gnf0W8bS01` |
| Semestral | R$ 5.040,00 | `prod_VYbHvDxrrYlCML` | `price_1UXU5PRtfVHyZXkvhYBmyRts` | `buy.stripe.com/test_8x2cN7akmeRZdMTaKG8bS02` |
| Anual | R$ 9.480,00 | `prod_VYbIGHHht2qM2j` | `price_1UXU5RRtfVHyZXkv3Jx3AjrQ` | `buy.stripe.com/test_7sY8wR646aBJ6kr8Cy8bS03` |

Todos com `trial_period_days=2` e recorrência em BRL. Nenhuma cobrança real; **test mode**.

## Residual

- Serviço `zeus-cloud` (checkout autenticado, webhook, entitlement, portal) — issues #34/#35.
- Migração para live mode, preços live e revisão fiscal — decisão do owner.
- Gate de assinatura no runtime (grace offline, JWT Ed25519) — issue #35.
- Site comercial público — issue #34.

A configuração não autoriza release/deploy; o app local segue funcionando offline.
