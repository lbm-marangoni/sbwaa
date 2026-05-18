# SBWAA — Guia de Comandos

> Referência completa de todos os comandos do sistema.
> Para instalação e configuração inicial: [`README.md`](README.md)

**Versão: v2.2.9**

---

## O que é o SBWAA

SBWAA é um sistema pessoal de gestão de portfólio e análise de ativos financeiros que combina:

- **7 agentes de IA especializados** que analisam ativos do zero ao veredicto final
- **Pipeline de dados automático** via Brapi (BR) e Yahoo Finance (macro/internacional)
- **Base de conhecimento RAG** com indexação semântica de PDFs, relatórios e notícias RSS
- **Painel visual** customtkinter com todos os comandos acessíveis por botão
- **Vault Obsidian** como repositório de notas, teses, decisões e relatórios

O sistema opera em dois modos:
- **Modo Claude Code** (padrão) — sem API key, comandos de IA rodam no chat do Claude Code
- **Modo API** — com `ANTHROPIC_API_KEY` no `.env`, agentes executam via subprocess

---

## Configuração inicial

### 1. Instalar dependências

```powershell
pip install -r requirements.txt
```

Pacotes principais: `anthropic`, `yfinance`, `pandas`, `numpy`, `chromadb`,
`sentence-transformers`, `PyPDF2`, `feedparser`, `customtkinter`, `plotly`,
`python-docx`, `openpyxl`, `beautifulsoup4`, `python-dotenv`, `requests`, `scipy`.

### 2. Configurar API key (opcional — só para modo API)

```powershell
Copy-Item ".env.template" ".env"
notepad ".env"    # substituir 'sua_chave_aqui' pela ANTHROPIC_API_KEY
```

Sem API key, todos os comandos locais funcionam normalmente.
Comandos de IA funcionam digitando os slash commands no chat do Claude Code.

### 3. Configurar UTF-8 no terminal (Windows — uma vez por sessão)

```powershell
$env:PYTHONUTF8 = "1"
```

> **Importante:** Use sempre **PowerShell** para rodar `python sbwaa.py /comando`.
> O Git Bash converte argumentos `/comando` em caminhos do sistema (`C:/Program Files/Git/comando`),
> o que quebra o roteamento. O sistema tenta corrigir isso automaticamente, mas PowerShell é mais seguro.

---

## Ponto de entrada

Todos os comandos passam pelo mesmo arquivo:

```powershell
python sbwaa.py /COMANDO [argumentos]
```

Para ver todos os comandos disponíveis com exemplos de uso:

```powershell
python sbwaa.py /help
python sbwaa.py /status    # versão atual e modo do sistema
```

---

## Comandos locais (sem IA / sem API key)

Estes comandos rodam scripts Python locais e retornam output no terminal imediatamente.

> **Dica — rodar comandos direto no chat do Claude Code:**
> Prefixe qualquer comando com `!` para executá-lo sem sair do chat.
> ```
> ! python sbwaa.py /carteira
> ! python sbwaa.py /risco-carteira
> ! python sbwaa.py /snapshot
> ```
> O output aparece diretamente na conversa. Útil para combinar um comando local
> com um slash command de IA na mesma sessão.

---

### `/carteira` — Snapshot da carteira

Atualiza cotações via Brapi/Yahoo e exibe posições, P&L e alocação vs IPS.

```powershell
python sbwaa.py /carteira
```

Output: tabela de posições com preço médio, preço atual, P&L% e alocação por classe.

---

### `/adicionar` — Adicionar ativo à carteira

Valida o ticker nas APIs, insere na `carteira.md`, registra no `historico-trades.md`
e cria pasta `vault/01-ativos/TICKER/` com nota de tese inicial.

```powershell
python sbwaa.py /adicionar --ticker PETR4 --tipo acao-on --quantidade 100 --preco-medio 38.50 --setor energia
python sbwaa.py /adicionar --ticker MXRF11 --tipo fii --quantidade 500 --preco-medio 9.80 --setor fundos-imobiliarios
python sbwaa.py /adicionar --ticker IVV --tipo etf-intl --quantidade 10 --preco-medio 520.00 --setor global

# Pular validação nas APIs (útil offline ou para ativos não suportados)
python sbwaa.py /adicionar --ticker XPTO3 --tipo acao-on --quantidade 50 --preco-medio 12.00 --setor tecnologia --skip-validacao
```

**Tipos válidos para `--tipo`:**

