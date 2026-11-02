# Zeus Experience 2.0 + Zeus Cloud — roadmap de produto

**Status:** proposta do executor para decisão do owner · **Data:** 2026-11-02
**Escopo:** evolução do Zeus local (ADR-003) para um produto comercial com conta, assinatura,
experiência “Dots-like” e recursos de empresa. Nada aqui autoriza gasto, conta externa, deploy ou
publicação; integrações reais de pagamento/auth dependem de ativos e aprovação do owner.

## 1. Visão

Zeus deixa de ser “um agente local com dashboard” e passa a ser um **sistema operacional de
força de trabalho de IA**: o usuário descreve o objetivo, o **Orquestrador** decompõe, cria/atribui
skills e acompanha os agentes em uma **constelação visual**. O produto tem duas camadas:

- **Zeus Runtime (local-first):** agentes, terminal, arquivos, memória, skills, Kanban, gateway.
  Continua funcionando offline e com BYOK.
- **Zeus Cloud (control plane):** site comercial, conta (e-mail/telefone), assinatura, entitlement,
  sincronização opcional, equipes e auditoria. O runtime não depende da nuvem para operar; a nuvem
  autoriza o uso e entrega conveniência.

## 2. Princípios

1. **Dark-first, calmo e legível** — preto/grafite, alto contraste, movimento discreto; nada de
   interface “clara” por padrão.
2. **Um objetivo, vários agentes** — o Orquestrador é o único ponto de entrada; especialistas
   aparecem como nós e só recebem o que precisam.
3. **Consentimento antes de ação** — auto-healing, instalação de skill e alteração de configuração
   pedem permissão explícita, com diff e rollback.
4. **BYOK + assinatura** — o plano paga o produto (orquestração, nuvem, suporte); o modelo pode ser
   do usuário (OpenCode Go, OpenAI, Anthropic, MiniMax, DeepSeek, Gemini, endpoint próprio).
5. **Empresa-ready** — RBAC, auditoria exportável, SSO, limites de custo e política por workspace.
6. **Nada de telemetria sem opt-in**; dados de cliente não viram treino.

## 3. Fases

### Fase 0 — Fundação visual (1º incremento, sem bloqueios)
- Tema **Zeus Night** como padrão (web + desktop), removendo o claro/“Nous Blue” da primeira
  impressão.
- Onboarding sem **Nous Portal** e sem **self-hosted endpoint** na tela inicial; foco em
  login/plano + provedores: **OpenCode Go, OpenAI, Anthropic (Claude), MiniMax, DeepSeek, Gemini**.
- Página **Constelação**: canvas escuro com o Orquestrador no centro, especialistas em órbita,
  arestas animadas de delegação/mensagem, inspetor lateral e estados vazios.
- Novo mark/wordmark Zeus (SVG) e aplicação em favicon, app icon, banner TUI e instalador.

### Fase 1 — Conta e assinatura
- Site comercial (planos mensal/semestral/anual) com checkout hospedado.
- Conta por **e-mail e telefone** (OTP/magic link), device login no desktop/CLI.
- Entitlement assinado (JWT curto + refresh), *grace period* offline, revogação e Portal do cliente.
- Gate no primeiro-run: sem assinatura ativa, o app oferece plano/entrar; modo local de
  desenvolvimento continua disponível por flag.

### Fase 2 — Orquestrador e Skill Forge
- Perfil mestre “Zeus” que decompõe objetivo, escolhe especialistas e mantém orçamento.
- Skill Forge: propor skill → sandbox → testes → aprovação → versão → atribuição por papel.
- Catálogo visual de skills e permissões (“quem pode usar o quê”).

### Fase 3 — Auto-healing
- Health checks: gateway, banco, disco, credenciais, provider, portas, atualização.
- Diagnóstico explicável + pedido de permissão ao dono da máquina.
- Reparos allowlisted (restart de gateway, rebuild de ambiente, limpar cache, rotacionar log,
  restaurar backup), sempre com verificação e auditoria.
- Nunca reparo destrutivo silencioso; rollback obrigatório.

### Fase 4 — Enterprise
- Workspaces/equipes, RBAC (owner/admin/operator/viewer), auditoria exportável (JSONL/CSV).
- SSO SAML/OIDC, políticas de retenção, spend caps, endpoints privados e licença offline.
- Pacotes de skills por vertical (jurídico, financeiro, suporte, dev).

## 4. Arquitetura comercial recomendada

```
Desktop/CLI ──device login──> Zeus Cloud (Auth + Billing + Entitlements)
     │                              │
     │  license JWT (curto)         │  Stripe/Paddle webhooks
     └── runtime local (offline) <──┘
```

- **Auth:** Supabase Auth (e-mail OTP + telefone/SMS) ou Clerk se o requisito de telefone/UX for
  mais forte; ambos evitam construir hash/OTP do zero. Decisão do owner.
