# Zeus Cloud setup helpers

## Stripe (planos)

`stripe_setup.py` creates the four Zeus Pro products and BRL recurring prices:

| Plano | Preço | Intervalo |
|---|---|---|
| Mensal | R$ 990,00 | 1 mês |
| Trimestral | R$ 2.670,00 | 3 meses |
| Semestral | R$ 5.040,00 | 6 meses |
| Anual | R$ 9.480,00 | 12 meses |

Trial: **2 dias**, aplicado pelo Checkout (`trial_period_days: 2`), não pelo Price.

```bash
# 1. Sem rede: confira o catálogo
python -I scripts/zeus_cloud/stripe_setup.py --dry-run

# 2. Chave de TESTE (nunca commitar)
STRIPE_SECRET_KEY=sk_test_... python scripts/zeus_cloud/stripe_setup.py \
  --out ../zeus-build-cache/stripe-plans.json

# 3. Só depois de validar no test mode:
STRIPE_SECRET_KEY=sk_live_... python scripts/zeus_cloud/stripe_setup.py --live \
  --out ../zeus-build-cache/stripe-plans-live.json
```

O script é idempotente: reutiliza produto cujo `metadata.zeus_plan` casa e preço com
valor/moeda/intervalo iguais. Ele nunca imprime a chave secreta.

## Clerk (conta)

Criar o app no dashboard Clerk (e-mail + telefone/OTP, MFA). Configurar:

- Redirect de desktop: `zeus://auth/callback`
- Redirect local: `http://127.0.0.1:9119/*`
- Produção: domínio do site comercial (a definir)
- Chaves no `.env` do home **local**: `CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`

A criação do app e a cópia das chaves exigem a sessão do owner no Clerk (não há API
pública de criação de aplicação fora do Clerk Platform). A integração runtime é a
issue #33.

## Ordem de ativação

1. Clerk app + chaves.
2. Stripe test mode + script acima (4 Price IDs).
3. Checkout/Portal com `trial_period_days=2`.
4. Webhook de assinatura no Zeus Cloud (#34).
5. Gate de entitlement no runtime (#35) com grace offline.
