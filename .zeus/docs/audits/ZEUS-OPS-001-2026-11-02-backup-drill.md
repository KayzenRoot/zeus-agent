# ZEUS-OPS-001 | Drill de backup/restore e metas locais — 2026-11-02

> Executa o contrato de prova da #19 (M14) com **dados sintéticos em home descartável**.
> VPS permanece fora de escopo (execução no host real é owner-gated em #20/#4).

## 1. Bug real encontrado e corrigido

O backup grava bancos sob o namespace interno `dbs/` (para não colidir com arquivos do home).
O restore, porém, mantinha esse prefixo: `dbs/state.db` era restaurado em
`<home>/dbs/state.db`, mas o app lê `<home>/state.db` e `<home>/profiles/<p>/state.db`.
Resultado: **recuperação silenciosamente incompleta** — o home voltava sem as sessões.

O teste existente havia sido ajustado para o caminho errado (`target/dbs/state.db`), então
passava. Corrigido:

- `scripts/zeus_backup.py::restore_backup` remove o prefixo `dbs/` antes do restore
  (`dbs/state.db` → `<home>/state.db`; `dbs/profiles/p/state.db` → `<home>/profiles/p/state.db`).
- `tests/scripts/test_zeus_backup.py` agora cobre o DB raiz **e** o DB de um perfil, e exige
  que `<home>/dbs` **não** exista após o restore. 3/3 PASS.

## 2. Drill (home descartável, dados sintéticos)

Home semeado:

- `state.db`: 3 sessões + 10 mensagens;
- `profiles/work/state.db`: 1 linha;
- `memories/MEMORY.md` (hash registrado), `config.yaml`, `sessions/abc.json`, `logs/zeus.log`;
- `cache/` e `image_cache/` com arquivos que **não** devem entrar no backup.

Fluxo: backup → apagar o home → restore → verificar.

| Métrica | Resultado |
|---|---|
| Backup | exit 0, **0,23 s**, arquivo de 1.455 bytes |
| Conteúdo | `dbs/state.db`, `dbs/profiles/work/state.db`, memórias, config, sessões e logs presentes; `cache/` e `image_cache/` excluídos |
| Restore | exit 0, **0,24 s** |
| Integridade | `PRAGMA integrity_check` = `ok` |
| Dados | 3 sessões, 10 mensagens, perfil `work` restaurado, hash das memórias idêntico |
| Caminhos | DBs nas rotas reais do app; nenhum `<home>/dbs` remanescente |
| Voláteis | não ressuscitados no restore |

Todas as 15 verificações: **ALL_OK**.

## 3. Metas explícitas (locais)

| Item | Meta | Como é medida |
|---|---|---|
| **RPO** | último backup bem-sucedido; backup obrigatório antes de update e recomendado diário (`scripts/zeus_backup.py --out <dir>`) | mtime do arquivo `zeus-home-backup-*.zip` |
| **RTO** | restore abaixo de 60 s para um home local típico | `restore_seconds` no drill; cresce com o tamanho do `state.db` |
| **Retenção** | 30 dias por padrão (`--retention-days`), aplicada a cada backup | contagem de arquivos após `prune_backups` |
| **Disponibilidade** | dashboard responde `GET /api/health` = 200; restart documentado | health probe + `hermes dashboard --status` |
| **Update seguro** | `scripts/zeus_update.sh --check` antes; `--apply` registra SHA, recompõe, checa `/api/health` e faz rollback automático | log do script |
| **Segredos** | nenhum segredo no Git; backups contêm `.env` e devem ser tratados como segredo | revisão + `.gitignore` |

## 4. Runbook de incidente (local)

1. **Parar novas tarefas**: `hermes pause --reason "<incidente>"` (in-flight termina sozinho).
2. **Preservar evidência**: copiar `logs/` e o `state.db` atual para um diretório fora do home.
3. **Backup do estado atual** (mesmo que degradado): `python scripts/zeus_backup.py --label pre-recovery`.
4. **Restaurar** o último backup íntegro: `python scripts/zeus_backup.py --restore <zip> --home <home> --yes`.
5. **Subir o dashboard** e checar `/api/health`; rodar `hermes kanban dispatch` para retomar tarefas.
6. **Resume**: `hermes resume`.
7. **Registrar**: horário, RTO real, causa e backup usado.

## 5. Residual

- Drill com **dados reais** e restore no host VPS continuam owner-gated (#20/#4); este drill
  prova o mecanismo, não o hardware remoto.
- O restore não valida esquema/versão do app; um backup antigo restaurado sobre um app novo
  depende das migrations do próprio Hermes (comportamento inalterado).
