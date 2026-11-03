# ZEUS-CLOUD-004 — Gate de assinatura no runtime e ativação do desktop

**Data:** 2026-11-03
**Escopo:** camadas 2 e 3 do gate comercial. Test mode; sem cobrança real, deploy ou live mode.
**Status:** implementado e verificado localmente; sem aprovação independente.

## Entregue

### Cloud (código de ativação)
- `device_codes` em SQLite: hash do código, `user_id`, `device_id`, expiração de 10 min e uso
  único.
- `POST /api/device/authorize` (Bearer Clerk): exige assinatura ativa e devolve um código de uso
  único vinculado ao `device_id`.
- `POST /api/device/exchange`: consome o código atomicamente, recheca a assinatura e emite o token
  Ed25519. Código inválido/expirado/reutilizado/dispositivo errado falha fechado.

### Runtime Python
- `zeus_entitlement.py`: verifica assinatura Ed25519, `iss=zeus-cloud`, `device_id` local e `exp`;
  lê/grava `<HERMES_HOME>/zeus-entitlement.json` com 0600 e `atomic_json_write`.
- Gate no início de `AIAgent.run_conversation` (`agent/turn_facade.py`), antes do lease, do prompt
  e de qualquer chamada ao modelo; devolve recusa tipada `entitlement_required` sem tocar no
  prefixo cacheado.
- `ZEUS_DEV_UNLOCK=1` estrito (checado em tempo de chamada) para desenvolvimento; a suíte de testes
  o define e os testes de recusa o removem.
- `hermes entitlement status|activate|device-id` para inspeção e ativação manual.

### Desktop
- `apps/desktop/electron/entitlement.ts`: verificação Ed25519 local (Node `crypto`), geração de
  `device_id`, troca do código no cloud e persistência 0600.
- IPC `zeus:entitlement:status|activate|open` + preload/typings.
- Overlay bloqueante “Ative sua assinatura” com botão para o site e campo de código.
- Deep link `zeus://auth/callback?code=…&device_id=…` reconhecido por
  `resolveDeepLinkAction` e trocado pelo store de entitlement.
- Landing: painel de ativação quando `?device_id=` está presente; mostra o código, abre o app e
  explica o comando CLI.

## Evidência local

- `tests/cloud/test_cloud_service.py` — **25/25 PASS** (token, device codes, expiração, reuso,
  device binding, assinatura cancelada, webhooks).
- `tests/test_zeus_entitlement.py` — **7/7 PASS** (token válido/expirado/adulterado, issuer,
  device mismatch, dev unlock, persistência, recusa tipada no turno).
- Fluxo real no PC: usuário ativo no SQLite → `/api/device/authorize` 200 → `device-id` local →
  `hermes entitlement activate <code>` 200 → `hermes entitlement status` ativo com plano annual e
  expiração de 7 dias, verificado pela chave pública versionada. Nenhum segredo impresso.
- Desktop empacotado (`release/win-unpacked`, Electron 44.9.3) no PC: sem token, o overlay
  “Ative sua assinatura” bloqueia o chat; com um código novo, `zeus://auth/callback?code=…` foi
  entregue ao app, o main gravou `zeus-entitlement.json` (0600, 495 bytes) e o overlay sumiu sem
  reiniciar o processo. O runtime relê o arquivo como `active`, plano annual, 10 seats.
- `tests/hermes_cli/test_finite_chat_delegation.py` — **6/6 PASS** com o gate ativo.
- Desktop: `npm run typecheck` e `npm run lint` (0 erros); `entitlement.test.ts` **4/4**;
  `deeplink-routes.test.ts` **8/8**.

## Residual

1. O gateway de mensageria ainda não recusa o boot sem assinatura; o gate cobre os turnos e o
   desktop. Um gate de boot pode ser adicionado sem bloquear a UI de ativação.
2. Revogação/denylist online, rotação por `kid` e reconciliação periódica ainda não existem.
3. O E2E visual do desktop foi validado no PC (overlay → deep link → app liberado); o pacote
   segue UNSIGNED e o gate de boot do gateway fica para o próximo ciclo.
