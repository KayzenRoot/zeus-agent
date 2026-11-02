# ADR-007 — Zeus Cloud: Clerk + Stripe, trial e planos

**Status:** APPROVED pelo owner em 2026-11-02 (mensagem: "1 - clerk; 2 - Stripe; 3 - 2 dias de
trial - plano mensal 990 reais depois planos trimestral semestral e anual").
**Contexto:** EXP-002 (#41) exige conta e assinatura para o Zeus comercial, mantendo o runtime
local-first.

## Decisão

- **Auth:** Clerk (e-mail + telefone, OTP, sessões e MFA gerenciados).
- **Billing:** Stripe Billing + Stripe Tax; Checkout e Customer Portal hospedados; nenhum cartão
  no Zeus.
- **Trial:** 2 dias (`trial_period_days: 2`) no primeiro checkout; sem cobrança antes do fim.
- **Plano mensal:** R$ 990,00.
- **Trimestral/semestral/anual:** proposta do executor, sujeita a confirmação de preço:

  | Plano | Preço | Equivalente mensal | Desconto |
  |---|---|---|---|
  | Mensal | R$ 990,00 | R$ 990,00 | — |
  | Trimestral | R$ 2.670,00 | R$ 890,00 | ~10% |
  | Semestral | R$ 5.040,00 | R$ 840,00 | ~15% |
  | Anual | R$ 9.480,00 | R$ 790,00 | ~20% |

## Entitlement

- Stripe é a fonte da assinatura; o Zeus Cloud emite um JWT curto assinado (Ed25519) com `plan`,
  `features`, `seats`, `exp`, `device_id`.
- Grace offline de 7–14 dias; revogação por denylist; nunca apagar dados locais por inadimplência.
- Feature flags por plano: constelação, sync, nº de agentes, skills enterprise.

## Consequências

- Requer contas/projetos Clerk e Stripe e chaves (owner); sem elas, o fluxo roda com mocks locais.
- Stripe Tax exige cadastro fiscal; avaliar Paddle no futuro se a carga tributária global crescer.
- O modo de desenvolvimento local continua liberado por flag (`ZEUS_DEV_UNLOCK=1`), sem burlar
  produção.
