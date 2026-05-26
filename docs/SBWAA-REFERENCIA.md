# SBWAA — Referência de Comandos

> Documento complementar ao [`GUIA-COMANDOS.md`](docs/GUIA-COMANDOS.md).
> O guia cobre sintaxe e flags. Esta referência cobre **o que cada comando entrega**:
> campos, estrutura do output e o que você pode esperar ver.

**Versão: v2.11.0**

---

## Índice

**Local (sem IA)**
- [/carteira](#carteira)
- [/watchlist](#watchlist)
- [/risco-carteira](#risco-carteira)
- [/otimizar-expansao](#otimizar-expansao)
- [/dividendos](#dividendos)
- [/snapshot](#snapshot)
- [/stress-test](#stress-test)
- [/simulacao](#simulacao)
- [/ips](#ips)
- [/adicionar](#adicionar)
- [/vender](#vender)
- [/knowledge](#knowledge)

**IA — digitar no chat do Claude Code**
- [/morning-call](#morning-call)
- [/analisar](#analisar)
- [/tese](#tese)
- [/earnings](#earnings)
- [/pm TICKER](#modo-a----pm-ticker-ativo-específico) — decisão por ativo
- [/pm · /pm 700](#modo-b----pm--pm-700-modo-aporte) — distribuição de capital novo
- [/comparar](#comparar)
- [/mundo-economico](#mundo-economico)
- [/investimento-do-dia](#investimento-do-dia)
- [/metas](#metas)
- [/relatorio-semanal](#relatorio-semanal)
- [/relatorio-mensal](#relatorio-mensal)
- [/rebalancear](#rebalancear)
- [/revisar-carteira](#revisar-carteira)

---

## Comandos Locais (sem IA)

---

### /carteira

Atualiza cotações via Brapi e exibe o estado atual do portfólio.

**Campos:**

| Campo | Descrição |
|-------|-----------|
| Ticker | Código do ativo |
| Tipo | Classe do ativo (ação-pn, fii, etf-intl...) |
| Qtd | Quantidade de cotas/ações |
| Preço Médio | Custo médio de aquisição |
| Preço Atual | Cotação atualizada via API |
| Valor (R$) | Qtd × Preço Atual |
| P&L (R$) / (%) | Lucro/prejuízo realizado vs custo médio |
| Alocação (%) | Peso do ativo no portfólio total |

**Exemplo de output:**

```
══════════════════════════════════════════════════════
  SBWAA — Carteira | 2026-05-20 08:31
══════════════════════════════════════════════════════

  Ticker   Tipo       Qtd   P. Médio   Atual     Valor       P&L(R$)     P&L%     Aloc%
  PETR4    acao-pn    200   38,50      46,09     9.218,00   +1.518,00   +19,7%   46,4%
  XPML11   fii        100   108,00     106,56   10.656,00    -144,00    -1,3%    53,6%

  ──────────────────────────────────────────────────
  Patrimônio Total : R$ 19.874,00
  Total Investido  : R$ 18.500,00
  P&L Total        : R$ +1.374,00 (+7,4%)
  Última atualização: 2026-05-20 08:31

══════════════════════════════════════════════════════
  PROJEÇÃO — METAS FINANCEIRAS
══════════════════════════════════════════════════════

  📈 PATRIMÔNIO TOTAL
     Alvo: R$ 500.000 | Atual: R$ 19.874
     [##------------] 4%
     Sem aporte : ~28,6 anos  (2054-11)
     Com aporte : ~15,2 anos  (2041-07)  [ATENÇÃO — 5,2 a após o prazo]

  💰 RENDA PASSIVA MENSAL
     Alvo: R$ 3.000/mês | Atual: R$ 1.350/mês  (yield 8,1% a.a.)
     [#######-------] 45%
     Projeção patrimônio necessário: R$ 444.444
     Com aporte : ~14,8 anos  (2041-03)

  ──────────────────────────────────────────────────
  METAS LIVRES
  ──────────────────────────────────────────────────

  🎯 Viagem Europa
     Alvo: R$ 15.000 | Falta: R$ 12.900 | Aporte: R$ 500/mês
     [#-------------] 14%
     Previsão: Fev/2028  [ATENÇÃO — 8 meses após o prazo Jun/2027]
══════════════════════════════════════════════════════
```

> Proventos recebidos aparecem no Resumo quando `/dividendos` já foi executado no dia.
> A seção PROJECAO aparece apenas quando `vault/00-portfolio/metas.md` existe e tem pelo menos uma meta configurada.
> Projeções usam Monte Carlo (1k simulações, GBM) com parâmetros do cache `/risco-carteira`.

---

### /watchlist

Lista todos os ativos analisados (`vault/01-ativos/`) mais os ativos em carteira, com o último veredicto registrado e frescor da análise.

**Campos:**

| Campo | Descrição |
|-------|-----------|
| Ticker | Código do ativo |
| C | `●` = em carteira / `○` = watchlist puro (analisado, não comprado) |
| Tipo | Label de classe do ativo |
| Veredicto | Último veredicto extraído do frontmatter da análise mais recente |
| Data | Data da análise mais recente |
| Frescor | `✅` <45 dias / `⚠️` 45–90 dias / `🔴` >90 dias (rever urgente) |
| Preço-Alvo | Preço-alvo registrado na última análise |

**Flag `--rever`:** exibe apenas os ativos com análise defasada (>45 dias) ou sem análise.

**Exemplo de output:**

```
══════════════════════════════════════════════════════════════════════════════════
  SBWAA — Watchlist  [3 ativos]  |  2026-05-20
══════════════════════════════════════════════════════════════════════════════════

  Ticker     C   Tipo           Veredicto              Data         Frescor      Preço-Alvo
  ──────────────────────────────────────────────────────────────────────────────
  PETR4      ●   🟦 AÇÃO PN      ⏳ AGUARDAR             2026-04-10   ✅ 40d        R$ 42.50
  VALE3      ○   —              🚫 EVITAR               2026-01-15   🔴 125d       R$ 58.00
  XPML11     ●   🟩 FII          ✅ COMPRAR              2026-05-08   ✅ 12d        R$ 115.00

  Legenda: ● carteira  ○ watchlist  ✅ recente  ⚠️ defasado  🔴 rever
  Dica: /pm TICKER para reavaliar  |  /analisar TICKER para análise completa
```

> **Quando usar:** início de semana para ver o que precisa de atenção. Com `--rever` vira um to-do de análises pendentes.

---

### /risco-carteira

Calcula e exibe as métricas de risco quantitativas da carteira com base no histórico de preços.

**Campos:**

| Campo | Descrição |
|-------|-----------|
| VaR 95% hist | Perda máxima esperada em 1 dia com 95% de confiança (histórico) |
| VaR 95% param | Versão paramétrica do VaR (pressupõe distribuição normal) |
| CVaR 95% | Expected Shortfall — perda média nos piores 5% dos dias |
| Drawdown atual | Queda acumulada desde o pico mais recente |
| Drawdown máx histórico | Maior queda registrada no período analisado |
| Sharpe (12m) | Retorno ajustado ao risco vs Selic |
| Beta IBOV | Sensibilidade ao índice Bovespa |
| Concentração máx | Ativo com maior peso e seu % |
| Circuit breakers | Status de cada limite do IPS: ✅ OK / 🚨 VIOLAÇÃO |

**Exemplo de output:**

```
══════════════════════════════════════════════════════
  RISCO — Carteira | 2026-05-20
══════════════════════════════════════════════════════
  VaR 95% hist (1 dia):      1,3%
  VaR 95% param (1 dia):     1,8%
  CVaR 95% (1 dia):          2,1%
  Drawdown atual:            -4,2%
  Drawdown máx histórico:    -14,7%
  Sharpe (12m):              1,24
  Beta IBOV:                 0,68
  Concentração máxima:       XPML11 — 38,2%
  HHI (diversificação):      0,28

  Circuit Breakers:
    VaR < 2%          ✅ OK (1,3%)
    Drawdown < 18%    ✅ OK (4,2%)
    Concentração < 20% ⚠️ ATENÇÃO (38,2%)
    Correlação média  ✅ OK

  🎯 Fronteira Eficiente (Markowitz — 10k simulações)
  ────────────────────────────────────────────────────
  Carteira atual:       Sharpe 1,24  |  Vol 11,2%
  Máx Sharpe possível:  Sharpe 1,61  |  Vol 9,8%    → +30% de eficiência
  Mín Volatilidade:     Sharpe 1,18  |  Vol 8,1%

  Ajustes sugeridos (delta ≥ 2%):
    PETR4   46,4% → 28,0%  ▼ -18,4%
    XPML11  53,6% → 38,0%  ▼ -15,6%
    (+ diversificação em outras classes)
══════════════════════════════════════════════════════
```

> Para análise de expansão com watchlist, use `/otimizar-expansao`.

---

### /otimizar-expansao

Análise de Fronteira Eficiente dual: compara a fronteira da carteira atual com a fronteira expandida (carteira + ativos da watchlist). Identifica quais candidatos da watchlist melhorariam, degradariam ou seriam neutros ao portfólio.

**Tipo:** Local (sem IA) — roda `scripts/data/optimize_expansao.py`

**Campos:**

| Campo | Descrição |
|-------|-----------|
| Ticker | Ativo da watchlist analisado |
| Correlação | Correlação com a carteira atual (12 meses) |
| ΔSharpe | Variação do Sharpe ao adicionar o ativo a 5% de peso |
| Peso ótimo | Peso sugerido no portfólio Max Sharpe expandido |
| Classificação | MELHORA / NEUTRO / PIORA |

**Classificação:**
- **MELHORA:** peso ótimo ≥ 2% e ΔSharpe ≥ 0 — candidato a entrada
- **PIORA:** peso ótimo < 1% e ΔSharpe < -0,01 — evitar ou aguardar
- **NEUTRO:** demais casos — impacto marginal

**Exemplo de output:**

```
══════════════════════════════════════════════════════════════════
  OTIMIZAR EXPANSÃO — 2026-05-20
  Carteira base: 2 ativos | Watchlist: 3 candidatos
══════════════════════════════════════════════════════════════════

  📊 FRONTEIRA BASE (carteira atual)
  Sharpe atual:         1,24
  Máx Sharpe (base):   1,61  |  Vol 9,8%
  Mín Vol (base):      1,18  |  Vol 8,1%

  📈 FRONTEIRA EXPANDIDA (+ watchlist)
  Máx Sharpe expandido: 1,82  |  Vol 9,1%
  Ganho de eficiência:  +13,0% de Sharpe

  🔍 ANÁLISE POR CANDIDATO
  ────────────────────────────────────────────────────────────────
  Ticker    Correlação   ΔSharpe   Peso ótimo   Classificação
  VALE3        +0,32      +0,18       12,0%     ✅ MELHORA
  MXRF11       +0,18      +0,09        8,0%     ✅ MELHORA
  BOVA11       +0,72      -0,04        0,5%     ⚠️ NEUTRO

  💾 Salvo em: scripts/data/cache/optim_expansao_2026-05-20.json
══════════════════════════════════════════════════════════════════
```

> Para análise mais aprofundada de um candidato MELHORA, use `/tese TICKER` ou `/analisar TICKER`.

---

### /dividendos

Busca e exibe o histórico de proventos da carteira via Yahoo Finance.

**Seções do output:**

- **Próximos dividendos (60 dias):** ativos com pagamentos programados, data e valor estimado
- **Dividendos declarados:** anúncios recentes com data ex e data de pagamento
- **Histórico do ano:** total recebido por ativo no ano corrente
- **Yield on Cost:** DY calculado sobre o preço médio de aquisição (não o preço atual)

**Exemplo de output:**

```
  DIVIDENDOS — 2026-05-20
  ──────────────────────────────────────
  Próximos 60 dias:
    XPML11   Ex: 2026-05-28   R$ 0,92/cota   DY mensal: 0,86%

  Histórico 2026:
    XPML11   Jan–Mai: R$ 4,38/cota   Total recebido: R$ 438,00
    PETR4    Mar: R$ 1,20/ação       Total recebido: R$ 240,00

  Yield on Cost:
    XPML11   YoC anualizado: ~9,7% (base PM R$ 108,00)
    PETR4    YoC anualizado: ~3,7% (base PM R$ 38,50)
```

---

### /snapshot

Coleta dados de mercado macro (via Yahoo Finance) e cotações da carteira. Salva snapshot diário em `vault/02-relatorios/diarios/`.

**Dados coletados:**

| Indicador | Fonte |
|-----------|-------|
| IBOV, S&P 500, Nasdaq | Yahoo Finance |
| DXY (índice dólar), BRL/USD | Yahoo Finance |
| Petróleo WTI, Ouro | Yahoo Finance |
| Juros EUA 10Y | Yahoo Finance |
| Cotações da carteira | Brapi / Yahoo Finance |

**Exemplo de output:**

```
  SNAPSHOT — 2026-05-20 08:15
  ──────────────────────────────────────────────────────
  Indicador        Valor        Variação
  IBOV             128.450      +0,42%
  S&P 500          5.312        -0,18%
  Nasdaq           16.820       -0,31%
  BRL/USD          5,14         +0,22%
  Petróleo WTI     78,30        +1,10%
  Ouro             2.340        +0,05%
  Juros EUA 10Y    4,32%        +3bps
  ──────────────────────────────────────────────────────
  Salvo: vault/02-relatorios/diarios/snapshot-2026-05-20.md
```

---

### /stress-test

Simula o impacto de cenários históricos de crise na carteira atual.

**Cenários disponíveis:**

| Cenário | Descrição |
|---------|-----------|
| Crise 2008 | IBOV -41% no ano, câmbio +40% |
| COVID-2020 | IBOV -30% em 30 dias |
| Eleições 2022 | IBOV -15%, juros longos +200bps |
| Lula 2002 | Spread soberano +800bps, câmbio +50% |
| Custom | Choque percentual livre (ex: -25%) |

**Exemplo de output:**

```
  STRESS TEST — COVID-2020 | Carteira: R$ 100.000 (normalizado)
  ──────────────────────────────────────────────────────────────
  Ativo       Peso    Beta    Impacto estimado
  PETR4       46,4%   1,15    -16,1%   →  -R$ 7.470
  XPML11      53,6%   0,72    -10,1%   →  -R$ 5.413

  Impacto total estimado: -13,8%  →  -R$ 13.800*
  Carteira pós-stress:    R$ 86.200*

  * Valores normalizados (R$ 100k) — privacidade preservada.
```

---

### /simulacao

Projeta o patrimônio da carteira via Monte Carlo (GBM) com parâmetros históricos.

**Campos:**

| Campo | Descrição |
|-------|-----------|
| Horizonte | Anos de projeção configurados |
| Aporte mensal | Valor mensal adicionado ao patrimônio |
| P10 / P50 / P90 | Percentis de resultado ao final do horizonte |
| Drift anual | Retorno esperado ajustado (μ - σ²/2) |
| Volatilidade anual | Desvio padrão histórico anualizado |

> Output: cabeçalho com parâmetros (drift, vol, nº de simulações) + tabela com P10/P50/P90 por ano + linha de resumo com patrimônio esperado no horizonte final.
> Parâmetros lidos do cache `logs/simulacao/params_cache.json` (gerado pelo `/risco-carteira`).
> Com `--salvar`, grava gráfico em `vault/05-risk/simulacao-YYYY-MM-DD.png`.

---

### /ips

Exibe o Investment Policy Statement completo: perfil, alocação alvo, bandas e limites de risco.

**Não produz cálculos** — apenas lê e formata `vault/00-portfolio/ips.md`.

---

### /adicionar

Registra um novo ativo na carteira ou incrementa posição existente.

**Flags obrigatórias:** `--ticker`, `--tipo`, `--quantidade`, `--preco-medio`, `--setor`
**Flags opcionais:** `--data YYYY-MM-DD` (padrão: hoje), `--skip-validacao`

**Comportamento:**
- Ativo novo: cria entrada em `carteira.md` e pasta em `vault/01-ativos/TICKER/`
- Ativo existente: recalcula preço médio ponderado e exibe P&L antes e depois

**Renda Fixa (`renda-fixa` | `tesouro` | `debenture` | `cri-cra`):**
- Validação de API pulada automaticamente (sem ticker em bolsa)
- `--setor` = emissor (XP, BTG, Tesouro Nacional…)
- Unidade exibida: "unidades" (não "ações")
- Flags exclusivas RF: `--nome`, `--indexador` (CDI|IPCA|Selic|PRE|IGPM), `--taxa`, `--vencimento`
- Nota `tese.md` gerada com tabela estruturada (indexador, taxa, vencimento, emissor) e `status: ativo`

---

### /vender

Registra venda parcial ou total de um ativo.

**Flags obrigatórias:** `--ticker`, `--quantidade`, `--preco`
**Flag opcional:** `--data YYYY-MM-DD`

**Comportamento:**
- Venda parcial: atualiza quantidade em `carteira.md`, registra P&L realizado em `historico-trades.md`
- Venda total: remove ativo da carteira, mantém histórico

---

### /knowledge

Gerencia a base de conhecimento local (RAG) usada pelos agentes de IA.

**Subcomandos:**

| Flag | O que faz |
|------|-----------|
| `--status` | Total de documentos, tamanho da base, última atualização |
| `--adicionar <caminho>` | Indexa arquivo (PDF, DOCX, TXT, MD) ou pasta inteira |
| `--buscar <query>` | Busca semântica — retorna trechos rankeados por relevância |
| `--coletar-rss` | Coleta notícias dos feeds configurados (Valor, InfoMoney, BCB...) |
| `--listar` | Lista todos os documentos indexados |

> A base é consultada automaticamente por todos os agentes de IA durante as análises.

---

## Comandos de IA (chat do Claude Code)

> Estes comandos usam LLM. O botão na UI copia o comando para o clipboard — cole no chat do Claude Code para executar.

---

### /morning-call

Briefing diário pré-abertura. Roda o Market Researcher com dados do snapshot do dia.

**Seções do output:**

| Seção | Conteúdo |
|-------|----------|
| Macro Global | Tabela com IBOV, S&P, Nasdaq, DXY, BRL/USD, petróleo, ouro, juros EUA 10Y — cotação, variação e contexto em 1 linha |
| Cenário do Dia | 2–3 parágrafos: o que move o mercado, riscos e oportunidades |
| Impacto na Carteira | Apenas os ativos com exposição relevante ao cenário do dia |
| Alertas Ativos | Flags CRÍTICO/ALTO do sistema de alertas |
| Ponto de Atenção do Dia | 1 insight acionável: ativo, setor ou evento específico para monitorar |

**Exemplo de output (fragmento):**

```markdown
## 🌍 Cenário do Dia

Risk-off moderado: S&P recua 0,3% na abertura com dados de inflação
acima do esperado nos EUA (CPI +3,4% vs 3,2% consenso). Juros longos
americanos subiram 4bps para 4,32%, pressionando ativos de risco globais.
IBOV abre em leve alta (+0,4%) sustentado por petróleo (+1,1%).

## 🏠 Impacto na Carteira

XPML11 (FII — Shoppings): juros longos em alta são negativos para FIIs
de tijolo no curto prazo. Monitorar se o movimento persiste.

## 🚩 Ponto de Atenção do Dia

PETR4: petróleo em alta +1,1% após dados do EIA. Catalisador de curto
prazo positivo — monitorar se sustenta acima de US$ 79.
```

> Salvo em: `vault/02-relatorios/diarios/morning-call-YYYY-MM-DD.md`

---

### /analisar

Pipeline completo de análise — 10 etapas em sequência (0–9). Aceita **um ou mais tickers** separados por espaço.

**Sintaxe:**
```
/analisar PETR4
/analisar PETR4 VALE3 XPML11
```

Em batch (2+ tickers): executa o pipeline completo e isolado para cada ticker em sequência, gerando output individual normal para cada um, e uma **tabela comparativa de veredictos ao final**.

**Etapas (por ticker):**

| Etapa | Agente | O que entrega |
|-------|--------|---------------|
| 0 | Scripts | Coleta Brapi + Yahoo macro + BCB (Selic/IPCA/BRL/IBC-Br) + consenso de analistas |
| 1 | Market Researcher | Contexto macro, setor, catalisadores do dia |
| 2 | Earnings Reviewer | Revisão do resultado mais recente (QoQ, YoY, qualidade) |
| 3 | Model Builder | DCF com premissas explícitas (WACC, g, FCL projetado) |
| 4 | Valuation Reviewer | Crítica ao DCF + múltiplos + **preço teto/chão (Graham/Bazin)** + consenso de sell-side + veredicto BARATO/JUSTO/CARO |
| 5 | Quant | Sharpe, volatilidade, drawdown, beta, correlação com carteira |
| 6 | Econometrician | GARCH (vol dinâmica, persistência, half-life), beta dinâmico rolling (60d/126d/252d), Fama-French 3F proxies BR (alpha, SMB, HML), regressão macro BCB (Selic/IPCA/BRL/IBC-Br), correlações rolling vs carteira, drawdown avançado (Calmar/Ulcer/Pain) |
| 7 | Risk Engineer | VaR, CVaR, stress test, circuit breakers |
| 8 | Portfolio Manager | Decisão final: COMPRAR / AGUARDAR / EVITAR + sizing + stop |
| 9 | Salvar | Nota `vault/01-ativos/TICKER/analise-TICKER-YYYY-MM-DD.md` com frontmatter + wikilinks |

**Exemplo de output final (PM):**

```markdown
## ⚡ Veredicto: COMPRAR

Valuation barato (DCF upside +22%, múltiplos abaixo da média histórica),
resultado recente confirmou tendência de expansão de margem, risco controlado.

**Sizing sugerido:** 8% do portfólio (atualmente 0%)
**Entrada:** até R$ 42,00 (margem de segurança de 12% vs valor justo R$ 47,80)
**Stop/Revisão:** resultado abaixo de R$ 1,8B EBITDA no próximo trimestre

📡 Consenso sell-side: 12 analistas | Target médio R$ 48,50 | COMPRA
```

> Salvo em: `vault/01-ativos/TICKER/analise-TICKER-YYYY-MM-DD.md` (um arquivo por ticker)

**Exemplo de tabela comparativa final (batch):**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ticker  Tipo         Veredicto  Valuation  Upside DCF  P. Teto    Cotação   Sizing
─────────────────────────────────────────────────────────────────────────────────
PETR4   🟦 AÇÃO PN   COMPRAR    BARATO     +28%        R$ 89,00   R$ 38,00  8%
XPML11  🟩 FII       AGUARDAR   JUSTO      +9%         R$ 115,00  R$ 106,00 —

Prioridade de aporte: PETR4
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### /tese

Versão condensada do `/analisar`. Roda Market Researcher + DCF básico + decisão do PM. Sem Quant e Risk standalone.

**Quando usar:** primeiro contato com um ativo novo, antes de decidir se vale o pipeline completo.

**Tempo estimado:** ~40% do tempo do `/analisar`.

**Output:** mesma estrutura do `/analisar`, mas com menos profundidade nas métricas quantitativas e de risco.

> Salvo em: `vault/01-ativos/TICKER/tese-TICKER-YYYY-MM-DD.md`

---

### /earnings

Revisão focada no resultado trimestral mais recente. Não faz DCF nem decisão de PM.

**Campos do output:**

| Campo | Descrição |
|-------|-----------|
| Números do Trimestre | Tabela com Receita, EBITDA, Lucro Líquido — atual vs anterior (QoQ) e vs mesmo período ano anterior (YoY) |
| Qualidade do Resultado | Crescimento orgânico? Margem expansão ou contração? Itens não-recorrentes? |
| Impacto na Tese | CONFIRMA / ENFRAQUECE / NEUTRO — com justificativa direta |
| Flags para o PM | O que mudou que impacta o modelo: revisão de premissas? Urgência? |

**Exemplo de output:**

```markdown
## 📋 Números do Trimestre

| Métrica | 1T26 | 4T25 | QoQ | YoY |
|---------|------|------|-----|-----|
| Receita Líquida | R$ 4,2B | R$ 3,9B | +7,7% | +12,3% |
| EBITDA | R$ 1,8B | R$ 1,6B | +12,5% | +18,4% |
| Margem EBITDA | 42,9% | 41,0% | +190bps | +220bps |

## 📌 Impacto na Tese
CONFIRMA — expansão de margem acelerou, guidance reafirmado.
```

> Salvo em: `vault/01-ativos/TICKER/earnings-TICKER-TRIMESTRE.md`

---

### /pm

O comando `/pm` opera em dois modos distintos conforme o argumento passado:

---

#### Modo A — `/pm TICKER` (ativo específico)

Decisão do Portfolio Manager para um ativo específico, usando análises já existentes em `vault/01-ativos/TICKER/`. Não refaz o pipeline completo.

**Quando usar:** análise recente (<60 dias), mas você quer uma decisão atualizada de comprar/aguardar/evitar com base no contexto atual da carteira.

**Output:**

| Campo | Descrição |
|-------|-----------|
| Veredicto | COMPRAR / AGUARDAR / EVITAR |
| Tese em 3 bullets | Por que este veredicto agora |
| Sizing | % sugerido do portfólio, posição atual vs alvo |
| Nível de entrada | Preço máximo aceitável ou gatilho de evento |
| Stop/Revisão | Condição que invalidaria a tese |
| Adequação ao IPS | Confirmação de que respeita limites de risco |

**Diferença vs `/analisar`:** não reconstrói o modelo — usa o que já existe. Mais rápido, menos contexto consumido.

**Saving automático (pós-veredicto):**
- Acrescenta linha na tabela de `vault/00-portfolio/decisoes.md` — histórico permanente
- Cria `vault/01-ativos/TICKER/pm-decisao-TICKER-YYYY-MM-DD.md` com frontmatter (`tags`, `veredicto`, `ticker`, `data`, `sizing`) e output completo da decisão

---

#### Modo B — `/pm` · `/pm 700` (Modo Aporte)

PM conversacional para distribuição de dinheiro novo entre múltiplos ativos. Opera exclusivamente com capital de entrada — sem movimentar posições existentes.

**Sintaxe:**
```
/pm            → perguntas interativas completas
/pm 700        → atalho: pula a pergunta de valor
```

**Perguntas do fluxo:**

| # | Pergunta | Opções |
|---|----------|--------|
| 1 | Valor disponível (R$) | valor livre — pulado no atalho `/pm 700` |
| 2 | Classe de ativo | [1] Auto-IPS / [2] FII / [3] Ação / [4] ETF / [5] RF+TD |
| 3 | Nº de ativos para distribuir | número inteiro (ex: 3, 5) |
| 4 | Restrições / observação | campo livre — Enter para pular |

**Lógica de seleção (automática):**

| Critério | Peso |
|----------|------|
| Veredicto AUMENTAR (já em carteira) | +3.0 pts |
| Veredicto COMPRAR (fora da carteira) | +2.0 pts |
| Gap de IPS da classe (subpesada) | até +5.0 pts |
| Análise fresca (≤ 45 dias) | +1.0 pt |
| Análise completa via /analisar | +1.5 pts |

**Distribuição de capital:**
- Base: 60% igual entre os N ativos selecionados
- Ajuste: +40% ponderado pelo gap de IPS de cada classe
- Arredondamento: cotas inteiras pelo preço atual (cache ou carteira)

**Requisito de análise:**
- Mínimo: `/pm TICKER` executado (arquivo `pm-decisao-*.md` presente)
- Ideal: `/analisar TICKER` completo (arquivo `equity-research-*.md` presente)
- Se faltar: PM lista os pendentes → oferece executar `/analisar` → retoma automaticamente

**Output do PM:**

| Seção | Conteúdo |
|-------|----------|
| Validação | PM ajusta pesos se necessário com justificativa |
| Por ativo | Veredicto, razão, risco principal |
| Alerta IPS | Flag se alguma alocação ultrapassar concentração máx |
| Tabela final | Ticker \| Valor (R$) \| Cotas \| Prioridade \| Observação |
| Loop ajuste | Campo livre para refinar — PM recalcula sem reiniciar |

**Mockup de tabela final:**
```
| Ticker | Valor    | Cotas | Prioridade | Observação          |
|--------|----------|-------|------------|---------------------|
| MXRF11 | R$ 420   | 51    | 1ª         | FIIs 3% abaixo IPS  |
| KNRI11 | R$ 180   | 2     | 2ª         | Diversifica logíst. |
| XPML11 | R$ 100   | 1     | 3ª         | Shoppings — AUMENTAR|
```

**Saving automático:**
- `vault/00-portfolio/pm-aporte-YYYY-MM-DD.md` com frontmatter + análise completa + tabela de distribuição
- Linha no log `vault/00-portfolio/decisoes.md` com tag `APORTE(TICKER1, TICKER2, ...)`

---

### /comparar

Análise lado a lado de dois ativos. Útil para decidir entre dois candidatos ou avaliar troca de posição.

**Seções:**

- Valuation comparado (P/L, EV/EBITDA, P/VP, DY — atual e histórico)
- Qualidade dos resultados (margem, crescimento, alavancagem)
- Risco relativo (volatilidade, beta, drawdown)
- Retorno histórico (1m, 3m, 6m, 12m)
- Alocação relativa sugerida pelo PM

**Exemplo:** `/comparar PETR4 PRIO3` → qual das duas tem melhor risco/retorno para o portfólio atual.

---

### /mundo-economico

Análise macro do dia — cenário global e impacto no Brasil. Mais profundo que o bloco macro do `/morning-call`.

**Seções:**

- EUA: Fed, inflação, emprego, mercado de crédito
- China: crescimento, commodities, demanda por minério/petróleo
- Europa: BCE, câmbio EUR/USD
- Brasil: Selic, câmbio, fiscal, IBOV vs pares emergentes
- Impacto por setor na carteira do usuário

> Útil quando ocorre evento macro relevante (decisão do Fed, dados de inflação, eleição, crise).

---

### /investimento-do-dia

Sugere 1–2 ativos para explorar com análise, com base no IPS do usuário e no cenário macro atual.

**Sintaxe:**
```
/investimento-do-dia
/investimento-do-dia fii
/investimento-do-dia acao
/investimento-do-dia etf
/investimento-do-dia etf-br
/investimento-do-dia etf-intl
/investimento-do-dia rf
/investimento-do-dia td
```

Sem argumento: sugere qualquer tipo de ativo (comportamento padrão).
Com argumento: restringe as sugestões à categoria informada.

**Não é uma recomendação de compra** — é uma sugestão de onde focar a análise do dia.

**Critérios usados:**

- Alinhamento com a alocação alvo do IPS (qual classe está sub-alocada?)
- Contexto macro favorável para qual setor?
- Ativos da watchlist com análise recente que podem ter melhorado de patamar

---

### /metas

Dashboard de progresso das metas financeiras. Sem API key — leitura local.

**Configuração:** editar `vault/00-portfolio/metas.md` com os valores-alvo.

**Metas suportadas:**

| Meta | Cálculo | Atualização |
|------|---------|-------------|
| Renda Passiva Mensal | Dividendos reais da carteira (DPA × cotas) | Automático |
| Reserva de Emergência | Saldo de RF + TD na carteira | Automático |
| Patrimônio Total | Valor total da carteira a mercado | Automático |
| Metas Livres | Campo `atual` no arquivo | Manual pelo usuário |

**Exemplo de output:**

```
══════════════════════════════════════════════════════════
METAS FINANCEIRAS — 2026-05-22
══════════════════════════════════════════════════════════

💰 RENDA PASSIVA MENSAL
   Alvo: R$ 3.000/mês | Atual: R$ 1.350/mês
   ███████░░░░░░░░ 45%
   → Projeção: Jun/2028 (no ritmo atual)

🏦 RESERVA DE EMERGÊNCIA
   Alvo: R$ 50.000 | Atual: R$ 40.000
   ████████████░░░ 80% ⭐⭐⭐ Reta final

📈 PATRIMÔNIO TOTAL
   Alvo: R$ 500.000 | Atual: R$ 160.000
   ████░░░░░░░░░░░ 32%

──────────────────────────────────────────────────────────
METAS LIVRES
──────────────────────────────────────────────────────────

🎯 Viagem Europa
   Alvo: R$ 15.000 | Atual: R$ 2.100 | Prazo: Jun/2027
   ██░░░░░░░░░░░░░ 14%  ⚠️ em risco de prazo
══════════════════════════════════════════════════════════
```

> Integrado ao `/morning-call`: exibe resumo compacto com % por meta e alertas de milestone.
> Configurar metas em `vault/00-portfolio/metas.md`. Agentes de análise **não leem** este arquivo.

---

### /relatorio-semanal

Relatório de performance da semana. Agente: Portfolio Manager.

**Seções:**

| Seção | Conteúdo |
|-------|----------|
| Sumário da Semana | Performance da carteira vs IBOV + retorno absoluto normalizado (R$ 100k) |
| Performance por Ativo | Tabela: Ticker / Retorno 1S / Contribuição / Destaque |
| Top 3 Melhores / Piores | Maiores contribuições positivas e negativas |
| Métricas HF | Sharpe, volatilidade, drawdown, VaR — status dos circuit breakers |
| Dividendos Recebidos | Se houver registro na semana |
| Outlook Próxima Semana | 2–3 eventos/catalisadores a acompanhar |

> Salvo em: `vault/02-relatorios/semanais/semana-YYYY-WNN.md`
> Gera também: `vault/05-risk/snapshots/risk-YYYY-MM-DD.md` — tabela de métricas vs limites IPS (VaR, CVaR, drawdown, concentração, circuit breakers)

---

### /relatorio-mensal

Relatório completo do mês. Mais profundo que o semanal.

**Seções adicionais vs semanal:**

- Benchmark: carteira vs IBOV, CDI, IPCA no mês e no acumulado do ano
- Análise de risco: evolução do VaR, drawdown e Sharpe no mês
- Revisão de teses: as análises do mês ainda sustentam os veredictos?
- Movimentações: aportes, vendas e dividendos recebidos no mês
- Plano para o próximo mês: onde aportar, o que revisar

> Salvo em: `vault/02-relatorios/mensais/YYYY-MM.md`

---

### /rebalancear

PM verifica a alocação atual vs alvos e bandas do IPS, e sugere ajustes.

**Campos da tabela:**

| Campo | Descrição |
|-------|-----------|
| Classe | Ações BR, FIIs, Renda Fixa, ETFs Intl, Tesouro Direto |
| Alvo % | Meta definida no IPS |
| Mín / Máx % | Banda de tolerância do IPS |
| Atual % | Peso atual calculado da carteira |
| Desvio | Diferença entre atual e alvo |
| Status | ✅ OK / ⚠️ Fora da banda / 🚨 Violação |

**Exemplo:**

```
| Classe      | Alvo | Mín | Máx | Atual | Desvio | Status |
|-------------|------|-----|-----|-------|--------|--------|
| Ações BR    | 25%  | 20% | 30% | 46%   | +21%   | 🚨     |
| FIIs        | 35%  | 30% | 40% | 54%   | +19%   | 🚨     |
| Renda Fixa  | 20%  | 15% | 25% | 0%    | -20%   | 🚨     |
| TD          | 12%  | 7%  | 17% | 0%    | -12%   | ⚠️     |
| ETFs Intl   | 8%   | 3%  | 13% | 0%    | -8%    | ⚠️     |
```

**Ações sugeridas:** para cada classe fora da banda, o PM indica o que fazer (aportar / reduzir / aguardar aporte) e qual ativo dentro da classe priorizar.

> Regra: só sugere redução se desvio > 5% do alvo. Nunca sugere alavancagem.

---

### /revisar-carteira

PM revisa **todas as posições em carteira de uma vez** — não chama `/pm` nem `/analisar` em loop. É uma visão panorâmica em uma única chamada.

> Se após a revisão um ativo precisar de atenção mais profunda, aí você roda `/pm TICKER` ou `/analisar TICKER` individualmente.

**Seções do output:**

| Seção | Conteúdo |
|-------|----------|
| Painel de Revisão | Tabela com todos os ativos: Ação / Sizing Alvo / Data da análise / Justificativa |
| Prioridades Imediatas | Top 3 ações mais urgentes da carteira |
| O que não mudar | Ativos sólidos — sem intervenção necessária |
| Alertas de IPS | Violações ou proximidade de limites |
| Métricas HF | Bloco de Sharpe, VaR, drawdown, concentração, circuit breakers |
| Próximos Passos | Por ativo: `/pm` ou `/analisar` + motivo |

**Ações possíveis:** `MANTER` / `AUMENTAR` / `REDUZIR` / `SAIR`

**Critério para próximo passo:**
- `/pm TICKER` → análise existe e tem menos de 60 dias
- `/analisar TICKER` → análise ausente, >60 dias ou evento relevante desde a última

**Exemplo de output:**

```markdown
## 📋 Painel de Revisão

| Ticker | Peso Atual | Ação    | Sizing Alvo | Análise    | Justificativa |
|--------|-----------|---------|-------------|------------|---------------|
| PETR4  | 46,4%     | REDUZIR | ~25%        | 2026-04-10 | Concentração 2× acima do limite IPS |
| XPML11 | 53,6%     | MANTER  | ~35%        | 2026-05-08 | Tese recente válida; aguardar reequilíbrio |

## ⚡ Prioridades Imediatas
1. Aportar em Renda Fixa — classe zerada, 20% do alvo IPS
2. Aportar em TD — zerado, 12% do alvo IPS
3. Diversificar Ações BR — PETR4 único representante da classe

## 🔜 Próximos Passos
| Ticker | Ação    | Próximo Passo | Motivo |
|--------|---------|---------------|--------|
| PETR4  | REDUZIR | /pm PETR4     | Análise 40 dias — ainda válida |
| XPML11 | MANTER  | —             | Análise 12 dias — ok |
```

> Salvo em: `vault/02-relatorios/revisoes/revisao-carteira-YYYY-MM-DD.md`

---

## Wikilinks e Vault

Todo output de IA gera um arquivo `.md` no vault com wikilinks automáticos para os documentos relacionados. No Obsidian, isso cria o grafo de conexões entre ativos, relatórios, teses e notas macro.

Estrutura de pastas:

```
vault/
├── 00-portfolio/        → carteira.md, ips.md, historico-trades.md, decisoes.md
├── 01-ativos/TICKER/    → tese, analise, earnings, equity-research, pm-decisao
├── 02-relatorios/
│   ├── diarios/         → morning-call, snapshot
│   ├── semanais/        → relatorio-semanal
│   ├── mensais/         → relatorio-mensal
│   └── revisoes/        → revisar-carteira
├── 03-macro/            → notas de cenário macro (mundo-economico)
├── 04-knowledge/        → documentos indexados na base RAG
├── 05-risk/snapshots/   → risk snapshots semanais (gerados pelo /relatorio-semanal)
└── _templates/          → 11 templates Obsidian (tese, analise, earnings, equity-research,
                           pm-decisao, snapshot, morning-call, macro, risk-snapshot, semana, mensal)
```
