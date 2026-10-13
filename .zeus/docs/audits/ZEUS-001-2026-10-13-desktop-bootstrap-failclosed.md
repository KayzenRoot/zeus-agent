# ZEUS-001 | Desktop Bootstrap/Windows Recovery | Correction Delta R2

Data: 2026-10-13. **CORRECTION REQUIRED / DRAFT / NO-GO merge, release, VPS.**

## 1. Autoridade e Context Lock

- Repositório: `KayzenRoot/zeus-agent`; PR #1, branch `work/ZEUS-001-import-brand`.
- Base `main`: `23145d788a39453fcb6d81a6a53415a822b4655f`.
- Snapshot de implementação desta correção (antes deste relatório): `bd2aa27a41a8f79651aef8608e89c73b0c0cc601`.
- Fontes canônicas consultadas: checkpoint, Decisions Ledger (ADR-001 a 004), Scope, Architecture, Definition of Done, Work Order `ZEUS-001`, Security, Windows validation e [auditoria dos instaladores](ZEUS-001-2026-10-13-installer-failclosed.md).
- ADR-003 mantém desenvolvimento e teste em Windows/WSL2 local antes da VPS; ADR-004 mantém atribuição upstream e identificadores internos de compatibilidade.
- Classificação: **NECESSARY**, segurança de caminhos já existentes dentro do mesmo WO. Nenhuma liberação de distribuição ou reescrita ampla de identificadores.

## 2. Achados de inspeção (não presumir cobertura anterior)

**A. Instalação remota a partir do desktop.** O runner `apps/desktop/electron/bootstrap-runner.ts` tinha `downloadInstallScript` que montava a URL `raw.githubusercontent.com/NousResearch/hermes-agent/<ref>/scripts/install.ps1|install.sh` e gravava scripts em `bootstrap-cache`. O `runBootstrap` resolvia o instalador antes de executar seu manifesto e etapas. Proteger apenas `scripts/install.cmd/.ps1/.sh` no checkout Zeus não interrompia esse fluxo remoto.

**B. Handoff Windows antes do runner.** `apps/desktop/electron/main.ts` tinha `handOffWindowsBootstrapRecovery()` chamado no caso `bootstrap-needed` *antes* de `runBootstrap()`. A função podia descobrir executável do updater, consultar marcador e iniciar subprocesso de handoff. O guard do runner sozinho não o cobria.

**C. IPC repair/continue.** `hermes:bootstrap:repair` podia alterar `bootstrapRepairAttempt`, derrubar conexão e forçar próxima instalação. `hermes:bootstrap:continue-local` podia sinalizar continuação de instalação. A política Zeus precisa recusar antes desses efeitos, sem depender do estado de um pacote previamente instalado.

**D. Native smoke `fresh`.** `apps/desktop/scripts/test-desktop.mjs` usa `npm run pack` e lança Electron em processo separado. `HERMES_HOME` e Electron userData temporários não provam isolamento total do OS, descoberta do runtime ou ausência de bootstrap. Não é um instalador assinado ou teste de segurança nativo por si só.

## 3. Correction Delta aplicada à branch

| Commit | Mudança |
| --- | --- |
| `8d0222d`, `1dff8b7` | `runBootstrap` recusa antes de resolver instalador ou abrir log; `downloadInstallScript` default deixa de executar rede/gravação e rejeita `zeus-release-unapproved`. |
| `b16db56` | `bootstrap-runner.test.ts`: falha cedo com event `failed`, sem log, marcador de execução ou cache; preserva testes de resolução puramente injetada. |
| `60216d0` | Primeira recusa no `handOffWindowsBootstrapRecovery`, antes da resolução de updater/marker/spawn. |
| `748de1c` | Regressões estáticas Python de ordem de guard e bloqueio do downloader. |
| `0858ce8` | Validação desktop do CI executa `electron/bootstrap-runner.test.ts`. |
| `071afc6` | Runbook Windows proíbe `test:desktop:fresh` sem preflight e backend isolados. |
| `5562562`, `469f8d0`, `61bd115` | Política `zeus-bootstrap-policy.ts` independente da atualização. Runner e main usam a mesma autoridade fonte; repair/continue-local recusam antes de alterar estado. O handoff requer bootstrap e updater autorizados (nenhum dos dois está). |
| `bd2aa27` | Testes estáticos incluem os IPCs e política única. |

