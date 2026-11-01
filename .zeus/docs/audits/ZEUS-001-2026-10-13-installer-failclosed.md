# ZEUS-001 | Correction Delta: installer entrypoints and Windows diagnostics

**Data:** 2026-10-13. **Veredito:** CORRECTION REQUIRED. **Merge/release/VPS:** NO-GO.

## Context Lock
- Repositório: `KayzenRoot/zeus-agent`. PR #1 (draft), branch `work/ZEUS-001-import-brand`.
- Base `main`: `23145d788a39453fcb6d81a6a53415a822b4655f`.
- Snapshot de implementação testado: `43b35d347e3cea34f2050f31fc087e8aa81f9f6c`.
- Commit posterior de CI: `ac9c9ac345b9e62351495bbda39c1535bed04732`; requer verificação separada.
- Fontes canônicas consultadas: `.zeus/docs/checkpoint.md`, `decisions.md`, `scope.md`, `definition-of-done.md`, `architecture.md` e `work-orders/ZEUS-001.md`. ADR-003 mantém desenvolvimento/teste Windows/WSL2 antes de qualquer VPS. Nenhuma decisão aprovada foi substituída.

## Escopo implementado nesta Correction Delta (issue #5)

1. `scripts/install.cmd`: remove o lançamento PowerShell remoto via `iex (irm ...)`. Retorna erro `zeus-release-unapproved`, código 2. Não instala nem baixa artefatos.
2. `scripts/install.ps1`: bloqueia o caminho padrão e qualquer `-Stage` antes da normalização de perfil e do despacho de etapas. Preserva `-Manifest`, `-ProtocolVersion`, `-ShowResolvedPaths` e definição de funções via dot-source. Em invocação `-File`, retorna 2; para `iex`, retorna sem terminar o PowerShell chamador.
3. `scripts/install.sh`: após o parser de flags e o `--manifest` informativo, bloqueia todas as etapas de instalação antes de criar traps, recibos e executar `check_platform`; código 2.
4. `.zeus/tests/test_zeus_install_cmd_guard.py` e `.zeus/tests/test_zeus_install_stage_guard.py`: verificam ordem dos guards e executam as recusas em sandbox temporário. Os testes nativos são limitados às plataformas compatíveis.
5. `.github/workflows/zeus-windows-install-cmd-safety.yml`: runner Windows para entrada CMD e PowerShell; não instala MSIX nem invoca rede pelo instalador.
6. `.github/workflows/zeus-windows-test-diagnostics.yml`: agora dispara a suíte completa Windows/Node 26.4 também em alterações relevantes do frontend/configuração, mantendo `workflow_dispatch` para Node 24.

### Evidências verificadas no GitHub para `43b35d3`
- [Brand/unit + POSIX run 38434725178](https://github.com/KayzenRoot/zeus-agent/actions/runs/38434725178): **PASS**, executando `python3 -m unittest discover -s .zeus/tests -p 'test_*.py' -v`.
- [Windows installers run 38434725148](https://github.com/KayzenRoot/zeus-agent/actions/runs/38434725148): **PASS**, executando a recusa nativa CMD e PowerShell.
- Passagem em CI prova as rotas e os asserts cobertos, mas não audita todo mecanismo externo de distribuição ou configuração de registro do Windows.

### Pendente de verificação no commit `ac9c9ac`
- [Windows Node 26.4 full diagnostics run 38434942670](https://github.com/KayzenRoot/zeus-agent/actions/runs/38434942670): **RUNNING na coleta deste documento**, sem inferir resultado.
- `dashboard-checks`, `desktop-static-checks`, demais checks de HEAD, relatórios locais e execução nativa Windows/WSL2: consultar novamente antes de alegar PASS.

## Risco residual e exclusões
- **HIGH_ASSURANCE no canal de instalação/distribuição.** Ainda não há instalador próprio Zeus nem distribuição assinada. Os arquivos de entrada são recusados intencionalmente. `--manifest`, `-Manifest`, `-ProtocolVersion` e `-ShowResolvedPaths` foram preservados, mas não tiveram auditoria independente completa nesta correção.
- Não foram executados Windows MSIX, certificados, App Installer externo, lojas OS-managed, pacote macOS DMG/notarização, autenticação/modelo/gateway/PT Y, nem rollback de release.
- Os guards não revogam registros de instalação preexistentes ou update feeds externos. Permanecem abertas as issues #2, #3, #4 e #5.
- Nenhum segredo, credencial, log pessoal ou arquivo de máquina foi incluído. Não executar instaladores da Nous para testar o fork.

## Auditoria / Checkpoint Delta proposto
- Reconhecer como **implementados e testados em CI** os três guards de entrada e os dois arquivos de testes no snapshot `43b35d3`.
- Manter status da ZEUS-001: **DRAFT / CORRECTION REQUIRED**. Não promover o checkpoint a APPROVED.
- Próxima ação NECESSARY: coletar resultado completo Windows Node 26.4 no HEAD e diagnosticar falhas; completar auditoria de updater e smoke local nativo Windows/WSL2. Só depois considerar assinatura, distribuição e merge.

**STOP CONDITION:** nenhuma aprovação, merge, release, instalação não validada ou implantação VPS sem Evidence Bundle completo e revisão independente.
