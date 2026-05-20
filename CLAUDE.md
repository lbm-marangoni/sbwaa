# SBWAA — CLAUDE.md
# Second Brain Wealth + Asset + Assessor Individual
# Configuração global do sistema — lida por todos os agentes

---

## ⚠️ SECURITY POLICY — CONFIDENCIAL

Este sistema contém dados financeiros privados e confidenciais.
As regras abaixo são absolutas e nunca podem ser ignoradas por nenhum agente.

- Todos os dados deste vault são estritamente privados
- Nenhuma informação de portfólio, posições, patrimônio, custo médio
  ou dados pessoais pode ser transmitida para qualquer serviço externo
- APIs externas recebem APENAS: tickers públicos, datas e parâmetros
  de mercado — nunca valores investidos ou dados pessoais
- Logs ficam exclusivamente em /sbwaa/logs/ local
- Em caso de dúvida sobre o que é dado privado, considerar privado

---

## MODEL ROUTING POLICY

Seguir este roteamento de modelos em todas as operações:

| Agente                  | Modelo              | Effort |
|-------------------------|---------------------|--------|
| Portfolio Manager       | claude-opus-4-6     | medium |
| Model Builder (DCF)     | claude-opus-4-6     | medium |
| Risk Engineer           | claude-opus-4-6     | medium |
| Market Researcher       | claude-sonnet-4-6   | medium |
| Earnings Reviewer       | claude-sonnet-4-6   | medium |
| Valuation Reviewer      | claude-sonnet-4-6   | medium |
| Quant / Data Engineer   | claude-sonnet-4-6   | medium |
| Heartbeat / Alertas     | claude-sonnet-4-6   | medium |
| Comandos diários        | claude-sonnet-4-6   | medium |

---

## WIKILINKS — REGRA GLOBAL

Todo output gerado por qualquer agente deve criar wikilinks automáticos
para todos os documentos relacionados dentro do vault. Regras:

- Nota de ativo → linka setor, macro relacionada, relatórios, tese, DCF
- Relatório → linka todos os ativos mencionados
- Tese de ativo → linka DCF, earnings, valuation, risk snapshot
- Nota macro → linka ativos da carteira afetados
- Output do PM → linka tudo que consumiu para a decisão
- Usar sempre formato [[nome-do-arquivo]] sem extensão

---

## TIPOS DE ATIVO — LABELS

Sempre identificar e exibir o tipo de cada ativo em todos os outputs:

| Label    | Tipo                    |
|----------|-------------------------|
| 🟦 AÇÃO ON   | Ação Ordinária      |
| 🟦 AÇÃO PN   | Ação Preferencial   |
| 🟩 FII       | Fundo Imobiliário   |
| 🟨 ETF BR    | ETF Brasileiro      |
| 🟥 ETF INTL  | ETF Internacional   |
| ⬜ RF        | Renda Fixa          |
| 🟪 TD        | Tesouro Direto      |
| 🟫 DEB       | Debênture           |
| 🟧 CRI/CRA   | CRI ou CRA          |

---

## VERSIONAMENTO — REGRA GLOBAL

- Todo agente que realizar qualquer alteração no sistema deve
  atualizar VERSION.md e CHANGELOG.md automaticamente
- Padrão semântico: MAJOR.MINOR.PATCH
  - MAJOR: mudança estrutural (novo agente, nova arquitetura)
  - MINOR: nova funcionalidade ou melhoria
  - PATCH: ajuste, correção, refinamento de prompt
- Nunca pular etapas de versionamento
- **Versões de módulos:** sempre bumpar o módulo afetado junto com a versão global

### REGRA DE PACK — PATCHES CONSECUTIVOS

Quando múltiplos bugs ou ajustes estão sendo resolvidos em sequência
na mesma sessão, **não gerar uma versão nova a cada fix individual**.
Em vez disso:

1. Acumular todas as correções do pack como um conjunto
2. Gerar **um único PATCH** ao final do pack — quando houver
   "interrupção": mudança de tipo de tarefa, uso normal do sistema,
   ou encerramento de sessão
3. O CHANGELOG desse patch lista todos os itens do pack juntos
4. Commits intermediários (durante o pack) podem ser feitos sem bump
   de versão; o bump acontece uma única vez no commit de fechamento do pack

| Módulo          | Cobre                                                        |
|-----------------|--------------------------------------------------------------|
| `investments`   | Agentes (.claude/agents/), pipeline de dados, comandos de portfólio |
| `heartbeat`     | scripts/heartbeat/, scripts/alerts/                          |
| `knowledge-base`| knowledge/                                                   |
| `interface`     | ui.py, splash.py, iniciar.vbs, iniciar.bat, SBWAA-LOGO.md   |

## ATUALIZAÇÃO OBRIGATÓRIA DE DOCS — REGRA GLOBAL

A cada modificação no sistema — sem exceção — os seguintes arquivos
DEVEM ser atualizados antes de encerrar qualquer sessão de trabalho:

| Arquivo             | Quando atualizar                                              |
|---------------------|---------------------------------------------------------------|
| `VERSION.md`        | Sempre — bumpar versão global e módulo afetado               |
| `CHANGELOG.md`      | Sempre — entrada com data, versão, Added/Fixed/Changed/Removed|
| `README.md`         | Quando mudar pré-requisitos, estrutura geral ou versão        |
| `GUIA-COMANDOS.md`    | Quando mudar sintaxe de comandos, flags ou exemplos de uso   |
| `SBWAA-REFERENCIA.md` | Quando adicionar, remover ou alterar qualquer comando — atualizar descrição de campos, mockup de output e comportamento esperado |
| `sbwaa.py` `/help`    | Quando adicionar, remover ou renomear qualquer comando        |
| `ui.py`               | Quando adicionar, remover ou renomear qualquer comando que deva aparecer na tela do painel |
| `SBWAA-LOGO.md`             | A cada bump de versão — atualizar a string de versão no arquivo                              |
| `SBWAA-MASTER-BLUEPRINT.md` | Quando mudar arquitetura, adicionar agente, alterar fluxo de dados ou bumpar versão MINOR/MAJOR — atualizar cabeçalho, tabela de histórico e seção Estado Atual |

Regras de execução:
- Atualizar na mesma sessão em que a mudança foi feita — nunca deixar para depois
- O CHANGELOG deve ter: data absoluta (YYYY-MM-DD), versão, e seção
  Added / Fixed / Changed / Removed conforme aplicável
- O README deve refletir o estado atual do sistema — não o histórico
- Nunca incrementar versão sem entrada correspondente no CHANGELOG

## GIT + GITHUB RELEASES — REGRA GLOBAL

Ao encerrar qualquer sessão que contenha mudanças prontas no sistema:

1. **Commitar e fazer push** para `origin/master` com mensagem descritiva
2. **Criar GitHub Release** apenas para versões significativas — não para
   todo PATCH, mas obrigatório para:
   - Qualquer versão MINOR (x.Y.0) ou MAJOR (X.0.0)
   - PATCHes que corrijam bugs críticos ou completem uma feature importante
   - Critério prático: se a mudança vale ser destacada no histórico público,
     ela merece um release

Formato do release:
- **Tag:** `vX.Y.Z` (igual ao VERSION.md)
- **Título:** `vX.Y.Z — <descrição curta da mudança principal>`
- **Notas:** copiar a entrada correspondente do CHANGELOG.md, com seções
  Added / Fixed / Changed / Removed. Para o release mais recente, adicionar
  `--latest` ao criar via `gh release create`.

Comando padrão:
```bash
git add <arquivos>
git commit -m "tipo: descrição"
git push origin master
gh release create vX.Y.Z --title "vX.Y.Z — Título" --notes "..." --latest --target master
```

Regras de segurança:
- Nunca commitar `.env`, `vault/00-portfolio/`, `scripts/data/cache/`,
  `knowledge/.chromadb/`, `knowledge/raw/` — todos já estão no `.gitignore`
- Confirmar com `git status` antes de qualquer `git add` para evitar
  expor dados privados acidentalmente

---

## PROTOCOLO DE SESSÃO — CHECKLIST OBRIGATÓRIO

Este arquivo é lido automaticamente pelo Claude Code em toda sessão.
As etapas abaixo são obrigatórias — não opcionais, não delegáveis.

### AO INICIAR UMA SESSÃO DE TRABALHO

1. Ler VERSION.md e verificar versão atual do sistema
2. Verificar se README.md e GUIA-COMANDOS.md têm a mesma versão que VERSION.md
3. Se divergentes → registrar e corrigir antes de encerrar a sessão
4. Aplicar TODAS as regras deste arquivo durante a sessão

### AO ENCERRAR UMA SESSÃO QUE TEVE MUDANÇAS

Execute nesta ordem (sem pular nenhuma):

1. **VERSION.md** — bumpar versão global E o módulo afetado (investments / heartbeat / knowledge-base / interface)
2. **CHANGELOG.md** — entrada com data absoluta, versão e seções Added/Fixed/Changed/Removed
3. **README.md** — atualizar versão no topo; refletir mudanças estruturais se houver
4. **GUIA-COMANDOS.md** — atualizar versão no topo; refletir novos/alterados comandos se houver
5. **sbwaa.py /help** — atualizar se adicionou, removeu ou renomeou qualquer comando
6. **ui.py** — atualizar se adicionou, removeu ou renomeou qualquer comando no painel
7. **SBWAA-REFERENCIA.md** — atualizar se adicionou, removeu ou alterou qualquer comando (campos, mockup de output, comportamento)
8. **SBWAA-LOGO.md** — atualizar a string de versão a cada bump
9. **SBWAA-MASTER-BLUEPRINT.md** — atualizar cabeçalho (versão + data), tabela de histórico e seção Estado Atual a cada MINOR/MAJOR ou mudança estrutural
10. `git status` — confirmar que nenhum arquivo privado será commitado
11. `git add <arquivos>` — somente arquivos do projeto, nunca vault/00-portfolio/ nem knowledge/raw/
12. `git commit -m "tipo: descrição"` + `git push origin master`
13. `gh release create vX.Y.Z --title "..." --notes "..." --latest --target master`
   — obrigatório para MINOR/MAJOR; para PATCHes, avaliar criticidade

> O script `scripts/check_session_compliance.py` roda automaticamente ao final de cada sessão
> (via Claude Code Stop hook) e exibe quais etapas estão pendentes.

---

## IDIOMA E TOM

- Português brasileiro em todos os outputs ao usuário
- Tom técnico e direto
- Sem explicações desnecessárias
- Dados sempre com formatação clara (tabelas, blocos de código)