| Flag          | Tipo                  | Label exibido   |
|---------------|-----------------------|-----------------|
| `acao-on`     | Ação Ordinária        | 🟦 AÇÃO ON      |
| `acao-pn`     | Ação Preferencial     | 🟦 AÇÃO PN      |
| `fii`         | Fundo Imobiliário     | 🟩 FII          |
| `etf-br`      | ETF Brasileiro        | 🟨 ETF BR       |
| `etf-intl`    | ETF Internacional     | 🟥 ETF INTL     |
| `renda-fixa`  | Renda Fixa            | ⬜ RF           |
| `tesouro`     | Tesouro Direto        | 🟪 TD           |
| `debenture`   | Debênture             | 🟫 DEB          |
| `cri-cra`     | CRI ou CRA            | 🟧 CRI/CRA      |

---

### `/risco-carteira` — Métricas quantitativas de risco

Roda o Quant/Data Engineer e o Risk Engineer localmente (sem IA, só cálculo numérico)
e exibe VaR, CVaR, Sharpe, drawdown, beta e circuit breakers do IPS.

```powershell
python sbwaa.py /risco-carteira
```

Output: VaR 95% (1 dia), CVaR, Sharpe 12m, volatilidade anual, drawdown máximo,
beta vs IBOV, concentração máxima e status dos circuit breakers.

> Valores monetários normalizados em R$ 100k para preservar privacidade.

---

### `/dividendos` — Calendário e histórico de proventos

Busca dados de dividendos via Yahoo Finance para todos os ativos da carteira.

```powershell
python sbwaa.py /dividendos
```

Output: próximos dividendos (60 dias), total recebido no ano por ativo e Yield on Cost.

---

### `/stress-test` — Simulação de choques na carteira

Aplica cenários históricos ou choque personalizado ao beta da carteira.

```powershell
# Todos os cenários históricos de uma vez
python sbwaa.py /stress-test

# Cenário específico (busca por nome parcial)
python sbwaa.py /stress-test crise-2008
python sbwaa.py /stress-test covid-2020
python sbwaa.py /stress-test eleicoes-2022
python sbwaa.py /stress-test lula-2002

# Choque personalizado (qualquer percentual)
python sbwaa.py /stress-test custom -20
python sbwaa.py /stress-test custom -35
python sbwaa.py /stress-test custom 15
```

Cenários disponíveis: Crise Financeira 2008 (-41%), COVID Março 2020 (-30%),
Incerteza Eleitoral 2022 (-15%), Crise de Confiança 2002 (-17%).

> Patrimônio normalizado em R$ 100k — privacidade preservada.

---

### `/ips` — Exibir e editar o IPS

Exibe o Investment Policy Statement atual com perfil, alocação alvo e limites de risco.

```powershell
python sbwaa.py /ips
python sbwaa.py /ips --editar    # abre o arquivo para edição
```

---

### `/snapshot` — Snapshot diário de mercado

Busca dados macro globais (IBOV, S&P500, Nasdaq, DXY, BRL/USD, Petróleo WTI,
Ouro, Juros EUA 10Y) e cotações da carteira e salva nota no vault.

```powershell
python sbwaa.py /snapshot
```

Output salvo em: `vault/02-relatorios/diarios/snapshot-YYYY-MM-DD.md`

---

### `/knowledge` — Base de conhecimento RAG

Gerencia a base vetorial de documentos financeiros (ChromaDB + embeddings multilingual).

```powershell
# Ver status da base (total de documentos, tamanho, última indexação)
python sbwaa.py /knowledge --status

# Indexar arquivo único (PDF, DOCX, TXT, MD)
python sbwaa.py /knowledge --adicionar "C:\relatorios\resultado-petr4-3t24.pdf"

# Indexar pasta inteira recursivamente
python sbwaa.py /knowledge --adicionar "vault/01-ativos/PETR4/"

# Busca semântica (retorna chunks relevantes rankeados por score)
python sbwaa.py /knowledge --buscar "valuation petróleo Brasil"
python sbwaa.py /knowledge --buscar "resultado EBITDA 2024 siderurgia"

# Coletar e indexar notícias dos feeds RSS configurados
python sbwaa.py /knowledge --coletar-rss

# Listar todos os documentos indexados
python sbwaa.py /knowledge --listar
```

Fontes RSS padrão: Valor Econômico, InfoMoney, BCB, Bloomberg, Reuters.

---

### `/ui` — Painel visual

Abre o painel desktop em customtkinter com todos os comandos acessíveis por botão,
formulários para entrada de dados e output em tempo real na janela.

```powershell
python sbwaa.py /ui
# ou diretamente:
python ui.py
```

O painel tem 5 abas: **Portfólio**, **Análise (IA)**, **Mercado**, **Relatórios (IA)**, **Knowledge**.
Comandos locais executam direto. Comandos de IA copiam o comando para o clipboard.

