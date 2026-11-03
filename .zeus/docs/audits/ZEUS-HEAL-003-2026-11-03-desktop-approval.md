# ZEUS-HEAL-003 — Aprovação nativa no desktop

**Data:** 2026-11-03
**Escopo:** terceira camada do #50; distribuição de skills com revisão fica para a próxima camada.
**Status:** implementado e verificado localmente; sem aprovação independente.

## Entregue

- `apps/desktop/electron/heal-approval.ts`: watcher de `<HERMES_HOME>/heal-proposals/` a cada 2 s,
  somente arquivos `pending` não expirados, ID hexadecimal e nome de arquivo coincidente.
- Modal nativo do app com ação, motivo, até três sinais, rollback e horário de expiração.
  `Aprovar` é o único caminho que executa; fechar/cancelar/rejeitar registra rejeição e não executa.
- A aprovação reutiliza o gate do CLI: spawn em PTY de `zeus heal approve <id>`, espera o prompt
  `Type APPROVE to continue:` e só então escreve `APPROVE`. Nada é executado antes do clique.
- Janela oculta/inexistente é ignorada (a proposta continua pendente); backend local ausente falha
  fechado e registra no log do app.
- `backend-identity.ts`: extração de `processIdentityMatches`/`backendParentMatches` do `main.ts`
  para compensar o file-lines ratchet da facade.
- Docs em `website/docs/reference/cli-commands.md` § `hermes heal`.

## Verificação

- `apps/desktop/electron/heal-approval.test.ts` — **7/7 PASS** (parse, BOM, arquivo errado,
  expiração, cópia do modal, aprovação, rejeição, janela/backend ausente, escrita do APPROVE).
- `npx tsc -p tsconfig.electron.json --noEmit` — PASS (sem saída).
- ESLint dos arquivos alterados — **0 errors**.
- `python scripts/check --only health` — PASS após a extração.
- PTY real no Windows: Python imprimiu o prompt, o runner escreveu `APPROVE`, o processo recebeu
  `got=APPROVE` e saiu 0.

## Residual

1. Distribuição/aprendizado de skills com revisão do curator fica para a próxima camada.
2. A criação da proposta continua vindo do CLI/agente; não há botão de “propor” no renderer nesta
   camada (superfície mínima, sem novas strings de i18n).
3. Apenas `restart-gateway` é executável; ações destrutivas/rede/credenciais/deploy seguem fora de
   escopo. Nenhuma mudança de prompt, toolsets ou cache.
