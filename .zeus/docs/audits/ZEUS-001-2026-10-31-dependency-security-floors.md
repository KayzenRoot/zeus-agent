# ZEUS-001 | Correction Delta CD09: dependency security floors, DEPS gate and scanner triage

**Data:** 2026-10-31. **Veredito:** CORRECTION REQUIRED (global ZEUS-001; delta concluído com evidência). **Merge/release/VPS:** NO-GO.

## Context Lock
- Repositório: `KayzenRoot/zeus-agent`. PR #1 (draft), branch `work/ZEUS-001-import-brand`.
- Base `main`: `23145d788a39453fcb6d81a6a53415a822b4655f`. Parent do delta: `7936faabc2b4820a958f8c6e759499614ce674a0`.
- Commits do delta: `64977dce60` (floors), `6d615255fc` (HEALTHCHECK — **revertido** por leitura errada de DS-0002), `910dec857f` (revert), `241a17d312` (resíduos + reparo de lockfile + simple-git v4), `6d4cd91212` (triagem CVE-2026-53869).
- CD08 conserva APPROVED individual; nenhum checkpoint canônico foi promovido por este delta.

## Escopo implementado

1. **Configuração de repositório (owner, via API):** dependency graph + Dependabot alerts habilitados (estavam desligados; causa raiz da falha do `dependency-review`). Nenhum arquivo de código alterado por isso.
2. **Python** (`pyproject.toml`, `uv.lock`): certifi `2026.10.18` (GHSA-6q48-6c7w-9gw2), PyJWT `2.14.0` (CVE-2026-102268), urllib3 `>=2.8.0` (CVE-2026-97687/97689), aiohttp `3.14.4` (CVE-2026-111064/111066, GHSA-2g87-pp6c-29x5), brotlicffi `1.2.1.0` (CVE-2026-111497), httpx2 `2.12.0` + httpcore2 `2.12.0` (CVE-2026-84381/84382 + follow-up), pyasn1 `0.6.5`; transitivos filelock `4.2.4`, msgpack `1.2.4`, oauthlib `4.0.0`, tornado `6.6`.
3. **npm raiz/workspaces**: simple-git `4.0.2` (+`@simple-git/argv-parser 2.0.1`, CVE-2026-102829), vite `8.3.5` (raiz+web+desktop+bootstrap-installer, CVE-2026-112942), overrides js-yaml `4.3.2`/brace-expansion `5.0.11`/source-map-js `1.2.2`/undici `6.29.1`,`7.30.1`; imports `simple-git` v4 corrigidos (`{ simpleGit }`) em `apps/desktop/electron/git-review-ops(.test).ts`.
4. **Standalone**: sidecar (`@grpc/grpc-js 1.14.5`, undici `7.30.1`), whatsapp-bridge (body-parser `1.20.9`, sharp `0.35.5`), website (17 floors + exclusões datadas de `min-release-age` em `website/.npmrc` para lançamentos <14d).
5. **`.trivyignore`** (triagem justificada, não silenciamento): DS-0002 ×2 (s6-overlay exige root PID 1; drop via s6-setuidgid no dispatcher); CVE-2026-53869 (self-entry `hermes-agent==0.0.0` vs advisory <0.16.0 — commits de fix `3c231eb3` e `d9ec9058` ancestrais de `53df274b`, verificado por `git merge-base`).
6. **Regressão**: `.zeus/tests/test_zeus_dep_security_floor.py` — 10 testes afirmam os floors e o pareamento Pillow↔browser-harness.

## Incidente documentado: reestruturação do lockfile por `--legacy-peer-deps`
`npm update vite --legacy-peer-deps` resolveu sem peer deps e removeu `ink`/`ws` (47 entradas; `source-backend.test.ts` perdeu `ws`). Lock restaurado de `7936faa` e re-resolvido com install/update simples após alinhar os pins de vite em `8.3.5` (elimina o conflito de peer sem override). Contagem final de entradas: 1427; `ink 7.1.1` e `ws 8.21.1` de volta à raiz.

## Evidência por SHA
- **HEAD `6d4cd91212`** — [run 41210970087](https://github.com/KayzenRoot/zeus-agent/actions/runs/41210970087): 16 checks PASS, incluindo CodeQL (python 19m16s), CodeQL (js-ts), **New dependency vulnerability gate PASS**, desktop-static-checks (21m40s), dashboard-checks, voice-prefs 24/26.4, windows-bootstrap-deny, windows-installer-deny. FAIL (3, documentados): check "CodeQL" (756 alertas herdados — inventário em #8), Trivy (28 pillow BLOCKED), audit gate (downstream do Trivy).
- **HEAD `241a17d312`** — [windows-js-tests run 41208939512](https://github.com/KayzenRoot/zeus-agent/actions/runs/41208939512): SUCCESS (diferença para o HEAD final: apenas `.trivyignore`).
- **Artifact Trivy sanitizado** (run 41210970087): Misconfigurations 0, Secrets 0, Vulnerabilities 28 — todas pillow 12.3.0.
- **Local (Windows 11, Node 26.4.0, npm 11.17.0, uv 0.11.31)**: `npm ci` 1337 pacotes exit 0; suíte `.zeus/tests` 10/10 novos testes OK, 2 erros de guard pré-existentes reproduzem no estado base (verificado por `git stash`); `trivy 0.76.1 fs` local = 28 pillow após triagens.

## Bloqueios registrados (decisão necessária, não tomada unilateralmente)
- **Pillow 12.3.0 (28 HIGH/CRIT)**: `browser-harness==0.1.13` (última release, 2026-09-04) fixa exatamente `pillow==12.3.0`; `uv lock` não resolve com 13.0.0 (erro reproduzido). Caminhos: repin upstream do browser-harness OU override uv justificado — decisão do owner; gate Trivy permanece vermelho por contrato.
- **756 alertas CodeQL**: classe dominante (94× clear-text-logging) triada por amostragem — nenhum sítio imprime chave em claro; 1 hardening real identificado (`notarize.mjs:41` temp path previsível para .p8, build-time). Inventário e vereditos: issue #8 (M02).
- **Gates nativos** (Windows/WSL2 runtime, instalador Zeus-owned, MSIX/DMG/publisher): pendentes conforme #2/#4/#5; CI não substitui execução nativa.

## Risco residual
Atualizações major (simple-git 4, oauthlib 4, filelock 4, tinypool 2) cobertas pelas suítes hospedadas PASS; runtime Python completo não é exercido pelo CI desta PR — validação de runtime permanece gate nativo. Nenhum segredo adicionado; exclusões de idade de release têm data de remoção explícita.