---

## Comandos de IA (Claude Code — sem API key)

Estes comandos acionam agentes de IA. No modo padrão (sem API key),
o terminal exibe a instrução de uso e o botão `/ui` copia para o clipboard.
**Para executar: digite o comando diretamente no chat do Claude Code.**

---

### `/analisar TICKER` — Pipeline completo de análise (8 etapas)

Executa todos os 7 agentes em sequência para um ativo.

```
/analisar PETR4
/analisar VALE3
/analisar MXRF11
```

Etapas: dados de mercado → Market Researcher → Earnings Reviewer →
Model Builder (DCF) → Valuation Reviewer → Quant → Risk Engineer → Portfolio Manager.

Output gerado em `vault/01-ativos/TICKER/`.

---

### `/tese TICKER` — Tese rápida (Research + DCF + PM)

Versão acelerada do pipeline — pula Earnings detalhado e Quant/Risk standalone.
Ideal para primeira avaliação de um ativo.

```
/tese PETR4
/tese VALE3 --completo
```

---

### `/earnings TICKER` — Revisão de resultados trimestrais

Analisa os resultados mais recentes do ativo: receita, EBITDA, lucro líquido,
dívida e guidance. Compara com trimestres anteriores.

```
/earnings PETR4
/earnings WEGE3
```

---

### `/comparar TICKER1 TICKER2` — Análise comparativa

Coloca dois ativos lado a lado em valuation, qualidade, risco e retorno.
Gera recomendação de alocação relativa.

```
/comparar PETR4 VALE3
/comparar MXRF11 HGLG11
```

---

### `/pm TICKER` — Decisão do Portfolio Manager

Executa apenas o Portfolio Manager com base nos dados já cacheados do ativo.
Retorna veredicto COMPRAR / AGUARDAR / EVITAR com sizing sugerido.

```
/pm PETR4
/pm VALE3
```

> O sizing é calculado localmente (sem enviar patrimônio à API).

---

### `/morning-call` — Briefing pré-abertura

Compila snapshot macro + Market Researcher + alertas ativos em um briefing diário.

```
/morning-call
```

---

### `/mundo-economico` — Macro do dia

Panorama do cenário econômico global e impactos no Brasil.

```
/mundo-economico
```

---

### `/investimento-do-dia` — Oportunidade do dia

Sugere 1-2 ativos para explorar análise com base no IPS e no cenário macro atual.

```
/investimento-do-dia
```

---

### `/relatorio-semanal` — Relatório semanal

P&L da semana, métricas de performance e outlook. Gera `.md` e `.docx`.

```
/relatorio-semanal
```

Output em: `vault/02-relatorios/semanais/`

---

### `/relatorio-mensal` — Relatório mensal

Relatório completo do mês: performance, análise de risco, revisão de teses,
comparação com benchmarks. Gera `.md` e `.docx`.

```
/relatorio-mensal
```

Output em: `vault/02-relatorios/mensais/`

---

### `/rebalancear` — Sugestão de rebalanceamento

Compara alocação atual com os alvos do IPS, identifica desvios acima de ±5%
e sugere ajustes com valores estimados de compra/venda.

```
/rebalancear
```

---

## Comandos de sistema

```powershell
python sbwaa.py /help      # lista todos os comandos com sintaxe
python sbwaa.py /status    # versão atual, modo e data
```

---

## Os 7 agentes

| Agente             | Modelo            | Função                                         |
|--------------------|-------------------|------------------------------------------------|
| Market Researcher  | claude-sonnet-4-6 | Análise macro, setorial e posicionamento        |
| Earnings Reviewer  | claude-sonnet-4-6 | Revisão de resultados trimestrais               |
| Model Builder      | claude-opus-4-6   | Construção de DCF e modelos de valuation        |
| Valuation Reviewer | claude-sonnet-4-6 | Revisão crítica do modelo, equity research      |
| Quant/Data Eng.    | claude-sonnet-4-6 | Métricas quantitativas: Sharpe, VaR, correlação |
| Risk Engineer      | claude-opus-4-6   | VaR, CVaR, stress tests, circuit breakers       |
| Portfolio Manager  | claude-opus-4-6   | Decisão final: COMPRAR / AGUARDAR / EVITAR      |

Cada agente tem um `SKILL.md` com seu sistema de instruções e um `run_*.py`
que pode ser chamado diretamente ou via pipeline `/analisar`.

---

## Rotina de uso sugerida

### Diário (manhã — 5 min)
```powershell
python sbwaa.py /snapshot       # macro global + carteira
# ou no Claude Code:
/morning-call                   # snapshot + análise macro + alertas
```

