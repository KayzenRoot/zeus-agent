# ZEUS-SYNC-001 | Comparação upstream verificável (prep) — 2026-11-01

> **Análise read-only.** Nenhum `hermes update`, merge, download de instalador ou alteração
> na VPS foi executado. Este documento prepara a Work Order de sincronização da #7 e registra
> os backports de segurança aplicáveis já feitos.

## 1. Refs revalidadas (fetch read-only de `NousResearch/hermes-agent`)

| Ref | SHA | Data |
|---|---|---|
| Baseline importado (`53df274b08`) | `53df274b08f2bbbe82bb67bb50c7571952e95809` | 2026-10-12 |
| Release estável `v0.22.5` (tag anotada; o SHA da issue é o commit, não o objeto tag) | `bf0203a794a07aac3ff764972ab9087baa4e4f4e` | 2026-10-22 |
| Canary mais recente `v0.22.5+canary.20261101T064348Z` | `86ab9b8d17…` | 2026-10-31 |
| `upstream/main` no fetch | `557254faa2…` | 2026-11-01 |

Ancestralidade: `53df274b` **é ancestral** de `v0.22.5^{}` (sem divergência histórica).
O objeto tag carrega manifesto de release (`releaseId`, `candidateManifestSha256`,
`dockerManifestDigest`) — metadados a conferir na WO de sync.

## 2. Tamanho do delta (baseline → `v0.22.5^{}`)

- **6.044 commits**, **5.387 arquivos**, **+426.304 / −96.164** linhas.
- Áreas com maior movimento: `tests/gateway`, `apps/desktop`, `apps/shared`, `tests/hermes_cli`,
  `ui-tui/src`, `tests/agent`, `gateway/platforms`.
- 181 commits com marcadores de segurança (`CVE|GHSA|security|vulnerab|sanitiz|SSRF|injection|leak|exploit`).

## 3. Correções de dependência critical/high no upstream estável

Exemplos verificados por mensagem de commit (não exaustivo):

| Pacote | Upstream | Severidade |
|---|---|---|
| Pillow | 12.3.0 → **13.0.0** | critical (GHSA-8g5g-8vmr-9782) |
| PyJWT | 2.13.0 → **2.15.1** | critical (PYSEC-2026-175/177/178/179 + GHSAs) |
| certifi | 2026.5.20 → **2026.10.19** | critical (GHSA-6q48-6c7w-9gw2) |
| simple-git | 3.36.0 → **4.0.2** | critical (GHSA-x6jw-m9v5-85vh) |
| tinypool | 1.1.1 → **2.2.0** | critical (GHSA-85c8-ppgw-ccpr) |
| aiohttp | 3.14.3 → **3.14.5** | high (GHSA-9xw5-w5jj-pvcg) |
| @xmldom/xmldom | 0.8.13 → **0.8.15**, 0.9.10 → 0.9.12 | high |
| nanoid | 3.x → **3.3.20** | high (GHSA-2v37-7h3g-55p8) |
| follow-redirects | → **1.16.1** | high |
| vite | → **8.2.4** | (build tooling) |
| js-yaml | → **4.3.2** | |
| webpack-dev-middleware | 7.4.5 → **7.4.6** | high |

**Sobreposição com o Zeus**: Pillow 13, simple-git 4.0.2, @xmldom 0.8.15, nanoid, follow-redirects,
vite, js-yaml, webpack-dev-middleware, aiohttp já estavam corrigidos por backports/floors do
ZEUS-001 (nem sempre na mesma versão). Faltavam dois pins Python atrás do upstream — corrigidos
nesta rodada.

## 4. Delta de dependências Python (nosso `pyproject` × `v0.22.5`)

Antes desta rodada (comparação de pins `==`):

