# Zeus Agent | Catálogo documental de módulos, fases e gates até produção

> **PROPOSTA DE PLANEJAMENTO, NÃO DECISÃO APROVADA.** Work Order documental `ZEUS-DOC-CAT-001`. Este arquivo não modifica Scope, DoD, ADRs, checkpoint, código, dependências ou políticas existentes. Nenhum módulo é declarado funcional por estar descrito aqui.

## 1. Identidade e Context Lock

- Repositório: `KayzenRoot/zeus-agent`. Criação documental a partir de `main@23145d788a39453fcb6d81a6a53415a822b4655f`; branch de trabalho `docs/ZEUS-DOC-CAT-001-product-modules`.
- Implementação importada ainda na [PR #1 Draft](https://github.com/KayzenRoot/zeus-agent/pull/1), HEAD observado `7936faabc2b4820a958f8c6e759499614ce674a0` em 2026-10-31. Revalidar antes de qualquer novo incremento.
- [Roadmap MVP, issue #17](https://github.com/KayzenRoot/zeus-agent/issues/17) é uma proposta de planejamento: não altera automaticamente autoridade canônica.
- O checkout da `main` nesta data contém somente `.zeus/`; o produto importado está na PR #1, **sem merge**. Portanto o catálogo na main não comprova que os módulos estão implementados.
- Se HEAD, ADR, Scope, DoD ou checkpoint mudar: **STALE**; reconsultar/rebasear o planejamento antes de executar.

### Hierarquia de autoridade (imutável nesta PR)

1. `.zeus/docs/checkpoint.md`
2. `.zeus/docs/decisions.md` (ADR-001 a ADR-004 APPROVED; ADR-005 PROPOSED)
3. `.zeus/docs/scope.md`
4. `.zeus/docs/definition-of-done.md`
5. `.zeus/docs/architecture.md`
6. `.zeus/docs/requirements.md`
7. `work-orders/ZEUS-001.md`, backlog, issues e este catálogo de PROPOSTAS.

### Fingerprints da fonte, blob SHA Git (main)

| Fonte relativa a `.zeus/docs/` | Git blob SHA |
|---|---|
| `checkpoint.md` | `9d16da6f3d32959b0e4c877b283884b2c90b382b` |
| `decisions.md` | `fb422a7d17b6f99cb8e4ca3c5663567cbe088e8e` |
| `scope.md` | `0e8af7350006496167d8db48b737aa9c66eeaa02` |
| `definition-of-done.md` | `f43686226e0e22aa2695861846a6c2843b9cf7b1` |
| `architecture.md` | `4d79f0410f769912ce449bec95cda06b6c010c02` |
| `requirements.md` | `ee3e1a2546da1d8e801065488df6da4d0877ac5c` |
| `backlog.md` | `2a031f7af0c59df7487cfe70e364969602691efb` |
| `deployment.md` | `d4cdcb843741a7e4e973c2ced55420a6b76c6615` |
| `work-orders/ZEUS-001.md` | `53111eff700e3c4ea9fc7d3c94e818bc76f2e321` |

**Restrições aprovadas:** Windows/WSL2 local-first (ADR-003); repositório público e segredos fora do Git; MIT/Nous e histórico preservados; marca Zeus própria sem substituição global de APIs/`HERMES_*` (ADR-004); usar dashboard/TUI/PT Y existente sem segundo chat (arquitetura); VPS e distribuição não autorizadas. Nunca substituir evidência por suposição de issue ou de scanner.

## 2. Fases e caminhos de produto

| Fase | Objetivo | Critério de saída | Situação |
|---|---|---|---|
| **P0** Base e correções ZEUS-001 | Histórico, branding, CI, bloqueios updater, instalação e gates nativos aprovados | **ZEUS-001 APPROVED objetivamente** pelo DoD vigente; PR #1 permanece Draft até então | CORRECTION REQUIRED para a ZEUS-001, CD08 individual APPROVED sem promoção global |
| **P1** Triagens preparatórias | Segurança, confiabilidade e inventário GAF/GEF, principalmente leitura | Resultados comprovados e WOs autorizadas para eventual código | Planejamento e diagnóstico, nenhum avanço automático |
| **P2** MVP pessoal local | BYOK, chat, memória, 3 agentes, tarefas e Control Room | E2E, isolamento, recovery, CI, security e revisão independente; DoD MVP **proposto** exige aprovação formal | Futuro, condicionado à ZEUS-001 |
| **P3** Produção local / distribuição | Runbooks, recuperação, releases assinados, gates e operação suportada | DoD de produção/release separado, owner go-ahead, plataformas de fato testadas | Futuro, não autorizado para execução |
| **P4** Evolução opcional | VPS, upstream sync, conectores, identidade, especializações | Cada recurso exige novo escopo/ADR/WO, custos e permissões explícitas | Fora do escopo atual |

**Duas metas não equivalentes:** (a) uso local pessoal confiável e (b) distribuição pública assinada. A existência de uma não dispensa automaticamente os gates da outra. Alterar a exigência de MSIX/DMG/Publisher exige decisão expressa e atualização canônica após auditoria.

## 3. Índice rastreável de módulos

| Módulo | Nome | Fase | Classe no planejamento | Dependências | Referências |
|---|---|---|---|---|---|
| `M00` | Fundação, upstream MIT e identidade Zeus | P0 | NECESSARY (ZEUS-001 vigente) | — | [#1](https://github.com/KayzenRoot/zeus-agent/issues/1), [#17](https://github.com/KayzenRoot/zeus-agent/issues/17) |
| `M01` | Bootstrap, atualização e Windows/WSL2 seguros | P0 | NECESSARY (gates ZEUS-001 vigentes) | `M00` | [#2](https://github.com/KayzenRoot/zeus-agent/issues/2), [#3](https://github.com/KayzenRoot/zeus-agent/issues/3), [#5](https://github.com/KayzenRoot/zeus-agent/issues/5) |
| `M02` | Triagem de segurança, autorização e isolamento | P1 | NECESSARY proposto para MVP (issue #8) | `M00` | [#8](https://github.com/KayzenRoot/zeus-agent/issues/8) |
| `M03` | Confiabilidade de fila, cron e recuperação | P1 | NECESSARY proposto para MVP (issue #9) | `M00` | [#9](https://github.com/KayzenRoot/zeus-agent/issues/9) |
| `M04` | Inventário GAF/GEF e componentes obsoletos | P1 | NECESSARY somente inventário (issue #6) | `M00` | [#6](https://github.com/KayzenRoot/zeus-agent/issues/6) |
| `M05` | Runtime local, BYOK, gateway e autenticação | P2 | NECESSARY proposto para MVP (issue #10) | `M00`, `M01`, `M02`, `M03` | [#10](https://github.com/KayzenRoot/zeus-agent/issues/10) |
| `M06` | Sessões, memória, persistência e restauração | P2 | NECESSARY proposto para MVP (issue #10) | `M05` | [#10](https://github.com/KayzenRoot/zeus-agent/issues/10) |
| `M07` | Perfis, permissões e aprovação humana | P2 | NECESSARY proposto para equipe (issues #8/#11) | `M05`, `M02` | [#8](https://github.com/KayzenRoot/zeus-agent/issues/8), [#11](https://github.com/KayzenRoot/zeus-agent/issues/11) |
| `M08` | Equipe de três agentes e delegação auditável | P2 | NECESSARY proposto para MVP (issue #11) | `M06`, `M07`, `M03` | [#11](https://github.com/KayzenRoot/zeus-agent/issues/11) |
| `M09` | Fluxo durável de tarefas, Kanban e agendamento | P2 | NECESSARY proposto para operação MVP (issue #9) | `M08`, `M03` | [#9](https://github.com/KayzenRoot/zeus-agent/issues/9), [#11](https://github.com/KayzenRoot/zeus-agent/issues/11) |
| `M10` | Control Room e dashboard autenticado | P2 | IMPORTANT proposto para MVP (issue #12) | `M08`, `M09` | [#12](https://github.com/KayzenRoot/zeus-agent/issues/12) |
| `M11` | Observabilidade, histórico, custo e controle operacional | P2 | IMPORTANT proposto, transversal ao MVP | `M09`, `M10` | [#9](https://github.com/KayzenRoot/zeus-agent/issues/9), [#12](https://github.com/KayzenRoot/zeus-agent/issues/12) |
| `M12` | QA, benchmark e revisão independente | P0-P4 | NECESSARY como gate transversal, não novo escopo | `M00` | [#1](https://github.com/KayzenRoot/zeus-agent/issues/1), [#2](https://github.com/KayzenRoot/zeus-agent/issues/2), [#8](https://github.com/KayzenRoot/zeus-agent/issues/8), [#9](https://github.com/KayzenRoot/zeus-agent/issues/9), [#17](https://github.com/KayzenRoot/zeus-agent/issues/17) |
| `M13` | Empacotamento, assinatura, instalação e atualização | P0/P3 | NECESSARY como gate ZEUS-001 #4/#5; release futuro condicionado | `M00`, `M01`, `M12` | [#3](https://github.com/KayzenRoot/zeus-agent/issues/3), [#4](https://github.com/KayzenRoot/zeus-agent/issues/4), [#5](https://github.com/KayzenRoot/zeus-agent/issues/5) |
| `M14` | Operação local estável, backup e recuperação | P3 | IMPORTANT proposto, necessário se DoD de produção local exigir | `M06`, `M09`, `M11`, `M12` | [#10](https://github.com/KayzenRoot/zeus-agent/issues/10), [#17](https://github.com/KayzenRoot/zeus-agent/issues/17) (referências; detalhamento futuro) |
| `M15` | Gate de lançamento e aceitação da produção local | P3 | IMPORTANT proposto (não aprovado) | `M12`, `M13`, `M14` | [#4](https://github.com/KayzenRoot/zeus-agent/issues/4), [#5](https://github.com/KayzenRoot/zeus-agent/issues/5), [#17](https://github.com/KayzenRoot/zeus-agent/issues/17) (referências; decisão futura) |
| `M16` | Implantação remota/VPS e operação 24/7 | P4 | FUTURE/OUT OF CURRENT SCOPE (ADR-003) | `M15` | [#17](https://github.com/KayzenRoot/zeus-agent/issues/17) (futuro, sem WO aprovada) |
| `M17` | Sincronização controlada com Hermes upstream | P4 | IMPORTANT pós ZEUS-001 (issue #7) | `M00`, `M12` | [#7](https://github.com/KayzenRoot/zeus-agent/issues/7) |
| `M18` | Paridade visual e migração compatível de marca | P4 | IMPORTANT pós estabilização (issue #15) | `M00`, `M12` | [#15](https://github.com/KayzenRoot/zeus-agent/issues/15) |
| `M19` | Integrações pessoais de e-mail, WhatsApp e suporte | P4 | IMPORTANT pós-MVP (issue #13) | `M15`, `M07` | [#13](https://github.com/KayzenRoot/zeus-agent/issues/13) |
| `M20` | Capacidades extras e agentes especializados | P4 | FUTURE (issue #16) | `M15` | [#16](https://github.com/KayzenRoot/zeus-agent/issues/16) |
| `M21` | Pesquisa financeira e paper trading | P4 | FUTURE (issue #14); dinheiro real OUT OF SCOPE | `M15`, `M02` | [#14](https://github.com/KayzenRoot/zeus-agent/issues/14) |

**Interpretação de classe:** NECESSARY para ZEUS-001 é vigente quando amparado no Scope/DoD; NECESSARY *proposto para MVP* reflete apenas o roadmap/issues e não amplia a versão atual. IMPORTANT/FUTURE não entra automaticamente. Nenhuma decisão nova é APPROVED pelo catálogo.

## 4. Especificação resumida, critérios de aceite e estado

### M00 | Fundação, upstream MIT e identidade Zeus

- **Fase/classe/risco:** P0 · NECESSARY (ZEUS-001 vigente) · STANDARD/ELEVATED.
- **Pré-requisitos:** nenhum módulo anterior; evidência do gate da fase exigida.
- **Rastreabilidade:** [#1](https://github.com/KayzenRoot/zeus-agent/issues/1), [#17](https://github.com/KayzenRoot/zeus-agent/issues/17).
- **Objetivo:** Preservar ancestralidade do Hermes, avisos MIT, fonte canônica, identidade pública Zeus e aliases retrocompatíveis sem alterar contratos internos.
- **Aceite proposto/contrato de prova:** Histórico/Licença comprovados, assets visíveis revistos, baseline e testes pertinentes registrados por SHA, Work Order ZEUS-001 auditada integralmente.
- **Estado:** IN_PROGRESS: PR #1 Draft; aprovação global ausente.

### M01 | Bootstrap, atualização e Windows/WSL2 seguros

- **Fase/classe/risco:** P0 · NECESSARY (gates ZEUS-001 vigentes) · ELEVATED.
- **Pré-requisitos:** `M00`; evidência do gate da fase exigida.
- **Rastreabilidade:** [#2](https://github.com/KayzenRoot/zeus-agent/issues/2), [#3](https://github.com/KayzenRoot/zeus-agent/issues/3), [#5](https://github.com/KayzenRoot/zeus-agent/issues/5).
- **Objetivo:** Auditar bootstrap, instaladores, guardas fail-closed, atualizações e execução local Windows/WSL2 incluindo gateway, PTY, autenticação e recuperação.
- **Aceite proposto/contrato de prova:** Testes negativos sem rede/escritas indevidas; integração Windows/WSL2 nativa e erro/código de saída documentados; nenhum updater ou instalador Nous reativado.
- **Estado:** GATES PENDENTES; não confundir CI com instalação nativa.

### M02 | Triagem de segurança, autorização e isolamento

- **Fase/classe/risco:** P1 · NECESSARY proposto para MVP (issue #8) · ELEVATED.
- **Pré-requisitos:** `M00`; evidência do gate da fase exigida.
- **Rastreabilidade:** [#8](https://github.com/KayzenRoot/zeus-agent/issues/8).
- **Objetivo:** Verificar alertas CodeQL/Trivy e relatos upstream sobre aprovações, segredos, perfis, toolsets, compaction, limites e integridade de instruções.
- **Aceite proposto/contrato de prova:** Achados com IDs, linha, SHA, origem, aplicabilidade; correções só se comprovadas; testes negativos de acesso cruzado e autorização; zero HIGH/CRITICAL aplicável conhecido antes de liberar conectores.
- **Estado:** PLANNED; triagem somente leitura pode anteceder conclusão de ZEUS-001.

### M03 | Confiabilidade de fila, cron e recuperação

- **Fase/classe/risco:** P1 · NECESSARY proposto para MVP (issue #9) · ELEVATED.
- **Pré-requisitos:** `M00`; evidência do gate da fase exigida.
- **Rastreabilidade:** [#9](https://github.com/KayzenRoot/zeus-agent/issues/9).
- **Objetivo:** Validar estado persistente de tarefas, concorrência, timeout, retry idempotente, deduplicação, cancelamento, limites de custos e comportamento após falha.
- **Aceite proposto/contrato de prova:** Cenários de crash/restart/retry com task IDs; sem duplicação de efeitos externos; limites, stop e tratamento de erro comprovados em testes.
- **Estado:** PLANNED; verificar herança upstream antes de implementar.

### M04 | Inventário GAF/GEF e componentes obsoletos

- **Fase/classe/risco:** P1 · NECESSARY somente inventário (issue #6) · STANDARD/ELEVATED.
- **Pré-requisitos:** `M00`; evidência do gate da fase exigida.
- **Rastreabilidade:** [#6](https://github.com/KayzenRoot/zeus-agent/issues/6).
- **Objetivo:** Localizar dependências e componentes GAF/GEF caso existam, classificar proveniência e uso e proteger bootstraps legítimos.
- **Aceite proposto/contrato de prova:** Inventário por caminho/linha/consumidor e estados VERIFIED_DEAD, PROBABLY_DEAD, DUPLICATE_OR_OBSOLETE, GENERATED_OR_VENDORED ou UNKNOWN; remover apenas VERIFIED_DEAD em WO própria, após baseline.
- **Estado:** PLANNED; ausência ainda não demonstrada integralmente.

### M05 | Runtime local, BYOK, gateway e autenticação

- **Fase/classe/risco:** P2 · NECESSARY proposto para MVP (issue #10) · ELEVATED.
- **Pré-requisitos:** `M00`, `M01`, `M02`, `M03`; evidência do gate da fase exigida.
- **Rastreabilidade:** [#10](https://github.com/KayzenRoot/zeus-agent/issues/10).
- **Objetivo:** Executar um modelo/API LLM compatível com BYOK, login local, gateway loopback/WSL2, chat existente e segredo armazenado fora do Git.
- **Aceite proposto/contrato de prova:** E2E autenticado com modelo real e logs sanitizados, recusa a anônimo, shutdown limpo, portas restritas, sem assinatura proprietária obrigatória.
- **Estado:** PLANNED; implementação somente após ZEUS-001 APPROVED.

### M06 | Sessões, memória, persistência e restauração

- **Fase/classe/risco:** P2 · NECESSARY proposto para MVP (issue #10) · ELEVATED.
- **Pré-requisitos:** `M05`; evidência do gate da fase exigida.
- **Rastreabilidade:** [#10](https://github.com/KayzenRoot/zeus-agent/issues/10).
- **Objetivo:** Validar armazenamento durável por sessão/perfil, migração compatível, recuperação de restart, integridade de estado e política de retenção.
- **Aceite proposto/contrato de prova:** Testes de crash/restauração/concorrência, isolamento negativo entre perfis, backup/restore com dados sintéticos e zero perda silenciosa comprovável.
- **Estado:** PLANNED; não presumir schema novo.

### M07 | Perfis, permissões e aprovação humana

- **Fase/classe/risco:** P2 · NECESSARY proposto para equipe (issues #8/#11) · ELEVATED.
- **Pré-requisitos:** `M05`, `M02`; evidência do gate da fase exigida.
- **Rastreabilidade:** [#8](https://github.com/KayzenRoot/zeus-agent/issues/8), [#11](https://github.com/KayzenRoot/zeus-agent/issues/11).
- **Objetivo:** Definir fronteiras de agente, identidade, configurações/segredos, toolsets mínimos, autorização de ferramentas e aprovação humana para efeitos externos.
- **Aceite proposto/contrato de prova:** Testes negativos de escalada/acesso cruzado, delegação de menor privilégio, deny-by-default, registro e revogação de consentimento por ação.
- **Estado:** PLANNED; sem execução externa por padrão.

### M08 | Equipe de três agentes e delegação auditável

- **Fase/classe/risco:** P2 · NECESSARY proposto para MVP (issue #11) · ELEVATED.
- **Pré-requisitos:** `M06`, `M07`, `M03`; evidência do gate da fase exigida.
- **Rastreabilidade:** [#11](https://github.com/KayzenRoot/zeus-agent/issues/11).
- **Objetivo:** Configurar Orquestrador, Analista e Auditor separados, reusando profiles/delegate_task/Kanban já existentes e evitando duplicar funcionalidades.
- **Aceite proposto/contrato de prova:** Demo E2E objetivo→delegação→evidências→revisão→resposta, auditor capaz de BLOCKED, identidades e custos rastreáveis, resume/retry seguros.
- **Estado:** PLANNED; sem novos 9 agentes automáticos.

### M09 | Fluxo durável de tarefas, Kanban e agendamento

- **Fase/classe/risco:** P2 · NECESSARY proposto para operação MVP (issue #9) · ELEVATED.
- **Pré-requisitos:** `M08`, `M03`; evidência do gate da fase exigida.
- **Rastreabilidade:** [#9](https://github.com/KayzenRoot/zeus-agent/issues/9), [#11](https://github.com/KayzenRoot/zeus-agent/issues/11).
- **Objetivo:** Unificar estados de tarefa, cron local, retomada, retries, concorrência, idempotência, orçamento e kill switch sem duplicar o motor herdado.
- **Aceite proposto/contrato de prova:** Estados terminais corretos; testes end-to-end incluindo crash, loop, retry e pausa; ausência de efeitos duplicados; persistência medida.
- **Estado:** PLANNED; requisitos em issue #9, não implementado por este catálogo.

### M10 | Control Room e dashboard autenticado

- **Fase/classe/risco:** P2 · IMPORTANT proposto para MVP (issue #12) · STANDARD/ELEVATED.
- **Pré-requisitos:** `M08`, `M09`; evidência do gate da fase exigida.
- **Rastreabilidade:** [#12](https://github.com/KayzenRoot/zeus-agent/issues/12).
- **Objetivo:** Reutilizar web/src e apps/desktop/src para mostrar agentes, tarefas, aprovações, falhas e custos, preservando Ink/TUI/PT Y e sem criar segundo chat.
- **Aceite proposto/contrato de prova:** UI responsiva/acessível; estados vazio/erro/carregando; autenticação e permissões; E2E/visual com backend simulado e real; lint/typecheck/build.
- **Estado:** PLANNED; ADR-005 ainda PROPOSED.

### M11 | Observabilidade, histórico, custo e controle operacional

- **Fase/classe/risco:** P2 · IMPORTANT proposto, transversal ao MVP · STANDARD/ELEVATED.
- **Pré-requisitos:** `M09`, `M10`; evidência do gate da fase exigida.
- **Rastreabilidade:** [#9](https://github.com/KayzenRoot/zeus-agent/issues/9), [#12](https://github.com/KayzenRoot/zeus-agent/issues/12).
- **Objetivo:** Expor trilhas redigidas, métricas verificáveis de uso/tokens/custo, limites, health/status, erros e ações pausar/parar sem dados sensíveis.
- **Aceite proposto/contrato de prova:** Logs sem segredos, retenção delimitada, métricas de fonte real, alertas exercitados, falhas recuperáveis e custo rastreável por agente quando disponível.
- **Estado:** PLANNED; métricas estimadas identificadas como estimativas.

### M12 | QA, benchmark e revisão independente

- **Fase/classe/risco:** P0-P4 · NECESSARY como gate transversal, não novo escopo · Conforme incremento: LOW a HIGH_ASSURANCE.
- **Pré-requisitos:** `M00`; evidência do gate da fase exigida.
- **Rastreabilidade:** [#1](https://github.com/KayzenRoot/zeus-agent/issues/1), [#2](https://github.com/KayzenRoot/zeus-agent/issues/2), [#8](https://github.com/KayzenRoot/zeus-agent/issues/8), [#9](https://github.com/KayzenRoot/zeus-agent/issues/9), [#17](https://github.com/KayzenRoot/zeus-agent/issues/17).
- **Objetivo:** Consolidar evidência por SHA, baseline, CI, testes unit/integration/E2E/Windows/WSL2, lint, typecheck, build, segurança, performance, rollback e auditoria independente.
- **Aceite proposto/contrato de prova:** Evidence Bundle verificável, suites aplicáveis PASS ou NOT_RUN justificado, regressões e risco explicitados, nenhum HIGH/CRITICAL conhecido aberto para avanço.
- **Estado:** CICLO OBRIGATÓRIO por incremento; não substitui CI existente.

### M13 | Empacotamento, assinatura, instalação e atualização

- **Fase/classe/risco:** P0/P3 · NECESSARY como gate ZEUS-001 #4/#5; release futuro condicionado · ELEVATED/HIGH_ASSURANCE se distribuição.
- **Pré-requisitos:** `M00`, `M01`, `M12`; evidência do gate da fase exigida.
- **Rastreabilidade:** [#3](https://github.com/KayzenRoot/zeus-agent/issues/3), [#4](https://github.com/KayzenRoot/zeus-agent/issues/4), [#5](https://github.com/KayzenRoot/zeus-agent/issues/5).
- **Objetivo:** Atestar instalador Zeus-owned, MSIX Publisher real, certificados, deep links, DMG Zeus, notarização, feeds próprios, assinatura, verificação de artefatos e rollback.
- **Aceite proposto/contrato de prova:** Provas nativas por plataforma, cadeia de publicação controlada, testes de instalação/desinstalação/recovery e zero ativação de upstream updater sem aprovação; lacunas explicitamente BLOCKED.
- **Estado:** PENDENTE na ZEUS-001; NÃO autorizado publicar ou assinar agora.

### M14 | Operação local estável, backup e recuperação

- **Fase/classe/risco:** P3 · IMPORTANT proposto, necessário se DoD de produção local exigir · ELEVATED.
- **Pré-requisitos:** `M06`, `M09`, `M11`, `M12`; evidência do gate da fase exigida.
- **Rastreabilidade:** [#10](https://github.com/KayzenRoot/zeus-agent/issues/10), [#17](https://github.com/KayzenRoot/zeus-agent/issues/17) (referências; detalhamento futuro).
- **Objetivo:** Planejar runbook local: instalação isolada permitida, health, retenção, backups, restauração, atualização segura, incidentes, suporte e limites de uso.
- **Aceite proposto/contrato de prova:** Teste documentado de restart, backup/restore, observabilidade, recuperação, rollback/roll-forward e metas de disponibilidade explicitamente medidas; nenhum segredo no repositório.
- **Estado:** PLANNED; production readiness depende de ADR/Scope/DoD próprios.

### M15 | Gate de lançamento e aceitação da produção local

- **Fase/classe/risco:** P3 · IMPORTANT proposto (não aprovado) · ELEVATED/HIGH_ASSURANCE quando houver distribuição.
- **Pré-requisitos:** `M12`, `M13`, `M14`; evidência do gate da fase exigida.
- **Rastreabilidade:** [#4](https://github.com/KayzenRoot/zeus-agent/issues/4), [#5](https://github.com/KayzenRoot/zeus-agent/issues/5), [#17](https://github.com/KayzenRoot/zeus-agent/issues/17) (referências; decisão futura).
- **Objetivo:** Separar E2E local funcional de distribuição pública; revisar suporte, risco, conformidade, segurança, titularidade de domínio/certificados e aceite explícito.
- **Aceite proposto/contrato de prova:** Matriz DoD/AC objetiva, Evidence Bundle assinado por SHA, decisão formal de release, sem riscos HIGH/CRITICAL; canais, rollback e ownership confirmados, release somente após autorização distinta.
- **Estado:** CONCEITUAL: não declara produção pronta nem altera gates da ZEUS-001.

### M16 | Implantação remota/VPS e operação 24/7

- **Fase/classe/risco:** P4 · FUTURE/OUT OF CURRENT SCOPE (ADR-003) · ELEVATED.
- **Pré-requisitos:** `M15`; evidência do gate da fase exigida.
- **Rastreabilidade:** [#17](https://github.com/KayzenRoot/zeus-agent/issues/17) (futuro, sem WO aprovada).
- **Objetivo:** Somente se formalmente aprovado: arquitetura de hospedagem, secret store, TLS/rede privada, autenticação, observabilidade, backup, recuperação, provisionamento e custos.
- **Aceite proposto/contrato de prova:** ADR/Scope/DoD e orçamento aprovados, isolamento e segurança testados, prova de rollback/restore e monitoramento; nenhuma ação remota sem autorização específica.
- **Estado:** BLOQUEADO: nenhum deploy/VPS autorizado.

### M17 | Sincronização controlada com Hermes upstream

- **Fase/classe/risco:** P4 · IMPORTANT pós ZEUS-001 (issue #7) · ELEVATED.
- **Pré-requisitos:** `M00`, `M12`; evidência do gate da fase exigida.
- **Rastreabilidade:** [#7](https://github.com/KayzenRoot/zeus-agent/issues/7).
- **Objetivo:** Selecionar releases upstream fixas com diff, licenças, CVEs e contratos; preservar marca, histórico, MIT, armazenamento e aliases.
- **Aceite proposto/contrato de prova:** SHA de origem, changelog, diff, lockfiles, baseline e regressão reproduzíveis; PR/WO isolados, rollback; sem merge automático de upstream.
- **Estado:** PLANNED; exceção somente a correções do WO corrente com prova e autorização.

### M18 | Paridade visual e migração compatível de marca

- **Fase/classe/risco:** P4 · IMPORTANT pós estabilização (issue #15) · STANDARD/ELEVATED.
- **Pré-requisitos:** `M00`, `M12`; evidência do gate da fase exigida.
- **Rastreabilidade:** [#15](https://github.com/KayzenRoot/zeus-agent/issues/15).
- **Objetivo:** Inventariar superfícies públicas Hermes remanescentes sem remover atribuições jurídicas ou renomear identificadores internos indiscriminadamente.
- **Aceite proposto/contrato de prova:** Inventário legal/compatibilidade, snapshots, alias/migração reversível se necessária, testes regressivos e acessibilidade; MIT intacto.
- **Estado:** PLANNED; ADR-004 prevalece.

### M19 | Integrações pessoais de e-mail, WhatsApp e suporte

- **Fase/classe/risco:** P4 · IMPORTANT pós-MVP (issue #13) · ELEVATED.
- **Pré-requisitos:** `M15`, `M07`; evidência do gate da fase exigida.
- **Rastreabilidade:** [#13](https://github.com/KayzenRoot/zeus-agent/issues/13).
- **Objetivo:** Primeiro leitura e rascunho, depois mensagens externas por consentimento explícito; usar APIs autorizadas, segredos isolados, quotas, deduplicação e revogação.
- **Aceite proposto/contrato de prova:** Contratos e custos aprovados, integração sandbox, testes negativos de envio/identidade, aprovação por ação, sem vazamento de segredos ou disparo automático sem consentimento.
- **Estado:** PLANNED; sem contas ou envios ativos.

### M20 | Capacidades extras e agentes especializados

- **Fase/classe/risco:** P4 · FUTURE (issue #16) · STANDARD/ELEVATED conforme capacidade.
- **Pré-requisitos:** `M15`; evidência do gate da fase exigida.
- **Rastreabilidade:** [#16](https://github.com/KayzenRoot/zeus-agent/issues/16).
- **Objetivo:** Avaliar habilidades, UX e ideias upstream uma a uma, reutilizando motor atual e evitando aumento automático de perfis e custos.
- **Aceite proposto/contrato de prova:** Benefício e necessidade demonstrados, compatibilidade e licenças revisadas, WO própria, testes/evidência antes de cada inclusão.
- **Estado:** IDEAS ONLY, não incrementos automaticamente aprovados.

### M21 | Pesquisa financeira e paper trading

- **Fase/classe/risco:** P4 · FUTURE (issue #14); dinheiro real OUT OF SCOPE · HIGH_ASSURANCE se eventual dinheiro real.
- **Pré-requisitos:** `M15`, `M02`; evidência do gate da fase exigida.
- **Rastreabilidade:** [#14](https://github.com/KayzenRoot/zeus-agent/issues/14).
- **Objetivo:** Se aprovado futuramente, prover pesquisa de mercado verificável, backtest sem viés e carteira 100% simulada; credenciais read-only.
- **Aceite proposto/contrato de prova:** Proveniência dos preços, replay determinístico, slippage/taxas, drawdown, limites e kill switch; operações reais requerem nova aprovação e proof obligations independentes.
- **Estado:** IDEAS ONLY; nenhuma negociação real ou API de corretora autorizada.

## 5. Dependências e ordem segura de execução

- **Bloqueio inicial:** P0/ZEUS-001 e issues #2–#5; não autorizar M05+ enquanto ZEUS-001 não obtiver aprovação global. CD08 possui APPROVED individual, não reabrir sem nova evidência.
- **Em paralelo, somente leitura:** M02, M03 e M04 podem analisar incidentes upstream e estabelecer baselines, sem implementar correções fora da WO vigente. Correção de vulnerabilidade comprovada pode seguir Correction Delta permitido da ZEUS-001, sem avançar dependências.
- **MVP:** M05 → M06/M07 → M08 → M09 → M10/M11, com M12 como gate contínuo. A ordem é candidata, não cronograma aprovado.
- **Distribuição:** M13 contém obrigações atuais da ZEUS-001 e possíveis passos futuros; M14/M15 são propostas para operação local sustentada, nunca licença para instalar/publicar.
- **Pós-MVP opcional:** M16–M21 somente após novo Scope/DoD/ADR, análise de custos/licenças e Work Order próprios. A atualização upstream M17 é revisão controlada, não `git pull` cego.

## 6. Matriz mínima de evidência por gate

| Gate | Prova obrigatória | Falha ou ausência |
|---|---|---|
| G0 - Context Lock | base/head SHA, fingerprints críticos, diff e fontes aprovadas | STALE/BLOCKED, nenhuma execução |
| G1 - Implementação funcional | testes direcionados, baseline, contratos, logs redigidos e smoke adequado | CORRECTION REQUIRED |
| G2 - Segurança/isolamento | autenticação/segredos/RBAC, ferramenta com menor privilégio, scanner e análise de aplicabilidade; riscos HIGH/CRITICAL resolvidos | BLOCKED |
| G3 - Qualidade transversal | unit/integration, lint, typecheck, build, E2E relevante e CI para HEAD exato; benchmarks quando aplicável | NOT_RUN justificado ou BLOCKED segundo DoD |
| G4 - Plataforma nativa | Windows/WSL2 com gateway, modelo/PTY/auth; assinatura/instalação/MSIX/DMG e restore quando aplicável | não promover release |
| G5 - Operação local | runbook, health, logs, backup/restore, incidentes, rollback e limites mensurados | não chamar produção pronta |
| G6 - Aprovação de lançamento | decisão formal do owner, auditoria independente, autorização de custos, revisão de escopo e checkout/release seguro | NO-GO release/deploy/VPS |

**Vereditos:** APPROVED (incremento específico e evidência objetiva), CORRECTION REQUIRED (Correction Delta na mesma WO/PR), BLOCKED (depende de acesso, risco ou decisão), NOT_RUN/NÃO VERIFICADO (não é PASS). Checkpoint Delta é proposta do executor; só é promovido após auditoria, jamais sozinho.

## 7. Operação e suporte em produção (PLANEJAMENTO, NÃO IMPLEMENTAÇÃO)

- **Ambiente local:** host Windows/WSL2 com perfil dedicado e acesso loopback por padrão; credenciais BYOK fora do Git; não publicar endpoints de dashboard sem autenticação e barreiras.
- **Proteção dos dados:** sessões, memória, arquivo de configuração, logs, backups, retenção e exclusão precisam de política e testes. Sem backups reais neste documento.
- **Continuidade:** startup/shutdown, upgrades assinados e rollback/roll-forward, restart após crash, filas reprocessadas de modo idempotente, manutenção e pause/kill switch; só implementar após aprovar a WO correspondente.
- **Sinais operacionais:** health/readiness, erro, execução por agente, consumo/token verificável, fila, cron, alertas e auditoria sem segredos. Definir métricas/SLI/SLO por versão, sem inventar percentuais.
- **Distribuição:** origem e licença das dependências, SBOM quando aplicável, artefatos com hashes/assinatura, Publisher válido e rollback testado por SO. Publish e updater permanecem bloqueados.
- **VPS/24×7 opcional:** threat model, TLS, exposição de rede, custos/quotas, criptografia e recuperação antes de qualquer habilitação. **Nenhum contato com a VPS nesta PR.**

## 8. Handoff restrito para Zcode (não executar módulos futuros)

1. Leia `checkpoint → decisions → scope → DoD → architecture → requirements → ZEUS-001 WO → este catálogo → issue #17`; derive Context Lock do Git real.
2. Revalide `main`, PR #1 e checks. Se PR #1 exigir correção, gere **somente** o próximo Correction Delta conforme a WO vigente; não avance por ordem numérica de módulos.
3. O executor deve inspecionar repositório, implementar apenas WO expressamente autorizada, testar, registrar Evidence Bundle, abrir/atualizar PR Draft, auditar e entregar veredito em português. Sem autoaprovação/automerge.
4. Não marcar `DOCUMENTED/PLANNED` como `IMPLEMENTED`, `TESTED`, `DEPLOYED` ou `APPROVED`. Não editar fontes canônicas em consequência desta PR; somente após decisão de implementação aprovada por auditoria.

## 9. Work Order documental ZEUS-DOC-CAT-001

- **OBJECTIVE:** registrar mapa completo de planejamento e operação de M00–M21 até produção local, distinguindo opções futuras.
- **CONTEXT:** `main@23145d788a39453fcb6d81a6a53415a822b4655f`, ZEUS-001 Draft@`7936faabc2b4820a958f8c6e759499614ce674a0`, roadmap #17, fontes e fingerprints da seção 1.
- **SCOPE:** adicionar somente este arquivo Markdown em branch isolada e PR Draft, com Evidence Bundle em descrição/artefato externo.
- **OUT OF SCOPE:** código, package/lockfiles, Source Pack existente, checkpoint/ADRs, testes runtime, decisões aprovadas, comentários em outras issues/PRs, merge, deploy, release, VPS, gastos.
- **FILES/SOURCES TO READ:** hierarquia canônica da seção 1, Work Order ZEUS-001, issue #17 e issues #2–#16.
- **REQUIREMENTS/ARCHITECTURE RULES:** R1–R8; MIT/Nous; brand compatível; local-first; reutilizar Ink/TUI/PTY e web existentes; sem segundo chat.
- **CONSTRAINTS:** uma adição documental; não produzir mudanças invisíveis, nunca reescrever histórico ou alterar políticas do GitHub.
- **ACCEPTANCE CRITERIA:** M00–M21 únicos, fases P0–P4, dependências acíclicas, estados honestos, rastreio #2–#17, produção/ops coberta, stop conditions e autoridade canônica preservados.
- **TESTS:** verificação estrutural estática do documento, referência de issues, path allowlist, compare base/head e leitura de volta; lint/build/runtime = NOT_RUN, porque nenhuma linha de produto foi alterada.
- **DELIVERABLES:** `product-modules.md`, PR Draft e Evidence Bundle do diff; Checkpoint Delta = NONE.
- **REVIEW FORMAT:** PT-BR, fatos por SHA, riscos, `APPROVED` documental ou `CORRECTION REQUIRED/BLOCKED`; não emitir aprovação de ZEUS-001 ou do MVP.
- **STOP CONDITION:** sem merge, deploy, release, VPS ou autorização automática para o módulo seguinte; se drift, interromper e recompilar contexto.

## 10. STOP explícito

Este catálogo é **documentação proposta**. Não altera as decisões `ADR-001`–`ADR-004`, não promove `ADR-005`, não conclui ZEUS-001, não substitui provas nativas, não habilita instalador/update, não autoriza integração externa, operações financeiras, produção pública, VPS, compras ou assinatura. **A PR #1 permanece independente e Draft; CD08 conserva APPROVED individual.**