### Por demanda (quando for estudar um ativo)
```
/analisar TICKER    # análise completa
/tese TICKER        # visão rápida
```

### Semanal
```powershell
python sbwaa.py /risco-carteira
# no Claude Code:
/relatorio-semanal
/rebalancear
```

### Mensal
```
/relatorio-mensal
```

---

## Estrutura de arquivos

```
SBWAA/
├── sbwaa.py                    ← ponto de entrada único de todos os comandos
├── ui.py                       ← painel visual (customtkinter)
├── requirements.txt
├── .env                        ← API key (não versionado)
├── .env.template
├── CLAUDE.md                   ← políticas globais, roteamento de modelos
├── VERSION.md
├── CHANGELOG.md
│
├── .claude/
│   ├── agents/
│   │   ├── market-researcher/      ← SKILL.md + run_market_researcher.py
│   │   ├── earnings-reviewer/      ← SKILL.md + run_earnings_reviewer.py
│   │   ├── model-builder/          ← SKILL.md + run_model_builder.py
│   │   ├── valuation-reviewer/     ← SKILL.md + run_valuation_reviewer.py
│   │   ├── quant-data-engineer/    ← SKILL.md + run_quant.py + calculators/
│   │   ├── risk-engineer/          ← SKILL.md + run_risk_engineer.py + calculators/
│   │   └── portfolio-manager/      ← SKILL.md + run_pm.py + run_analisar.py
│   └── commands/                   ← script de cada slash command local
│       ├── carteira.py
│       ├── risco_carteira.py
│       ├── dividendos.py
│       ├── stress_test.py
│       ├── ips.py
│       └── ...
│
├── scripts/
│   ├── data/
│   │   ├── fetch_brapi.py          ← cotações e fundamentalistas BR (Brapi)
│   │   ├── fetch_yahoo.py          ← macro, ETFs e histórico (Yahoo Finance)
│   │   ├── update_carteira.py      ← atualiza preços e P&L na carteira.md
│   │   ├── add_ativo.py            ← adiciona ativo à carteira
│   │   ├── market_snapshot.py      ← snapshot diário de mercado
│   │   └── cache/                  ← cache JSON com TTL de 4h
│   ├── alerts/
│   │   └── check_alerts.py         ← 8 tipos de alerta automático
│   ├── heartbeat/
│   │   ├── heartbeat.py            ← processo diário automatizado
│   │   └── schedule_heartbeat.py   ← instruções de agendamento
│   └── diagnostico.py              ← auditoria de integridade do sistema
│
├── knowledge/
│   ├── indexer.py                  ← indexação de documentos no ChromaDB
│   ├── retriever.py                ← busca semântica
│   ├── rss_collector.py            ← coleta de feeds RSS
│   ├── knowledge_cmd.py            ← handler do comando /knowledge
│   ├── save_synthesis.py           ← salva sínteses RAG no vault
│   ├── raw/                        ← documentos brutos (.gitignore)
│   ├── indexed/                    ← log de indexação (hash MD5)
│   └── sources/                    ← configuração de feeds RSS
│
└── vault/                          ← notas Obsidian
    ├── 00-portfolio/
    │   ├── carteira.md             ← posições ativas (gerenciado automaticamente)
    │   ├── ips.md                  ← Investment Policy Statement
    │   ├── historico-trades.md     ← log de operações
    │   └── decisoes.md             ← log de decisões do PM
    ├── 01-ativos/                  ← uma pasta por ticker (tese, DCF, earnings...)
    ├── 02-relatorios/              ← diários, semanais, mensais
    ├── 03-macro/                   ← notas do Market Researcher
    ├── 04-knowledge/               ← sínteses RAG
    └── 05-risk/                    ← snapshots de risco quantitativo
```

---

## Segurança

- Dados de portfólio (posições, preço médio, patrimônio) **nunca saem do vault local**
- APIs externas recebem apenas tickers públicos, datas e parâmetros de mercado
- Sizing do Portfolio Manager é calculado localmente — a API recebe apenas pesos percentuais
- Stress tests normalizam o patrimônio em R$ 100k para exibição
- Cache em `scripts/data/cache/` fica exclusivamente local

Regras completas: `CLAUDE.md` — seção Security Policy.

---

## Dependências e compatibilidade

- **Python:** 3.10+
- **SO:** Windows 10/11 (testado), macOS e Linux (compatível)
- **Terminal:** PowerShell recomendado no Windows
- **Obsidian:** opcional — vault funciona sem o app aberto

```powershell
pip install -r requirements.txt
```
