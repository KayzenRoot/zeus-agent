# ZEUS | Runbook de produção na VPS Oracle Cloud (ADR-006)

> **Autorização:** ADR-006 (owner, 2026-11-01; provider corrigido para Oracle Cloud no mesmo dia).
> Nenhuma etapa remota executa sem a autorização do owner para aquela etapa. Segredos vivem
> só no host. Nada deste documento habilita o instalador/updater da Nous ou distribuição
> pública (#4/#20 continuam gates separados).

## 0. Pré-condições

- [ ] Produção local validada (backup/restore testado — M14/#19; dashboard autenticado).
- [ ] Acesso SSH do owner ao host com **chave** (senha desabilitada). Chave nunca colada em chat.
- [ ] **Oracle Cloud Security List / NSG**: apenas 22/tcp aberto para seu IP. O dashboard NUNCA fica público — acesso por túnel SSH (seção 5).
- [ ] Distro confirmada no primeiro acesso: **Ubuntu 22.04/24.04** ou **Oracle Linux** (seção 2 cobre ambas).
- [ ] Backup do estado antes de qualquer mudança (seção 6).

## 1. Identidade e compatibilidade

- A imagem é construída **a partir do checkout Zeus** (main auditado). Nenhum download da Nous.
- Identificadores internos `hermes_*` preservados por compatibilidade (R4/ADR-004) — não renomear à mão.
- O container roda com `/init` do s6-overlay como PID 1. Não trocar o entrypoint.

## 2. Preparo do host (uma vez)

### Ubuntu
```bash
sudo apt update && sudo apt install -y docker.io docker-compose-v2 git
sudo systemctl enable --now docker
sudo usermod -aG docker $USER   # re-login para aplicar
```

### Oracle Linux (RHEL-family)
```bash
sudo dnf install -y docker-ce git || sudo dnf install -y docker git
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

### ⚠️ Armadilha Oracle Cloud (famosa): firewall DENTRO do host
As imagens Ubuntu da Oracle vêm com `iptables` já populado com REJECT além do
Security List — abrir a porta no console NÃO basta. Se o dashboard ou algo mais
precisar de porta externa (recomendado: nada — túnel SSH), é preciso liberar no
iptables/persistent. Para o desenho deste runbook (túnel SSH apenas) **nenhuma
porta extra precisa ser aberta** — o que é a configuração mais segura.

## 3. Deploy

```bash
git clone https://github.com/KayzenRoot/zeus-agent.git zeus-agent
cd zeus-agent
git rev-parse HEAD   # registrar o SHA do deploy
export HERMES_UID=$(id -u) HERMES_GID=$(id -g)
docker compose build           # imagem a partir do checkout local (sem registry público)
docker compose up -d
docker logs -f hermes          # acompanhar boot do s6 (gateway + dashboard)
```

- Estado do agente: volume `~/.hermes:/opt/data` no host (fora do container — backup trivial, seção 6).
- Dashboard: **bind 127.0.0.1 dentro do host** por padrão — nunca editar para `0.0.0.0`.

## 4. Configuração BYOK (DeepSeek v4.1 Flash)

```bash
docker exec -it hermes hermes setup    # wizard dentro do container; a chave grava em /opt/data (= ~/.hermes no host)
```

- Provider: **DeepSeek** (perfil first-class; contrato thinking V4 tratado no código). Id canônico pós-refresh: `deepseek-flash` (o perfil também cobre ids `deepseek-v4*`).
- A chave fica em `~/.hermes/.env`/keyring **no host** — nunca em Git, nunca em chat.
- Smoke: `docker exec -it hermes hermes --version` e um `hermes chat -q "ping"`.

## 5. Acesso ao dashboard (NUNCA público)

```bash
ssh -L 9119:127.0.0.1:9119 <vps>   # túnel do owner
# navegador local: http://127.0.0.1:9119
```

- Configurar auth provider (senha/token) no primeiro acesso.

## 6. Backup / restore (M14)

```bash
python3 scripts/zeus_backup.py --home ~/.hermes --out /var/backups/zeus   # snapshot sqlite-safe + arquivos
# restore: parar container → restaurar → subir → conferir sessions/config
```

- Agendar: `cron` diário no host + retenção (`--retention-days`).
- Testar restore com dados sintéticos ANTES do primeiro dia de produção (M14/#19).
- Enviar uma cópia do backup para fora do host (ex.: download local via scp) — backup só no mesmo host não é backup.

## 7. Atualização controlada (não existe auto-update — proposital)

```bash
cd zeus-agent && git fetch origin && git log HEAD..origin/main --oneline   # revisar
git checkout origin/main && git rev-parse HEAD   # registrar novo SHA
docker compose build && docker compose up -d
docker exec -it hermes hermes --version && curl -s http://127.0.0.1:9119/api/health
```

- Rollback: `git checkout <SHA-anterior> && docker compose build && up -d` (estado do agente vive fora da imagem — rollback de código não toca dados).

## 8. Hardening (checklist mínimo de produção)

- [ ] Security List/NSG: só 22; host iptables conferido (armadilha acima); dashboard/health apenas via túnel.
- [ ] SSH: somente chaves; `PasswordAuthentication no`; root login desabilitado.
- [ ] Auth provider configurado no dashboard (senha/token).
- [ ] Nenhum segredo em env do compose além do necessário; `.env` do compose fora do Git.
- [ ] `docker logs hermes` + `~/.hermes/logs/` sem segredos (rotina de conferência).
- [ ] Atualizações do host (`apt upgrade`/`dnf update`) em janela de manutenção com backup prévio.
- [ ] Health: `GET /api/health` → 200 (liveness) após cada operação.

## 9. Rollback de desastre

1. `docker compose down` (estado do agente fica no host).
2. Restaurar `~/.hermes` do último backup (seção 6).
3. `git checkout <SHA-bom> && docker compose build && up -d`.
4. Validar health + uma sessão.

## 10. Estados honestos

| Etapa | Estado |
|---|---|
| Kit documentado | ✅ este runbook (2026-11-01, provider Oracle Cloud) |
| Produção local validada | ✅ Stage 1/2 + WSL2 parcial (ver readiness report) |
| Backup/restore implementado e testado | ✅ `scripts/zeus_backup.py` + testes (M14) |
| Execução na VPS | ⏳ aguarda owner: distro confirmada, acesso, autorização por etapa |
| Distribuição pública assinada | 🔴 NO-GO (#4/#20) |
