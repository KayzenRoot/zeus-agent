# ZEUS-PROD-001 — Prontidão de produção (sem domínio nem live mode)

**Data:** 2026-11-03
**Escopo:** parte executável do #52 antes do go-live; domínio, DNS/TLS, deploy, webhook público e
Stripe live ficam owner-gated.
**Status:** implementado e verificado localmente; sem aprovação independente.

## Entregue

- `GET /api/readiness` público, somente booleanos e sem segredos:
  `stripe`, `stripe_webhook`, `clerk`, `entitlement_signing`, `plans` (quatro preços) e
  `database`; `ready` é a conjunção de todos, e `mode` distingue `test`/`live`.
- `signing_key_configured()` valida a chave Ed25519 (base64, 32 bytes) antes de reportar pronto.
- `EntitlementStore.ping()` faz um `SELECT 1` real no SQLite.
- `cloud/site/terms.html` e `cloud/site/privacy.html` em pt-BR, linkados no rodapé da landing,
  com placeholders explícitos para os dados do controlador e aviso de revisão jurídica.
- `cloud/README.md` com checklist de produção e o que permanece bloqueado até a compra do domínio.

## Verificação

- `tests/cloud/test_cloud_service.py` — **43/43 PASS**, incluindo readiness pronto, falta de
  preço, webhook/chave ausentes, ausência de segredos na resposta e DB acessível.
- `python scripts/check` — **12/12 OK**.
- Links legais validados contra os arquivos de `cloud/site/`.
- CI #59 — **14/14 PASS**. A primeira versão reprovou no Sonar com **6,3% de duplicação**
  (requisito ≤ 3%); as duas páginas passaram a compartilhar `cloud/site/legal.css` e o gate
  ficou verde. Merge commit `247b51b311`.

## Residual

1. Comprar domínio, definir DNS/TLS e publicar `api.<domínio>` + landing (owner).
2. Criar preços live no Stripe, configurar webhook público e `ZEUS_CLOUD_ALLOW_LIVE=1` na janela
   de go-live aprovada (owner).
3. Preencher razão social, CNPJ, endereço, suporte, DPO e foro; revisão jurídica.
4. Deploy do serviço com backup do SQLite e confirmação de readiness no ambiente final.
5. SSO/SAML/OIDC segue dependente do IdP no Clerk.

Nenhum gasto, cobrança real, deploy ou publicação foi executado nesta etapa.
