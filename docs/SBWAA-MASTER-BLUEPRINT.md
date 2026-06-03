# SBWAA — MASTER BLUEPRINT
## Guia Completo de Reconstrução do Sistema do Zero

**Versão de referência:** v2.20.0  
**Data de geração:** 2026-06-02  
**Objetivo:** Recriar o sistema SBWAA completo a partir do zero, com todas as fases, correções e estado atual.

---

## O QUE É O SBWAA

**Second Brain Wealth + Asset + Assessor Individual** — sistema multi-agente de análise financeira pessoal que roda 100% local no seu computador. Nenhum dado privado (patrimônio, posições, custo médio) sai da máquina. APIs externas recebem apenas tickers públicos.

**Arquitetura:**
- 8 agentes de IA especializados em pipeline sequencial
- Pipeline de dados (Brapi + Yahoo Finance) com cache local de 4h
- Base de conhecimento RAG (ChromaDB + sentence-transformers)
- Interface desktop (customtkinter) + terminal (slash commands)
- Vault Obsidian como banco de dados em markdown

**Stack principal:** Python 3.11+, Claude API (claude-sonnet-4-6 / claude-opus-4-6), ChromaDB, customtkinter, yfinance, Brapi

---

## ÍNDICE

1. [Pré-requisitos e Setup](#1-pré-requisitos-e-setup)
2. [CLAUDE.md — Configuração Global](#2-claudemd--configuração-global)
3. [Estrutura de Pastas Completa](#3-estrutura-de-pastas-completa)
4. [Fase 0 — Base do Sistema](#4-fase-0--base-do-sistema)
5. [Fase 1 — Pipeline de Dados](#5-fase-1--pipeline-de-dados)
6. [Fase 2 — Market Researcher + Earnings Reviewer](#6-fase-2--market-researcher--earnings-reviewer)
7. [Fase 3 — Model Builder + Valuation Reviewer](#7-fase-3--model-builder--valuation-reviewer)
8. [Fase 4 — Quant/Data Engineer + Risk Engineer](#8-fase-4--quantdata-engineer--risk-engineer)
9. [Fase 5 — Portfolio Manager + /analisar](#9-fase-5--portfolio-manager--analisar)
10. [Fase 6 — Comandos + Heartbeat + Alertas](#10-fase-6--comandos--heartbeat--alertas)
11. [Fase 7 — RAG Knowledge Base](#11-fase-7--rag-knowledge-base)
12. [Fase 8 — Interface Visual (customtkinter)](#12-fase-8--interface-visual-customtkinter)
13. [Fase 9 — Econometrician](#13-fase-9--econometrician)
14. [Fase 10 — Simulação de Carteira](#14-fase-10--simulação-de-carteira)
15. [sbwaa.py — Ponto de Entrada Atual](#15-sbwaapy--ponto-de-entrada-atual)
16. [Correções Críticas Aplicadas](#16-correções-críticas-aplicadas)
17. [Rotina de Testes](#17-rotina-de-testes)
18. [Estado Atual e Versões](#18-estado-atual-e-versões)

---

## 1. PRÉ-REQUISITOS E SETUP

### Sistema operacional
- Windows 10/11 (testado), Linux/Mac compatível
- **Windows:** usar PowerShell, não Git Bash (Git Bash expande `/cmd` → `C:/Program Files/Git/cmd`)
- Definir `$env:PYTHONUTF8 = "1"` no início de cada sessão PowerShell

### Python e pip
```bash
python --version    # 3.11+ recomendado
pip --version
```

### Dependências completas — `requirements.txt`
```
# SBWAA — Requirements
# pip install -r requirements.txt

# Dados de mercado
requests==2.31.0
yfinance==0.2.38
pandas==2.2.2
numpy==1.26.4
scipy==1.13.1

# Documentos
PyPDF2==3.0.1
python-docx==1.1.0
openpyxl==3.1.2

# RAG / Knowledge Base
chromadb==0.5.0
sentence-transformers==3.0.1
beautifulsoup4==4.12.3
feedparser==6.0.11

# Interface desktop
customtkinter==5.2.2

# Anthropic
anthropic==0.28.0

# Utilitários
python-dotenv==1.0.1
```

Instalar:
```bash
pip install -r requirements.txt
```

### Variável de ambiente
Criar `/sbwaa/.env` (nunca commitar):
```
ANTHROPIC_API_KEY=sua_chave_aqui
```

Adicionar ao `.gitignore`:
```
.env
knowledge/.chromadb/
knowledge/raw/
scripts/data/cache/
logs/
__pycache__/
*.pyc
vault/assets/agents-pixel/*.png
```

### UTF-8 no Windows
Adicionar ao topo de **todos** os scripts Python:
```python
import os, sys
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
```

---

## 2. CLAUDE.md — CONFIGURAÇÃO GLOBAL

Criar `/sbwaa/CLAUDE.md` — lido por todos os agentes no Claude Code:

```markdown
# SBWAA — CLAUDE.md
# Second Brain Wealth + Asset + Assessor Individual
# Configuração global do sistema — lida por todos os agentes

---

## ⚠️ SECURITY POLICY — CONFIDENCIAL

- Todos os dados deste vault são estritamente privados
- Nenhuma informação de portfólio, posições, patrimônio, custo médio
  ou dados pessoais pode ser transmitida para qualquer serviço externo
- APIs externas recebem APENAS: tickers públicos, datas e parâmetros
  de mercado — nunca valores investidos ou dados pessoais
- Logs ficam exclusivamente em /sbwaa/logs/ local
- Em caso de dúvida sobre o que é dado privado, considerar privado

---

## MODEL ROUTING POLICY

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

Todo output gerado por qualquer agente deve criar wikilinks automáticos:
- Nota de ativo → linka setor, macro, relatórios, tese, DCF
- Relatório → linka todos os ativos mencionados
- Tese de ativo → linka DCF, earnings, valuation, risk snapshot
- Usar sempre formato [[nome-do-arquivo]] sem extensão

---

## TIPOS DE ATIVO — LABELS

| Label        | Tipo                  |
|--------------|-----------------------|
| 🟦 AÇÃO ON   | Ação Ordinária        |
| 🟦 AÇÃO PN   | Ação Preferencial     |
| 🟩 FII       | Fundo Imobiliário     |
| 🟨 ETF BR    | ETF Brasileiro        |
| 🟥 ETF INTL  | ETF Internacional     |
| ⬜ RF        | Renda Fixa            |
| 🟪 TD        | Tesouro Direto        |
| 🟫 DEB       | Debênture             |
| 🟧 CRI/CRA   | CRI ou CRA            |

---

## VERSIONAMENTO — REGRA GLOBAL

- Padrão semântico: MAJOR.MINOR.PATCH
  - MAJOR: mudança estrutural (novo agente, nova arquitetura)
  - MINOR: nova funcionalidade ou melhoria
  - PATCH: ajuste, correção, refinamento

---

## ATUALIZAÇÃO OBRIGATÓRIA DE DOCS — REGRA GLOBAL

A cada modificação no sistema, ANTES de encerrar qualquer sessão:

| Arquivo           | Quando atualizar                                       |
|-------------------|--------------------------------------------------------|
| VERSION.md        | Sempre — bumpar versão global e módulo afetado         |
| CHANGELOG.md      | Sempre — entrada com data, versão, Added/Fixed/Changed |
| README.md         | Quando mudar comandos, dependências ou estrutura       |
| GUIA-COMANDOS.md  | Quando mudar sintaxe de comandos, flags ou uso         |
| sbwaa.py /help    | Quando adicionar, remover ou renomear qualquer comando |

---

## GIT + GITHUB RELEASES — REGRA GLOBAL

Ao encerrar qualquer sessão com mudanças prontas:

1. Commitar e fazer push para `origin/master`
2. Criar GitHub Release para versões significativas:
   - Obrigatório: qualquer MINOR (x.Y.0) ou MAJOR (X.0.0)
   - Obrigatório: PATCHes que corrijam bugs críticos ou completem features
   - Opcional: PATCHes menores de ajuste/refinamento
3. Formato do release:
   - Tag: `vX.Y.Z` | Título: `vX.Y.Z — <descrição curta>`
   - Notas: entrada correspondente do CHANGELOG (Added/Fixed/Changed/Removed)
   - Release mais recente sempre com flag `--latest`
4. Verificar `git status` antes de qualquer `git add` — nunca expor
   `.env`, `vault/00-portfolio/`, `cache/`, `.chromadb/`, `knowledge/raw/`

---

## IDIOMA E TOM

- Português brasileiro em todos os outputs ao usuário
- Tom técnico e direto
- Sem explicações desnecessárias
- Dados sempre com formatação clara (tabelas, blocos de código)
```

---

## 3. ESTRUTURA DE PASTAS COMPLETA

```
sbwaa/
├── sbwaa.py                          ← ponto de entrada único
├── CLAUDE.md                         ← config global (lida pelos agentes)
├── VERSION.md                        ← versionamento semântico
├── CHANGELOG.md                      ← histórico de mudanças
├── README.md                         ← documentação principal
├── requirements.txt                  ← dependências
├── iniciar.bat / iniciar.vbs         ← launchers Windows
├── .env                              ← ANTHROPIC_API_KEY (não commitar)
├── .gitignore
│
├── .claude/
│   ├── agents/
│   │   ├── market-researcher/
│   │   │   ├── SKILL.md
│   │   │   └── run_market_researcher.py
│   │   ├── earnings-reviewer/
│   │   │   ├── SKILL.md
│   │   │   └── run_earnings_reviewer.py
│   │   ├── model-builder/
│   │   │   ├── SKILL.md
│   │   │   └── run_model_builder.py
│   │   ├── valuation-reviewer/
│   │   │   ├── SKILL.md
│   │   │   └── run_valuation_reviewer.py
│   │   ├── quant-data-engineer/
│   │   │   ├── SKILL.md
│   │   │   ├── run_quant.py
│   │   │   └── calculators/
│   │   │       ├── returns.py
│   │   │       ├── portfolio_metrics.py
│   │   │       ├── correlation.py
│   │   │       └── optimization.py       ← Fronteira Eficiente (Markowitz)
│   │   ├── risk-engineer/
│   │   │   ├── SKILL.md
│   │   │   ├── run_risk_engineer.py
│   │   │   └── calculators/
│   │   │       ├── var.py
│   │   │       └── stress_test.py
│   │   ├── econometrician/               ← NOVO — Fase 9
│   │   │   ├── SKILL.md
│   │   │   ├── run_econometrician.py
│   │   │   └── modules/
│   │   │       ├── garch_model.py        ← GARCH(1,1) via arch
│   │   │       ├── dynamic_beta.py       ← beta rolling OLS
│   │   │       ├── factor_model.py       ← Fama-French 3F proxies BR
│   │   │       ├── macro_regression.py   ← regressão vs BCB (Selic/IPCA/BRL/IBC-Br)
│   │   │       ├── rolling_stats.py      ← correlações + vol rolling
│   │   │       └── advanced_drawdown.py  ← Calmar / Ulcer / Pain Index
│   │   └── portfolio-manager/
│   │       ├── SKILL.md
│   │       ├── run_pm.py                 ← Modo A/B + econometria + veredictos expandidos
│   │       └── run_analisar.py           ← orquestrador (8 etapas + Econometrician)
│   └── commands/
│       ├── carteira.py                   ← + projeção Monte Carlo ao final
│       ├── dividendos.py
│       ├── stress_test.py
│       ├── ips.py
│       ├── risco_carteira.py
│       ├── watchlist.py                  ← NOVO
│       ├── morning_call.py
│       ├── mundo_economico.py
│       ├── investimento_do_dia.py
│       ├── relatorio_semanal.py
│       ├── relatorio_mensal.py
│       ├── rebalancear.py                ← + sinais econométricos
│       ├── tese.py                       ← + Modo A/B
│       └── comparar.py
│
├── scripts/
│   ├── data/
│   │   ├── fetch_brapi.py            ← cotações BR (Brapi API)
│   │   ├── fetch_yahoo.py            ← dados globais (Yahoo Finance)
│   │   ├── fetch_bcb.py              ← NOVO — macro BCB (Selic, IPCA, BRL, IBC-Br)
│   │   ├── fetch_consensus.py        ← NOVO — consenso de analistas
│   │   ├── update_carteira.py        ← atualiza cotações na carteira.md
│   │   ├── add_ativo.py              ← adiciona ativo ao vault
│   │   ├── vender_ativo.py           ← NOVO — registra venda (parcial ou total)
│   │   ├── market_snapshot.py        ← snapshot diário macro
│   │   ├── optimize_expansao.py      ← fronteira dual carteira vs watchlist
│   │   └── cache/                    ← JSONs com cache de 4h
│   ├── simulacao_carteira.py         ← NOVO — backtest histórico + Monte Carlo
│   ├── heartbeat/
│   │   ├── heartbeat.py
│   │   └── schedule_heartbeat.py
│   └── alerts/
│       └── check_alerts.py
│
├── knowledge/
│   ├── .chromadb/                    ← banco de vetores (no .gitignore)
│   ├── raw/                          ← docs brutos (no .gitignore)
│   │   ├── books/
│   │   ├── research/
│   │   ├── gestoras/
│   │   └── macro/
│   ├── indexed/
│   │   └── index_log.json
│   ├── sources/
│   │   └── sources.json              ← Valor, InfoMoney, BCB, Bloomberg, Reuters
│   ├── indexer.py
│   ├── retriever.py
│   ├── rss_collector.py
│   ├── knowledge_cmd.py
│   └── save_synthesis.py
│
├── vault/
│   ├── 00-portfolio/
│   │   ├── carteira.md               ← posições + cotações
│   │   ├── ips.md                    ← Investment Policy Statement
│   │   ├── metas.md                  ← NOVO — metas financeiras (renda, reserva, patrimônio)
│   │   ├── historico-trades.md       ← log de operações (COMPRA/VENDA)
│   │   └── decisoes.md               ← decisões do PM
│   ├── 01-ativos/
│   │   └── {TICKER}/
│   │       ├── tese.md
│   │       ├── dcf-{TICKER}-v1.xlsx
│   │       ├── earnings-{TICKER}-{DATA}.md
│   │       ├── equity-research-{TICKER}-{DATA}-curta.md
│   │       └── equity-research-{TICKER}-{DATA}-curta.docx
│   ├── 02-relatorios/
│   │   ├── diarios/
│   │   │   ├── snapshot-{DATA}.md
│   │   │   └── morning-call-{DATA}.md
│   │   ├── semanais/
│   │   │   └── semana-{ANO}-W{N}.md
│   │   └── mensais/
│   │       └── relatorio-{ANO}-{MES}.md
│   ├── 03-macro/
│   │   └── market-researcher-{DATA}.md
│   ├── 04-knowledge/
│   │   └── sintese-*.md
│   ├── 05-risk/
│   │   └── snapshots/
│   │       └── risk-{DATA}.md
│   └── assets/
│       └── agents-pixel/             ← PNGs 64x64 dos agentes (opcional)
│
├── interface/
│   ├── ui.py                         ← interface desktop customtkinter
│   └── splash.py                     ← splash screen terminal
│
└── logs/
    ├── heartbeat.log
    ├── alerts.log
    └── simulacao/                    ← NOVO — PNGs backtest + Monte Carlo
        ├── backtest_{DATA}.png
        ├── montecarlo_{DATA}.png
        └── params_cache.json         ← parâmetros μ/σ para /carteira
```

---

## 4. FASE 0 — BASE DO SISTEMA

### Prompt de execução no Claude Code:
> Crie a estrutura base do SBWAA. Crie todas as pastas listadas na estrutura acima. Crie os arquivos base: CLAUDE.md (conteúdo da Seção 2 deste blueprint), VERSION.md, CHANGELOG.md, README.md esqueleto, .gitignore e a estrutura inicial do vault.

### Arquivos vault base

**`vault/00-portfolio/carteira.md`:**
```markdown
---
tags: [portfolio, carteira]
cssclasses: [node-portfolio]
---

# Carteira

| Ticker | Tipo | Qtd | Preço Médio | Preço Atual | Valor R$ | P&L R$ | P&L % | Aloc% | Setor |
|--------|------|-----|-------------|-------------|----------|--------|-------|-------|-------|

**Patrimônio Total:** R$ 0,00
**Total Investido:** R$ 0,00
**P&L Total:** R$ 0,00 (0,00%)
**Última atualização:** (nunca)
```

**`vault/00-portfolio/ips.md`:**
```markdown
---
tags: [portfolio, ips]
cssclasses: [node-portfolio]
---

# Investment Policy Statement (IPS)

## Perfil do Investidor
- **Horizonte:** 10-30 anos
- **Perfil:** Moderado-Agressivo
- **Objetivo:** Crescimento + Renda passiva via dividendos

## Alocação Alvo
| Classe       | Alvo % | Mín % | Máx % |
|--------------|--------|-------|-------|
| Ações BR     | 40%    | 30%   | 55%   |
| FIIs         | 35%    | 25%   | 45%   |
| ETFs Intl    | 15%    | 10%   | 25%   |
| Renda Fixa   | 10%    | 5%    | 20%   |

## Limites de Risco (Circuit Breakers)
- VaR 95% (1 dia): máx 2,5%
- Drawdown máximo tolerado: 18%
- Concentração máxima por ativo: 20%
- Stop loss individual: -25%

## Regras de Rebalanceamento
- Rebalancear quando desvio > 5% da alocação alvo
- Preferir compras para rebalancear (evitar venda com imposto)
- Revisar IPS anualmente ou após mudança significativa de vida
```

**`vault/00-portfolio/historico-trades.md`:**
```markdown
---
tags: [portfolio, historico]
cssclasses: [node-portfolio]
---

# Histórico de Operações

| Data | Ticker | Tipo | Operação | Qtd | Preço | Total R$ |
|------|--------|------|----------|-----|-------|----------|
```

**`vault/00-portfolio/decisoes.md`:**
```markdown
---
tags: [portfolio, decisoes]
cssclasses: [node-portfolio]
---

# Decisões do Portfolio Manager

| Data | Ticker | Veredicto | Confiança | Preço Alvo | Stop | Observações |
|------|--------|-----------|-----------|------------|------|-------------|
```

### CSS para Obsidian
Criar `vault/.obsidian/snippets/sbwaa.css`:
```css
.node-portfolio { --node-color: 40, 120, 200; }
.node-ativo     { --node-color: 80, 180, 80;  }
.node-relatorio { --node-color: 200, 140, 40; }
.node-macro     { --node-color: 180, 60, 60;  }
.node-knowledge { --node-color: 140, 80, 200; }
.node-risk      { --node-color: 220, 80, 80;  }
```

### VERSION.md inicial
```markdown
# SBWAA — VERSION CONTROL

## Global
**v1.0.0** — Base do sistema criada

## Módulos
| Módulo          | Versão  | Status       |
|-----------------|---------|--------------|
| investments     | v1.0.0  | ✅ Criado    |
| heartbeat       | —       | ⏳ Pendente  |
| knowledge-base  | —       | ⏳ Pendente  |
| interface       | —       | ⏳ Pendente  |
```

---

## 5. FASE 1 — PIPELINE DE DADOS

### Prompt de execução no Claude Code:
> Crie o pipeline de dados do SBWAA. São 5 scripts na pasta scripts/data/: fetch_brapi.py, fetch_yahoo.py, update_carteira.py, add_ativo.py e market_snapshot.py. Todos devem usar cache JSON local com TTL de 4 horas. fetch_brapi.py busca cotações de ativos BR via Brapi (sem API key pública, header Accept: application/json). fetch_yahoo.py busca dados macro globais (IBOV=^BVSP, S&P500=^GSPC, DXY=DX-Y.NYB, ouro=GC=F, petróleo=CL=F, BRL/USD=USDBRL=X). update_carteira.py lê carteira.md e atualiza cotações. add_ativo.py adiciona ativo com flags --ticker, --tipo, --quantidade, --preco-medio, --setor. market_snapshot.py gera snapshot markdown em vault/02-relatorios/diarios/.

### Especificações críticas

**`fetch_brapi.py`** — busca cotações BR:
- URL: `https://brapi.dev/api/quote/{TICKER}`
- Headers: `{"Accept": "application/json", "User-Agent": "SBWAA/1.0"}`
- Cache: `scripts/data/cache/brapi_{TICKER}_{DATA}.json` com TTL 4h
- **CRÍTICO:** erros HTTP devem lançar `ValueError`, não `SystemExit` — assim o fallback funciona
- Fallback automático para Yahoo Finance com sufixo `.SA` se Brapi retornar 401/403

```python
# Padrão correto para tratamento de erros (não usar SystemExit):
try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    raise ValueError(f"Erro HTTP ao buscar {ticker}: {e}")
except requests.exceptions.ConnectionError:
    raise ValueError(f"Erro de conexão ao buscar {ticker}.")
except requests.exceptions.Timeout:
    raise ValueError(f"Timeout ao buscar {ticker}.")
```

**`add_ativo.py`** — adiciona ativo à carteira:
- Valida ticker na Brapi (com flag `--skip-validacao` para pular)
- Atualiza `vault/00-portfolio/carteira.md` inserindo linha na tabela
- Atualiza `vault/00-portfolio/historico-trades.md`
- Cria pasta `vault/01-ativos/{TICKER}/` com `tese.md` inicial
- Tipos aceitos: `acao-on | acao-pn | fii | etf-br | etf-intl | renda-fixa | tesouro | debenture | cri-cra`

**`update_carteira.py`** — atualiza cotações:
- Lê todas as linhas da tabela em `carteira.md`
- Para cada ticker: busca cotação atual via `fetch_brapi` (com fallback para Yahoo)
- Recalcula: Valor R$ = Qtd × Preço Atual; P&L R$ = Valor − (Qtd × Preço Médio); P&L % = P&L R$ / (Qtd × Preço Médio) × 100
- Recalcula Patrimônio Total, P&L Total
- Atualiza "Última atualização" com data e hora atuais

**`market_snapshot.py`** — snapshot diário:
- Chama `fetch_yahoo.py` para dados macro
- Gera markdown em `vault/02-relatorios/diarios/snapshot-{DATA}.md`
- Salva JSON em `scripts/data/cache/snapshot_{DATA}.json`
- Inclui: IBOV, S&P500, NASDAQ, DXY, BRL/USD, ouro, petróleo, juros 10Y US

### Estrutura de cache JSON (fetch_brapi)
```json
{
  "ticker": "PETR4",
  "nome": "Petrobras PN",
  "cotacao_atual": 38.50,
  "variacao_dia_pct": 1.2,
  "volume": 45000000,
  "timestamp": "2026-05-16T10:30:00",
  "fonte": "brapi"
}
```

---

## 6. FASE 2 — MARKET RESEARCHER + EARNINGS REVIEWER

### Prompt de execução no Claude Code:
> Crie os dois primeiros agentes do SBWAA: Market Researcher e Earnings Reviewer. Cada agente tem uma pasta em .claude/agents/, com SKILL.md (prompt do agente) e run_{agente}.py (script que monta o contexto, chama a API e salva o output no vault). Market Researcher: analisa macro BR e global, usa snapshot do dia, gera nota em vault/03-macro/. Earnings Reviewer: analisa último resultado trimestral de um ticker, usa dados da Brapi, gera nota em vault/01-ativos/{TICKER}/. Modelo: claude-sonnet-4-6.

### SKILL.md — Market Researcher

```markdown
# Market Researcher — SBWAA

## Identidade
Você é o Market Researcher do SBWAA. Especialista em análise macroeconômica
e de mercados. Seu trabalho é processar dados do dia e produzir análise
concisa e acionável para o Portfolio Manager.

## Inputs que você receberá
- Snapshot macro do dia (IBOV, S&P500, DXY, commodities, câmbio, juros)
- Data e contexto econômico

## Outputs que você deve gerar

### 1. Contexto Macro Global
- 3-5 drivers principais do dia (o que está movendo os mercados)
- Posição de risco global (risk-on ou risk-off e por quê)
- Dólar e commodities: tendência e impacto para Brasil

### 2. Contexto Macro Brasil
- IBOV: nível técnico e sentimento
- Juros (SELIC, DI futuro): posição e expectativas
- BRL/USD: tendência e pressões
- Agenda econômica relevante (COPOM, IPCA, PIB, resultados)

### 3. Impacto Setorial
- Quais setores BR são favorecidos/prejudicados hoje
- Destaque 2-3 temas que o PM deve monitorar

## Regras
- Dados sempre têm prioridade sobre opinião
- Se dado não disponível, indicar "dado indisponível" — não inventar
- Citar variação % sempre que disponível
- Output máximo: 600 palavras
- Salvar em vault com wikilinks para ativos afetados da carteira

## BASE DE CONHECIMENTO (RAG)
Quando contexto RAG for fornecido no prompt:
- Priorizar informações da base sobre conhecimento geral
- Citar a fonte: (Fonte: nome_do_documento)
- Se base contradiz dados atuais, usar dados atuais e registrar contradição
```

### run_market_researcher.py — estrutura
```python
#!/usr/bin/env python3
"""SBWAA — Market Researcher"""
import sys, os, json
from pathlib import Path
from datetime import datetime

# Setup paths e UTF-8
os.environ["PYTHONUTF8"] = "1"
ROOT = Path(__file__).resolve().parent.parent.parent.parent
import anthropic
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

CACHE = ROOT / "scripts" / "data" / "cache"
VAULT_MACRO = ROOT / "vault" / "03-macro"
hoje = datetime.now().strftime("%Y-%m-%d")

def montar_contexto():
    """Carrega snapshot do cache e formata para o agente."""
    snapshots = sorted(CACHE.glob("snapshot_*.json"), reverse=True)
    if not snapshots:
        return "Snapshot não disponível. Execute /snapshot primeiro."
    return snapshots[0].read_text(encoding="utf-8")

def main():
    skill = (Path(__file__).parent / "SKILL.md").read_text(encoding="utf-8")
    contexto = montar_contexto()

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=skill,
        messages=[{"role": "user", "content": f"DATA: {hoje}\n\nSNAPSHOT:\n{contexto}"}]
    )

    output = response.content[0].text

    # Salvar no vault
    saida = VAULT_MACRO / f"market-researcher-{hoje}.md"
    VAULT_MACRO.mkdir(parents=True, exist_ok=True)
    saida.write_text(
        f"---\ntags: [macro, market-researcher]\ncssclasses: [node-macro]\ndata: {hoje}\n---\n\n"
        f"# Market Research — {hoje}\n\n{output}\n\n"
        f"## Links\n- [[carteira]]\n- [[ips]]\n- [[snapshot-{hoje}]]\n",
        encoding="utf-8"
    )
    print(output)

if __name__ == "__main__":
    main()
```

### SKILL.md — Earnings Reviewer

```markdown
# Earnings Reviewer — SBWAA

## Identidade
Você é o Earnings Reviewer do SBWAA. Especialista em análise de resultados
trimestrais de empresas listadas na B3.

## Inputs que você receberá
- Ticker e dados básicos do ativo (via Brapi)
- Contexto macro do dia
- Dados históricos disponíveis no cache

## O que analisar

### Resultado do Trimestre
- Receita líquida: realizado vs esperado vs trimestre anterior
- EBITDA e margem EBITDA: expansão ou contração?
- Lucro líquido e EPS
- Dívida líquida/EBITDA: leverage subindo ou caindo?

### Qualidade do Resultado
- Resultado recorrente vs não-recorrente
- Geração de caixa (FCF) vs lucro contábil
- Guidance revisado? Para cima ou para baixo?

### Veredicto do Resultado
- POSITIVO / NEGATIVO / NEUTRO
- 2-3 linhas de justificativa
- Impacto estimado no valuation (múltiplo P/L, EV/EBITDA)

## Regras
- Para FIIs: focar em DY, vacância, FFO por cota, portfólio
- Se não houver dados de earnings recentes (< 6 meses), indicar
- Output máximo: 500 palavras
- Salvar em vault/01-ativos/{TICKER}/earnings-{TICKER}-{DATA}.md
```

---

## 7. FASE 3 — MODEL BUILDER + VALUATION REVIEWER

### Prompt de execução no Claude Code:
> Crie os agentes Model Builder (DCF) e Valuation Reviewer. Model Builder: constrói modelo DCF para ações ordinárias/preferenciais e modelo Gordon Growth para FIIs. Usa claude-opus-4-6. Gera XLSX com o modelo e JSON com premissas no cache. Valuation Reviewer: valida o DCF, compara com comps de mercado, produz equity research em 2 versões (curta 1 página e longa 2 páginas) em .md e .docx. Usa claude-sonnet-4-6.

### SKILL.md — Model Builder

```markdown
# Model Builder — SBWAA

## Identidade
Você é o Model Builder do SBWAA. CFA charterholder com 15 anos de
experiência em valuation de empresas brasileiras. Sua responsabilidade
é construir o modelo financeiro que fundamenta cada decisão de investimento.

## Para ações (ON/PN) — DCF
Construir modelo DCF com:
- Projeções de receita, EBITDA e FCF: 5 anos explícitos + perpetuidade
- WACC com: taxa livre de risco (SELIC ou NTN-B 2030), prêmio de risco BR,
  beta setorial ajustado, custo da dívida pós-imposto, estrutura de capital
- Valor terminal: método Gordon (g = PIB BR nominal estimado)
- Saídas: preço justo, upside/downside vs preço atual, range de sensibilidade

## Para FIIs — Gordon Growth Model
- DY atual, crescimento estimado de dividendos (2-4% para shoppings/lajes,
  4-6% para logística), taxa de desconto (NTN-B + spread)
- Preço justo via P/VP histórico e cap rate implícito

## Outputs
1. JSON de premissas salvo em scripts/data/cache/dcf_{TICKER}_{DATA}.json
2. XLSX com o modelo completo em vault/01-ativos/{TICKER}/dcf-{TICKER}-v1.xlsx

## Premissas padrão por setor
- Petróleo: Brent $75-85, câmbio USDBRL 5.20
- Varejo: crescimento PIB + 2-3%
- Financeiro: ROE 15-20%, provisões históricas
- FII CRI: spread CDI + 1-2%

## Regras
- Sempre apresentar bear / base / bull case
- Sensibilidade: variar WACC ±1% e crescimento ±2%
- Se dados insuficientes: montar modelo simplificado e indicar limitações
```

### SKILL.md — Valuation Reviewer

```markdown
# Valuation Reviewer — SBWAA

## Identidade
Você é o Valuation Reviewer do SBWAA. Analista sênior de equity research
com especialização em mercado brasileiro.

## Inputs
- Output do Model Builder (DCF/Gordon)
- Dados de mercado atuais (cotação, volume, liquidez)
- Output do Earnings Reviewer (resultado trimestral)

## O que revisar e produzir

### Validação do DCF
- As premissas do WACC são defensáveis para o setor?
- O crescimento projetado é consistente com o histórico da empresa?
- Comparar com consenso de mercado (se disponível)

### Análise de Múltiplos (Comps)
- P/L atual vs histórico 5a vs pares do setor
- EV/EBITDA atual vs histórico vs pares
- P/VP (para bancos e FIIs)
- DY trailing 12m e forward

### Veredicto de Valuation
- BARATO / JUSTO / CARO (vs histórico e vs DCF)
- Preço alvo consolidado (média ponderada DCF + múltiplos)
- Upside/downside em % e em R$

## Output — duas versões

### Versão Curta (1 página)
Estrutura obrigatória:
1. Cabeçalho: ticker, tipo, setor, preço atual, preço alvo, upside
2. Resumo executivo (3 linhas)
3. Tabela de múltiplos
4. Veredicto de valuation
5. Wikilinks

### Versão Longa (2 páginas)
Versão curta + análise qualitativa da empresa, SWOT resumido,
riscos principais, catalisadores, histórico de dividendos.

## Formato de saída
- .md salvo em vault/01-ativos/{TICKER}/equity-research-{TICKER}-{DATA}-{versao}.md
- .docx gerado com python-docx
```

### Geração de XLSX (openpyxl)
```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

wb = Workbook()
ws_premissas = wb.active
ws_premissas.title = "Premissas"
ws_dcf = wb.create_sheet("DCF")
ws_sensibilidade = wb.create_sheet("Sensibilidade")

# Premissas — preencher com dados do agente
# DCF — projeções anuais
# Sensibilidade — tabela WACC vs crescimento

wb.save(str(output_path))
```

---

## 8. FASE 4 — QUANT/DATA ENGINEER + RISK ENGINEER

### Prompt de execução no Claude Code:
> Crie os agentes Quant/Data Engineer e Risk Engineer com suas calculadoras em Python puro. Quant: calcula métricas de portfólio (Sharpe, volatilidade, beta IBOV, correlação, retornos). Risk: calcula VaR 95% histórico e paramétrico, CVaR, drawdown, stress tests e circuit breakers. Ambos leem o histórico de preços do cache (Yahoo Finance) e salvam JSON no cache. Risk Engineer usa claude-opus-4-6 para gerar interpretação narrativa.

### Calculadoras — Quant (`calculators/returns.py`)
```python
import pandas as pd
import numpy as np

def retorno_total(precos: pd.Series) -> float:
    """Retorno total do período."""
    return (precos.iloc[-1] / precos.iloc[0]) - 1

def retornos_diarios(precos: pd.Series) -> pd.Series:
    return precos.pct_change().dropna()

def volatilidade_anualizada(precos: pd.Series, dias_ano: int = 252) -> float:
    ret = retornos_diarios(precos)
    return ret.std() * np.sqrt(dias_ano)

def sharpe(retorno_anual: float, volatilidade_anual: float,
           taxa_livre_risco: float = 0.1275) -> float:
    """Sharpe ratio anualizado. taxa_livre_risco = SELIC atual."""
    if volatilidade_anual == 0:
        return 0.0
    return (retorno_anual - taxa_livre_risco) / volatilidade_anual

def retorno_1m(precos: pd.Series) -> float:
    """Retorno do último mês (21 dias úteis)."""
    if len(precos) < 22:
        return float("nan")
    return (precos.iloc[-1] / precos.iloc[-22]) - 1

def retorno_12m(precos: pd.Series) -> float:
    """Retorno dos últimos 12 meses (252 dias úteis)."""
    if len(precos) < 253:
        return float("nan")
    return (precos.iloc[-1] / precos.iloc[-253]) - 1
```

### Calculadoras — Risk (`calculators/var.py`)
```python
import numpy as np
import pandas as pd
from scipy import stats

def var_historico(retornos: pd.Series, confianca: float = 0.95) -> float:
    """VaR histórico: percentil simples dos retornos."""
    return abs(np.percentile(retornos.dropna(), (1 - confianca) * 100))

def var_parametrico(volatilidade_diaria: float,
                    confianca: float = 0.95) -> float:
    """VaR paramétrico (Normal): z-score × volatilidade."""
    z = stats.norm.ppf(confianca)
    return abs(z * volatilidade_diaria)

def cvar(retornos: pd.Series, confianca: float = 0.95) -> float:
    """CVaR (Expected Shortfall): média das perdas além do VaR."""
    var = var_historico(retornos, confianca)
    perdas_extremas = retornos[retornos < -var]
    if perdas_extremas.empty:
        return var
    return abs(perdas_extremas.mean())

def drawdown_atual(precos: pd.Series) -> float:
    """Drawdown atual: queda do pico mais recente."""
    pico = precos.cummax()
    dd = (precos / pico) - 1
    return abs(dd.iloc[-1])

def drawdown_maximo(precos: pd.Series) -> float:
    """Drawdown máximo histórico do período."""
    pico = precos.cummax()
    dd = (precos / pico) - 1
    return abs(dd.min())
```

### Calculadoras — Stress Test (`calculators/stress_test.py`)
```python
CENARIOS = {
    "crise-2008":    {"nome": "Crise Financeira 2008",   "ibov_pct": -41.0},
    "covid-2020":    {"nome": "COVID Março 2020",         "ibov_pct": -30.0},
    "eleicoes-2022": {"nome": "Incerteza Eleitoral 2022", "ibov_pct": -15.0},
    "lula1-2002":    {"nome": "Crise de Confiança 2002",  "ibov_pct": -17.0},
}

def stress_test_cenario(valor_carteira: float, beta: float,
                         choque_ibov_pct: float) -> dict:
    impacto_pct = beta * (choque_ibov_pct / 100)
    impacto_rs  = valor_carteira * impacto_pct
    return {
        "choque_ibov_pct":  choque_ibov_pct,
        "impacto_pct":      impacto_pct * 100,
        "impacto_reais":    impacto_rs,
        "impacto_reais_normalizado": 100_000 * impacto_pct,
    }
```

### Circuit Breakers (verificados pelo Risk Engineer)
```python
circuit_breakers = {
    "var_ok":          var_atual <= limite_var_ips,         # ex: 2.5%
    "drawdown_ok":     drawdown_atual <= limite_dd_ips,     # ex: 18%
    "concentracao_ok": concentracao_max <= limite_conc_ips, # ex: 20%
}
```

### Outputs salvos em cache
- `scripts/data/cache/quant_{DATA}.json` — métricas quantitativas
- `scripts/data/cache/risk_{DATA}.json` — métricas de risco + circuit breakers
- `vault/05-risk/snapshots/risk-{DATA}.md` — nota narrativa no vault

---

## 9. FASE 5 — PORTFOLIO MANAGER + /ANALISAR

### Prompt de execução no Claude Code:
> Crie o Portfolio Manager e o orquestrador /analisar. O PM é o agente decisor final — ele recebe todos os outputs das fases anteriores e retorna COMPRAR/AGUARDAR/EVITAR com sizing, preço de entrada, stop e tese de investimento em 1 página. Usa claude-opus-4-6. run_analisar.py é o orquestrador que executa todos os 7 agentes em sequência para um ticker.

### SKILL.md — Portfolio Manager

> **Atualização v2.8.x:** O PM agora opera em dois modos detectados automaticamente:
> - **Modo A** — ativo não está na carteira → veredictos: COMPRAR / AGUARDAR / EVITAR
> - **Modo B** — ativo já está na carteira → veredictos: AUMENTAR / MANTER / REDUZIR / SAIR
>
> Adicionalmente, o PM recebe e incorpora o output do **Econometrician** (cache JSON) em sua análise.

```markdown
# Portfolio Manager — SBWAA

## Identidade e Missão
Você é o Portfolio Manager do SBWAA — o decisor final do sistema.
Você NÃO é um assistente. Você é um gestor de portfólio experiente,
crítico e direto, responsável por proteger e fazer crescer o capital.

**[MODO A — Novo ativo]** Sua decisão é uma de três:
- **COMPRAR** — convicção suficiente, sizing e entrada definidos
- **AGUARDAR** — tese válida mas entrada não favorável ainda
- **EVITAR** — tese fraca, risco elevado ou melhor alocação disponível

**[MODO B — Posição existente]** Sua decisão é uma de quatro:
- **AUMENTAR** — tese se fortaleceu, há espaço no IPS, entry favorável
- **MANTER** — posição adequada, sem catalisador para mudar
- **REDUZIR** — risco subiu, tese deteriorou, concentração alta, ou oportunidade de custo
- **SAIR** — tese quebrada, stop atingido, ou realocação prioritária

Nunca retorne respostas ambíguas. Sempre conclua com veredicto claro.

## Inputs que você receberá
1. Output do Market Researcher (macro do dia)
2. Output do Earnings Reviewer (resultado trimestral)
3. Output do Model Builder (DCF/preço justo)
4. Output do Valuation Reviewer (múltiplos + equity research)
5. Output do Quant/Data Engineer (métricas HF da carteira)
6. Output do Econometrician (GARCH, beta dinâmico, FF3F, macro BCB, drawdown avançado)
7. Output do Risk Engineer (VaR, circuit breakers, stress tests)
8. IPS do usuário (perfil, alocação alvo, limites)
9. Posição atual na carteira (peso atual, P&L, data de entrada) — se Modo B

## Estrutura da Decisão

### 1. Síntese dos 6 agentes (máx 3 linhas cada)
Resumo objetivo dos inputs. Sem repetir dados — apenas o essencial.

### 2. Análise de Portfólio
- Esta posição melhora o Sharpe da carteira?
- Correlação com ativos existentes?
- Impacto no VaR da carteira?
- Espaço de alocação disponível vs IPS?

### 3. Veredicto Final
**[COMPRAR/AGUARDAR/EVITAR]**
- Nível de confiança: Alto / Médio / Baixo
- Justificativa em 3 linhas

### 4. Parâmetros (se COMPRAR)
- Entrada sugerida: R$ XX,XX (preço ou range)
- Sizing sugerido: X% da carteira (em R$)
- Stop loss: R$ XX,XX (-X%)
- Preço alvo 12m: R$ XX,XX (+X%)
- Prazo esperado: X meses

### 5. Riscos Principais
- 3 riscos que invalidariam a tese

### 6. Pontos de Monitoramento
- 2-3 métricas a acompanhar

## Regras de Sizing
- ALTO risco/convicção: 2-5% da carteira
- MÉDIO risco/convicção: 1-3% da carteira
- Nunca sugerir posição > limite IPS de concentração
- Sempre considerar liquidez (volume médio diário)

## Personalidade e Tom
- Direto e técnico
- Não bajula — se a tese não presta, diz claramente
- Usa dados para justificar — sem achismo
- Pensa no portfólio como um todo, não no ativo isolado
```

### run_analisar.py — orquestrador sequencial
```python
#!/usr/bin/env python3
"""SBWAA — Orquestrador /analisar: 7 agentes em sequência."""
import sys, subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent.parent
hoje = datetime.now().strftime("%Y-%m-%d")

ETAPAS = [
    ("📊 Snapshot de mercado",   ROOT/"scripts"/"data"/"market_snapshot.py",        []),
    ("🌍 Market Researcher",      ROOT/".claude"/"agents"/"market-researcher"/"run_market_researcher.py",   []),
    ("📋 Earnings Reviewer",      ROOT/".claude"/"agents"/"earnings-reviewer"/"run_earnings_reviewer.py",   [ticker]),
    ("🏗️  Model Builder (DCF)",   ROOT/".claude"/"agents"/"model-builder"/"run_model_builder.py",          [ticker]),
    ("🔍 Valuation Reviewer",     ROOT/".claude"/"agents"/"valuation-reviewer"/"run_valuation_reviewer.py",[ticker, "--versao", versao]),
    ("📐 Quant/Data Engineer",    ROOT/".claude"/"agents"/"quant-data-engineer"/"run_quant.py",            []),
    ("🛡️  Risk Engineer",         ROOT/".claude"/"agents"/"risk-engineer"/"run_risk_engineer.py",          []),
    ("🎯 Portfolio Manager",      ROOT/".claude"/"agents"/"portfolio-manager"/"run_pm.py",                 [ticker]),
]

def main():
    ticker = sys.argv[1].upper() if len(sys.argv) > 1 else None
    versao = "curta"
    if "--versao" in sys.argv:
        idx = sys.argv.index("--versao")
        versao = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "curta"

    print(f"\n{'='*60}")
    print(f"SBWAA — /analisar {ticker} | {hoje}")
    print(f"{'='*60}\n")

    for i, (nome, script, args) in enumerate(ETAPAS, 1):
        print(f"[{i}/{len(ETAPAS)}] {nome}...")
        if script.exists():
            result = subprocess.run(
                [sys.executable, str(script)] + args,
                capture_output=False
            )
            if result.returncode != 0:
                print(f"  ⚠️  {nome} retornou código {result.returncode}")
        else:
            print(f"  ❌ Script não encontrado: {script}")

    print(f"\n{'='*60}")
    print(f"✅ Análise de {ticker} concluída")
    print(f"   Relatórios em: vault/01-ativos/{ticker}/")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
```

---

## 10. FASE 6 — COMANDOS + HEARTBEAT + ALERTAS

### Prompt de execução no Claude Code:
> Crie o ponto de entrada sbwaa.py e todos os comandos em .claude/commands/. Também crie o heartbeat automático (scripts/heartbeat/heartbeat.py) e o sistema de alertas (scripts/alerts/check_alerts.py). sbwaa.py roteia slash commands para os scripts corretos.

### Comandos implementados

**Locais** (`.claude/commands/` e `scripts/` — rodam via Python puro, sem IA):

| Arquivo              | Comando              | Descrição                                        |
|----------------------|----------------------|--------------------------------------------------|
| carteira.py          | /carteira            | Atualiza cotações, exibe posições + P&L + alocação vs IPS + **projeção Monte Carlo** ao final |
| dividendos.py        | /dividendos          | Próximos dividendos (60d), histórico do ano e Yield on Cost |
| stress_test.py       | /stress-test         | Simula choques de mercado (4 cenários + custom)  |
| ips.py               | /ips                 | Exibe o IPS completo do usuário                  |
| watchlist.py         | /watchlist           | **NOVO** — lista ativos analisados + carteira com veredicto, data e frescor (atual/defasado/rever) |
| risco_carteira.py    | /risco-carteira      | VaR, CVaR, Sharpe, drawdown, circuit breakers, Fronteira Eficiente |
| simulacao_carteira.py (scripts/) | /simulacao | **NOVO** — backtest 5 anos + Monte Carlo 10/20/30a com fan chart; gera PNGs; atualiza cache de μ/σ |
| add_ativo.py (scripts/) | /adicionar        | Adiciona ativo à carteira (valida na API, cria pasta vault) |
| vender_ativo.py (scripts/) | /vender        | **NOVO** — registra venda parcial ou total; calcula P&L realizado |
| optimize_expansao.py (scripts/) | /otimizar-expansao | Fronteira dual: carteira vs carteira + watchlist; candidatos MELHORA/NEUTRO/PIORA |
| market_snapshot.py (scripts/) | /snapshot   | Snapshot diário macro (IBOV, S&P, DXY, commodities...) |
| knowledge_cmd.py (knowledge/) | /knowledge  | Gerencia base RAG: status, adicionar, buscar, listar, coletar-rss |

**IA** (chat do Claude Code — sem ANTHROPIC_API_KEY):

| Skill/Comando          | Descrição                                        |
|------------------------|--------------------------------------------------|
| /analisar TICKER       | Pipeline completo: 8 agentes em sequência (inclui Econometrician como etapa 6) |
| /tese TICKER           | Research + DCF + PM rápido; Modo A/B automático  |
| /pm TICKER             | Só Portfolio Manager com dados cacheados         |
| /earnings TICKER       | Resultado trimestral                             |
| /comparar A B          | Análise lado a lado                              |
| /morning-call          | Briefing pré-abertura + alertas econométricos    |
| /mundo-economico       | Análise macro do dia                             |
| /investimento-do-dia [cat] | Sugestão IPS-aware; filtro: fii/acao/etf/rf/td |
| /metas                 | **NOVO** — dashboard: renda passiva, reserva, patrimônio, metas livres |
| /relatorio-semanal     | P&L da semana, métricas e outlook                |
| /relatorio-mensal      | Relatório completo do mês com benchmarks         |
| /rebalancear           | Desvios vs IPS + sinais econométricos por ativo  |
| /revisar-carteira      | **NOVO** — PM revisa cada posição: MANTER/AUMENTAR/REDUZIR/SAIR com sizing |

### Alertas implementados (`check_alerts.py`)
```python
ALERTAS = {
    "queda_ativo":              {"threshold_pct": 5.0,  "severidade": "ALTO"},
    "alta_ativo":               {"threshold_pct": 7.0,  "severidade": "MÉDIO"},
    "circuit_breaker_var":      {"severidade": "CRÍTICO"},
    "circuit_breaker_drawdown": {"severidade": "CRÍTICO"},
    "circuit_breaker_concentracao": {"severidade": "ALTO"},
    "earnings_amanha":          {"severidade": "MÉDIO"},
    "dividendo_proximo":        {"severidade": "BAIXO"},
    "correlacao_subiu":         {"threshold": 0.15, "severidade": "MÉDIO"},
}
```

### Heartbeat (`heartbeat.py`)
Executa diariamente às 07h15 em dias úteis:
1. Verificar se é dia útil
2. Rodar market_snapshot.py
3. Rodar run_quant.py
4. Rodar run_risk_engineer.py
5. Verificar circuit breakers → registrar alertas
6. Coletar RSS (knowledge base)
7. Gerar morning-call automático
8. Registrar em `logs/heartbeat.log`

---

## 11. FASE 7 — RAG KNOWLEDGE BASE

### Prompt de execução no Claude Code:
> Crie a base de conhecimento RAG do SBWAA usando ChromaDB + sentence-transformers. Scripts em knowledge/: indexer.py (processa PDF/DOCX/TXT/MD), retriever.py (busca semântica), rss_collector.py (coleta feeds RSS), knowledge_cmd.py (comando /knowledge). Modelo de embedding: paraphrase-multilingual-MiniLM-L12-v2 (suporta PT-BR). Base fica 100% local em knowledge/.chromadb/.

### Configuração ChromaDB
```python
import chromadb
from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
client = chromadb.PersistentClient(path="knowledge/.chromadb")
collection = client.get_or_create_collection(
    name="sbwaa_knowledge",
    metadata={"hnsw:space": "cosine"}
)
```

### Chunking (words, não tokens)
```python
def chunk_texto(texto: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    palavras = texto.split()
    chunks = []
    i = 0
    while i < len(palavras):
        chunk = palavras[i:i + chunk_size]
        chunks.append(" ".join(chunk))
        i += chunk_size - overlap
    return chunks
```

### Metadados por chunk
```python
metadata = {
    "fonte": "nome_do_arquivo",
    "tipo": "livro|research|gestora|macro|outro",
    "autor": "extraído ou 'desconhecido'",
    "ano": "extraído ou 'desconhecido'",
    "idioma": "pt|en",
    "chunk_id": N,
    "total_chunks": N
}
```

### RSS Feeds configurados (`sources/sources.json`)
```json
{
  "rss_feeds": [
    {"nome": "Valor Econômico", "url": "https://valor.globo.com/rss/financas", "tipo": "macro", "idioma": "pt", "ativo": true},
    {"nome": "InfoMoney",       "url": "https://www.infomoney.com.br/feed/",    "tipo": "macro", "idioma": "pt", "ativo": true},
    {"nome": "Bloomberg Markets","url": "https://feeds.bloomberg.com/markets/news.rss", "tipo": "macro", "idioma": "en", "ativo": true},
    {"nome": "Reuters Business", "url": "https://feeds.reuters.com/reuters/businessNews", "tipo": "macro", "idioma": "en", "ativo": true}
  ],
  "coleta_max_artigos_por_feed": 5,
  "coleta_max_idade_dias": 3
}
```

### Subcomandos do /knowledge
```bash
python sbwaa.py /knowledge --status           # métricas da base
python sbwaa.py /knowledge --adicionar arq    # indexar documento
python sbwaa.py /knowledge --buscar "query"   # busca semântica
python sbwaa.py /knowledge --listar           # listar documentos
python sbwaa.py /knowledge --coletar-rss      # forçar coleta RSS
```

### Documentos recomendados para indexar (priority 1)
- **Livros:** Security Analysis (Graham), Intelligent Investor, Damodaran on Valuation
- **Research BR:** relatórios XP, BTG, Itaú BBA; Relatório de Estabilidade Financeira (BCB)
- **Gestoras BR:** cartas mensais Verde Asset, SPX, Truxt, Absolute, Ibiuna, Kinea

---

## 12. FASE 8 — INTERFACE VISUAL (CUSTOMTKINTER)

> **Nota:** O prompt original (F8) especificava Streamlit. Durante a implementação, foi substituído por **customtkinter** — interface desktop nativa, sem servidor, sem browser. Esta seção descreve a implementação atual.

### Prompt de execução no Claude Code:
> Crie ui.py na raiz do projeto com interface customtkinter. 5 abas: Portfólio, Análise (IA), Mercado, Relatórios (IA), Knowledge. Painel de output embutido que cresce com a janela. Auto-clear no início de cada comando. Comandos locais rodam via subprocess com output em tempo real. Comandos de IA copiam o comando para a área de transferência (não chamam IA diretamente — o usuário digita no chat do Claude Code).

### Estrutura do `ui.py`

```python
#!/usr/bin/env python3
"""SBWAA — Interface Desktop (customtkinter)"""
import os, sys, subprocess, threading
import customtkinter as ctk
from pathlib import Path
from datetime import datetime

os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

PROJECT_ROOT = Path(__file__).parent
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SBWAAApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SBWAA — Second Brain")
        self.geometry("1000x720")
        self.minsize(800, 600)

        self.grid_rowconfigure(0, weight=0)  # tabs
        self.grid_rowconfigure(1, weight=1)  # conteúdo
        self.grid_rowconfigure(2, weight=2)  # output (maior)
        self.grid_columnconfigure(0, weight=1)

        self._build_tabs()
        self._build_output()

    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5,0))
        for aba in ["Portfólio", "Análise (IA)", "Mercado", "Relatórios (IA)", "Knowledge"]:
            self.tabview.add(aba)
        self._build_tab_portfolio()
        self._build_tab_analise()
        self._build_tab_mercado()
        self._build_tab_relatorios()
        self._build_tab_knowledge()

    def _build_output(self):
        frame = ctk.CTkFrame(self)
        frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(5,10))
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text="Output", anchor="w").grid(
            row=0, column=0, sticky="w", padx=8, pady=(4,0))
        ctk.CTkButton(frame, text="Limpar", width=70, height=24,
                      command=self._clear_output).grid(
            row=0, column=1, sticky="e", padx=8, pady=(4,0))

        self.output = ctk.CTkTextbox(frame, state="disabled",
                                      font=("Courier New", 11))
        self.output.grid(row=1, column=0, columnspan=2, sticky="nsew",
                         padx=8, pady=(4,8))

    # ── Aba Portfólio ────────────────────────────────────────────────
    def _build_tab_portfolio(self):
        tab = self.tabview.tab("Portfólio")
        tab.grid_columnconfigure((0,1,2), weight=1)

        # Botões de ação rápida
        botoes = [
            ("📊 /carteira",       ["/carteira"]),
            ("💰 /dividendos",     ["/dividendos"]),
            ("🛡️  /risco-carteira", ["/risco-carteira"]),
            ("📋 /ips",            ["/ips"]),
        ]
        for col, (label, args) in enumerate(botoes):
            ctk.CTkButton(tab, text=label,
                          command=lambda a=args: self._local(a)).grid(
                row=0, column=col % 4, padx=5, pady=5, sticky="ew")

        # Formulário /adicionar
        sep = ctk.CTkFrame(tab, height=2)
        sep.grid(row=1, column=0, columnspan=4, sticky="ew", pady=8)
        ctk.CTkLabel(tab, text="Adicionar Ativo",
                     font=("Helvetica", 13, "bold")).grid(
            row=2, column=0, columnspan=4, sticky="w", padx=5)

        # Campos: ticker, tipo, qtd, preço, setor
        campos = [
            ("Ticker",   "ticker_var",   None),
            ("Quantidade", "qtd_var",   None),
            ("Preço Médio (R$)", "preco_var", None),
            ("Setor",    "setor_var",    None),
        ]
        self.ticker_var = ctk.StringVar()
        self.qtd_var    = ctk.StringVar()
        self.preco_var  = ctk.StringVar()
        self.setor_var  = ctk.StringVar()
        self.tipo_var   = ctk.StringVar(value="acao-pn")

        for i, (label, var_name, _) in enumerate(campos):
            ctk.CTkLabel(tab, text=label).grid(
                row=3, column=i, padx=5, sticky="w")
            ctk.CTkEntry(tab, textvariable=getattr(self, var_name),
                         width=140).grid(row=4, column=i, padx=5, pady=2)

        ctk.CTkLabel(tab, text="Tipo").grid(row=5, column=0, padx=5, sticky="w")
        tipos = ["acao-on","acao-pn","fii","etf-br","etf-intl",
                 "renda-fixa","tesouro","debenture","cri-cra"]
        ctk.CTkComboBox(tab, variable=self.tipo_var, values=tipos,
                        width=140).grid(row=6, column=0, padx=5, pady=2)

        self.skip_val = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(tab, text="--skip-validacao",
                        variable=self.skip_val).grid(
            row=6, column=1, padx=5)

        ctk.CTkButton(tab, text="➕ Adicionar",
                      command=self._adicionar).grid(
            row=6, column=2, padx=5, pady=5)

    def _adicionar(self):
        args = ["/adicionar",
                "--ticker",      self.ticker_var.get().upper(),
                "--tipo",        self.tipo_var.get(),
                "--quantidade",  self.qtd_var.get(),
                "--preco-medio", self.preco_var.get(),
                "--setor",       self.setor_var.get() or "geral"]
        if self.skip_val.get():
            args.append("--skip-validacao")
        self._local(args)

    # ── Aba Análise (IA) ─────────────────────────────────────────────
    def _build_tab_analise(self):
        tab = self.tabview.tab("Análise (IA)")
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="Ticker:",
                     font=("Helvetica", 12)).grid(
            row=0, column=0, sticky="w", padx=5, pady=4)
        self.ticker_ia = ctk.StringVar()
        ctk.CTkEntry(tab, textvariable=self.ticker_ia, width=120).grid(
            row=0, column=1, padx=5)

        botoes_ia = [
            ("/analisar",    "/analisar"),
            ("/tese",        "/tese"),
            ("/earnings",    "/earnings"),
            ("/pm",          "/pm"),
        ]
        for col, (label, cmd) in enumerate(botoes_ia):
            ctk.CTkButton(tab, text=label,
                          command=lambda c=cmd: self._ia_com_ticker(c)).grid(
                row=1, column=col, padx=5, pady=5)

        ctk.CTkLabel(tab, text="Comparar:",
                     font=("Helvetica", 12)).grid(
            row=2, column=0, sticky="w", padx=5, pady=4)
        self.ticker_a = ctk.StringVar()
        self.ticker_b = ctk.StringVar()
        ctk.CTkEntry(tab, textvariable=self.ticker_a, width=90,
                     placeholder_text="Ticker A").grid(row=2, column=1, padx=5)
        ctk.CTkEntry(tab, textvariable=self.ticker_b, width=90,
                     placeholder_text="Ticker B").grid(row=2, column=2, padx=5)
        ctk.CTkButton(tab, text="/comparar",
                      command=self._comparar).grid(row=2, column=3, padx=5)

        ctk.CTkLabel(
            tab,
            text="ℹ️  Comandos de IA copiam o comando para área de transferência.\n"
                 "   Cole no chat do Claude Code para executar.",
            font=("Helvetica", 11), text_color="gray"
        ).grid(row=3, column=0, columnspan=4, pady=8)

    def _ia_com_ticker(self, cmd: str):
        ticker = self.ticker_ia.get().upper().strip()
        self._clipboard(f"{cmd} {ticker}".strip() if ticker else cmd)

    def _comparar(self):
        a = self.ticker_a.get().upper().strip()
        b = self.ticker_b.get().upper().strip()
        self._clipboard(f"/comparar {a} {b}")

    # ── Aba Mercado ──────────────────────────────────────────────────
    def _build_tab_mercado(self):
        tab = self.tabview.tab("Mercado")
        tab.grid_columnconfigure((0,1,2), weight=1)

        botoes_locais = [
            ("📸 /snapshot",    ["/snapshot"]),
        ]
        botoes_ia = [
            ("/morning-call",        "/morning-call"),
            ("/mundo-economico",     "/mundo-economico"),
            ("/investimento-do-dia", "/investimento-do-dia"),
        ]
        for col, (label, args) in enumerate(botoes_locais):
            ctk.CTkButton(tab, text=label,
                          command=lambda a=args: self._local(a)).grid(
                row=0, column=col, padx=5, pady=5, sticky="ew")

        for col, (label, cmd) in enumerate(botoes_ia):
            ctk.CTkButton(tab, text=label,
                          command=lambda c=cmd: self._clipboard(c)).grid(
                row=1, column=col, padx=5, pady=5, sticky="ew")

        # Stress test
        sep = ctk.CTkFrame(tab, height=2)
        sep.grid(row=2, column=0, columnspan=3, sticky="ew", pady=8)
        ctk.CTkLabel(tab, text="Stress Test",
                     font=("Helvetica", 13, "bold")).grid(
            row=3, column=0, columnspan=3, sticky="w", padx=5)

        cenarios = [
            ("Crise 2008",     ["/stress-test", "crise-2008"]),
            ("COVID 2020",     ["/stress-test", "covid-2020"]),
            ("Eleições 2022",  ["/stress-test", "eleicoes-2022"]),
            ("Lula 2002",      ["/stress-test", "lula1-2002"]),
            ("Todos",          ["/stress-test"]),
        ]
        for col, (label, args) in enumerate(cenarios):
            ctk.CTkButton(tab, text=label, width=110,
                          command=lambda a=args: self._local(a)).grid(
                row=4, column=col % 3, padx=5, pady=3)

        ctk.CTkLabel(tab, text="Choque custom (%):").grid(
            row=5, column=0, padx=5, sticky="w")
        self.choque_var = ctk.StringVar()
        ctk.CTkEntry(tab, textvariable=self.choque_var, width=80).grid(
            row=5, column=1, padx=5)
        ctk.CTkButton(tab, text="Executar",
                      command=self._stress_custom).grid(row=5, column=2, padx=5)

    def _stress_custom(self):
        val = self.choque_var.get().strip()
        if val:
            self._local(["/stress-test", "custom", val])

    # ── Aba Relatórios (IA) ──────────────────────────────────────────
    def _build_tab_relatorios(self):
        tab = self.tabview.tab("Relatórios (IA)")
        tab.grid_columnconfigure((0,1), weight=1)

        botoes = [
            ("/relatorio-semanal", "/relatorio-semanal"),
            ("/relatorio-mensal",  "/relatorio-mensal"),
            ("/rebalancear",       "/rebalancear"),
        ]
        for col, (label, cmd) in enumerate(botoes):
            ctk.CTkButton(tab, text=label,
                          command=lambda c=cmd: self._clipboard(c)).grid(
                row=0, column=col, padx=5, pady=5, sticky="ew")

    # ── Aba Knowledge ────────────────────────────────────────────────
    def _build_tab_knowledge(self):
        tab = self.tabview.tab("Knowledge")
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(tab, text="📊 Status da base",
                      command=lambda: self._local(["/knowledge", "--status"])).grid(
            row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(tab, text="🌐 Coletar RSS",
                      command=lambda: self._local(["/knowledge", "--coletar-rss"])).grid(
            row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(tab, text="📋 Listar documentos",
                      command=lambda: self._local(["/knowledge", "--listar"])).grid(
            row=0, column=2, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(tab, text="Busca semântica:").grid(
            row=1, column=0, padx=5, sticky="w")
        self.busca_var = ctk.StringVar()
        ctk.CTkEntry(tab, textvariable=self.busca_var,
                     placeholder_text="valuation petróleo Brasil").grid(
            row=1, column=1, padx=5, sticky="ew")
        ctk.CTkButton(tab, text="Buscar",
                      command=self._buscar_knowledge).grid(
            row=1, column=2, padx=5)

    def _buscar_knowledge(self):
        q = self.busca_var.get().strip()
        if q:
            self._local(["/knowledge", "--buscar", q])

    # ── Helpers ──────────────────────────────────────────────────────
    def _clear_output(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    def _append(self, text: str):
        self.output.configure(state="normal")
        self.output.insert("end", text)
        self.output.see("end")
        self.output.configure(state="disabled")

    def _local(self, args: list):
        """Roda comando local (sbwaa.py) com output em tempo real."""
        cmd = [sys.executable, str(PROJECT_ROOT / "sbwaa.py")] + args
        self._clear_output()
        self._append(f"[{datetime.now().strftime('%H:%M:%S')}] > {' '.join(args)}\n\n")
        threading.Thread(target=self._run_proc, args=(cmd,), daemon=True).start()

    def _run_proc(self, cmd: list):
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                bufsize=1
            )
            for line in proc.stdout:
                self.after(0, self._append, line)
            proc.wait()
            self.after(0, self._append,
                       f"\n[Processo encerrado — código {proc.returncode}]\n")
        except Exception as e:
            self.after(0, self._append, f"\n❌ Erro: {e}\n")

    def _clipboard(self, cmd: str):
        """Copia comando de IA para área de transferência."""
        self._clear_output()
        self.clipboard_clear()
        self.clipboard_append(cmd)
        self._append(f"📋 Copiado para área de transferência:\n\n  {cmd}\n\n"
                     "Cole no chat do Claude Code e pressione Enter.")


if __name__ == "__main__":
    app = SBWAAApp()
    app.mainloop()
```

---

## 13. FASE 9 — ECONOMETRICIAN

### O que é
O Econometrician é o **8º agente** do pipeline `/analisar` (Etapa 6, após Quant e antes de Risk). Produz análise quantitativa avançada de um único ativo usando séries temporais e econometria aplicada. Resultado: JSON em cache (`econometria_{TICKER}_{DATA}.json`) consumido pelo PM e pelos comandos `/rebalancear` e `/revisar-carteira`.

**Modelo:** `claude-sonnet-4-6` | **Effort:** medium

### Módulos (`.claude/agents/econometrician/modules/`)

| Módulo | Função |
|--------|--------|
| `garch_model.py` | GARCH(1,1) via biblioteca `arch`: volatilidade condicional, previsão 5 dias, regime de vol (BAIXA/NORMAL/ALTA) |
| `dynamic_beta.py` | Beta rolling OLS 63d/126d/252d; detecta convergência/divergência; compara com beta ingênuo |
| `factor_model.py` | Fama-French 3 Fatores com proxies BR: MKT=^BVSP, SMB=SMALL11.SA, HML=DIVO11.SA; R² e alfas |
| `macro_regression.py` | Regressão vs variáveis macro do BCB: Selic, IPCA, BRL/USD, IBC-Br; sensibilidades e R² |
| `rolling_stats.py` | Volatilidade rolling 21/63/252d; correlação rolling 63d vs IBOV + outros ativos da carteira |
| `advanced_drawdown.py` | Calmar ratio (retorno/maxDD), Ulcer Index (profundidade média ao quadrado), Pain Index; série de drawdowns individuais |

### Dependências novas
- `arch>=7.0.0` — estimação GARCH
- `fetch_bcb.py` — séries macro BCB (Selic diário série 11, IPCA mensal série 433, BRL/USD série 1, IBC-Br série 24363)

### Output — estrutura do JSON de cache
```json
{
  "ticker": "PETR4",
  "data": "2026-05-22",
  "garch": {
    "vol_condicional_hoje": 0.018,
    "vol_anualizada": 28.5,
    "previsao_5d": 0.020,
    "regime": "NORMAL",
    "omega": 0.0001, "alpha": 0.09, "beta": 0.88
  },
  "beta_dinamico": {
    "beta_63d": 1.12, "beta_126d": 1.08, "beta_252d": 1.05,
    "tendencia": "ESTAVEL",
    "beta_ingenuo_252d": 1.06
  },
  "factor_model": {
    "alpha_anual": 0.02, "beta_mkt": 1.05, "beta_smb": 0.15, "beta_hml": -0.08,
    "r2": 0.72, "periodo": "252d"
  },
  "macro_regression": {
    "sensibilidade_selic": -0.35, "sensibilidade_ipca": 0.12,
    "sensibilidade_brl": -0.28, "sensibilidade_ibc": 0.45,
    "r2": 0.41
  },
  "rolling_stats": {
    "vol_21d": 0.022, "vol_63d": 0.019, "vol_252d": 0.017,
    "corr_ibov_63d": 0.68, "corr_ibov_252d": 0.71
  },
  "advanced_drawdown": {
    "calmar_ratio": 1.42, "ulcer_index": 8.3, "pain_index": 4.1,
    "max_drawdown": -0.21, "n_drawdowns": 7
  },
  "para_o_pm": [
    "Vol GARCH ALTA — regime de estresse; PM deve aplicar sizing mais conservador",
    "Beta dinâmico crescente (63d > 252d) — sensibilidade ao mercado aumentando",
    "Calmar < 1 — retorno ajustado a drawdown abaixo do aceitável"
  ]
}
```

### Integração no Pipeline
- **run_econometrician.py** rodado como Etapa 6 do `run_analisar.py`
- Saída salva em `scripts/data/cache/econometria_{TICKER}_{DATA}.json`
- Janela de cache: 8 dias (considerado "recente" para PM e comandos)
- **run_pm.py** lê o cache e injeta bloco `ECONOMETRICIAN` no prompt do PM
- **/rebalancear** e **/revisar-carteira** leem caches de todos os ativos da carteira e exibem tabela "Sinais Econométricos por Ativo"

### Regras de incorporação no PM
```
GARCH ALTA           → sizing conservador, mencionar risco de vol
Beta 63d > Beta 252d → sensibilidade crescente ao mercado
Calmar < 0.5         → histórico de drawdown ruim
Corr instável        → diversificação em risco
Sinais positivos     → reforçam MANTER / AUMENTAR
```

---

## 14. FASE 10 — SIMULAÇÃO DE CARTEIRA

### O que é
Sistema de análise de longo prazo com **backtest histórico** e **projeção Monte Carlo**. Tem dois pontos de acesso:

1. **`python sbwaa.py /simulacao`** — script completo com download de dados, backtest 5 anos, Monte Carlo 10k simulações, gráficos PNG dark mode. Atualiza `logs/simulacao/params_cache.json`.
2. **`/carteira`** — usa params_cache.json para exibir projeção inline ao final (sem rede, ~1 segundo).

### `/simulacao` — `scripts/simulacao_carteira.py`

**Proxies IPS (quando carteira vazia):**
| Classe IPS | Proxy | Peso |
|------------|-------|------|
| Ações BR | BOVA11.SA | 25% |
| FIIs | KNRI11.SA | 35% |
| ETFs Internac. | IVVB11.SA | 8% |
| Renda Fixa | CDI (BCB série 12) | 20% |
| Tesouro Direto | IPCA + 5% a.a. (BCB série 433) | 12% |

**Parte B — Backtest:**
- Monta retornos diários ponderados pelas classes IPS
- Benchmarks: ^BVSP (IBOV) e CDI diário (BCB)
- Gráfico triplo: retorno acumulado / rolling 12m / drawdown
- Métricas: retorno anualizado, volatilidade, Sharpe, max drawdown

**Parte A — Monte Carlo:**
- GBM paramétrico: drift = μ − σ²/2 (correção Itô)
- 10.000 simulações por horizonte
- Fan chart P5/P25/P50/P75/P95
- Suporte a `--aporte` mensal (loop diário, +aporte a cada 22 dias)
- Tabela de percentis finais (P5/P25/P50/P75/P95) por horizonte

**Flags:**
```bash
python sbwaa.py /simulacao
python sbwaa.py /simulacao --patrimonio 50000 --aporte 1000
python sbwaa.py /simulacao --anos 5 10 20 --historico 5
python sbwaa.py /simulacao --no-graficos   # só terminal, sem PNGs
```

**Outputs:**
- `logs/simulacao/backtest_{DATA}.png`
- `logs/simulacao/montecarlo_{DATA}.png`
- `logs/simulacao/params_cache.json` — `{mu_anual, sigma_anual, data, historico_anos}`

### Projeção no `/carteira`

Ao final de todo output do `/carteira`, exibe automaticamente:

```
PROJECAO DE LONGO PRAZO
  Patrimonio atual: R$ 50,000   |   mu: 11.2%  sigma: 7.2%  |  5,000 sims  |  base: 2026-05-22

  Sem aportes adicionais:
  Anos    P10 (pessim.)   P50 (esperado)  P90 (otimist.)
  10            R$106k          R$142k          R$188k
  20            R$264k          R$397k          R$600k
  30            R$688k         R$1.13M         R$1.89M

  Mantendo aporte medio de R$ 870/mes (6 meses de historico):
  Anos    P10 (pessim.)   P50 (esperado)  P90 (otimist.)   Ganho vs sem
  10            R$252k          R$317k          R$397k        +R$175k
  20            R$768k         R$1.07M         R$1.50M        +R$669k
  30           R$2.12M         R$3.21M         R$4.98M       +R$2.08M

  Graficos + backtest historico:  python sbwaa.py /simulacao
```

**Como o aporte é calculado:**
- Lê `vault/00-portfolio/historico-trades.md`
- Filtra linhas com `COMPRA`, agrupa por mês (YYYY-MM)
- Soma o `Total R$` por mês → média sobre meses com compras
- Se sem histórico → mostra só cenário "sem aportes" com mensagem orientativa

**Requisito:** rodar `/simulacao` pelo menos uma vez para criar o `params_cache.json`. Após isso, `/carteira` sempre exibe a projeção sem acesso à rede.

### Dependência nova
- `matplotlib>=3.9.0`

---

## 15. SBWAA.PY — PONTO DE ENTRADA ATUAL

Estado atual do `sbwaa.py` (v2.8.6 — pós todas as fases):

```python
#!/usr/bin/env python3
"""
SBWAA — Second Brain Wealth + Asset + Assessor Individual
Ponto de entrada único para todos os comandos.

Uso:
    python sbwaa.py /carteira
    python sbwaa.py /stress-test
    python sbwaa.py /adicionar --ticker PETR4 --tipo acao-pn --quantidade 100 --preco-medio 45.00 --setor energia
    python sbwaa.py /help

Comandos com IA (sem API key): use diretamente no chat do Claude Code
    /analisar PETR4        /tese VALE3         /morning-call
    /earnings MXRF11       /comparar A B       /pm PETR4
    /mundo-economico       /investimento-do-dia
    /relatorio-semanal     /relatorio-mensal   /rebalancear
    /revisar-carteira      /metas
"""

import sys
import os
import subprocess
from datetime import datetime
from pathlib import Path

# Forçar UTF-8 no stdout/stderr e em todos os subprocessos (Windows)
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).parent

MODO_CLAUDE_CODE = True

# Comandos que rodam localmente (sem IA / sem API key)
COMANDOS_LOCAIS = {
    "/carteira":            ".claude/commands/carteira.py",
    "/watchlist":           ".claude/commands/watchlist.py",
    "/adicionar":           "scripts/data/add_ativo.py",
    "/vender":              "scripts/data/vender_ativo.py",
    "/risco-carteira":      ".claude/commands/risco_carteira.py",
    "/dividendos":          ".claude/commands/dividendos.py",
    "/stress-test":         ".claude/commands/stress_test.py",
    "/simulacao":           "scripts/simulacao_carteira.py",
    "/ips":                 ".claude/commands/ips.py",
    "/snapshot":            "scripts/data/market_snapshot.py",
    "/knowledge":           "knowledge/knowledge_cmd.py",
    "/otimizar-expansao":   "scripts/data/optimize_expansao.py",
}

# Comandos de IA — redirecionados para Claude Code (sem API key)
COMANDOS_IA = {
    "/analisar":            "analisar",
    "/tese":                "tese",
    "/pm":                  "pm",
    "/decidir":             "pm",
    "/earnings":            "earnings",
    "/comparar":            "comparar",
    "/morning-call":        "morning-call",
    "/mundo-economico":     "mundo-economico",
    "/investimento-do-dia": "investimento-do-dia",
    "/relatorio-semanal":   "relatorio-semanal",
    "/relatorio-mensal":    "relatorio-mensal",
    "/rebalancear":         "rebalancear",
    "/revisar-carteira":    "revisar-carteira",
    "/metas":               "metas",
}


def exibir_help():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║            SBWAA — Referência de Comandos  v2.8.6               ║
╚══════════════════════════════════════════════════════════════════╝

  Uso:  python sbwaa.py /COMANDO [argumentos]
  Dica: use PowerShell — Git Bash pode quebrar argumentos com /

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PORTFÓLIO  (local — sem IA, sem API key)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  python sbwaa.py /carteira
      Atualiza cotações e exibe posições, P&L% e alocação vs IPS.
      Ao final: projeção Monte Carlo 10/20/30 anos (2 cenários).

  python sbwaa.py /watchlist
      Lista todos os ativos analisados + carteira com último veredicto,
      data da análise e frescor (OK / defasado / rever).
      Flag: --rever   (mostra apenas os que precisam de nova análise)

  python sbwaa.py /adicionar --ticker PETR4 --tipo acao-on \\
                             --quantidade 100 --preco-medio 38.50 \\
                             --setor energia
  python sbwaa.py /vender --ticker PETR4 --quantidade 50 --preco 45.00
  python sbwaa.py /dividendos
  python sbwaa.py /risco-carteira
  python sbwaa.py /otimizar-expansao

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  MERCADO  (local)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  python sbwaa.py /snapshot
  python sbwaa.py /stress-test
  python sbwaa.py /stress-test covid-2020
  python sbwaa.py /stress-test custom -25
  python sbwaa.py /simulacao
      Backtest histórico 5 anos + Monte Carlo 10/20/30 anos com gráficos.
      Salva PNGs em logs/simulacao/ e atualiza params_cache.json.
      Flags: --patrimonio 50000  --aporte 1000  --no-graficos

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  KNOWLEDGE BASE  (local)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  python sbwaa.py /knowledge --status
  python sbwaa.py /knowledge --adicionar "C:\\relatorios\\doc.pdf"
  python sbwaa.py /knowledge --buscar "valuation petróleo Brasil"
  python sbwaa.py /knowledge --coletar-rss
  python sbwaa.py /knowledge --listar

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ANÁLISE COM IA  (digitar no chat do Claude Code)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /analisar PETR4       (pipeline completo: 8 agentes, 10 etapas)
  /tese PETR4           (Research + DCF + PM — rápido)
  /earnings MXRF11      (resultado trimestral)
  /comparar PETR4 VALE3 (análise lado a lado)
  /pm PETR4             (só Portfolio Manager, dados cacheados)
  /morning-call
  /mundo-economico
  /investimento-do-dia [categoria]
  /metas                (dashboard de metas financeiras)
  /relatorio-semanal
  /relatorio-mensal
  /rebalancear
  /revisar-carteira     (PM revisa cada posição: MANTER/AUMENTAR/REDUZIR/SAIR)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  SISTEMA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  python sbwaa.py /ips
  python sbwaa.py /ui          (interface desktop customtkinter)
  python sbwaa.py /status
  python sbwaa.py /help

══════════════════════════════════════════════════════════════════════
""")


def exibir_status():
    versao_path = PROJECT_ROOT / "VERSION.md"
    print(f"\n{'═'*55}")
    print(f"SBWAA — Status do Sistema")
    print(f"Modo: {'Claude Code (sem API key)' if MODO_CLAUDE_CODE else 'API key (anthropic)'}")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'═'*55}")
    if versao_path.exists():
        print(versao_path.read_text(encoding="utf-8"))
    print(f"{'═'*55}\n")


def redirecionar_claude_code(comando, args_extra):
    slash = COMANDOS_IA[comando]
    ticker = " ".join(args_extra).upper() if args_extra else ""
    exemplo = f"/{slash} {ticker}".strip()
    print(f"""
  Este comando usa IA e roda no Claude Code (sem API key).

  -> Digite no chat do Claude Code:
    {exemplo}

  O Claude Code vai executar os scripts de dados e fazer
  a analise completa sem precisar de ANTHROPIC_API_KEY.
""")


def main():
    if len(sys.argv) < 2:
        exibir_help()
        return

    raw = sys.argv[1]
    # Git Bash no Windows expande /cmd para C:/Program Files/Git/cmd
    # Normaliza extraindo só o nome base e prefixando com /
    if not raw.startswith("/") and "/" in raw:
        raw = "/" + Path(raw).name
    comando = raw.lower()
    args_extra = sys.argv[2:]

    if comando == "/help":
        exibir_help()
        return
    if comando == "/status":
        exibir_status()
        return
    if comando == "/ui":
        interface_path = PROJECT_ROOT / "interface" / "ui.py"
        if not interface_path.exists():
            print("\n Interface nao encontrada.\n")
            return
        subprocess.run([sys.executable, str(interface_path)])
        return
    if comando in COMANDOS_IA:
        redirecionar_claude_code(comando, args_extra)
        return
    if comando not in COMANDOS_LOCAIS:
        print(f"\n Comando '{comando}' nao reconhecido.")
        print("   Use /help para ver todos os comandos disponiveis.\n")
        return

    script_rel = COMANDOS_LOCAIS[comando]
    script_path = PROJECT_ROOT / script_rel
    if not script_path.exists():
        print(f"\n Script nao encontrado: {script_rel}\n")
        return

    subprocess.run([sys.executable, "-u", str(script_path)] + args_extra)


if __name__ == "__main__":
    main()
```

---

## 14. CORREÇÕES CRÍTICAS APLICADAS

Estas correções foram descobertas durante testes e devem ser aplicadas durante a reconstrução:

### Correção 1 — Git Bash path expansion (`sbwaa.py`)
**Problema:** No Windows, Git Bash expande `/carteira` para `C:/Program Files/Git/carteira`.  
**Solução:** Normalizar o argumento antes de processar:
```python
raw = sys.argv[1]
if not raw.startswith("/") and "/" in raw:
    raw = "/" + Path(raw).name
comando = raw.lower()
```

### Correção 2 — `SystemExit` em `fetch_brapi.py`
**Problema:** Erros HTTP lançavam `SystemExit` em vez de exceção catchable, impedindo o fallback para Yahoo Finance.  
**Solução:** Substituir todos os `raise SystemExit(...)` por `raise ValueError(...)`:
```python
except requests.exceptions.HTTPError as e:
    raise ValueError(f"Erro HTTP ao buscar {ticker}: {e}")
except requests.exceptions.ConnectionError:
    raise ValueError(f"Erro de conexão ao buscar {ticker}.")
except requests.exceptions.Timeout:
    raise ValueError(f"Timeout ao buscar {ticker}.")
```

### Correção 3 — Índices de coluna errados em `carteira.py`
**Problema:** P&L% estava sendo lido da coluna de P&L R$ (índice 6 em vez de 7).  
**Solução:**
```python
"pl_rs":  cols[7] if len(cols) > 7 else "",   # era cols[6]
"pl_pct": cols[8] if len(cols) > 8 else "",   # era cols[7]
```

### Correção 4 — Regex "Última atualização" em `carteira.py`
**Problema:** Pattern `r"Última atualização.*?:\s*(.+)"` capturava `** 2026-05-16` (com `**` do markdown bold).  
**Solução:**
```python
m = re.search(r"Última atualização[^0-9]*(\d{4}-\d{2}-\d{2}[^\n]+)", linha)
```

### Correção 5 — Linha em branco em `historico-trades.md`
**Problema:** Linha placeholder `|   |   |   |` na tabela fazia `add_ativo.py` inserir trades depois dela em vez de no início correto.  
**Solução:** Manter a tabela com apenas o header — sem linhas de placeholder:
```markdown
| Data | Ticker | Tipo | Operação | Qtd | Preço | Total R$ |
|------|--------|------|----------|-----|-------|----------|
```

### Correção 6 — UI output panel não crescia
**Problema:** Output panel tinha tamanho fixo e não expandia com a janela.  
**Solução:** Usar `grid` com `weight` e `sticky="nsew"`:
```python
self.grid_rowconfigure(2, weight=2)  # linha do output panel
frame.grid(row=2, column=0, sticky="nsew", ...)
```

### Correção 7 — Função morta `safe()` no `run_quant.py`
**Problema:** Função `safe()` definida mas nunca chamada (só `safe_pct()` é usada).  
**Solução:** Remover a função `safe()`.

### Correção 8 — `PROJECT_ROOT` errado em `ui.py`
**Problema:** `ui.py` foi movido para `interface/ui.py` mas ainda usava `PROJECT_ROOT = Path(__file__).parent` (apontava para `interface/` em vez da raiz do projeto). Todos os caminhos de scripts quebravam.  
**Solução:**
```python
PROJECT_ROOT = Path(__file__).parent.parent  # interface/ -> raiz
```

### Correção 9 — `/metas` ausente em `COMANDOS_IA` no `sbwaa.py`
**Problema:** O comando `/metas` foi adicionado ao sistema (v2.7.0) mas não foi incluído no dicionário `COMANDOS_IA` de `sbwaa.py`, causando "Comando não reconhecido" ao tentar redirecionar.  
**Solução:** Adicionar ao `COMANDOS_IA`:
```python
"/metas": "metas",
```

### Correção 10 — Parsing errado de total em `calcular_aporte_medio()`
**Problema:** O formato `{:,.2f}` do Python usa vírgula como separador de milhar e ponto como decimal (ex: `"1,200.00"`). O código inicial fazia `.replace(".", "").replace(",", ".")` invertendo separadores, resultando em `"1.200"` = 1.2 em vez de 1200.  
**Solução:**
```python
# CORRETO — vírgula = milhar, ponto = decimal; remover só a vírgula
total = float(total_str.replace(",", "").replace("R$", "").strip())
```

### Correção 11 — `UnicodeEncodeError` no Windows em `simulacao_carteira.py`
**Problema:** Caracteres Unicode (`→`, `═`, `✅`) em `print()` causavam `charmap codec can't encode character` no terminal Windows (cp1252).  
**Solução:** Adicionar no topo do script:
```python
import io, sys
if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
```
E executar com `python -X utf8 sbwaa.py /simulacao` (ou via `sbwaa.py` que já define `PYTHONUTF8=1`).

---

## 15. ROTINA DE TESTES

Após reconstrução, executar nesta ordem:

```bash
# 1. Dependências
python -c "import anthropic, yfinance, chromadb, customtkinter, pandas, numpy, scipy, matplotlib, arch; print('OK')"

# 2. sbwaa.py funcional
python sbwaa.py /help
python sbwaa.py /status

# 3. Pipeline de dados
python scripts/data/fetch_brapi.py PETR4
python scripts/data/fetch_yahoo.py
python scripts/data/market_snapshot.py

# 4. Adicionar ativo de teste e testar comandos de portfólio
python sbwaa.py /adicionar --ticker VALE3 --tipo acao-on --quantidade 50 --preco-medio 60.00 --setor mineracao
python sbwaa.py /carteira
python sbwaa.py /watchlist
python sbwaa.py /risco-carteira
python sbwaa.py /stress-test
python sbwaa.py /dividendos
python sbwaa.py /ips

# 5. Simulação (gera params_cache.json e PNGs)
python sbwaa.py /simulacao --no-graficos   # modo rápido sem janelas
python sbwaa.py /carteira                  # deve exibir projeção ao final

# 6. Knowledge base
python sbwaa.py /knowledge --status

# 7. Interface desktop
python sbwaa.py /ui

# 8. Limpar dados de teste
# (remover manualmente vault/01-ativos/VALE3/ e linha da carteira.md)
```

**Checklist de validação:**
- [ ] `fetch_brapi.py` retorna JSON (fallback para Yahoo se 401)
- [ ] `update_carteira.py` atualiza cotações corretamente
- [ ] `/carteira` exibe P&L% (não P&L R$) na coluna certa e projeção ao final
- [ ] `/watchlist` lista ativos com veredicto e frescor corretos
- [ ] `/stress-test` exibe impactos de todos os 4 cenários
- [ ] `/risco-carteira` exibe VaR, CVaR e circuit breakers
- [ ] `/simulacao` gera `logs/simulacao/params_cache.json` + PNGs
- [ ] `/carteira` usa params_cache.json para exibir dois cenários de projeção
- [ ] `ui.py` abre com PROJECT_ROOT correto (raiz do projeto), output cresce com a janela
- [ ] Comandos de IA redirecionam corretamente (não travam)
- [ ] Knowledge base inicializa sem erro

---

## 16. ESTADO ATUAL E VERSÕES

```
SBWAA v2.12.0 — 2026-05-28

Módulos:
  investments     v1.20.2 ✅ Operacional
                          /pm modo aporte: distribuição de capital multi-ativo
                          Outputs visuais Obsidian: carteira.md (barras █░, callouts), dividendos.md,
                            risco-carteira.md, stress-test.md, watchlist datado
                          DY ponderado e renda mensal no /dividendos e /carteira
                          Despolução de comandos (sem outputs intermediários poluentes)
  heartbeat       v2.0.0  ✅ Operacional — Automation Layer
                          scripts/automation/: dispatcher modular (main.py), executor Python+Claude
                            (runner.py), toast notification Windows (notifier.py), launcher.vbs
                            silencioso, setup_scheduler.py (instala tarefas reais no Task Scheduler)
                          3 slots automatizados: morning 07:45 / EOD 17:00 / weekend 08:00
                          WakeToRun + StartWhenAvailable ativados
                          heartbeat.py legado mantido para execução manual
  knowledge-base  v1.2.0  ✅ Operacional (RAG ativo; referências Markowitz indexadas; ~1.200 chunks)
  interface       v2.5.0  ✅ Operacional
                          vault/_templates/: 11 templates Obsidian (tese, analise, earnings, equity-research,
                            pm-decisao, snapshot, morning-call, macro, risk-snapshot, semana, mensal)
                          Obsidian app.json: templateFolder configurado para _templates
                          graph.json: color group #screening adicionado
                          docs/SBWAA-APRESENTACAO.md: documento apresentável do sistema

Modo de operação: Claude Code (sem API key)
  -> Comandos locais rodam via Python puro
  -> Comandos de IA são executados via chat do Claude Code / claude -p (automação)
  -> ANTHROPIC_API_KEY não necessária — usa subscription Claude Code
```

### Histórico de versões (v2.2.2 → v2.8.9)

| Versão  | Data       | Descrição                                                        |
|---------|------------|------------------------------------------------------------------|
| v2.2.2  | 2026-05-16 | Master Blueprint criado                                          |
| v2.2.3  | 2026-05-16 | Repositório GitHub + GUIA-COMANDOS.md separado do README         |
| v2.2.4  | 2026-05-17 | RAG integrado em todos os agentes LLM; livros corrigidos no log  |
| v2.2.5  | 2026-05-17 | Política de Git + GitHub Releases adicionada ao CLAUDE.md        |
| v2.2.6  | 2026-05-17 | Graph view Obsidian com hierarquia de cores; injeção de tipo-tag |
| v2.2.7  | 2026-05-18 | Protocolo de sessão + Stop hook de compliance + catch-up de docs |
| v2.2.8  | 2026-05-18 | Fix iniciar.vbs (sem CMD), botão IPS na UI, CLAUDE.md completo   |
| v2.2.9  | 2026-05-18 | Splash screen no terminal (splash.py) ao abrir pelo iniciar.vbs  |
| v2.2.10 | 2026-05-18 | SBWAA-LOGO.md para preview VS Code; Blueprint sincronizado        |
| v2.2.11 | 2026-05-18 | Gitignore para temp Windows (GUIDs); compliance script mais claro  |
| v2.2.12 | 2026-05-18 | Versões de módulos sincronizadas: investments v1.9.0, interface v2.0.3  |
| v2.2.13 | 2026-05-18 | Regra de versionamento de módulos adicionada ao CLAUDE.md              |
| v2.2.14 | 2026-05-18 | SBWAA-LOGO.md versionado + regra obrigatória no CLAUDE.md              |
| v2.2.15 | 2026-05-18 | Compliance script verifica SBWAA-LOGO.md automaticamente               |
| v2.2.16 | 2026-05-18 | ui.py label sincronizado com versão atual                              |
| v2.3.0  | 2026-05-19 | /vender, dividendos reescrito (Yahoo Finance), proventos na carteira   |
| v2.4.0  | 2026-05-20 | Consenso de analistas no Valuation Reviewer (fetch_consensus.py)       |
| v2.4.1  | 2026-05-20 | /watchlist (local) e /revisar-carteira (IA) adicionados                |
| v2.4.2  | 2026-05-20 | Reorganização de pastas: docs/, interface/, prompts/, _standby/        |
| v2.4.3  | 2026-05-20 | README.md atualizado com nova estrutura de pastas                      |
| v2.5.0  | 2026-05-20 | Fronteira Eficiente Markowitz no Quant (optimization.py, 10k Monte Carlo + SLSQP); /risco-carteira exibe fronteira + ajustes sugeridos |
| v2.5.1  | 2026-05-20 | /otimizar-expansao: análise dual carteira vs carteira+watchlist; marginal Sharpe contribution por candidato |
| v2.5.2  | 2026-05-20 | docs/SBWAA-WORKFLOW.md: workflow operacional completo (6 cadências, 5 fluxos oportunísticos, árvores de decisão) |
| v2.5.3  | 2026-05-20 | Auditoria docs: SBWAA-REFERENCIA.md (versão + /otimizar-expansao + mockup fronteira), SBWAA-MASTER-BLUEPRINT.md (versão + Estado Atual), ui.py (versão + botão Otimizar Expansão) |
| v2.6.0  | 2026-05-22 | Preço teto/chão no Valuation Reviewer: Graham (ações) √(22,5×LPA×VPA) com MS 10/15/20%; Bazin (FIIs) DPA/8% teto + DPA/12% chão; novo Passo 5 no pipeline; tabelas curta e longa atualizadas |
| v2.6.1  | 2026-05-22 | /analisar em batch: aceita múltiplos tickers separados por espaço; pipeline completo e isolado por ticker; tabela comparativa de veredictos ao final com prioridade de aporte |
| v2.6.2  | 2026-05-22 | /investimento-do-dia com filtro de categoria opcional: fii, acao, etf, etf-br, etf-intl, rf, td |
| v2.7.0  | 2026-05-22 | Sistema de Metas Financeiras: vault/metas.md, /metas (dashboard + projeções + milestones), integração morning-call, seção Metas no IPS, botão UI |
| v2.8.0  | 2026-05-22 | Agente Econometrician: GARCH(1,1), beta dinâmico rolling OLS, Fama-French 3F proxies BR, regressão macro BCB (Selic/IPCA/BRL/IBC-Br), correlações rolling, drawdown avançado (Calmar/Ulcer/Pain); Etapa 6 do /analisar; fetch_bcb.py; arch>=6.0.0 |
| v2.8.1  | 2026-05-22 | PM veredictos contextuais: 7 veredictos (COMPRAR/AGUARDAR/EVITAR para Modo A; AUMENTAR/MANTER/REDUZIR/SAIR para Modo B); Econometrician expandido com recomendação de tamanho de posição |
| v2.8.2  | 2026-05-22 | Correção PROJECT_ROOT em ui.py (interface/ → raiz); /metas adicionado a COMANDOS_IA em sbwaa.py |
| v2.8.3  | 2026-05-22 | Econometrician expandido com veredicto interpretativo final; veredictos contextuais em todos os comandos de análise |
| v2.8.4  | 2026-05-22 | Fix PROJECT_ROOT em ui.py confirmado; /metas em COMANDOS_IA de sbwaa.py |
| v2.8.5  | 2026-05-22 | /simulacao (scripts/simulacao_carteira.py): backtest 5 anos proxy IPS + Monte Carlo GBM 10/20/30 anos; fan chart P5/P25/P50/P75/P95; params_cache.json; projeção integrada no /carteira (sem aportes); matplotlib>=3.9.0 adicionado ao requirements |
| v2.8.6  | 2026-05-22 | Projeção /carteira com dois cenários: sem aporte e com aporte médio histórico (lê historico-trades.md); calcular_aporte_medio(); _mc_finais() iterativo; coluna "Ganho vs sem" no cenário com aporte |
| v2.8.7  | 2026-05-22 | Seção METAS — PROJECAO no /carteira: projeta quando cada meta de metas.md será atingida; patrimônio (analítico + MC); renda passiva (yield real ou 6% default → MC); metas livres (linear por aporte); status OK/ATENCAO vs data_alvo |
| v2.8.8  | 2026-05-22 | Renda passiva real: renda_atual = total_no_ano/12 (dividendos reais do ano); yield = total_no_ano/patrimônio (correto, anualizado); barra de progresso [###---] em patrimônio, renda passiva e metas livres |
| v2.8.9  | 2026-05-22 | /adicionar RF: --nome, --indexador, --taxa, --vencimento; auto-skip API; setor vira emissor; nota com tabela e frontmatter estruturado; TIPOS_OFF_EXCHANGE |
| v2.9.0  | 2026-05-25 | Rebranding completo UI (ciano, sidebar, header live); /watchlist --rever, /ips --editar, /simulacao flags, /status, RF fields no form, investimento-do-dia combobox; /analisar Etapa 9 separada por tipo |
| v2.10.0 | 2026-05-25 | vault/_templates/ com 11 templates Obsidian; /pm Passo 3 salva decisoes.md + pm-decisao-*.md; /relatorio-semanal Passo 4 gera risk snapshot semanal; Obsidian app.json configurado; graph.json #screening |
| v2.10.1 | 2026-05-25 | fetch_fundamentals.py substitui fetch_brapi.py por Yahoo Finance (sem API key); templates de análise enriquecidos com dados fundamentalistas |
| v2.10.2 | 2026-05-25 | fetch_investidor10.py — scraping Investidor10: P/VP, DY 12m, vacância, VPA, DPA, dividendos mensais (FIIs) e dados complementares de ações |
| v2.10.3 | 2026-05-25 | Fluxo interativo de aporte em /pm e /analisar: intenção → valor → validação → confirmação → registro |
| v2.10.4 | 2026-05-25 | SBWAA-GLOSSARIO.md: ~80 termos técnicos em 11 seções |
| v2.11.0 | 2026-05-25 | /pm modo aporte: distribuição de capital multi-ativo, ranqueamento por IPS+score, auto-reflow após /analisar |
| v2.11.1 | 2026-05-26 | Outputs visuais Obsidian: carteira.md (barras █░, callouts), dividendos.md, risco-carteira.md, stress-test.md, watchlist datado; despolução de comandos |
| v2.11.2 | 2026-05-27 | Varredura completa testes (55/55 OK); fix /help versão; fix optimize_expansao conflito de módulo |
| v2.12.0 | 2026-05-28 | Automation Layer: scripts/automation/ — dispatcher modular, 3 slots Task Scheduler, launcher.vbs silencioso, toast notification, WakeToRun; SBWAA-APRESENTACAO.md |
| v2.13.0 | 2026-05-29 | Motor tributário IR/IOF + RF Oportunidade (Caixinha Nubank): /vender RF, /comprar RF com check automático; TIPOS_OFF_EXCHANGE |
| v2.13.1 | 2026-05-29 | Fix /pm Modo Aporte: roteamento A/B/C correto; check RF Oportunidade integrado ao fluxo de aporte |
| v2.13.2 | 2026-05-29 | /att-info-system: protocolo completo de fechamento de sessão com 8 fases; releases individuais por versão |
| v2.14.0 | 2026-05-29 | /alerta: monitor de preços bidirecional com extração automática de teto/chão do vault |
| v2.14.1 | 2026-05-29 | /vender RF/TD: IR regressivo + IOF + resgate parcial por --valor; fix schtasks /D incompatível |
| v2.15.0 | 2026-05-29 | /performance: benchmark MTD/YTD/12m vs IBOV/CDI/IPCA; fetch_yahoo.py histórico de índices |
| v2.15.1 | 2026-05-29 | Persistência P&L diário em equity-curve.md + curva equity real no /carteira |
| v2.16.0 | 2026-05-29 | /fluxo-caixa: projeção de renda passiva mês a mês para 12 meses com calendário de dividendos |
| v2.17.0 | 2026-05-29 | /correlacao: heatmap ASCII por categoria; fix pipeline Quant (import relativo → absoluto) |
| v2.18.0 | 2026-05-29 | Suporte a ativos internacionais USD: fetch_yahoo.py cotação em dólar; conversão BRL no portfólio |
| v2.19.0 | 2026-05-29 | /earning-calendar: calendário de resultados com alertas D-7/D-1 integrados ao heartbeat |
| v2.20.0 | 2026-06-01 | cache_manager.py centralizado: TTL configurável por tipo via .env; /cache --status/--clear; fetchers migrados |

### Diferenças do projeto original para o atual

| Aspecto             | Original (F0-F8)          | Estado atual               |
|---------------------|---------------------------|----------------------------|
| Interface visual    | Streamlit (browser)       | customtkinter (desktop)    |
| `/ui`               | `streamlit run app.py`    | `python ui.py`             |
| Modo API            | Com ANTHROPIC_API_KEY     | Claude Code (sem key)      |
| Comandos IA         | Chamam API diretamente    | Redirecionam para chat CC  |
| UTF-8               | Não configurado           | Forçado via `PYTHONUTF8=1` |
| sbwaa.py            | `os.system(f"python...")` | `subprocess.run([...])` + correção Git Bash |

### Uso diário típico

```bash
# Manhã
python sbwaa.py /snapshot          # atualizar dados macro
python sbwaa.py /carteira          # ver posições + projeção integrada ao final

# Análise (no chat do Claude Code)
/morning-call
/analisar PETR4

# Aporte de capital (no chat do Claude Code)
/pm                  # PM conversacional — distribui valor entre múltiplos ativos
/pm 700              # atalho com valor pré-definido

# Semana
python sbwaa.py /risco-carteira    # métricas HF + Fronteira Eficiente
python sbwaa.py /watchlist         # veredictos e frescor das análises
# /relatorio-semanal               (no chat do Claude Code)

# Mensal / expansão de carteira
python sbwaa.py /otimizar-expansao # análise dual: carteira vs carteira+watchlist
python sbwaa.py /simulacao         # atualizar backtest e params Monte Carlo
# /revisar-carteira                (no chat do Claude Code)
# /rebalancear                     (no chat do Claude Code)
# /metas                           (no chat do Claude Code — dashboard de metas)

# Vender / rebalancear posição
python sbwaa.py /vender --ticker PETR4 --quantidade 50 --preco 45.00

# Adicionar novo ativo
python sbwaa.py /adicionar --ticker MXRF11 --tipo fii --quantidade 200 --preco-medio 9.80 --setor fiis
```

> Workflow completo (cadências diária, semanal, mensal, trimestral, anual e oportunístico):
> `docs/SBWAA-WORKFLOW.md`

---

*Blueprint atualizado em 2026-05-25 (v2.10.0). Para atualizar, editar este arquivo e bumpar VERSION.md.*
