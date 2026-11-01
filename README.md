<p align="center">
  <img src="assets/zeus-banner.svg" alt="Zeus Agent" width="100%" />
</p>

# Zeus Agent ⚡

**Agente de IA com interface visual, desenvolvido primeiro no computador local.**

[Repositório Zeus](https://github.com/KayzenRoot/zeus-agent) · [PR de integração e identidade #1](https://github.com/KayzenRoot/zeus-agent/pull/1) · [Documentação do projeto](.zeus/docs/README.md)

> **Status: desenvolvimento.** A importação do código e histórico upstream e a primeira camada de identidade Zeus estão na branch `work/ZEUS-001-import-brand`. Não há ainda versão Zeus integralmente testada ou publicada para instalação em produção.

## O que estamos construindo

Zeus Agent é uma evolução personalizada do projeto de código aberto Hermes Agent, com identidade própria e uma central visual no navegador para acompanhar e supervisionar agentes, suas tarefas e ferramentas.

A arquitetura mantém o núcleo do agente e as integrações atuais enquanto substitui gradualmente marca, componentes visuais e experiência de uso. O dashboard existente do upstream é nosso ponto de partida, não será construído um segundo chat incompatível.

### Entregue na branch de trabalho

- Código e histórico original do Hermes importados com rastreabilidade Git e licença MIT preservada.
- Primeiros SVGs originais do Zeus: ícone de raio e wordmark.
- Título, favicon e cabeçalho do dashboard adaptados para Zeus.
- Primeira conversão de imagens e mensagens visíveis para web e desktop.
- Testes automáticos de branding, TypeScript, lint e build do dashboard configurados no GitHub Actions.

**Em andamento:** revisão de todos os elementos de interface, marca e documentação; validação local Windows/WSL2; correções de bugs e evolução do monitor de agentes. O trabalho só recebe status de aprovado quando existir evidência de funcionamento e testes suficientes.

## Desenvolvimento local (Windows / WSL2)

Não use os instaladores oficiais da Nous Research para instalar o *Zeus*: eles instalam/atualizam o software original, não a nossa distribuição.

Para obter o código que estamos desenvolvendo:

```powershell
git clone --branch work/ZEUS-001-import-brand https://github.com/KayzenRoot/zeus-agent.git
cd zeus-agent
```

Com Node.js 24 e npm compatíveis, execute as verificações de frontend utilizadas pelo CI:

```powershell
npm ci
npm run --workspace web check
npm run --workspace web build
```

Para os testes do branding (Python 3):

```powershell
python -m unittest discover -s .zeus/tests -p "test_*.py"
```

Esses comandos **validam código e build**, mas não equivalem a testar uma sessão real com modelo e gateway. Para o chat embutido do dashboard, o upstream depende de PTY POSIX: execute o backend no WSL2 até existir suporte nativo equivalente. O ambiente Python deve seguir o gerenciador definido pelo upstream, sem instalar pacotes aleatórios globalmente.

**Compatibilidade temporária:** comandos `hermes`, nomes de pacotes, variáveis `HERMES_*`, caminhos de dados, endpoints e chaves de configuração podem continuar com nomes originais para não quebrar integrações. A interface pública deverá usar a marca Zeus. Não renomeie esses identificadores sem migração e testes.

**Proteção de atualização:** até existir um canal Zeus com origem, assinatura e rollback auditados, `zeus update` e `hermes update` são bloqueados preventivamente neste checkout; a interface desktop também recusa consulta, aplicação e troca de canal, e novos builds não embutem feeds de atualização. Isso evita importar uma versão upstream não revisada para o Zeus. Para consultar commits da própria branch, use `git fetch origin` e faça revisão antes de qualquer integração. Nunca execute o instalador ou o atualizador oficial do Hermes para "atualizar" o Zeus.

## Segurança e licença

O repositório é **público por decisão do proprietário**. Nunca envie `.env` com credenciais, tokens, logs de sessões, chaves, arquivos locais de estado ou dados particulares.

A base original é [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent), licenciada sob a **MIT License**. A licença e o aviso de copyright da Nous Research estão preservados no arquivo [LICENSE](LICENSE). Zeus Agent é uma personalização independente; a referência à origem não implica patrocínio ou endosso da Nous Research.

## Planejamento e evidências

- [Escopo e requisitos](.zeus/docs/scope.md)
- [Arquitetura](.zeus/docs/architecture.md)
- [Segurança](.zeus/docs/security.md)
- [Definition of Done](.zeus/docs/definition-of-done.md)
- [Checkpoint verificado](.zeus/docs/checkpoint.md)
- [Work Order ZEUS-001](.zeus/docs/work-orders/ZEUS-001.md)
- [Matriz de validação Windows/WSL2 e distribuição](.zeus/docs/windows-validation.md)

**Próxima etapa:** terminar a identidade e a validação local da ZEUS-001 antes de integrar na `main`. Implantação na VPS está fora do escopo atual.
