# ZEUS-001 Checkpoint | 2026-10-12

## Authority and boundaries
- Repository: `KayzenRoot/zeus-agent` (owner-approved public). Source Pack: `.zeus/docs`. Work Order: `ZEUS-001`.
- PR: https://github.com/KayzenRoot/zeus-agent/pull/1, **draft / CORRECTION REQUIRED**, base `main` at `23145d788a39453fcb6d81a6a53415a822b4655f`.
- Branch: `work/ZEUS-001-import-brand`. No authorized merge, force-push, external publication or VPS deployment.
- Import pinned from `NousResearch/hermes-agent` commit `53df274b08f2bbbe82bb67bb50c7571952e95809`. Upstream commit ancestry preserved by the import process; upstream MIT license and copyright retained.

## VERIFIED implementation
- Upstream import GitHub Action success: https://github.com/KayzenRoot/zeus-agent/actions/runs/38312076398
- Zeus SVG marks/banner, favicon, desktop icon PNG/ICO/ICNS, Icon Composer and MSIX tiles, i18n display text, dashboard title/sidebar/footer, own README.
- CLI `zeus` alias; `hermes` internal package and protocol names intentionally preserved for compatibility.
- Desktop product IDs/executable/MSIX declaration under `com.kayzenroot.*` / `KayzenRoot.*`; these are NOT proof of installable, valid signed packages.
- Brand assets regeneration succeeded: https://github.com/KayzenRoot/zeus-agent/actions/runs/38314034954
- Desktop display test expectation correction in commit `583465c625da7aac19123a379a72d0305141b5f2`.
- **All dashboard and desktop static/UI CI jobs passed at `583465c`**: https://github.com/KayzenRoot/zeus-agent/actions/runs/38317333954
- **Zeus brand unit tests passed at `583465c`**: https://github.com/KayzenRoot/zeus-agent/actions/runs/38317334118
- Source updater guard added in commit `ebc23a5a532f4e04cdcfaed1b11bbe4cb4c6000e`: blocks `zeus update` and `hermes update` for the marked Zeus source checkout until an independently audited Zeus update channel exists. Brand unit tests passed at this commit: https://github.com/KayzenRoot/zeus-agent/actions/runs/38337939300
- **CI on `ebc23a5` was still in progress at the time of this checkpoint**; recheck https://github.com/KayzenRoot/zeus-agent/actions/runs/38337939298 before claiming green.

## BLOCKERS / CORRECTION REQUIRED
1. Windows/WSL2 local runtime not validated (backend start, model, gateway, chat, PTY, auth and UI walkthrough); keep all tests local-first; VPS strictly out of scope.
2. Windows MSIX signature and actual Publisher certificate NOT validated. `CN=KayzenRoot` is only a provisional manifest value, not proof of any signing key. Do not publish installers.
3. Desktop OS URI registration is now `zeus://` (plus `zeus-dev://` in development) in commit `42091e483aecb375c2374f5fb343f0178728c0ff`; Electron `hermes:` IPC remains intact and forwarded legacy Hermes deep links may still be parsed. **Typecheck, desktop UI tests and a real Windows deep-link activation are pending for this change.** Internal `hermes:` IPC messages must not be blindly renamed.
4. Installer DMG packaging still references Nous-era background/icons (`packaging/nous-dmg-2b.tiff`, `packaging/dmg-volume.icns`). Replace only after asset inspection and native build tests.
5. No vetted Zeus-owned release distribution/update manifest, signature verification, forward/rollback pipeline or source publisher. Source updates are temporarily blocked by the guard; further packaged updater paths require audit.
6. Python regression suite, Electron platform-specific integration tests, macOS dmg/MSIX native packaging, image visual verification and authenticated dashboard security smoke still outstanding.
7. Full downstream replacement of every historical Hermes mention is NOT the goal. Preserve MIT legal notices, code identifiers and compatibility paths. Review public-visible brand leftovers scoped to shipped surfaces.

## Resume workflow
- Read this checkpoint, decisions, scope, DoD and `work-orders/ZEUS-001.md`.
- Revalidate GitHub PR HEAD and CI; fix failing gates on this same branch.
- Audit deep links/installer resources/update policy with isolated tests; produce a local Windows/WSL2 runbook and evidence.
- Only promote ZEUS-001 to APPROVED after all DoD evidence; otherwise keep the PR draft and record the exact blocked criteria.

**STOP CONDITION: do not merge or distribute until all critical acceptance gates have factual evidence.**


## 2026-10-13 | ZEUS-001 Correction Delta (NOT APPROVED)

**Base:** `23145d788a39453fcb6d81a6a53415a822b4655f`.
**Implementation snapshot before this checkpoint:** `59c0650bb070bed5357123f3c7738cb799546b5c`.
PR remains **DRAFT / CORRECTION REQUIRED**. No merge, deploy, Windows
installation, publisher approval or VPS changes.

