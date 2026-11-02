# ZEUS-001 | Design proposto: instalação local Zeus-owned e fronteira com release assinado

> **PROPOSTA DE DESIGN, NÃO APROVAÇÃO DE EXECUÇÃO.** Atende aos itens pendentes da
> issue #5 dentro da WO ZEUS-001. Nada disto autoriza instalar, publicar, assinar,
> distribuir ou tocar VPS. A implementação exige Work Order própria aprovada,
> baseline e auditoria.

## 1. As três superfícies que não devem ser confundidas

| Superfície | Origem do código | Assinatura | Gate |
|---|---|---|---|
| **A. Checkout fonte** (dev/dia-a-dia) | clone Git `KayzenRoot/zeus-agent` | n/a | Stage 1 do runbook + guardas fail-closed |
| **B. Instalação local Zeus-owned** (proposta deste documento) | build a partir do checkout A, verificado por SHA | sem assinatura de publisher, **uso pessoal na máquina de desenvolvimento** | instalação isolada, rollback testado, zero rede do instalador |
| **C. Release assinado/distribuição** | pipeline de release | Publisher real + certificado + notarização | issue #4 + [#20](https://github.com/KayzenRoot/zeus-agent/issues/20); hoje **NO-GO** |

A existência de B nunca dispensa C; C nunca é pré-requisito para A. `main` não é
canal de produção (issue #3).

## 2. Fluxo B — instalação local Zeus-owned (proposta)

1. **Entrada:** checkout verificado (`git rev-parse HEAD` registrado) + `scripts/`
   Zeus-local com validação de origem: o script só opera sobre o checkout em que
   está Commitado (prova: `git -C <root>` resolve para o mesmo remoto/HEAD), recusa
   execução a partir de diretório baixado (exit 2, `zeus-release-unapproved`).
2. **Validação de integridade antes de qualquer cópia:** `git status --porcelain`
   limpo nos paths que serão instalados; digest dos artefatos construídos
   registrado no log redigido; nenhum download — todo artefato vem do build local
   (Node + uv), nunca de `hermes-agent.nousresearch.com` nem de raw.githubusercontent
   da Nous.
3. **Isolamento:** `HERMES_HOME` e Electron userData em perfil dedicado criado pelo
   instalador; nenhum perfil Hermes/Zeus existente é tocado; rollback = lista de
   paths criados em recibo removível (`uninstall` espelha o recibo).
4. **Fronteiras rígidas herdadas (inalteradas):** `ZEUS_DESKTOP_BOOTSTRAP_APPROVED=false`,
   `ZEUS_NATIVE_UPDATES_APPROVED=false`, `publish:null`, guards de
   `zeus_update_guard.py`/bootstrap-runner — a instalação B **não liga** nenhum
   canal; o app instalado segue recusando update/bootstrap com
   `zeus-release-unapproved`.
5. **Espelhos de terceiros** (componentes baixados em build): pin por digest/SHA
   verificado na WO de implementação, com licença e origem anotadas — nunca
   substituição cega de URL da Nous (item já pendente na issue #5).

## 3. Compatibilidade de chamadores (inventário a atestar na WO)

`scripts/install.cmd|install.ps1|install.sh` são hoje recusa-pura (`zeus-release-unapproved`).
Os chamadores herdados a reatestar quando o fluxo B existir: setup do desktop,
`bootstrap-runner.ts` (recusa mantida para release C), `test-desktop.mjs` (modo
fresh — autorização separada do runbook Stage 2), e qualquer script de CI. Contrato:
nenhum chamador ganha poder de rede/instalação sem flag Zeus explícita e testada.

## 4. Estratégia de testes (contrato da WO futura)

- Testes de contrato PowerShell/CMD/bash em diretórios temporários isolados: zero
  downloads, zero escrita fora do recibo, recusa em paths não aprovados (padrão
  `test_zeus_install_*_guard.py`).
- Instalação B real **somente em máquina de teste isolada**, logs redigidos,
  captura de exit codes, prova de desinstalação limpa e reversibilidade.
- Stage 2 do runbook (`.zeus/docs/windows-validation.md`) continua autoridade:
  pré-condições de isolamento comprovadas antes de qualquer `test:desktop:fresh`.

## 5. Estados honestos

| Item | Estado |
|---|---|
| Recusa fail-closed dos instaladores herdados | **VERIFICADO** (CI Windows + testes) |
| Recusa runtime do updater na máquina real | **VERIFICADO** 2026-10-31 (`hermes update` → recusa, exit 0, checkout intocado) |
| Fluxo B implementado (local, não assinado) | **IMPLEMENTADO** 2026-11-01: `scripts/zeus-install.{sh,ps1,cmd}` + `scripts/zeus_install_local.py`; 13 contratos em `.zeus/tests/test_zeus_installer_local.py`; `--plan` verificado no checkout real (`0416f0b069`); WSL2 15/15 (`3cb8d12446`) |
| Auditoria dos mirrors de terceiros | **VERIFICADO para uso local** 2026-11-02 (`audits/ZEUS-001-2026-11-02-artifact-mirror-audit.md`): mirror content-addressed por SHA-256, fallback da origem oficial, verificação obrigatória; licenças de redistribuição (GPL/BSD/Bitwarden/FFmpeg) pendentes para a release C |
| Release C (assinatura/publisher/MSIX/DMG) | **NO-GO** (issue #4, [#20]) |

## 5.1 Fluxo B implementado — contrato

- **Entrada verificada**: `git rev-parse --show-toplevel` == root, origin em
  `KayzenRoot/zeus-agent` (https/ssh), HEAD resolvido, **árvore rastreada limpa**
  (`status --porcelain --untracked-files=no` vazio). Cópia baixada (sem `.git`) é recusada.
- **Isolamento**: `HERMES_HOME=<root>/home`; root padrão `%LOCALAPPDATA%\ZeusAgent`
  (Windows) ou `$XDG_DATA_HOME/zeus-agent` (POSIX), sempre fora do checkout. Nenhum
  perfil Hermes/Zeus existente é lido ou escrito.
- **Build**: delega ao `setup-hermes.{sh,ps1}` do próprio checkout em modo
  `--runtime-only`/`-RuntimeOnly`, herdando `HERMES_HOME`. O instalador não executa
  script remoto nem instalador upstream; a sincronização é a do lock commitado.
- **Launcher + recibo**: launcher ativa o ambiente pm do checkout com o home isolado;
  `receipt.json` registra schema, checkout, origem, HEAD, home, launchers, caminhos
  criados e `updates_enabled: false`. Canais de update/bootstrap permanecem desligados.
- **Desinstalação**: espelha o recibo; sem `--purge-data` preserva `sessions/`,
  `memories/` e `state.db`. Recibo ausente/estranho → recusa (exit 2).
- **Limites mantidos**: sem assinatura, sem MSIX/DMG, sem release, sem deploy.
  Fluxo B é uso pessoal na máquina de desenvolvimento, nunca canal de distribuição.

## 6. STOP

Sem rede do instalador, sem sideload unsigned, sem MSIX, sem release, sem merge,
sem VPS. Qualquer desvio = BLOCKED com evidência e decisão pendente.
