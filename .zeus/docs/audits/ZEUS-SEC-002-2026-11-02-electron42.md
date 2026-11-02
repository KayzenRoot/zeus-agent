# ZEUS-SEC-002 | Electron 42 e overrides moderados — evidência · 2026-11-02

> Complementa o comentário da #27. Executado em Windows 11 (10.0.26200), Node 26.4, npm do repo.

## 1. Resultado (`npm audit`)

| Escopo | Antes (início) | Depois |
|---|---|---|
| Todos os workspaces | 59 — 2 critical, 8 high | **45 — 0 critical, 0 high** |
| Produção (`--omit=dev`) | — | **18 — 0 critical, 0 high** |

Movimentos: `electron` 40.10.6 → **42.11.18**; `sanitize-html` 2.18.1; `ip-address` 10.7.5;
`brace-expansion` 5.0.12; `yaml` 2.9.1; `concurrently` 10.0.6; `zod` 4.6.7 (tests-js).
Exclusões datadas no `.npmrc`: `follow-redirects`, `joi`, `electron`, `ip-address`.

## 2. Por que 42.11.18

- OpenURL/popup highs: corrigidos a partir de **41.10.4**.
- Mitigação de certificados intermediários eMudhra (high): corrigida a partir de **42.11.16**;
  42.11.18 era a última 42.x disponível. `electron --version` → `v42.11.18`.

## 3. Verificação

| Gate | Resultado |
|---|---|
| `npm ci --dry-run` | OK |
| desktop `typecheck` | exit 0 |
| desktop `lint` | 0 errors (276 warnings pré-existentes) |
| desktop UI (`vitest --project ui`) | **1.225/1.225 arquivos**, exit 0 |
| desktop `build` | exit 0 |
| `web check` | typecheck + **429/429** + lint 0 errors |
| `web build` | OK |
| `scripts/check` | **12/12** |
| Empacotamento `pack --dir` | electron-builder 27.0.0-alpha.6, `electron=42.11.18`, asar integrity, node-pty prebuilds |
| Smoke do pacote | `release/win-unpacked/Zeus Agent.exe` iniciou e permaneceu vivo |
| PTY nativo sob Electron 42 | `node-pty.spawn(cmd.exe)` executou `echo pty-ok` e saiu 0 (`PTY_EXIT 0 OUT …pty-ok`) — ABI/prebuild compatíveis |
| SHA-256 do exe empacotado | `79c31270c2f65f63…d94c72` |
| `resources/app.asar` | 7.453.278 bytes; `version` = 42.11.18 |

Assinatura: `AZURE_SIGN_*` ausente → pacote **unsigned**, como esperado no fluxo local. Release
assinada continua NO-GO (#4).

## 4. Suíte `test:desktop:platforms` (local)

342/375 arquivos passam neste host. As 20 falhas são de ambiente, sem referência ao Electron:

- `mac-sign`: exige `HERMES_PYTHON` apontando para o runtime preparado.
- `after-pack-digests` / `run-electron-builder`: fixtures de empacotamento preparado
  (`app.asar`, seleção de toolchain Windows) ausentes no run direto.
- `channel-build-version`: cria clones git temporários e espera histórico de publicação.
- `bundle-electron-main`: `--ozone-platform` oscila entre `x11`/`wayland` conforme env do host.
- `ssh-connection`, `tray-host`, `log-rotation`, `windows-remote-lifecycle`: comportamento de
  Windows/spawn/DBus.
- `payload-sign-cache`: timeout de 30 s no host.

O CI Linux cobre a suíte canônica; este host não é o ambiente de aceite dela.

## 5. Residual

- 37 moderates (10 em produção): cadeias de build/dev (`electron-builder` alpha,
  `node-gyp`/`glob`/`minimatch`/`cacache`, `socks`) sem fix não-quebrante; nenhum critical/high.
- Repetir `npm audit` após o próximo ciclo de releases para reavaliar os moderates.