- **Billing:** **Paddle** como Merchant of Record (impostos globais, IVA, disputas) ou **Stripe**
  Billing + Tax se o owner preferir controle direto. Nunca armazenar cartão no Zeus.
- **Entitlement:** JWT assinado (Ed25519), claims `sub`, `plan`, `features`, `seats`, `exp`,
  `device_id`; refresh a cada 24 h; grace offline 7–14 dias; revogação via denylist.
- **Planos sugeridos:** Free (local, 1 agente/orçamento baixo), Pro (mensal/semestral/anual,
  constelação, sync, N agentes), Team (assentos, RBAC, auditoria), Enterprise (SSO, on-prem,
  licença offline). Anual com ~2 meses de desconto; semestral ~1 mês.
- **Antifraude:** device binding + limite de ativações; sem telemetria invasiva.
- **Site:** Next.js (marketing + pricing + checkout + webhook) em repositório/serviço separado;
  o Zeus não serve o checkout.

## 5. Constelação (Dots-like)

- Centro: **Orquestrador** (pulso contínuo quando pensa).
- Órbita: especialistas (pesquisa, código, arquivos, navegador, financeiro, suporte) com anel de
  estado (idle/working/waiting/done/error).
- Arestas: delegação (sólida), retorno (tracejada), mensagem (pulso), conflito (vermelho).
- Interações: clique abre inspetor (tarefa, modelo, tokens, custo, últimas mensagens); arrastar
  fixa; scroll dá zoom; “replay” reconstrói a linha do tempo.
- Dados: eventos reais de sessão/delegação/Kanban; modo demo para onboarding.
- Acessibilidade: navegação por teclado, lista textual equivalente, `prefers-reduced-motion`.

## 6. Auto-healing — contrato de segurança

1. Detectar (health check periódico + erro do usuário).
2. Explicar em linguagem simples e mostrar o que será tocado.
3. Pedir permissão (aprovar uma vez / sempre para este tipo).
4. Executar apenas reparo allowlisted, em sandbox quando possível.
5. Verificar (health + teste funcional).
6. Registrar auditoria e oferecer rollback.

## 7. Decisões pendentes do owner

| Decisão | Escolha | Bloqueia |
|---|---|---|
| Auth (e-mail + telefone) | **Clerk** (owner, 2026-11-02) | login/checkout |
| Pagamento | **Stripe** (owner, 2026-11-02) | site/assinatura |
| Trial | **2 dias** (owner) | checkout |
| Plano mensal | **R$ 990,00** (owner) | pricing |
| Trimestral/semestral/anual | **R$ 2.670 / R$ 5.040 / R$ 9.480** (proposta 10/15/20% off; confirmar) | pricing |
| Referência visual “Dots” | **ChatGPT Dots** (avatares-bolha, Activity View) — confirmado | refinamento da constelação |
| Marca | novo mark Zeus aprovado pelo owner (2026-11-02) | assets/instalador |
| Modo dev local sem assinatura | flag `ZEUS_DEV_UNLOCK=1` | testes locais |

## 8. Riscos

- **Bypass de licença**: mitigar com JWT curto + device binding + verificação periódica; aceitar
  que software local sempre é contornável e focar em valor contínuo (sync, updates, suporte).
- **SMS/OTP custa dinheiro**: rate limit, e-mail como padrão, telefone opcional.
- **Impostos globais**: Paddle reduz carga; Stripe Tax exige cuidado.
- **Privacidade (LGPD/GDPR)**: minimizar dados, retenção configurável, DPA, exclusão de conta.
- **Provider ToS**: revenda de inferência exige contrato; por isso o padrão é BYOK + OpenCode Go
  como conta do usuário.
- **Auto-healing**: qualquer reparo pode piorar; allowlist + backup + rollback + consentimento.

## 9. Issues

Épico: [#41](https://github.com/KayzenRoot/zeus-agent/issues/41) · Fase 0: [#30](https://github.com/KayzenRoot/zeus-agent/issues/30) constelação, [#31](https://github.com/KayzenRoot/zeus-agent/issues/31) dark/marca, [#32](https://github.com/KayzenRoot/zeus-agent/issues/32) onboarding, [#40](https://github.com/KayzenRoot/zeus-agent/issues/40) provedores · Fase 1: [#33](https://github.com/KayzenRoot/zeus-agent/issues/33) auth, [#34](https://github.com/KayzenRoot/zeus-agent/issues/34) billing, [#35](https://github.com/KayzenRoot/zeus-agent/issues/35) entitlements · Fase 2: [#36](https://github.com/KayzenRoot/zeus-agent/issues/36) orquestrador, [#37](https://github.com/KayzenRoot/zeus-agent/issues/37) auto-healing · Fase 3: [#38](https://github.com/KayzenRoot/zeus-agent/issues/38) enterprise, [#39](https://github.com/KayzenRoot/zeus-agent/issues/39) instalador.

Todas com label `enhancement`; critérios de aceite no corpo de cada uma. O épico agrega a ordem de
execução e as decisões do owner.
