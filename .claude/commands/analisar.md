---
description: Pipeline completo de análise de ativo (8 etapas) sem API key — usa Claude Code como agente. Aceita um ou mais tickers separados por espaço.
---

# /analisar $ARGUMENTS

Execute o pipeline completo de análise para: **$ARGUMENTS**

## DETECÇÃO DE MODO

Antes de iniciar, identifique quantos tickers estão em `$ARGUMENTS`:
- **1 ticker** (ex: `PETR4`): executar pipeline único — comportamento idêntico ao original.
- **2+ tickers** (ex: `PETR4 VALE3 XPML11`): executar pipeline completo e isolado para **cada ticker em sequência**. Ao final de todos, gerar tabela comparativa.

Para múltiplos tickers: informe no início quais serão analisados e em qual ordem, com o formato:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANÁLISE EM BATCH — {N} ativos
Ordem: TICKER1 → TICKER2 → TICKER3
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## PIPELINE POR TICKER

Execute as etapas abaixo integralmente para cada ticker antes de passar ao próximo.
Ao iniciar cada ativo em batch, exibir um cabeçalho de progresso:
```
══════════════════════════════════════════════
[1/2] ANALISANDO: TICKER1
══════════════════════════════════════════════
```

---

### ETAPA 0 — Preparação

Defina ROOT como `C:\Users\lbmma\Downloads\Local\SBWAA` e execute com `$env:PYTHONUTF8 = "1"`.

Rode em sequência:
```powershell
$env:PYTHONUTF8 = "1"; cd "C:\Users\lbmma\Downloads\Local\SBWAA"
python scripts/data/fetch_fundamentals.py {TICKER}
python scripts/data/fetch_yahoo.py --macro
python scripts/data/fetch_bcb.py
python scripts/data/fetch_consensus.py {TICKER}
python scripts/data/update_carteira.py
```

> Em batch: `fetch_yahoo.py --macro` e `fetch_bcb.py` rodam apenas uma vez para o primeiro ticker. Os demais aproveitam o cache do dia.

Leia os arquivos de cache gerados:
- `scripts/data/cache/fundamentals_{TICKER}_*.json` — dados fundamentalistas BR
- `scripts/data/cache/yahoo_*.json` — macro global (todos os arquivos do dia)
- `scripts/data/cache/consensus_{TICKER}_*.json` — consenso de analistas (disponível quando houver cobertura)

---

### ETAPA 1 — Market Researcher

Leia `.claude/agents/market-researcher/SKILL.md` e execute a análise de mercado para **{TICKER}**:
- Contexto macro (dados dos caches Yahoo)
- Setor e posicionamento competitivo
- Catalisadores e riscos macro relevantes hoje

> Em batch: o contexto macro global é compartilhado entre todos os ativos — foque na análise setorial e nos catalisadores específicos de cada ticker.

---

### ETAPA 2 — Earnings Reviewer

Leia `.claude/agents/earnings-reviewer/SKILL.md` e execute a revisão de resultados para **{TICKER}**:
- Use os dados do cache Brapi (P/L, P/VP, margem, ROE, dívida líquida/EBITDA)
- Qualidade dos resultados, tendência, surpresas vs estimativas

---

### ETAPA 3 — Model Builder (DCF)

Leia `.claude/agents/model-builder/SKILL.md` e execute a modelagem para **{TICKER}**:
- Se ação: modelo DCF com premissas explícitas (WACC, g, projeção de FCL)
- Se FII: modelo de Gordon (DY sustentável, cap rate, crescimento de aluguéis)
- Output: preço-alvo, upside/downside vs cotação atual, margem de segurança

---

### ETAPA 4 — Valuation Reviewer

Leia `.claude/agents/valuation-reviewer/SKILL.md` e execute a revisão de valuation para **{TICKER}**:
- Crítica ao modelo DCF construído acima
- Múltiplos comparáveis (P/L, EV/EBITDA, P/VP setorial)
- Preço teto/chão: Graham (ações) ou Bazin (FIIs)
- Veredicto de valuation: BARATO / JUSTO / CARO com justificativa

---

### ETAPA 5 — Quant / Data Engineer

Execute os scripts quantitativos (não precisam de API):
```powershell
python .claude/agents/quant-data-engineer/run_quant.py
```

Leia o cache gerado `scripts/data/cache/quant_*.json` e apresente as métricas chave:
- Sharpe, volatilidade anualizada, drawdown máximo, beta IBOV
- Correlação com outros ativos da carteira

---

### ETAPA 6 — Econometrician

Execute os modelos econométricos e estatísticos avançados:
```powershell
python .claude/agents/econometrician/run_econometrician.py {TICKER}
```

Leia `.claude/agents/econometrician/SKILL.md` e interprete o cache gerado
`scripts/data/cache/econometria_{TICKER}_{DATA}.json`:

- **GARCH**: regime de volatilidade, persistência de choques, half-life
- **Beta dinâmico**: betas em 60d / 126d / 252d, tendência, R²
- **Fama-French 3F (proxies BR)**: alpha anualizado, betas de fator (mercado, SMB, HML)
- **Macro sensibilidade (BCB)**: Δselic, IPCA, ΔBRL/USD, IBC-Br — driver principal
- **Correlações rolling**: estabilidade vs carteira, alertas de diversificação
- **Drawdown avançado**: Calmar, Ulcer Index, Pain Index, tempo médio de recuperação

---

### ETAPA 7 — Risk Engineer

Execute os scripts de risco (não precisam de API):
```powershell
python .claude/agents/risk-engineer/run_risk_engineer.py
```

