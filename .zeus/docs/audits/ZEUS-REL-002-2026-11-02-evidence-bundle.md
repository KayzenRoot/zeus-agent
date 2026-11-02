# ZEUS-REL-002 | Evidence Bundle — release candidate local

**Candidato:** `main` em `41c7aebc6b` · **Data:** 2026-11-02
**Escopo:** produção local pessoal (ADR-003), BYOK. **Veredito:** RC local pronto para decisão do owner
(#20); distribuição assinada **NO-GO** (#4). Nada foi publicado, deployado ou enviado a VPS.

## 1. Índice de artefatos canônicos

| Artefato | Caminho |
|---|---|
| Relatório de prontidão + DoD | [`ZEUS-REL-002-2026-11-02-release-candidate-report.md`](ZEUS-REL-002-2026-11-02-release-candidate-report.md) |
| Checkpoint canônico | [`../checkpoint.md`](../checkpoint.md) |
| Auditoria de dependências/floors | [`ZEUS-001-2026-10-31-dependency-security-floors.md`](ZEUS-001-2026-10-31-dependency-security-floors.md) |
| Electron 42 / npm | [`ZEUS-SEC-002-2026-11-02-electron42.md`](ZEUS-SEC-002-2026-11-02-electron42.md) |
| Mirrors de terceiros | [`ZEUS-001-2026-11-02-artifact-mirror-audit.md`](ZEUS-001-2026-11-02-artifact-mirror-audit.md) |
| Drill backup/restore | [`ZEUS-OPS-001-2026-11-02-backup-drill.md`](ZEUS-OPS-001-2026-11-02-backup-drill.md) |
| Comparação upstream | [`ZEUS-SYNC-001-2026-11-01-upstream-comparison.md`](ZEUS-SYNC-001-2026-11-01-upstream-comparison.md) |
| WO do sync | [`../work-orders/ZEUS-SYNC-001-upstream-v0.22.5.md`](../work-orders/ZEUS-SYNC-001-upstream-v0.22.5.md) |
| Design do instalador | [`../work-orders/ZEUS-001-installer-local-design.md`](../work-orders/ZEUS-001-installer-local-design.md) |

## 2. Evidência por domínio

### Fonte e proveniência
- Import `53df274b08` ancestral do HEAD; `LICENSE` MIT/Nous preservada; job **Canonical source and MIT provenance** verde no audit gate.
- Comparação upstream revalidada: tag anotada `v0.22.5` → commit `bf0203a794`.

### Identidade Zeus
- SOUL.md, `DEFAULT_AGENT_IDENTITY`, guidance ×2, setup intro, skin `zeus`, TUI banner, tema Liquid Glass, dots de atividade.
- Resposta real do agente comprovando a persona (sessão local).

### Segurança
| Superfície | Evidência |
|---|---|
| Trivy (Python/config/secrets) | **0 HIGH/CRIT** no audit gate |
| npm (todos os workspaces) | **0 critical / 0 high**; produção 0/0 |
| Dependabot (API, todos os manifestos) | **0 critical / 0 high**; 41 medium + 15 low |
| Sidecar photon | audit 0 |
| WS Host/Origin/rebinding | 37/37 testes |
| SSRF media proxy | redirects revalidados por hop; testes dedicados |
| Segredos | Trivy secrets 0; nenhum no Git; backup tratado como segredo |
| CodeQL | 908 alertas herdados abertos (triagem por classe em #8); top classes: path-injection 311, log-injection 229, overly-permissive-file 78, URL-substring 56 |

### Confiabilidade
- ESTOP cobre gateway + `kanban dispatch` + daemon; provado ao vivo (pause → refused → resume).
- Budget `--max-turns` provado ao vivo; 74 testes de controles (rate limit, iteration budget, empty guard).
- Kanban E2E com 3 perfis; reclaim/retry sem perda (run 3 → run 4, arquivo byte-exact).
- Drill backup/restore 15/15; bug de caminho `dbs/` corrigido.

### Instalação e operação
- Fluxo B Windows: instalação completa, launcher 1,95 s, uninstall seguro.
- WSL2: full install 2,2 GB, launcher 1,35 s, uninstall limpo; 17/17 contratos em ambos.
- Mirrors content-addressed por SHA-256; download real conferido byte a byte.
- RPO/RTO/retenção e runbook em `ZEUS-OPS-001`.

### Desktop (Electron 42.11.18)
- `pack --dir` e pacote **bundled**; lifecycle **PASS**: session-1 backend porta 59437, relaunch session-2 porta 54299, estado **113→116, lost 0**.
- node-pty abre PTY sob Electron 42 (`pty-ok`, exit 0).
- UI 1.225/1.225 arquivos; typecheck 0; lint 0 erros.

### Web e produção viva
- Web: typecheck + **429/429** + lint 0 erros + build.
- Dashboard `127.0.0.1:9119` health **200**; 7 sessões/47 mensagens preservadas; chat real DeepSeek v4.1 Flash via OpenCode Go.

## 3. Gates e CI

- `python scripts/check`: **12/12** (última execução local).
- Audit gate GitHub Actions: **success** em `2256fe3326`, `61892076d1`… série de commits; Trivy deps 0.
- Suítes direcionadas: PM 22, controles 74, áreas tocadas 85, backup 3 + drill, instalador 17×2, WS 37.
- A suíte completa (`scripts/run_tests.sh`, **45.435 testes**) não foi concluída nesta sessão por tempo (multi-hora); as matrizes por área acima cobrem as superfícies alteradas. Registro honesto.

## 4. Matriz de issues

| Issue | Estado | Evidência |
|---|---|---|
| #1 (ZEUS-001) | MERGED/APPROVED delegado | PR #1, checkpoint |
| #2 #3 #5 #6 #9 #10 #11 #12 #15 #19 #27 #28 | FECHADAS | comentários por issue + audits |
| #4 | aberta — owner (assinatura/MSIX/DMG) | RC §5 |
| #7 | aberta — WO de sync (spike 100 conflitos) | WO §8 |
| #13/#14 | abertas — credenciais/owner | — |
| #16/#17 | futuro/meta | — |
| #20 | aberta — **decisão de go** | RC + este bundle |

## 5. Reprodução

```bash
git -C <checkout> rev-parse HEAD      # 41c7aebc6b ou posterior
python scripts/check                  # 12/12
bash scripts/run_tests.sh tests/...   # matrizes por área
npm run --workspace web check && npm run --workspace web build
npm run --workspace hermes typecheck && npm run --workspace hermes build
npm run --workspace hermes test:desktop:lifecycle   # pacote bundled
curl -s http://127.0.0.1:9119/api/health
python scripts/zeus_backup.py --home <home> --out <dir>
```

**Limites:** sem release assinada, sem deploy, sem VPS, sem contas externas. Este bundle é evidência
para a decisão do owner, não uma aprovação independente.
