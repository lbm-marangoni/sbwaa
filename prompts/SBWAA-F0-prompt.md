# SBWAA — FASE 0: BASE DO SECOND BRAIN
**Prompt para execução no Claude Code**
**Versão:** 1.0.0
**Fase:** 0 de 8

---

## CONTEXTO

Você vai construir a base completa do **SBWAA (Second Brain Wealth + Asset + Assessor Individual)** — um sistema multi-agente de análise financeira pessoal, operando 100% local. Esta é a Fase 0: nenhum agente de análise será criado ainda. O objetivo é criar toda a estrutura de pastas, arquivos de configuração, políticas, versionamento e graph view do Obsidian. As fases seguintes dependerão desta base.

---

## TAREFA

Crie toda a estrutura abaixo **exatamente como especificada**. Nenhum item é opcional. Execute passo a passo, confirmando cada etapa antes de avançar.

---

## 1. ESTRUTURA DE PASTAS

Crie a seguinte estrutura de diretórios a partir da raiz `/sbwaa/`:

```
sbwaa/
├── .claude/
│   ├── agents/
│   │   ├── market-researcher/
│   │   ├── earnings-reviewer/
│   │   ├── model-builder/
│   │   ├── valuation-reviewer/
│   │   ├── quant-data-engineer/
│   │   ├── risk-engineer/
│   │   └── portfolio-manager/
│   └── commands/
├── scripts/
│   ├── data/
│   ├── heartbeat/
│   └── alerts/
├── knowledge/
│   ├── books/
│   ├── research/
│   └── sources/
├── logs/
└── vault/
    ├── 00-portfolio/
    ├── 01-ativos/
    ├── 02-relatorios/
    │   ├── diarios/
    │   ├── semanais/
    │   └── mensais/
    ├── 03-macro/
    ├── 04-knowledge/
    ├── 05-risk/
    │   └── snapshots/
    └── assets/
        └── agents-pixel/
```

---

## 2. ARQUIVO: `CLAUDE.md`

Crie o arquivo `/sbwaa/CLAUDE.md` com o seguinte conteúdo completo:

```markdown
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

---

## IDIOMA E TOM

- Português brasileiro em todos os outputs ao usuário
- Tom técnico e direto
- Sem explicações desnecessárias
- Dados sempre com formatação clara (tabelas, blocos de código)
```

---

## 3. ARQUIVOS DE PORTFÓLIO BASE

### `/sbwaa/vault/00-portfolio/carteira.md`

```markdown
---
tags: [portfolio, carteira]
cssclasses: [node-portfolio]
---

# Carteira — SBWAA

> Arquivo gerenciado automaticamente pelo sistema.
> Adicionar ativos via comando `/adicionar`.

## Posições Ativas

| Ticker | Tipo | Setor | Qtd | Preço Médio | Preço Atual | P&L (R$) | P&L (%) |
|--------|------|-------|-----|-------------|-------------|----------|---------|
|        |      |       |     |             |             |          |         |

## Resumo

- **Patrimônio Total:** R$ —
- **Total Investido:** R$ —
- **P&L Total:** R$ —
- **Última atualização:** —
```

### `/sbwaa/vault/00-portfolio/ips.md`

```markdown
---
tags: [portfolio, ips, perfil]
cssclasses: [node-portfolio]
---

# IPS — Investment Policy Statement

## Perfil do Investidor

- **Horizonte:** —
- **Tolerância ao risco:** —
- **Objetivo principal:** —
- **Restrições:** —

## Alocação Alvo

| Classe          | Alvo (%) | Mín (%) | Máx (%) |
|-----------------|----------|---------|---------|
| Ações BR        |          |         |         |
| FIIs            |          |         |         |
| Renda Fixa      |          |         |         |
| ETFs Internac.  |          |         |         |
| Tesouro Direto  |          |         |         |

## Limites de Risco

- **VaR máximo (95%, 1 dia):** —
- **Drawdown máximo tolerado:** —
- **Concentração máxima por ativo:** —
```

### `/sbwaa/vault/00-portfolio/historico-trades.md`

```markdown
---
tags: [portfolio, historico]
cssclasses: [node-portfolio]
---

# Histórico de Operações

| Data | Ticker | Tipo | Operação | Qtd | Preço | Total R$ |
|------|--------|------|----------|-----|-------|----------|
|      |        |      |          |     |       |          |
```

---

## 4. VERSIONAMENTO INICIAL

### `/sbwaa/VERSION.md`

```markdown
# SBWAA — VERSION CONTROL

## Global
**v1.0.0** — 2026-05-15 — Inicialização do sistema (Fase 0)

## Módulos
| Módulo          | Versão  |
|-----------------|---------|
| investments     | v1.0.0  |
| heartbeat       | v0.0.0  |
| knowledge-base  | v0.0.0  |
| interface       | v0.0.0  |
```

### `/sbwaa/CHANGELOG.md`

