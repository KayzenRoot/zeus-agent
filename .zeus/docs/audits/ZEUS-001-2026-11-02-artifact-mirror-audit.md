# ZEUS-001 | Auditoria dos artefatos terceiros e do mirror (item da #5) — 2026-11-02

> **Escopo:** confiança nos binários baixados pelo PM para **build/uso local**. Não autoriza
> redistribuição (release C segue NO-GO na #4). Nenhuma URL foi substituída em massa.

## 1. Como o PM obtém um artefato

1. `pm/artifact-mirror.json` define `origin = https://hermes-assets.nousresearch.com` e
   `prefix = upstream/sha256/`.
2. `pm/artifact_mirror.py::mirror_url(sha256)` exige um **SHA-256 completo em minúsculas** e
   monta `…/upstream/sha256/<sha256>` — o objeto é **content-addressed pelo próprio digest**.
3. `pinned_source()` tenta a **URL de origem** registrada no lock (GitHub Releases, nodejs.org,
   registry.npmjs.org, CDN do Playwright, etc.) e usa o mirror **apenas como fallback**.
4. Todo download pago por pacote é verificado contra o hash do lock
   (`pm/downloader.py::_sha256_file`); bytes divergentes falham com erro, nunca seguem adiante.
5. O lock carrega `sha256` para **todos** os artefatos listados (nenhum `NO-SHA` na inspeção).

Consequência: um mirror comprometido não consegue entregar conteúdo diferente — no pior caso
falha a verificação. E o mirror não cria lock-in: a origem oficial continua sendo a primeira
tentativa.

## 2. Verificação ao vivo (2026-11-02)

Baixado o `ripgrep` 15.2.0 win32-x64 **do mirror**:

```
mirror  : https://hermes-assets.nousresearch.com/upstream/sha256/71b2fef8…aafc5
bytes   : 1.789.611
sha256  : 71b2fef860abe467217a538ff31de02f5258807c0129f771846f87bd029aafc5
lock    : 71b2fef860abe467217a538ff31de02f5258807c0129f771846f87bd029aafc5   ✅
```

## 3. Inventário de origem e licença

| Pacote (lock) | Versão | Origem primária | Licença (metadata) | Nota |
|---|---|---|---|---|
| `uv` | 0.12.3 | astral-sh/uv | Apache-2.0 (dual MIT/Apache no projeto) | ok |
| `python` (build standalone) | 3.14.7+20260901 | astral-sh/python-build-standalone | MPL-2.0 (build) / PSF-2.0 (CPython) | ok |
| `node` | 26.7.0 | nodejs.org | MIT | ok |
| `npm` | 12.0.2 | registry.npmjs.org | Artistic-2.0 | ok |
| `git` (Git for Windows) | 2.53.0+3 | git-for-windows/git | **GPL-2.0** (e componentes) | obrigações GPL ao redistribuir |
| `gh` | 2.97.0 | cli/cli | MIT | ok |
| `ripgrep` | 15.2.0 | BurntSushi/ripgrep | Unlicense (dual MIT) | ok |
| `ffmpeg` | 9.0.1 | ffmpeg.martin-riedl.de | **depende do build** (LGPL/GPL) | revisar flags antes de redistribuir |
| `agent-browser` | 0.26.0 | npm | Apache-2.0 | ok |
| `cua-driver` | 0.21.0 | trycua/cua | MIT | ok |
| `bws` (Bitwarden SDK) | 2.0.0 | bitwarden/sdk-sm | **Bitwarden SDK License Agreement v1** (proprietária) | revisar termos antes de qualquer redistribuição |
| `llamacpp-*` | b11370 | ggml-org/llama.cpp | MIT | ok |
| `whispercpp-*` | b5130 | ggml-org/whisper.cpp | MIT | ok |
| `chromium` (Playwright) | 145.0.7632.6 | cdn.playwright.dev | BSD-style + licenças de terceiros | bundle de licenças acompanha o build |
| `dmgbuild` | 1.2.5 | electron-userland/electron-builder-binaries | repo sem metadata SPDX; dmgbuild é MIT | conferir bundle antes do DMG (release C) |
| `termux-docker` | digest imutável | Docker Hub (`docker://…@sha256:`) | componentes Termux (GPL/Apache) | usado só no fluxo Android/container |
| `iron-proxy` | 0.39.0 | — (sem artefato nesta plataforma) | — | não baixado neste host |

## 4. Riscos e decisões

1. **Mirror**: design content-addressed + verificação obrigatória + fallback → **aceitável para
   build local**. Não há substituição cega de URL da Nous; a origem oficial continua primária.
2. **Redistribuição (release C)**: os itens em negrito da tabela exigem avisos/licenças no pacote
   (Git for Windows GPL, Bitwarden SDK proprietária, FFmpeg conforme build, bundle do Chromium,
   dmgbuild/MIT). Nada disso bloqueia uso local; bloqueia **distribuir** sem revisão.
3. **FFmpeg**: o artefato vem de um espelho de builds de terceiros; a licença efetiva depende das
   flags do build. Antes de release C, substituir por build próprio ou verificar a configuração
   LGPL/GPL e incluir os avisos.
4. **Electron-builder-binaries**: repositório de distribuição sem `LICENSE` próprio; cada binário
   carrega sua licença upstream. Conferir no bundle DMG (relacionado à #4).

## 5. Evidência (comandos)

```bash
python -c "import json; d=json.load(open('pm/lock.json')); print(d['packages']['ripgrep']['artifacts']['win32-x64']['sha256'])"
curl -sSL -o /tmp/ripgrep.zip https://hermes-assets.nousresearch.com/upstream/sha256/<sha256>
sha256sum /tmp/ripgrep.zip
gh api repos/<owner>/<repo> --jq '.license.spdx_id'
```

**Estado:** item "auditar mirrors" da #5 **executado** para uso local; pendências de licença
ficam registradas para a release C (#4). Nenhum pacote foi instalado a partir de URL alterada.
