# ZEUS-001 | Relatório de prontidão e checklist integral do DoD

**Data:** 2026-10-31 · **HEAD:** `752d0a60e7` (base `main` `23145d788a39453fcb6d81a6a53415a822b4655f`)
**Veredito vigente:** CORRECTION REQUIRED (global) · **NO-GO merge/Ready/release/VPS** até revisão independente do owner e gates nativos.
CD08 (DOMPurify) APPROVED individual. Este relatório consolida evidências; **não é aprovação**.

## Checklist integral do DoD (definition-of-done.md)

| # | Item do DoD | Estado | Evidência |
|---|---|---|---|
| 1 | Proveniência da fonte + MIT LICENSE retidos; nenhum arquivo upstream ausente | ✅ VERIFICADO | Job "Canonical source and MIT provenance" PASS por HEAD; import com ancestralidade completa (`53df274b` ancestral do HEAD); `grep 'Nous Research' LICENSE` no job |
| 2 | Código/assets refletem o escopo Zeus sem quebrar identificadores de runtime | ✅ VERIFICADO | Suíte `.zeus/tests` (brand/rebrand/guards) PASS em CI e local; pins de compatibilidade mantidos (`HERMES_*`, pacotes, `hermes` alias) |
| 3 | Testes direcionados, lint/typecheck/build e checks de plataforma PASS ou indisponibilidade documentada | ✅ VERIFICADO (hospedado e local) | CI HEAD `4cce82c708`: **18 checks PASS**. Local Windows ocioso: npm ci, web build, typecheck ×3, release policy, **web check+tests 429/429 PASS**, **desktop UI 10.783/10.783 — paridade total com o runner** após 4 correções de causa raiz (locale, timeout, budgets de corrida/regrow) documentadas em #2 |
| 4 | Nenhuma chave ou segredo exposto | ✅ VERIFICADO | Trivy secrets: 0; secret scanning + push protection enabled; nenhum credential no diff (sanitizador de CI em vigor) |
| 5 | PR com base/head SHA, paths alterados, outputs de teste, riscos e resultado de revisão | ✅ documentado / ⏳ revisão pendente | Body da PR consolidado; CD05–CD10 por SHA; riscos por delta; **resultado de revisão: PENDENTE (owner)** |
| 6 | Funcionalidade local validada onde possível | ✅ VERIFICADO (sem BYOK) | `hermes update` recusa em runtime real; `hermes --version` executa; `uv sync` + imports; web build servido; **app empacotado: 2 sessões nativas com backend real (health 200), quit limpo e estado preservado**; chat/gateway/PTY com modelo real = pendente (exige BYOK) |
| 7 | Checkpoint canônico registra somente fatos VERIFICADOS | ✅ íntegro | `.zeus/docs/checkpoint.md` na `main` **não foi promovido** — Checkpoint Delta proposto no CD10 aguarda auditoria; nenhum fato especulativo adicionado |

## Superfícies de segurança (issue #8 / M02)

| Classe CodeQL (756 herdados) | Veredito |
|---|---|
| clear-text-logging (94) | FP de taint — 0 vazamentos reais em amostragem + varredura determinística; ~5 sítios de exceção revisados |
| weak-hash (4) | FP/aceitável (digests de alta entropia p/ cache) |
| bypass-checks (2), log-injection (13) | dev tooling por design |
| TOCTOU (13), temp-file (6), URL-substring (5) | padrões reais de risco baixo; 1 hardening real **corrigido** (notarize .p8 → mkdtemp); demais upstream-first em WO futura |
| Novos alerts em código próprio da PR (`.zeus/`, `.github/`) | **0** |

## Trivy — resíduo zero

99 → 0 HIGH/CRIT via: floors de dependências (6 superfícies), dependency graph habilitado, override documentado do Pillow (browser-harness pin), triagens `.trivyignore` justificadas (DS-0002 s6-root ×2; CVE-2026-53869 FP por merge-base). Scanner local 0.76.1 e CI concordam.

## Matriz nativa (runbook windows-validation.md)

| Stage | Estado |
|---|---|
| 1. Static/UI checks (Windows local) | ✅ executado 2026-10-31 (npm ci, policy test, web check/build, desktop typecheck; desktop UI: ver abaixo) |
| 2. Desktop empacotado | ✅ **EXECUTADO 2026-11-01** pós-auditoria do harness: `Zeus Agent.exe` (sha256 `0050a761…`) ×2 sessões com backend real do checkout (health 200), quit limpo (exit 0), **113/113 entradas do home preservadas no quit+relaunch**, zero bootstrap/instalador nos logs, perfil real intocado (evidência em #2) |
| 3. Backend+dashboard WSL2 com modelo | ⏸️ exige BYOK real (nunca recebida em Git); handoff Codex preparado |
| 4. Segurança/identidade | ✅ parcial: recusa de updater em runtime VERIFICADA; auth 401 real nos endpoints do dashboard; `zeus://`/MSIX/DMG pendentes |

Desktop UI na máquina real: 6 execuções completas (**12→4→10→1→1→0 falhas** vs runner sempre 10.783/10.783) — **paridade total** alcançada com 4 correções de causa raiz test-side (locale `Intl.RelativeTimeFormat`, timeout do fuzz, budgets de corrida do CronView, orçamento de convergência do regrow), nenhuma mudança de produto. Web local ocioso: check completo + 429/429 PASS.

## O que separa do APPROVED

1. **Revisão independente do owner** (Evidence Bundle completo nos comentários CD09/CD10 da PR #1).
2. **Gates nativos**: Stage 2 (empacotado, pós-auditoria de isolamento), Stage 3 (BYOK/WSL2), MSIX publisher/DMG (#4, [#20]).
3. CodeQL herdados: correção/demissão por classe (esforço longo, plano em #8).

**Nenhuma pendência foi silenciada ou declarada concluída sem execução.** Checkpoint Delta proposto no CD10; promoção somente após auditoria.