```markdown
# SBWAA — CHANGELOG

---

## [1.0.0] — 2026-05-15

### Added
- Estrutura de pastas completa do vault e do projeto
- CLAUDE.md com políticas de segurança, model routing, wikilinks,
  labels de ativos e regras de versionamento
- Arquivos base de portfólio: carteira.md, ips.md, historico-trades.md
- Sistema de versionamento: VERSION.md e CHANGELOG.md
- Graph view CSS: sbwaa-graph.css com coloração por tipo de ativo
- CSS snippet de coloração dos nós no Obsidian
```

---

## 5. GRAPH VIEW — CSS DO OBSIDIAN

Crie o arquivo `/sbwaa/vault/.obsidian/snippets/sbwaa-graph.css`:

```css
/* SBWAA — Graph View Color Scheme */
/* Ativar em Obsidian > Appearance > CSS Snippets */

/* Ações */
.graph-view.color-fill[data-tag="acao"] { color: #3B82F6; }
.graph-view.color-fill[data-tag="acao-on"] { color: #2563EB; }
.graph-view.color-fill[data-tag="acao-pn"] { color: #60A5FA; }

/* FIIs */
.graph-view.color-fill[data-tag="fii"] { color: #22C55E; }

/* ETFs */
.graph-view.color-fill[data-tag="etf-br"] { color: #EAB308; }
.graph-view.color-fill[data-tag="etf-intl"] { color: #EF4444; }

/* Renda Fixa */
.graph-view.color-fill[data-tag="renda-fixa"] { color: #D1D5DB; }
.graph-view.color-fill[data-tag="tesouro"] { color: #A855F7; }
.graph-view.color-fill[data-tag="debenture"] { color: #92400E; }
.graph-view.color-fill[data-tag="cri-cra"] { color: #F97316; }

/* Sistema */
.graph-view.color-fill[data-tag="portfolio"] { color: #F59E0B; }
.graph-view.color-fill[data-tag="relatorio"] { color: #E5E7EB; }
.graph-view.color-fill[data-tag="macro"] { color: #78350F; }
.graph-view.color-fill[data-tag="knowledge"] { color: #6B7280; }
.graph-view.color-fill[data-tag="risk"] { color: #DC2626; }
.graph-view.color-fill[data-tag="pm-decisao"] { color: #FBBF24; }
.graph-view.color-fill[data-tag="ips"] { color: #F59E0B; }
```

---

## 6. `.gitignore`

Crie `/sbwaa/.gitignore`:

```
# SBWAA — Dados privados — nunca versionar
vault/00-portfolio/carteira.md
vault/00-portfolio/ips.md
vault/00-portfolio/historico-trades.md
vault/05-risk/snapshots/
vault/02-relatorios/
logs/
*.env
secrets.json
```

---

## 7. `.claudeignore`

Crie `/sbwaa/.claudeignore`:

```
# Dados privados — nunca enviar para contexto externo
vault/00-portfolio/carteira.md
vault/00-portfolio/ips.md
vault/00-portfolio/historico-trades.md
vault/05-risk/
logs/
```

---

## 8. README INICIAL

Crie `/sbwaa/README.md`:

```markdown
# SBWAA — Second Brain Wealth + Asset + Assessor Individual

Sistema multi-agente de análise financeira pessoal.
Operação 100% local. Dados 100% privados.

## Status das Fases

| Fase | Descrição                          | Status      |
|------|------------------------------------|-------------|
| 0    | Base do sistema                    | ✅ Completo |
| 1    | Pipeline de dados                  | ⏳ Pendente |
| 2    | Market Researcher + Earnings       | ⏳ Pendente |
| 3    | Model Builder + Valuation          | ⏳ Pendente |
| 4    | Quant + Risk Engineer              | ⏳ Pendente |
| 5    | Portfolio Manager                  | ⏳ Pendente |
| 6    | Comandos + Heartbeat               | ⏳ Pendente |
| 7    | RAG — Knowledge Base               | ⏳ Pendente |
| 8    | Interface Visual                   | ⏳ Pendente |

## Versão Global
Consultar `VERSION.md`

## Segurança
Consultar `CLAUDE.md` — Seção Security Policy
```

---

## 9. VALIDAÇÃO FINAL

Após criar todos os arquivos, execute a seguinte checklist e confirme cada item:

- [ ] Estrutura de pastas criada completamente
- [ ] `CLAUDE.md` criado com todas as seções
- [ ] `carteira.md`, `ips.md`, `historico-trades.md` criados
- [ ] `VERSION.md` iniciado em v1.0.0
- [ ] `CHANGELOG.md` com entrada inicial
- [ ] `sbwaa-graph.css` criado na pasta de snippets do Obsidian
- [ ] `.gitignore` e `.claudeignore` configurados
- [ ] `README.md` criado

Ao finalizar, exiba a estrutura de pastas completa gerada com o comando `tree` e confirme: **"SBWAA Fase 0 concluída — v1.0.0"**

---

## OBSERVAÇÕES IMPORTANTES

1. **Não criar nenhum agente ainda** — isso é Fase 2 em diante
2. **Não criar scripts Python ainda** — isso é Fase 1
3. **O vault é o diretório** `/sbwaa/vault/` — abrir este diretório no Obsidian
4. **O CSS do graph view só funciona** após ativar o snippet em Obsidian > Appearance > CSS Snippets
5. Se qualquer pasta já existir, não sobrescrever — apenas criar o que falta