### Newly verified

- Earlier implementation HEAD `f3272786e9b82a7fa810e3dd8e5a0b21e5c63569`
  passed [Zeus brand tests](https://github.com/KayzenRoot/zeus-agent/actions/runs/38338428085)
  and [dashboard + desktop static/UI checks](https://github.com/KayzenRoot/zeus-agent/actions/runs/38338427952).
- Subsequent correction commits on the same PR added a fail-closed
  desktop update admission policy, refusing native update check/apply and
  channel selection before feed/network/handoff I/O
  (`apps/desktop/electron/zeus-update-policy.ts`,
  `apps/desktop/electron/main.ts`). Product packaging explicitly omits
  native updater feeds in all variants
  (`apps/desktop/electron-builder.config.cjs`).
- Added real-config Node regression cases for stable/light/bundled/store
  and release-like environment. The **specific packaging-policy step**
  succeeded in the intermediate
  [desktop CI run 38395118328](https://github.com/KayzenRoot/zeus-agent/actions/runs/38395118328).
  This is NOT a claim that the whole run succeeded.
- Updated desktop source repository metadata while retaining original
  Nous Research author and MIT attribution. Replaced DMG title and
  Linux summary strings, not uninspected DMG binary graphics.
- Updated `apps/desktop/scripts/test-desktop.mjs` to derive app/executable
  and DMG names from Zeus product identity. Added
  [Windows/WSL2 validation matrix](windows-validation.md).
  The harness has **not** been exercised on a real Windows machine.

### Explicitly unverified at this checkpoint

- Full latest HEAD dashboard/desktop CI, UI suite, typecheck and lint:
  running/pending; read the current PR head and its checks before
  declaring green. Re-runs cancelled by subsequent commits are not
  evidence of passing.
- Independent review of all native updater/OS-managed update routes,
  actual Windows MSIX Publisher certificate/signing, installation,
  `zeus://` OS handler, macOS notarized DMG, local gateway/model/PTY,
  authenticated UI and Python backend regressions.
- No native distribution channel, auto-update, release artifact or
  merge is authorized or validated. Package-level protection does not
  claim to cancel update registrations of any previously installed
  OS-managed packages.

**Next necessary gate:** finish the HEAD CI, correct failures on
the same ZEUS-001 PR, run isolated native Windows/WSL2 validation
and complete release signature/visual security evidence. Preserve
the **CORRECTION REQUIRED** verdict until independent audit confirms DoD.


## CI WINDOWS FOLLOW-UP 2026-10-13 | Verified HEAD `1766684270e4c96dfa47fd7190cedf45186c80bb`

**Current decisive evidence for implementation SHA `1766684270e4c96dfa47fd7190cedf45186c80bb` (supersedes earlier "CI pending" status above):** [run 38414479477](https://github.com/KayzenRoot/zeus-agent/actions/runs/38414479477) = **dashboard-checks SUCCESS, desktop-static-checks SUCCESS**, including desktop lint, UI tests, native update-policy tests, release-config tests and static OS protocol checks. [Zeus brand tests 38414481832](https://github.com/KayzenRoot/zeus-agent/actions/runs/38414481832) = **SUCCESS**. Fix commits: `fc6a3c870ce518751c9062356c4e77edb28021c0`, `1766684270e4c96dfa47fd7190cedf45186c80bb`; no rule disabled. Base main remains `23145d788a39453fcb6d81a6a53415a822b4655f`. PR #1 still DRAFT.

**Local Windows evidence (reported, not independently reproduced here):** Node 26.4, desktop lint exit 0 with 269 warnings, policy 5/5, update policy 2/2, web build/branding passed; `web check` timeout in SessionsPage tests, `test:ui` returned inconsistent failing sets (15 failures/6 files then 4 failures in other files). No complete local UI PASS is accepted. Linux CI and local Windows are not interchangeable. Review [audit & reproduction matrix](audits/ZEUS-001-2026-10-13-ci-windows-update-dmg.md).

**Remaining stop gates:** native Windows/WSL2 smoke with model, gateway, PTY and auth; deterministic diagnosis of test instability; MSIX real Publisher/signature/install/uninstall/rollback; updater route audit beyond UI gate, including OS-owned registrations; `zeus://` OS activation; inherited DMG TIFF/ICNS visual/legal inspection and Mac build. No independent proof of these exists. **Verdict: CORRECTION REQUIRED, NO-GO merge/release; do not deploy to VPS.** This checkpoint commit itself is a newer HEAD and must receive its own CI before claiming that newer HEAD green.


## NODE26 VOICE PREFS REPRO 2026-10-13 | Regression delta

**Last independently PASS implementation before this correction:** `f51c5582b0efd9f26eb82275e9c9538166494027` on [brand CI 38429315103](https://github.com/KayzenRoot/zeus-agent/actions/runs/38429315103) and [dashboard + desktop Linux CI 38429315149](https://github.com/KayzenRoot/zeus-agent/actions/runs/38429315149). PR #1 still DRAFT / CORRECTION REQUIRED; main unchanged at `23145d788a39453fcb6d81a6a53415a822b4655f`.

**Real failure reproduced on Windows/Node 26.4.0**: [Windows CI 38425723776](https://github.com/KayzenRoot/zeus-agent/actions/runs/38425723776) on earlier `229289d` ended **FAIL**, despite isolated SessionsPage and full web suites passing. Desktop UI: **10,781 passed / 2 failed out of 10,783**. Both failures are in `src/store/voice-prefs.test.ts` at lines 44 and 72: expected `localStorage.getItem('hermes.desktop.autoSpeakReplies')` to be `null` after mocked quota/security failure, but got `'false'`. CI log also emitted Node 26 native localStorage unavailability warnings. This confirms a test-environment spy mismatch (the Node 26 jsdom fallback has its own `setItem`, not inherited `Storage.prototype.setItem`), not an established runtime product data loss bug.

**Corrective candidate:** make the failing tests spy on `Storage.prototype` for real jsdom storage or on the actual fallback `localStorage` for the alternative object. Keep the quota/security exceptions and assertions intact, with NO blanket skip and NO relaxed timeouts. Added a targeted Windows matrix workflow for Node 24 and Node 26.4.0; **PENDING** at this documentation snapshot, must read the new commit's CI results before considering fixed. The full Windows Node 26.4 UI suite, local repro, native Windows/WSL2, signed MSIX and macOS DMG remain separate gates. No merge/release/VPS.


## 2026-11-01 | ZEUS-001 PROMOTED TO APPROVED (review under recorded owner delegation)

- Reviewed HEAD: `cb01c9981406eda82668d76327dc227123f5cd3c`; base `main` `23145d788a39453fcb6d81a6a53415a822b4655f`.
- Verdict: **APPROVED** — review executed by the executor under **explicit owner delegation recorded in the PR conversation** ("faça a revisão vc mesmo"); formal reviewer independence was NOT preserved and the owner retains the right to revert or reopen.
- Fresh verification at review time: import SHA `53df274b` ancestor of HEAD; ~51,700 upstream commits + 113 Zeus-authored commits; MIT LICENSE arrives with the import (main was docs-only) and is unchanged; only canonical files touched are checkpoint/WO (chronological honest logs); CI at HEAD 18 PASS incl. Trivy 0 HIGH/CRIT and the audit gate; local `.zeus` suite 47/49 with 2 pre-existing Windows-local-only guard errors (identical on base; gated green by Linux CI).
- Native evidence: packaged-app lifecycle smoke ×2 sessions (health 200, exit 0, 113/113 home entries preserved, exe sha256 `0050a761…`); WSL2 backend/CLI/dashboard with real auth 401; `hermes update` refusal at runtime on Windows and WSL2; runner↔machine JS parity 10.783/10.783 after 4 root-cause test fixes.
- Remaining tracks (NOT part of this WO's verdict): MSIX/publisher/DMG/deep links NO-GO (#4, #20); real-model chat/PTY requires owner BYOK; CodeQL 756 inherited alerts — per-class dismissal authorized by the owner, to be executed post-merge with per-alert justification; installer Zeus-owned design proposed, implementation requires its own WO (#5).
- Distribution remains NO-GO: APPROVED here is the import/brand work order, not a release authorization (#20 defines the separate release gate).


## 2026-11-01/02 | Produção local viva, confiabilidade, instalador e dependências

**HEAD de referência:** `ffee36711b` (main). Nada aqui autoriza release assinada, deploy ou VPS.

### Issues encerradas com evidência
- **#2, #3, #6, #10, #11, #15** — identidade, E2E multiagente, gates e documentação (commits anteriores na main).
- **#12 Control Room** — cartões de perfil com atividade real provada ao vivo (default 5 sessões, analyst 3, auditor 1; isolação confirmada pelos números distintos), Kanban, auth, estados vazios, tema Liquid Glass. `25b3f91716`.
- **#9 Confiabilidade** — ESTOP passou a cobrir **todos** os dispatchers: `hermes kanban dispatch` e o daemon standalone agora recusam dispatch pausado (`--json` com `paused: true`), com prova ao vivo (pause → refused → resume → operando) e 5 contratos novos. Budget demonstrado ao vivo (`--max-turns 1` → "Iteration budget exhausted (1/1)"). Rate-limit/circuit breakers cobertos por 74+65 testes. Relatos upstream triados; #146973 coberto no código, #146955 não reproduzido, #137170 residual documentado. Audit gate **success** (`0416f0b069`).

### Instalador Zeus-owned (fluxo B da #5)
- `scripts/zeus-install.{sh,ps1,cmd}` + `scripts/zeus_install_local.py`: só opera em checkout verificado (origin KayzenRoot, HEAD, árvore limpa), root isolado, `HERMES_HOME` próprio, recibo espelhável, uninstall preservando dados reais.
- Execução real Windows: instalação completa (1.8 GB), launcher operante, fast path por digests dos inputs (**1,95 s** vs 12,5 s do activate), uninstall sem tocar no perfil real (7 sessões/47 mensagens). 15 contratos; gate 12/12; **WSL2 15/15** (encontrou e corrigiu bug POSIX de uninstall). **Full install POSIX no WSL2** em clone ext4: exit 0, 2.2 GB, launcher 1,35 s, `kanban list` no home isolado, uninstall removeu o root; dois bugs corrigidos no caminho (`git status` em `/mnt/d` > 180 s com recusa clara; bit de execução do wrapper). Auditoria dos mirrors: content-addressed por SHA-256, fallback da origem oficial, verificação obrigatória; download real do mirror conferido byte a byte (`audits/ZEUS-001-2026-11-02-artifact-mirror-audit.md`). Commits `677b1d32c7`, `f35838f2fe`, `af08b3cd15`, `3cb8d12446`, `305ad9b7ec`, `eb1c049034`.
- Issue #5 permanece aberta: release assinada (#4) e licenças de redistribuição (GPL/Bitwarden/FFmpeg/BSD) + full-install POSIX.

### Dependências
- **Segurança de endpoints (CodeQL)**: 10 sites não-teste de `py/incomplete-url-substring-sanitization` endurecidos para **host/path matching** — Azure/MiniMax (Bearer auth + beta 1M), Gemini native/OpenAI-compat/Vertex express, StepFun region, Ollama finish_reason. 10 contratos anti-spoofing em `tests/agent/test_base_url_host_matching.py`; 155 testes PASS (`21c17640d1`). ReDoS: chave privada com corpo temperado e quoter FTS5 com grupos possessivos, testes temporizados (`950fb0a6c4`/`7436672b47`). A2A audit redige o resumo antes de gravar (`a9d9209db4`) e, junto com a saída de cron, é criado **0600 no POSIX** (`f93941c1f5`, 96 testes). **Campanha CodeQL: 908 → 736** — 147 alertas **somente de teste** (`used in tests`), 11 TLS como opt-in explícito (`ssl_verify:false` com warning), 2 ECB do iLink como protocolo obrigatório, 3 transcripts como FP (`_redact` não modelado), ~9 fechados pelo rescan. Relatório: `audits/ZEUS-SEC-002-2026-11-02-codeql-campaign.md`; restam 311 path-injection e 229 log-injection (por alerta).
- **#27 (nova)** — npm audit 59 (2 critical/8 high) → **45 (0 critical/0 high)**; produção 18 (0/0). Bumps diretos (concurrently, zod) + **Electron 40.10.6 → 42.11.18** (OpenURL/41.10.x + mitigação eMudhra 42.11.16), verificado com typecheck, lint 0 erros, suíte UI 1.225/1.225 arquivos, build, **empacotamento `--dir` real com Electron 42** e smoke do `Zeus Agent.exe` (iniciou e permaneceu vivo; assinatura ausente por design local). Overrides: axios 1.20.0, fast-uri 3.1.8, follow-redirects 1.16.2, joi 18.3.1, @xmldom 0.8.15, shell-quote 1.12.0, sanitize-html 2.18.1, ip-address 10.7.5, brace-expansion 5.0.12, yaml 2.9.1; exclusões datadas no `.npmrc`. **Dependabot (todos os manifestos): 144 (1c/45h) → 56 abertos, 0 critical/0 high** — locks separados corrigidos (sidecar zod 4.6.7, website fast-uri 3.1.8) e 5 alertas stale/falso-positivo demitidos com evidência (o DNS-rebinding do próprio app está coberto por guard nos 4 WS endpoints, 37/37 testes). Commits `df95e99a27`, `74703ecd2e`, `be48c72ff0`.
- **#7 prep** — comparação read-only com `v0.22.5` (tag → `bf0203a794`): 6.044 commits, 5.387 arquivos, 181 commits de segurança; superfície de conflito de identidade em 4 arquivos. Backports críticos aplicados: PyJWT 2.15.1, certifi 2026.10.19, aiohttp 3.14.5; `uv.lock` regenerado; floors atualizados. Relatório em `audits/ZEUS-SYNC-001-2026-11-01-upstream-comparison.md`; sync completo exige WO própria. Commit `ffee36711b`.
- **PM override-aware** — `uv pip check` passou a tolerar somente conflito coberto por `[tool.uv] override-dependencies` cuja versão instalada satisfaz o intervalo (o caso Pillow 13 × browser-harness); qualquer outro conflito continua fatal. Corrige o bootstrap de todo ambiente novo. 22 contratos; `pm/overrides.py`.
- **#19 (OPS, parte local)** — drill de backup/restore com dados sintéticos em home descartável (3 sessões/10 mensagens + DB de perfil + memórias/config/logs + caches voláteis): **15/15 checks ALL_OK**, backup 0,23 s, restore 0,24 s, integridade OK, hash das memórias idêntico, nenhum cache ressuscitado. O drill achou um **bug real de recuperação**: o restore deixava os DBs em `home/dbs/` em vez de `home/state.db`/`home/profiles/<p>/state.db`; corrigido e o teste (que validava o caminho errado) agora cobre DB raiz e de perfil. Metas de RPO/RTO/retenção e runbook de incidente em `audits/ZEUS-OPS-001-2026-11-02-backup-drill.md`. VPS/restore real seguem owner-gated.
- **Produção local** — dashboard reiniciado na geração PM atualizada (`certifi 2026.10.19`, `pyjwt 2.15.1`, `aiohttp 3.14.5`), health 200, 7 sessões/47 mensagens preservadas. `displayVersion` aparece "unknown" ao rodar da geração PM (metadado de release ausente no venv instalado) — cosmético, sem impacto funcional.

### Ainda aberto / owner-gated
- #4, #13, #14, #19, #20 (certificado/MSIX/DMG, credenciais, VPS, go de produção).
- **#28 (fechada como falso positivo)**: o pacote que falhou foi construído com `builder` **sem** `build` sob `HERMES_DESKTOP_VARIANT=bundled`; o stamp `payload=bundled` é gravado no build, então o boot caiu no launcher do home real. Rebuild correto (`build` + `builder` com a variante) fez o **lifecycle bundled PASSAR**: session-1 backend porta 59437, relaunch session-2 porta 54299, estado **113→116, lost 0**. Lição no bullet de desktop acima.
- #7 sync completo (WO), #137170 residual (core loop), licenças de redistribuição na release C, full-install POSIX do fluxo B.


## 2026-11-02 | Sync upstream v0.22.5 merged (PR #29, owner-approved)

- **`main` = `57b031a5c7`** (merge commit). Upstream `v0.22.5^{} = bf0203a794`; base `8930e5205f`. Autorização explícita do owner ("aprovo o merge"); branch de sync removida.
- **101 conflitos → 0**: 53 workflows deletados pelo Zeus (deleções mantidas), 24 i18n (upstream + marca em palavras isoladas), `electron/main.ts` (12 gates Zeus reaplicados via 3-way), PM adotou `pm/pip_check.py` upstream (lê overrides do `uv.lock`; `pm/overrides.py` removido com o teste), 4 locks regenerados, floors **filelock 4.2.4 / msgpack 1.2.4 / undici 7.30.1**, Pillow override exato aceito no teste.
- **CI do PR**: brand-unit, dashboard-checks, Trivy, dependency gate, provenance, Windows bootstrap/installer safety, CodeQL JS e Python **PASS**. Desktop UI **11.509/11.512** (1 teste upstream flaky: `dead-session-prune`, 0/20 falhas local). CodeQL comparison: **100 anotações herdadas do upstream**; SonarCloud new-code E — triagem pendente.
- **Pós-merge local**: `scripts/check` **12/12**; `.zeus/tests` com as 2 falhas Windows-only conhecidas (passam no WSL); ambiente PM reconstruído com **Pillow 13.0.0, PyJWT 2.15.1, certifi 2026.10.19**; dashboard na nova geração health **200**, 7 sessões/47 mensagens preservadas; `pip_check` upstream aceita o lock.
- **Residual**: matriz Python ampla/gateway/migrations SQLite, lifecycle bundled Electron **44.9.3**, instalador WSL2 pós-sync e triagem CodeQL/Sonar herdados.
- **CodeQL pós-merge**: 790 abertos em `main` (269 path-injection, 177 log-injection, 116 clear-text-logging, 28 file-system-race, 26 insecure-temp…). **789 herdados do upstream** v0.22.5; **1 em arquivo tocado pelo Zeus** (`anthropic_endpoints.py`, Vertex regional) — endurecido com checagem label+domínio e teste (`5417bb8309`). Triagem por classe permanece na WO.
- **2026-11-02 | GO + fechamento de escopo**: **#20 GO de produção local** registrado pelo owner; **#17** (roadmap) e **#16** (ideias) encerradas. Restam **#4** (assinatura/MSIX/DMG — BLOCKED por certificados), **#13** (e-mail/WhatsApp — BLOCKED por credenciais) e **#14** (financeiro — FUTURE/HIGH_ASSURANCE), cada uma com requisitos exatos registrados. Build bundled Electron 44.9.3 interrompido: payload upstream travou sem escrita por >90 min; payload parcial removido, release C retoma no ciclo próprio.

## 2026-11-02 | Dashboard servindo o código mergeado (listener obsoleto)

- **Sintoma:** após o rebuild do web, `/api/health` respondia 200 mas `GET /` devolvia 404 `Frontend not built`; `hermes dashboard --status` dizia não haver processo.
- **Causa:** PID 34236 — dashboard da geração PM **pré-merge** `7d81f8bd…` (removida na limpeza) ainda segurava `127.0.0.1:9119`; os assets que ele procurava não existiam mais. O start novo não bindava e saía.
- **Correção:** processo encerrado; dashboard iniciado do checkout mergeado (`.venv/Scripts/hermes.exe dashboard --skip-build --host 127.0.0.1 --port 9119`). `/api/health` reporta `commit 91b86350af…`, versão 0.22.5, e `GET /` serve `assets/index-DXNAyVGx.js` com HTTP 200.
- Sem alteração de código; os 7 perfis/sessões e 47 mensagens seguem os mesmos.

## 2026-11-02 | Residuais pós-GO: Dependabot, flake, migrações e lifecycle Electron 44

- **Dependabot high corrigido (`0039b4f46a`)**: o override `follow-redirects: 1.16.2` no `package.json` coexistia com **1.16.1 no `package-lock.json`** raiz (alerta 103, range 1.16.0–1.16.1). `npm install --package-lock-only` dizia "up to date"; `npm update follow-redirects --package-lock-only` atualizou **3 linhas** do lock, `npm ci --dry-run` confirmou consistência e o alerta passou a **fixed**. Default branch: **31 abertos, 0 critical/0 high** (20 moderate, 11 low).
- **Flake desktop corrigido (`7a42c73de5`)**: `dead-session-prune.test.ts > clamps the debounce...` contava **todos** os timers do ambiente (`vi.getTimerCount()` = 2 no runner) e falhava 1/11.512. A asserção agora mede o **delta** antes/depois do churn — o invariante "não empilha timer" continua testado, sem depender de timers alheios. 3/3 execuções locais PASS; lint desktop PASS.
- **Migrações pós-sync**: 10 arquivos de migração (gateway, config, docker, cron, secret scope, memória) **54 PASS, 1 skip**; schema SQLite/FTS/telegram **26 PASS, 10 skips**. Nenhuma falha.
- **Gate `profile-archives` vermelho corrigido**: caches de build (`.cache/desktop-inputs`, 402 MB de `.tar.gz`) tinham voltado para dentro do checkout; movidos para `D:\Projects\zeus-build-cache\desktop-inputs`. `python scripts/check` volta a **12/12 ok**.
- **Lifecycle Electron 44.9.3 source-backend PASS (`0b7472e1bd`)**: pacote `release/win-unpacked` (Electron 44.9.3) abriu nas duas sessões, gateway local ready nas duas, estado **134→136 entradas, lost 0**, quit limpo e sandbox removido. O harness agora (a) aceita o contrato real do modo source (`[boot] Hermes gateway is ready`, pois só o modo bundled anuncia `HERMES_BACKEND_READY port=`), (b) encerra o gateway **daemon** do sandbox via `gateway stop --all` antes de remover o diretório (ele sobrevive ao `app.close()` por design) e (c) faz a limpeza best-effort com retries, sem mascarar o erro real.
- **Payload bundled Electron 44 concluído** (~45 min, sem o travamento anterior): 16 ferramentas pinadas (482 s), venv **all-extras (46 extras)**, uv-cache lock-scoped (14 entradas podadas), verificação de hashes 7/7 e manifesto com launchers `bin/hermes{,-agent,-acp}.exe`. O packaging exige **`HERMES_PYTHON` também no `npm run builder`** (o hook `afterPack` re-hasheia os digests); sem ele falha em `runPython`, não no payload.
- **Lifecycle bundled Electron 44.9.3 PASS (`f8667ada7f`)**: `Zeus Agent Bundled.exe` (payload selado, `backendRoot: null`) abriu nas duas sessões, gateway local ready, estado **137→138 entradas, lost 0**, quit limpo e sandbox removido. O log do app prova `using bundled payload at …/resources/agent-payload`; o modo bundled também usa o **gateway local** (não anuncia `HERMES_BACKEND_READY`), por isso o harness unificou a prontidão: aceita o anúncio `serve` + `/api/health` quando existir e o boot `[boot] Hermes gateway is ready` caso contrário. `.publish-*` (staging do `durable_write_bytes`) passou a ser tratado como scratch transitório no snapshot de preservação.
- **Audit gate**: **success** em `7a1075b46e` e **success final em `4fa5f63a2b`** — todos os jobs: Trivy, CodeQL JS+Python, Sonar, proveniência, "Evidence and CI audit gate" (run 41493223915). CodeQL em `main`: **789 abertos, todos herdados do upstream**; nenhum em arquivo próprio do Zeus. O commit seguinte a este registro é docs-only.
- **Artefatos fora do checkout**: `apps/desktop/release` e `apps/desktop/build` movidos para `D:\Projects\zeus-build-cache\electron-44-bundled-2026-11-02\{release,build}`; `.cache/desktop-inputs` movido para `D:\Projects\zeus-build-cache\desktop-inputs`. Os gates `no-tmp`/`profile-archives` varrem arquivos ignored dentro do checkout, e o builder recria `.cache/desktop-inputs` (caminho fixo em `run-electron-builder.mjs`) — mover antes de `scripts/check`. Gate final: **12/12 ok**.

## 2026-11-02 | Zeus Cloud: Clerk + Stripe configurados (test mode)

- **Clerk**: app **Zeus** (`app_3LZQvceu62Q3uvSFc27zP0oekXj`, instância `ins_3LZQvgwvGabslL3kb3dKiuQDAc6`, frontend `adequate-viper-3823.clerk.accounts.dev`), tipo B2B com Organizations, **e-mail + telefone (SMS)** habilitados e verificação no sign-up; redirect nativo **`zeus://auth/callback`** salvo em Native applications. Chaves de desenvolvimento no `.env` local; segredo não transcrito.
- **Stripe** (conta PromptApp, test mode): 4 produtos/preços BRL criados de forma idempotente (`prod_VYbHywAKtOdw8K`/`price_1UXU5LRtfVHyZXkvkSTUS7Jz` mensal; `prod_VYbHHpFhteuTQt`/`price_1UXU5NRtfVHyZXkvAFPIZD4q` trimestral; `prod_VYbHvDxrrYlCML`/`price_1UXU5PRtfVHyZXkvhYBmyRts` semestral; `prod_VYbIGHHht2qM2j`/`price_1UXU5RRtfVHyZXkv3Jx3AjrQ` anual), **trial 2 dias** nos Payment Links. Chave de teste e Price IDs no `.env` local.
- **Landing comercial** em `cloud/site/index.html` (dark/Zeus, 4 planos, checkout Stripe, entrada Clerk) servida em `http://127.0.0.1:9120/`; configuração não secreta em `cloud/plans.json`; guia em `cloud/README.md`.
- **Evidência**: `audits/ZEUS-CLOUD-001-2026-11-02-vendor-setup.md`. **Nenhuma cobrança real**, nenhuma migração para live mode, nenhum deploy. Gate de assinatura/entitlement e serviço `zeus-cloud` continuam em #34/#35.

## 2026-11-03 | ZEUS-CLOUD-002 merged: control plane de checkout/entitlement (test mode)

- **PR #44 MERGED** com autorização do owner ("autorizado"); merge commit **`84766f6402`**; branch `feat/zeus-cloud-control-plane` removida. Commits: `de8002e083` (hook ruff pinado), `a745f3a6ed` (control plane), `959d785613` (SRI Clerk), `5c266ca855` (SSRF) e `3cb16eafe6` (ordenação).
- **Serviço** `cloud/service/`: `POST /api/checkout` (Clerk JWT → Stripe, trial 2 dias), `POST /api/stripe/webhook` (HMAC, tolerância 300 s), `GET /api/entitlement` (active/trialing + período), SQLite por `user_id`; `GET /health` e `/api/plans`; trava `sk_live_` e `dev:` auth bloqueado com chave live.
- **Landing** `cloud/site/index.html`: checkout autenticado; Payment Links não concedem acesso; Clerk pinado em `5.128.0` com SRI sha384.
- **Fail-closed**: checkout não pago não concede; `checkout.session.completed` grava `pending`; `customer.subscription.*` ativa com status/período; evento de assinatura adiantado + checkout atrasado não rebaixa; sem fetch por ID de webhook (SSRF parcial do CodeQL fechado).
- **Evidência**: 15/15 testes; `scripts/check` 12/12; PR #44 **14/14 checks PASS** (CodeQL JS+Python, Sonar gate+analysis, Trivy, desktop-static 26m18s, Evidence/CI audit gate); audit gate da main no merge commit **success** (run 41607735506).
- **Residual**: o runtime desktop/CLI ainda não consulta o entitlement nem aplica grace offline (próximo incremento); portal/cancelamento, webhook público, domínio, live mode e deploy seguem owner-gated. Nenhuma cobrança real.
- Evidência: `audits/ZEUS-CLOUD-002-2026-11-02-control-plane.md`.

## 2026-11-03 | Gate comercial completo: token, runtime, desktop, portal e devices

- **#45 MERGED `5b664b48bd`**: token de entitlement **Ed25519 device-bound** (`POST /api/entitlement/token`), TTL 7 dias, chave pública versionada e privada só no `.env`; 20/20 testes na época.
- **#46 MERGED `17acb56b3b`**: gate no início de `AIAgent.run_conversation` (antes de lease/prompt/modelo) com recusa tipada `entitlement_required`; `ZEUS_DEV_UNLOCK=1`; CLI `hermes entitlement status|activate|device-id`; desktop com verificação Ed25519, IPC, overlay bloqueante e deep link `zeus://auth/callback`; cloud com device codes de 10 min/uso único. **E2E real no PC**: sem token o overlay bloqueia; deep link gravou `zeus-entitlement.json` 0600 e liberou o app sem reiniciar. 7/7 testes de runtime + 4/4 Electron + 8/8 deep link.
- **#47 MERGED `85277cda51`**: **Stripe Customer Portal** (`POST /api/billing/portal`) para cancelar/trocar plano/recibos, com botão autenticado na landing; 29/29 testes na época.
- **#49 MERGED `b651fcb71a`**: **gestão de dispositivos** — tabela `devices`, listagem e revogação; dispositivo revogado não recebe novo código/token; seção Dispositivos na landing. (#48 foi fechado como superseded após rebase, sem force-push.)
- **Evidência final**: 32/32 testes cloud no branch combinado, 7/7 runtime, `scripts/check` 12/12; audit gate da main no merge `b651fcb71a` **success** (run 41652890848). Test token de test mode ativo no home real até 2026-11-10 (pode ser removido para voltar ao gate).
- **Residual/owner-gated**: issues **#50** (auto-healing com aprovação do owner), **#51** (seats/SSO/auditoria enterprise) e **#52** (live mode/domínio/deploy/termos). Nenhuma cobrança real, VPS ou deploy.
- Evidências: `audits/ZEUS-CLOUD-003-2026-11-03-signed-entitlement-token.md`, `ZEUS-CLOUD-004-2026-11-03-runtime-gate.md`, `ZEUS-CLOUD-005-2026-11-03-billing-portal.md`, `ZEUS-CLOUD-006-2026-11-03-device-management.md`.

## 2026-11-03 | Limpeza de artefatos e rebranding visível (#54 merged)

- **PR #54 MERGED `da8dd58fed`**: caches/artefatos ignored removidos, `.cache/desktop-inputs` movido para fora do checkout, branches mergeadas removidas e `payment_link` obsoletos retirados do catálogo.
- **Branding visível**: 60 arquivos de i18n desktop/web + 11 da TUI com valores Hermes→Zeus (0 chaves renomeadas); strings de console, gateway, catálogo, plugins, canais, status, notificações e onboarding; skin built-ins com branding Zeus; README/SECURITY rebrandados; console script **`zeus`** adicionado.
- **Limite consciente**: identificadores internos (`hermes_cli`, `HERMES_*`, `@hermes/*`, `X-Hermes-Session-Token`), caminhos de dados e atribuição MIT permanecem; renomeá-los apariam imports/dados/proveniência. Wake word padrão `hey hermes` também ficou intacta.
- **Verificação**: CI #54 14/14 verde (incl. desktop 11.513 testes), `.zeus/tests/test_rebrand.py` 5/5, `scripts/check` 12/12; desktop reconstruído, empacotado e aberto no PC com interface Zeus e backend ready. Evidência: `audits/ZEUS-CLEANUP-001-2026-11-03.md`.
- **Ainda aberto**: #50 auto-healing owner-gated, #51 enterprise, #52 live mode/deploy; `apps/desktop/build` locked no Windows.

## 2026-11-03 | Auto-healing determinístico owner-gated (#55 merged)

- **PR #55 MERGED `1731603b40`**: `zeus heal status|plan|apply` com diagnóstico de gateway/estado/disco/entitlement.
- **Sem correção silenciosa**: `apply` recusa ação fora do plano, recusa sem TTY e exige `APPROVE` digitado pelo owner; só `restart-gateway` é executado nesta camada. Auditoria em `logs/heal-audit.jsonl` 0600.
- **Verificação**: 6/6 testes; smoke real `gateway running`, 60.2 GB, entitlement active, sem problemas; `scripts/check` 12/12; CI #55 14/14 verde.
- **Residual**: orquestrador mestre/distribuição de skills, aprovação no desktop e outras ações (lock órfão, rotação de logs, reparo com backup) ficam para a próxima WO. Evidência: `audits/ZEUS-HEAL-001-2026-11-03-owner-approved-healing.md`.
