<p align="center">
  <img src="assets/zeus-banner.svg" alt="Zeus Agent" width="100%" />
</p>

# Zeus Agent ⚡

**Agente de IA local-first com constelação de agentes, orquestração e assinatura.**

[Repositório](https://github.com/KayzenRoot/zeus-agent) · [Documentação](.zeus/docs/README.md) · [Roadmap](.zeus/docs/product-roadmap-experience-v2.md)

> **Status:** produção local em evolução. O runtime, o dashboard, o instalador e o gate de assinatura
> têm evidência de testes; release assinada (MSIX/DMG) e live mode seguem owner-gated.

## O que está pronto

- **Runtime Zeus** com agente principal, subagentes, memória, skills, cron, Kanban e gateway.
- **Dashboard/constelação** com tema escuro, avatares e linhas de energia entre agentes.
- **Gate de assinatura**: entitlement Ed25519 vinculado ao dispositivo, com grace offline.
- **Zeus Cloud** (test mode): Clerk (e-mail/telefone), Stripe Checkout com trial de 2 dias,
  Customer Portal e gestão de dispositivos.
- **Instalador Zeus-owned** (`scripts/zeus-install.*`) com root isolado, launcher rápido e
  desinstalação que preserva dados.
- **Desktop Electron 44.9.3** com marca Zeus, onboarding por provedor e ativação por
  `zeus://auth/callback`.

## Desenvolvimento local

```powershell
# frontend
npm ci
npm run --workspace web check
npm run --workspace web build

# testes Python (runner canônico, ambiente isolado)
scripts/run_tests.sh

# gate de lint/saúde
python scripts/check
```

### Instalação local

```powershell
# Windows
.\scripts\zeus-install.ps1 --plan
.\scripts\zeus-install.ps1
.\scripts\zeus-install.ps1 --uninstall --yes
```

```bash
# Linux/WSL2/macOS
./scripts/zeus-install.sh --plan
./scripts/zeus-install.sh
./scripts/zeus-install.sh --uninstall --yes
```

O root padrão é `%LOCALAPPDATA%\ZeusAgent` (Windows) ou `$XDG_DATA_HOME/zeus-agent` (POSIX);
o home do runtime fica em `<root>/home`, isolado. O recibo em `<root>/receipt.json` registra
checkout, SHA, origem, launcher, digests e caminhos; a desinstalação preserva sessões/memórias
sem `--purge-data`.

### Zeus Cloud (test mode)

```bash
python -m cloud.service                 # API em 127.0.0.1:9121
python -m http.server 9120 --directory cloud/site
```

Chaves ficam apenas no `.env` do home; nunca no cliente. Veja [`cloud/README.md`](cloud/README.md).

## Compatibilidade

A marca pública é **Zeus**. O comando oficial é `zeus`; `hermes` permanece como alias e os
identificadores internos do upstream (pacotes, variáveis de ambiente e caminhos de dados)
continuam por compatibilidade. Não os renomeie sem uma migração testada.

`zeus update` e o updater upstream são bloqueados até existir um canal Zeus assinado com rollback.

## Segurança e licença

O repositório é **público por decisão do proprietário**. Nunca envie `.env` com credenciais,
tokens, logs de sessão, chaves ou dados particulares.

A base upstream é um projeto open source sob **MIT License**; o aviso de copyright original está
preservado em [LICENSE](LICENSE). Zeus Agent é uma personalização independente e não implica
patrocínio ou endosso do projeto original.
