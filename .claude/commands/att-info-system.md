---
description: Sincronização completa do sistema — versões, docs, sbwaa.py, ui.py, git commit + push + release.
---

# /att-info-system

Execute este protocolo de fechamento de sessão de forma completa e sequencial.
**Não pule nenhuma fase. Não resuma sem agir.**

---

## FASE 1 — LEITURA DE ESTADO (obrigatório antes de qualquer ação)

Execute em paralelo:

1. Leia `VERSION.md` → extraia a **versão canônica** (ex: `v2.13.1`) e os módulos com suas versões
2. Execute `git log --oneline -20` → identifique o histórico recente
3. Execute `git diff HEAD` → veja o que está pendente de commit (staged + unstaged)
4. Execute `git status --short` → liste os arquivos com mudanças
5. Leia as primeiras 10 linhas de cada doc para extrair a versão atual:
   - `README.md`
   - `docs/GUIA-COMANDOS.md`
   - `docs/SBWAA-REFERENCIA.md`
   - `docs/SBWAA-WORKFLOW.md`
   - `docs/SBWAA-APRESENTACAO.md` (frontmatter `versao:` e `atualizado:`)
   - `docs/SBWAA-MASTER-BLUEPRINT.md`
   - `docs/SBWAA-LOGO.md`
   - `CHANGELOG.md` (primeiras 20 linhas — verificar se tem entrada para a versão canônica)

Após a leitura, construa internamente:
- **Lista de docs desatualizados** (versão diferente da canônica)
- **Resumo das mudanças da sessão** a partir do git log e git diff:
  - Que módulos foram tocados? (`investments`, `heartbeat`, `knowledge-base`, `interface`)
  - Novos comandos adicionados ou removidos?
  - Novos fluxos ou comportamentos?
  - Bugs corrigidos?

---

## FASE 2 — DIAGNÓSTICO DE VERSÃO

Regras para decidir se é necessário bumpar VERSION.md:

- Se `git diff HEAD` mostra mudanças **substantivas não commitadas** (código, scripts, agentes, comandos) que não estão refletidas na versão canônica → bumpar:
  - Nova feature, novo agente, novo comando → **MINOR** (`x.Y.0`)
  - Correção de bug, ajuste, refinamento → **PATCH** (`x.y.Z`)
  - Mudança estrutural (nova arquitetura, novo módulo) → **MAJOR** (`X.0.0`)
- Se as mudanças pendentes são apenas atualizações de docs → **não bumpar**, apenas sincronizar

Se for necessário bumpar: atualize `VERSION.md` primeiro (versão global + módulo afetado), depois prossiga para as fases seguintes usando a nova versão como canônica.

---

## FASE 3 — CHANGELOG

Verifique se `CHANGELOG.md` tem uma entrada para a versão canônica.

- Se **não tiver**: crie a entrada no topo do CHANGELOG com:
  - Data: hoje (`2026-05-29` ou use `git log -1 --format=%ci` para data do último commit)
  - Versão canônica
  - Seções `Added` / `Fixed` / `Changed` / `Removed` conforme o que foi identificado na Fase 1
  - Conteúdo baseado no `git log` e `git diff` — seja específico, não genérico
- Se **já tiver**: verifique se está completa. Complemente se necessário.

---

## FASE 4 — ATUALIZAÇÕES MECÂNICAS DE VERSÃO

Para cada arquivo com versão desatualizada identificado na Fase 1, atualize a string de versão:

| Arquivo | Onde atualizar |
|---------|---------------|
| `README.md` | Linha com `**v` no topo |
| `docs/GUIA-COMANDOS.md` | Linha `**Versão: vX.Y.Z**` |
| `docs/SBWAA-REFERENCIA.md` | Linha `**Versão: vX.Y.Z**` |
| `docs/SBWAA-WORKFLOW.md` | Linha `**Versão: vX.Y.Z**` |
| `docs/SBWAA-APRESENTACAO.md` | Frontmatter `versao: vX.Y.Z` e `atualizado: YYYY-MM-DD` |
| `docs/SBWAA-MASTER-BLUEPRINT.md` | Linha `**Versão de referência:** vX.Y.Z` e `**Data de geração:** YYYY-MM-DD` |
| `docs/SBWAA-LOGO.md` | Ocorrência da versão antiga no arquivo |
| `sbwaa.py` | String de versão dentro de `exibir_help()` (ex: `v2.12.0` → nova versão) |

Use Edit para cada substituição. Não faça rewrites desnecessários do arquivo inteiro.

---

## FASE 5 — ATUALIZAÇÕES DE CONTEÚDO

Com base no que foi identificado na Fase 1 (novos comandos, novos fluxos, mudanças de comportamento):

### 5a. sbwaa.py — /help

Leia a função `exibir_help()` completa.

- Se novos comandos locais foram adicionados → adicione a entrada no bloco `PORTFÓLIO` ou no bloco correto
- Se comandos de IA foram adicionados → adicione no bloco `IA`
- Se comandos foram removidos → remova a entrada correspondente
- Se a sintaxe de algum comando mudou → atualize a documentação inline

### 5b. interface/ui.py — painel de botões

Leia o arquivo para identificar os botões existentes (`_btn_local`, `_btn_ia`).