| Pacote | Zeus | Upstream v0.22.5 | Ação |
|---|---|---|---|
| PyJWT | 2.14.0 | **2.15.1** | **aplicado** (critical) |
| certifi | 2026.10.18 | **2026.10.19** | **aplicado** (critical) |
| aiohttp (extras messaging/matrix/slack/sms/teams) | 3.14.4 | **3.14.5** | **aplicado** (high) |
| brotlicffi | 1.2.1.0 | 1.2.0.2 | mantido (nosso é mais novo) |
| pyasn1 | 0.6.5 | 0.6.4 | mantido (nosso é mais novo) |
| ruamel.yaml.clib | ausente | 0.2.15 (CPython, win/linux/mac) | avaliar na WO (não é security) |

`hermes pm lock` regenerou `uv.lock`; `.zeus/tests/test_zeus_dep_security_floor.py` passou a
exigir os novos floors.

## 5. Superfície de conflito com a identidade Zeus

Dos arquivos que o Zeus alterou para identidade, o upstream mudou apenas:

| Arquivo | Mudança upstream |
|---|---|
| `hermes_cli/config_defaults.py` | +153 linhas |
| `agent/prompt_builder.py` | +136 linhas |
| `agent/initiate_setup_prompt.py` | +121 linhas |
| `README.md` | +26 linhas |

**Não mudaram** no upstream: `web/src/themes/*`, `web/src/index.css`, `web/src/pages/ChatPage.tsx`,
`web/src/pages/ProfilesPage.tsx`, `ui-tui/src/theme.ts`, `ui-tui/src/banner.ts`,
`ui-tui/src/i18n/en/chatBits.ts`, `hermes_cli/skin_engine.py`, `SOUL.md`.

Conclusão: o risco de conflito é **concentrado em 4 arquivos**, não espalhado pela UI/marca.

## 6. Opções de sincronização

**A. Backports de segurança (caminho atual)** — menor risco; aplicável sem merge; mantém a
identidade intocada. Custo: repetir a cada release estável; perde correções funcionais e
refatorações.

**B. Sync completo para `v0.22.5^{}` (WO dedicada)** — branch de sync a partir de `main`,
`git merge v0.22.5^{}`, resolução dos 4 arquivos de identidade, matriz completa de testes e
rollback por SHA. Custo alto (5.387 arquivos), mas alinha 6.044 commits e zera dívida de
segurança estrutural.

**C. Proibido** — `hermes update`, instalador Nous, merge cego em `main` ou force-push.

Recomendação: **A agora** (produção local 24/7), **B após #20** em PR isolada com Evidence
Bundle, rollback e matriz de testes abaixo.

## 7. Matriz de testes exigida para a WO de sync completo

1. `python scripts/check` (12 checks) + `scripts/run_tests.sh` completo.
2. `web check` (typecheck + 429 testes + lint) e `web build`.
3. Desktop: `build`, E2E relevante e electron-builder dry-run; atenção ao major do Electron.
4. Dashboard contra backend real: chat/PTY, sessões, kanban, cron, logs, auth.
5. Gateway: mensagens, restart/stop, ESTOP (cron/kanban/gateway), rate-limit e retry.
6. Migrations SQLite (estado/sessões/kanban) a partir de um backup real da produção local.
7. Fluxo B do instalador (`--plan`, instalação isolada, launcher, uninstall) e `scripts/zeus_backup.py`.
8. Isolamento de perfis (zero leitura cruzada) e logs sanitizados.

## 8. Evidência (comandos)

```bash
git remote add upstream https://github.com/NousResearch/hermes-agent.git
git fetch upstream --tags
git merge-base --is-ancestor 53df274b 'v0.22.5^{}'
git rev-list --count 53df274b..'v0.22.5^{}'          # 6044
git diff --shortstat 53df274b..'v0.22.5^{}'          # 5387 files, +426304/-96164
git log --oneline -i --grep='CVE|GHSA|security|vulnerab|sanitiz|SSRF|injection|leak|exploit' \
  53df274b..'v0.22.5^{}'                             # 181
```

## 9. Estado

- Backports críticos desta rodada: `PyJWT 2.15.1`, `certifi 2026.10.19`, `aiohttp 3.14.5`.
- Sync completo: **não iniciado** — requer WO aprovada (critérios e matriz acima).
- Issue #7 permanece aberta; próxima ação é a WO de sync com baseline `v0.22.5^{}`.