A política tem `ZEUS_DESKTOP_BOOTSTRAP_APPROVED = false` **fixo no código**, sem variável de ambiente para ativá-la. `ZEUS_NATIVE_UPDATES_APPROVED = false` permanece uma autorização distinta. Um futuro instalador Zeus deve ser projetado, revisado, assinado e testado em WO autorizado, nunca ativado trocando uma flag de forma isolada.

## 4. Evidência e limites

- No snapshot `43b35d3` da correção anterior, [CI Python/Ubuntu 38434725178](https://github.com/KayzenRoot/zeus-agent/actions/runs/38434725178) e [Windows installer 38434725148](https://github.com/KayzenRoot/zeus-agent/actions/runs/38434725148) passaram. **Esses runs antecedem o código Electron e não comprovam a correção R2.**
- Para R2, os testes foram adicionados à suíte Python `.zeus/tests` e ao [CI dashboard/desktop](https://github.com/KayzenRoot/zeus-agent/actions/workflows/zeus-dashboard-validation.yml), mas uma aprovação do HEAD `bd2aa27` ou deste documento **não foi presumida**. A verificação exige SHA exato e conclusão dos jobs.
- [Windows Node 26.4 full diagnostics 38434942670](https://github.com/KayzenRoot/zeus-agent/actions/runs/38434942670) foi iniciado no commit anterior `ac9c9ac`; no momento desta coleta, `SessionsPage` isolado e web completa passaram, desktop UI completa ainda executava. Não extrapolar para R2.
- Não foi efetuado `test:desktop:fresh`, inicialização nativa, download de código de instalação, MSIX, sideload, atualização do SO, assinatura, DMG, gateway/modelo/PTY, autenticação de sessão ou VPS. Resultados estáticos/unitários não atestam ausência de operações por pacotes OS-managed preexistentes.
- A alteração de `main.ts` conserva os canais `hermes:` por compatibilidade e não altera a UI de chat/Ink. A observabilidade de recusas via UI e o comportamento de backend existente ainda requerem testes nativos.

## 5. Revisão preliminar e próximo gate

- **Segurança:** correção candidata fail-closed dos caminhos inspecionados. Validação dos testes R2, investigação de outros scripts de first-run e revisão independente ainda necessárias.
- **Funcionalidade:** em uma instalação Zeus nova, bootstrap e reparo instalador estão intencionalmente indisponíveis. Para desenvolvimento, usar checkout local auditado, sem instalador herdado. Isso ainda **não** significa que ambiente nativo esteja funcional.
- **Risco residual:** alto para cadeia de instalação/update e autenticação nativa. [Issue #3](https://github.com/KayzenRoot/zeus-agent/issues/3), [#4](https://github.com/KayzenRoot/zeus-agent/issues/4) e [#5](https://github.com/KayzenRoot/zeus-agent/issues/5) permanecem abertas.
- **Próximo gate necessário:** CI atualizado PASS no mesmo SHA; validar que Electron bootstrap/repair recusam sem rede/markers via testes; resultado full Windows Node 26.4; depois inspeção supervisionada em Windows/WSL2 isolado, publisher real, pacote assinado, OS protocols e rollback.

**CHECKPOINT DELTA proposto, não promovido:** registrar os guards como `IMPLEMENTED / CI PENDING` até finalizar checks do HEAD. **VEREDITO: CORRECTION REQUIRED. STOP sem merge/release/VPS.**