Leia o cache gerado `scripts/data/cache/risk_*.json` e avalie:
- VaR 95% histórico e paramétrico
- CVaR, drawdown atual
- Circuit breakers do IPS: estão dentro dos limites?

---

### ETAPA 8 — Portfolio Manager (Decisão Final)

Leia `.claude/agents/portfolio-manager/SKILL.md` e tome a decisão final sobre **{TICKER}**:
- Consolide os outputs das etapas anteriores
- Leia explicitamente `scripts/data/cache/econometria_{TICKER}_{DATA}.json` e incorpore os bullets de `## Para o Portfolio Manager` da nota do Econometrician na síntese — eles são inputs obrigatórios para o veredicto
- Verifique adequação ao IPS (`vault/00-portfolio/ips.md`)
- Verifique posição atual em `vault/00-portfolio/carteira.md`
- Emita veredicto: **COMPRAR / AGUARDAR / EVITAR** com sizing sugerido
- Justificativa em no máximo 5 bullets com dados concretos — pelo menos 1 bullet deve referenciar dados do Econometrician (regime GARCH, beta dinâmico, alpha ou correlação rolling)

---

### ETAPA 9 — Salvar Output

Salve os arquivos abaixo. Regra geral:
- **Específico do ativo** → `vault/01-ativos/{TICKER}/`
- **Geral / não vinculado a um ativo** → `vault/02-relatorios/diarios/` (como já estava)

#### 9a — Market Researcher (geral)
Salve em `vault/02-relatorios/diarios/market-researcher-YYYY-MM-DD.md`
usando o formato definido no SKILL do Market Researcher.
> Em batch: apenas um arquivo por dia — não duplicar se já existir.

#### 9b — Earnings Reviewer (específico do ativo)
Salve em `vault/01-ativos/{TICKER}/earnings-{TICKER}-{TRIMESTRE}.md`
usando o formato definido no SKILL do Earnings Reviewer.

#### 9c — Equity Research / Valuation Reviewer (específico do ativo)
Salve em `vault/01-ativos/{TICKER}/equity-research-{TICKER}-YYYY-MM-DD.md`
usando a **versão longa** definida no SKILL do Valuation Reviewer.

#### 9d — PM — Decisão (específico do ativo)
Salve em `vault/01-ativos/{TICKER}/pm-decisao-{TICKER}-YYYY-MM-DD.md`
usando o formato definido no SKILL do Portfolio Manager.

#### 9e — Nota consolidada (específico do ativo)
Salve em `vault/01-ativos/{TICKER}/analise-{TICKER}-YYYY-MM-DD.md` usando o template `vault/_templates/analise-ativo.md` como base. Preencher TODAS as seções com o conteúdo das etapas anteriores.

```markdown
---
tags: [ativo, equity-research, {tipo-lowercase}]
ticker: {TICKER}
tipo: {label do tipo conforme CLAUDE.md — ex: 🟩 FII}
data: {YYYY-MM-DD}
veredicto: COMPRAR | AGUARDAR | EVITAR
preco-alvo: {valor numérico}
upside: {+/-X%}
agente: portfolio-manager
---

# Análise — {TICKER} ({YYYY-MM-DD})

## Resumo Executivo

**Veredicto:** COMPRAR / AGUARDAR / EVITAR
**Preço-alvo:** R$ {XX,XX}
**Upside DCF:** {+/-X%}
**Preço teto (Graham/Bazin):** R$ {XX,XX}

## Market Research
{síntese do Market Researcher em 2-3 parágrafos — macro, setor, catalisadores}

## Earnings
{síntese do Earnings Reviewer — DPA/receita, tendência, impacto na tese}

## Valuation / DCF
{síntese do Model Builder + Valuation Reviewer — método, premissas chave, veredicto}

## Quant & Econometria
{síntese do Quant + Econometrician — GARCH, beta, Calmar, correlação carteira}

## Risco
{síntese do Risk Engineer — VaR, circuit breakers, drawdown}

## Decisão PM
{síntese da decisão — veredicto, sizing, nível de entrada, stop}

## Links
- [[carteira]]
- [[ips]]
- [[market-researcher-{YYYY-MM-DD}]]
- [[earnings-{TICKER}-{TRIMESTRE}]]
- [[equity-research-{TICKER}-{YYYY-MM-DD}]]
- [[pm-decisao-{TICKER}-{YYYY-MM-DD}]]
```

---

## TABELA COMPARATIVA FINAL (somente em batch — 2+ tickers)

Após concluir o pipeline de todos os tickers, gerar obrigatoriamente:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESUMO COMPARATIVO — {DATA}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ticker  Tipo         Veredicto  Valuation  Upside DCF  P. Teto    Cotação   Sizing
──────────────────────────────────────────────────────────────────────────────────
TICK1   🟦 AÇÃO PN   COMPRAR    BARATO     +28%        R$ 48,00   R$ 38,00  8%
TICK2   🟩 FII       AGUARDAR   JUSTO      +9%         R$ 115,00  R$ 106,00 —

──────────────────────────────────────────────────────────────────────────────────
Prioridade de aporte (PM): TICK1 > TICK2
```

Colunas obrigatórias: Ticker | Tipo | Veredicto PM | Valuation Reviewer | Upside DCF | Preço Teto (Graham ou Bazin) | Cotação atual | Sizing sugerido

Linha "Prioridade de aporte": ordenar os ativos com veredicto COMPRAR por upside DCF decrescente. Ativos AGUARDAR/EVITAR ficam fora da ordenação de prioridade.
