# ZEUS-SYNC-001 | Work Order proposta: sync controlado para o Hermes `v0.22.5`

> **PROPOSTA, NÃO EXECUÇÃO.** Requer autorização do owner antes do merge em `main`.
> Baseline e comparação: [`audits/ZEUS-SYNC-001-2026-11-01-upstream-comparison.md`](../audits/ZEUS-SYNC-001-2026-11-01-upstream-comparison.md).

## 1. Objetivo

Trazer o upstream estável `v0.22.5` (tag anotada → commit `bf0203a794a07aac3ff764972ab9087baa4e4f4e`)
para o Zeus preservando identidade, compatibilidade de runtime e as correções próprias já aplicadas.

## 2. Baseline verificado

| Ref | SHA |
|---|---|
| Baseline importado | `53df274b08f2bbbe82bb67bb50c7571952e95809` |
| Alvo estável | `bf0203a794a07aac3ff764972ab9087baa4e4f4e` (`v0.22.5^{}`) |
| Delta | 6.044 commits, 5.387 arquivos, +426.304/−96.164 |
| Zeus atual | `main` no SHA registrado no PR de sync |

## 3. Estratégia (branch isolada, nunca `main` direto)

```bash
git switch -c sync/ZEUS-SYNC-001-v0.22.5 origin/main
git merge --no-ff 'v0.22.5^{}'        # upstream remote já configurado
```

- Resolver conflitos **por arquivo**, com revisão de intenção (não escolher "ours/theirs" em bloco).
- Preservar: `LICENSE`/atribuição Nous, identidade Zeus (skin, SOUL, prompt, tema), aliases/rotas/
  endpoints internos, `HERMES_*`, paths de estado e SQLite contracts.
- Reaplicar, se o upstream não trouxer equivalente: floors de segurança do ZEUS-001, SSRF do media
  proxy, gates fail-closed de updater/instalador, `pm/overrides.py`, backup restore path fix.
- Nunca executar `hermes update`, instalador Nous, force-push ou merge em `main` sem aprovação.

## 4. Superfície de conflito conhecida

Mudaram no upstream **e** no Zeus:

| Arquivo | Risco |
|---|---|
| `hermes_cli/config_defaults.py` | +153 upstream; Zeus adiciona skin `zeus` |
| `agent/prompt_builder.py` | +136 upstream; identidade Zeus |
| `agent/initiate_setup_prompt.py` | +121 upstream; intro Zeus |
| `README.md` | +26 upstream; reescrito para Zeus |
| `pyproject.toml` / `uv.lock` / `package.json` / locks | floors e overrides de segurança |
| `scripts/`, `pm/environment.py`, `hermes_cli/kanban*`, `hermes_cli/web_routers/files.py` | correções próprias |

UI/tema/skin/banner/SOUL **não mudaram** no upstream — conflito concentrado, não difuso.

## 5. Matriz de aceite (obrigatória)

1. `python scripts/check` 12/12.
2. `bash scripts/run_tests.sh` completo (per-file isolation) — sem falhas novas vs. baseline.
3. `web check` (typecheck + testes + lint) e `web build`.
4. Desktop: typecheck, lint, UI suite, build, `pack --dir`, smoke do app, PTY.
5. Dashboard real: chat/PTY, sessões, kanban, cron, logs, auth; health 200.
6. Gateway: mensagens, restart/stop, ESTOP (cron/kanban/gateway), rate-limit/retry.
7. Migrations SQLite a partir de backup real da produção local (drill de restore).
8. Fluxo B: `--plan`, instalação isolada, launcher, uninstall; `zeus_backup.py` round-trip.
9. Isolamento de perfis (zero leitura cruzada) e logs sanitizados.
10. Trivy/CodeQL/Sonar verdes no HEAD do PR de sync.

## 6. Rollback

- O sync vive em branch/PR; `main` só muda por merge aprovado.
- Rollback = fechar o PR ou reverter o merge commit no `main` (`git revert -m 1 <merge>`).
- Antes do merge: backup do home real (`scripts/zeus_backup.py`) e registro do SHA atual.

## 7. Fora de escopo

Assinatura/MSIX/DMG (#4), credenciais (#13/#14), VPS (#20), release/publicação.

## 8. Spike de merge executado e abortado (2026-11-02)

Worktree isolado (`sync/ZEUS-SYNC-001-v0.22.5`), `git merge --no-commit --no-ff 'v0.22.5^{}'`:

- **5.387 arquivos** alterados pelo merge; **100 conflitos**.
- Distribuição:
  - **53** `.github/workflows/*` (upstream mudou/addiu workflows; Zeus tem audit/brand próprios);
  - **32** em `apps/` — 26 arquivos de i18n + `electron/main.ts`, `git-review-ops.ts|test`,
    `package.json`, `electron-builder.config.cjs`, `bootstrap-installer/package.json`;
  - **15** outros — `uv.lock`, `pyproject.toml`, `package*.json`, `web/package.json`,
    `website/{package,package-lock,.npmrc}`, `sidecar/package-lock.json`, `.npmrc`, `README.md`,
    `agent/initiate_setup_prompt.py`, `pm/{environment,operations,packages}.py`.
- **Abortado sem commit** (`git merge --abort`); worktree/branch removidos; `main` intocado.

### Estratégia de resolução recomendada

1. **i18n** (26): partir do upstream e reaplicar o **mapa de marca revisado** (nunca substituição
   global de "Hermes"→"Zeus"; preservar atribuição, identificadores e nomes de plugins).
2. **Workflows** (53): manter o conjunto Zeus próprio (audit, brand) e adotar o upstream nos
   compartilhados, revisando URLs/SHAs/permissões; não perder o gate de segurança.
3. **Locks**: regenerar com `hermes pm lock` / `npm update` e reaplicar floors + overrides
   (`pm/overrides.py`, check de ambiente override-aware).
4. **pm/**: reaplicar `check(source)` + `_fresh_build(source)` sobre a nova árvore.
5. **Identidade** (4 arquivos + README): merge manual preservando Zeus.
6. **Testes**: matriz completa (§5) antes de qualquer merge em `main`.

**Estimativa:** esforço dedicado de múltiplas horas + matriz ELEVATED. O spike está medido; a
execução continua condicionada à autorização do owner nesta WO.
