# ZEUS-CLOUD-005 — Portal do cliente (Stripe Billing Portal)

**Data:** 2026-11-03
**Escopo:** autoatendimento de assinatura. Test mode; sem cobrança real, deploy ou live mode.
**Status:** implementado e verificado localmente; sem aprovação independente.

## Entregue

- `POST /api/billing/portal` (Bearer Clerk): exige assinatura ativa e `stripe_customer_id`
  persistido; cria uma sessão do **Stripe Customer Portal** e devolve a URL.
- `stripe_api.create_billing_portal_session` com `customer` e `return_url`
  (`ZEUS_CLOUD_PORTAL_RETURN_URL`, default `http://127.0.0.1:9120/?portal=done`).
- Landing: botão **Gerenciar assinatura** com login Clerk, chamada autenticada e redirecionamento
  para o portal; mensagem de retorno `?portal=done`.
- Sem cartão no Zeus: cancelamento, troca de plano e recibos ficam no Stripe.

## Evidência local

- `scripts/run_tests.sh tests/cloud/test_cloud_service.py` — **29/29 PASS**, incluindo portal com
  customer (URL), conta sem customer (404), assinatura inativa (403) e payload
  `customer`/`return_url` no Stripe.
- `python scripts/check` — 12/12 (revalidar no commit).
- Nenhum segredo no código/testes.

## Residual

1. Customer Portal precisa ser ativado/ configurado no dashboard Stripe para os métodos de
   pagamento e produtos desejados.
2. O portal é somente autoatendimento; conciliação de upgrade/downgrade continua via webhook
   `customer.subscription.*`.
3. Live mode, domínio, termos e deploy seguem owner-gated.