- Se novos comandos locais foram adicionados → verifique se há botão correspondente
- Se novos comandos de IA foram adicionados → verifique se há botão correspondente
- Se algum comando foi removido → verifique se o botão foi removido também
- Só edite se houver divergência real entre o que existe no código e o que foi adicionado/removido

### 5c. docs/GUIA-COMANDOS.md

Leia o arquivo completo.

- Se novos comandos foram adicionados → adicione a entrada com sintaxe, flags e exemplos no bloco correto
- Se sintaxe/flags mudaram → atualize a entrada correspondente
- Se comandos foram removidos → remova a entrada

### 5d. docs/SBWAA-REFERENCIA.md

Leia o arquivo completo.

- Se novos comandos foram adicionados → adicione a seção com: campos do output, estrutura, o que esperar
- Se o comportamento de um comando mudou → atualize a seção correspondente
- Se comandos foram removidos → remova a seção e o item do índice

### 5e. docs/SBWAA-WORKFLOW.md

Leia o arquivo completo.

- Se novos comandos afetam alguma cadência diária/semanal/mensal → atualize a tabela de cadência correspondente
- Se há novo fluxo oportunístico → adicione a seção

### 5f. docs/SBWAA-APRESENTACAO.md

Leia o arquivo completo.

- Se foram adicionadas novas features, agentes ou comandos → atualize a seção de funcionalidades
- Se foram removidas → remova do doc
- Mantenha o tom do documento (apresentação institucional, sem histórico técnico)

### 5g. docs/SBWAA-MASTER-BLUEPRINT.md

Atualize apenas para versões **MINOR** ou **MAJOR**, ou quando a mudança for estrutural:

- Cabeçalho: versão + data
- Tabela de histórico de versões: adicione nova linha com a versão, data e descrição da mudança
- Seção "Estado Atual": reflita qualquer nova fase, agente ou módulo adicionado

Para PATCHes simples: apenas atualizar a versão no cabeçalho, sem mexer na tabela de histórico.

---

## FASE 6 — VERIFICAÇÃO DE SEGURANÇA GIT

Execute `git status` e examine a lista.

**Nunca adicionar ao commit:**
- `vault/00-portfolio/` — dados privados de posições e patrimônio
- `knowledge/.chromadb/` — índice vetorial local
- `knowledge/raw/` — documentos brutos
- `scripts/data/cache/` — cache de cotações
- `.env` — variáveis de ambiente e chaves
- Qualquer arquivo com GUID no nome ou extensão `.tmp`

Se algum desses aparecer no status: **não adicione, não mencione o conteúdo**.

---

## FASE 7 — COMMIT + PUSH + RELEASE

### 7a. Montar o git add

Adicione apenas os arquivos modificados que são arquivos de projeto legítimos.
Liste explicitamente os arquivos — nunca use `git add .` ou `git add -A`.

### 7b. Commit

Use o formato:
```
tipo(módulo): descrição concisa

- detalhe 1
- detalhe 2
```

Onde `tipo` é: `feat`, `fix`, `docs`, `chore`, `refactor`
Onde `módulo` é: `investments`, `heartbeat`, `knowledge-base`, `interface`, `docs`

Se as mudanças cobrem múltiplos módulos, use o módulo principal ou omita o escopo.

### 7c. Push

**Sempre** faça push para o repositório remoto:
```bash
git push origin master
```

### 7d. GitHub Release — SEMPRE criar

**Sempre crie um release** para qualquer versão (MAJOR, MINOR ou PATCH) — sem exceção.

#### Identificar o último release publicado

Execute:
```bash
gh release list --limit 5
```

Anote a tag do release mais recente (ex: `v2.19.0`).

#### Montar as release notes com histórico acumulado

As notas do release devem cobrir **todas as versões desde o último release publicado** até a versão canônica atual — não apenas a versão corrente.

Execute para extrair os commits entre o último release e o HEAD:
```bash
git log <ultima-tag>..HEAD --oneline
```

Em seguida, extraia do `CHANGELOG.md` **todas as entradas** cujas versões estejam entre `<ultima-tag>` (exclusive) e a versão canônica atual (inclusive).

Formate as notas assim:
```
## Mudanças desde <ultima-tag>

### vX.Y.Z — YYYY-MM-DD
#### Added
- ...
#### Fixed
- ...

### vX.Y.(Z-1) — YYYY-MM-DD  ← se houver versões intermediárias não liberadas
#### Added
- ...
```

Se a versão canônica for a mesma do último release (somente sincronização de docs), ainda assim crie o release com as notas da versão atual.

#### Criar o release

```bash
gh release create vX.Y.Z \
  --title "vX.Y.Z — <descrição curta da mudança principal>" \
  --notes "<notas acumuladas conforme acima>" \
  --latest \
  --target master
```

---

## FASE 8 — RELATÓRIO FINAL

Ao final, exiba um sumário compacto:

```
✅ /att-info-system concluído — vX.Y.Z

Docs atualizados: README, GUIA-COMANDOS, SBWAA-REFERENCIA, ...
Conteúdo atualizado: [lista do que foi alterado substantivamente]
Commit: <hash curto> — <mensagem>
Push: origin/master ✓
Release: [vX.Y.Z criado | não aplicável]
```

Se alguma fase não pôde ser completada, liste o motivo de forma direta.
