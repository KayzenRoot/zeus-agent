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
