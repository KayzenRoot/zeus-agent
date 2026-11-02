# ZEUS-REL-002 | Relatório de Release Candidate — produção local

**Data:** 2026-11-02 · **HEAD de evidência:** `be48c72ff0` (audit gate verde até `2256fe3326`; audit de `be48c72ff0` em execução)
**Escopo:** uso pessoal local (ADR-003), BYOK, sem assinatura de publisher.
**Veredito do executor:** **RC local PRONTO para a decisão do owner (#20)**; **distribuição assinada NO-GO (#4)**.
Este relatório consolida evidências; **não é aprovação independente** e não autoriza release/deploy/VPS.

## 1. Checklist do DoD (`definition-of-done.md`)

| # | Item | Estado | Evidência |
|---|---|---|---|
| 1 | Proveniência + MIT LICENSE; sem arquivos upstream ausentes | ✅ | Job "Canonical source and MIT provenance" PASS; `53df274b` ancestral; LICENSE Nous preservada |
| 2 | Código/assets no escopo Zeus sem quebrar identificadores de runtime | ✅ | Identidade em SOUL/prompt/skin/TUI/web; `HERMES_*`, pacotes, `hermes` alias e protocolos preservados; suíte de marca verde |
| 3 | Testes, lint/typecheck/build e checks de plataforma PASS ou indisponibilidade documentada | ✅ (com 2 exceções Windows documentadas) | Ver matriz §3; `.zeus/tests` 63 PASS + 2 falhas **Windows-local-only** que passam no WSL2 (4+2 OK) |
| 4 | Nenhuma chave/segredo exposto | ✅ | Trivy secrets 0; npm/Dependabot 0 critical/high; nenhum segredo em diff; backups tratados como segredo |
| 5 | PR/relatório com base/head, paths, testes, riscos e revisão | ✅ documento / ⏳ decisão do owner | Este relatório + checkpoint + issues; revisão independente delegada/registrada |
| 6 | Funcionalidade local validada onde possível | ✅ com modelo real | Chat real DeepSeek v4.1 Flash (OpenCode Go), PTY, memória, Kanban 3 perfis, ESTOP, backup/restore, installer Windows+WSL2 |
| 7 | Checkpoint canônico registra fatos VERIFICADOS | ✅ | `.zeus/docs/checkpoint.md` atualizado por SHA; nada especulativo promovido |

## 2. Segurança

| Superfície | Estado |
|---|---|
| Trivy (Python + config + secrets) | **0 HIGH/CRIT** no audit gate |
| npm audit (todos os workspaces) | **0 critical / 0 high** (45 total: 37 moderate, 8 low) |
| npm produção | **0 critical / 0 high** (18 total) |
| Dependabot (todos os manifestos) | **0 critical / 0 high** (56 abertos: 41 medium, 15 low) — era 144 (1c/45h) |
| Locks separados | sidecar **0 findings**; website 0 high |
| CodeQL | 908 alertas herdados abertos, por classe, triagem documentada (#8); correções próprias verdes |
| SSRF/dashboard | media proxy revalida allowlist em redirects; WS Host/Origin coberto em `/api/pty`, `/api/ws`, `/api/pub`, `/api/events` (37/37 testes) |
| Segredos | só no `.env` do home; `.gitignore` cobre; backups contêm `.env` por design |

## 3. Matriz de testes executada

| Suíte | Resultado |
|---|---|
| Audit gate (source/CodeQL/Trivy/Sonar) | **success** em `2256fe3326`; commits anteriores idem |
| `scripts/check` | **12/12** |
| `.zeus/tests` (Windows) | 63 PASS, 2 falhas de guarda POSIX-only (passam no WSL2: 4+2 OK), 1 skip |
| PM override-aware | 22/22 |
| Controles REL-001 (ESTOP, budget, rate limit, empty guard) | 74 PASS |
| Áreas tocadas (kanban, fingerprint, host cap, CLI) | 85 PASS |
| Instalador Zeus-owned | **17/17 Windows + 17/17 WSL2** |
| Backup/restore | 3/3 testes + drill sintético 15/15 checks |
| WS Host/Origin/auth | 37/37 |
| Web | typecheck + **429/429** + lint 0 erros + build |
| Desktop | typecheck 0; lint **0 erros**; UI **1.225/1.225 arquivos**; build; `pack --dir`; smoke do app; **PTY node-pty sob Electron 42**; pacote **bundled** gera `Zeus Agent Bundled.exe` + payload |
| Desktop lifecycle (bundled) | 🟡 app abre, carrega janela e sai limpo; **backend não sobe** porque o boot resolveu o launcher do home real em vez do payload selado (#28) — achado de boot-resolution, não de Electron |
| Desktop platform suite | 342/375 arquivos; 20 falhas local-only de ambiente (HERMES_PYTHON, fixtures de packaging, git temp, ozone/ssh/tray Windows) — CI Linux cobre |

## 4. Funcionalidade viva (produção local)

- Dashboard `http://127.0.0.1:9119`, health **200**, sessão autenticada por token por boot.
- **7 sessões / 47 mensagens** preservadas na geração PM atualizada.
- Chat real com **DeepSeek v4.1 Flash** via OpenCode Go (BYOK do owner); identidade Zeus provada.
- Tema **Zeus Liquid Glass**, skin `zeus`, banner TUI ZEUS AGENT, dots de atividade.
- **Kanban E2E** Orquestrador → Analista → Auditor com reclaim/retry; ESTOP cobre gateway, CLI e daemon.
- Backup/restore com o bug de caminho corrigido; update controlado com rollback; installer B com recibo.

## 5. Riscos residuais (não bloqueiam uso local)

1. **CodeQL herdado**: 908 alertas abertos; plano/dismissals por classe em #8. Não há evidência de exploração nas classes revisadas.
2. **Moderates npm**: 37 (10 em produção), cadeias de build/dev sem fix não-quebrante.
3. **Release C**: assinatura/publisher, MSIX/DMG, deep links e avisos de licença (GPL/Bitwarden/FFmpeg/BSD) — **NO-GO** (#4).
4. **Sync upstream**: 6.044 commits atrás de `v0.22.5`; backports críticos aplicados, sync completo exige WO (#7).
5. **#137170**: loop de chamadas mutantes idênticas com resultado variável não é interrompido; mitigações `max_turns`/`run_budget`/ESTOP.
6. **Platform suite local**: 20 falhas de ambiente no host Windows (não regressões; CI Linux cobre).
7. 429 real do provedor não induzido; evidência por testes de contrato.
8. **Desktop bundled (#28)**: em sandbox isolado o boot prefere o launcher do home real (Python base sem
   `ruamel`) ao payload selado, então o lifecycle serve-ready não completa. O app **abre e sai limpo**
   sob Electron 42 e o pacote contém payload válido; a correção de resolução é pré-requisito da release
   desktop (#4), não da produção via navegador.

## 6. Decisões do owner

| Issue | Decisão |
|---|---|
| **#20** | Aceitar este RC como produção local (go formal) |
| **#4** | Certificado/publisher, MSIX/DMG, deep links (release C) |
| **#13/#14** | Credenciais e aprovação para integrações |
| **#7** | Autorizar WO de sync completo para `v0.22.5^{}` |

## 7. Reprodução

```bash
git -C <checkout> rev-parse HEAD           # be48c72ff0 ou posterior
python scripts/check                       # 12/12
bash scripts/run_tests.sh                  # suíte completa
npm run --workspace web check && npm run --workspace web build
npm run --workspace hermes typecheck && npm run --workspace hermes build
python scripts/zeus_backup.py --home <home> --out <dir>
curl -s http://127.0.0.1:9119/api/health   # {"ok": true...}
```
