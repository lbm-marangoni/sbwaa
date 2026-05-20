# SBWAA — Referência de Comandos

> Documento complementar ao [`GUIA-COMANDOS.md`](docs/GUIA-COMANDOS.md).
> O guia cobre sintaxe e flags. Esta referência cobre **o que cada comando entrega**:
> campos, estrutura do output e o que você pode esperar ver.

**Versão: v2.4.1**

---

## Índice

**Local (sem IA)**
- [/carteira](#carteira)
- [/watchlist](#watchlist)
- [/risco-carteira](#risco-carteira)
- [/dividendos](#dividendos)
- [/snapshot](#snapshot)
- [/stress-test](#stress-test)
- [/ips](#ips)
- [/adicionar](#adicionar)
- [/vender](#vender)
- [/knowledge](#knowledge)

**IA — digitar no chat do Claude Code**
- [/morning-call](#morning-call)
- [/analisar](#analisar)
- [/tese](#tese)
- [/earnings](#earnings)
- [/pm](#pm)
- [/comparar](#comparar)
- [/mundo-economico](#mundo-economico)
- [/investimento-do-dia](#investimento-do-dia)
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
```

> Proventos recebidos aparecem no Resumo quando `/dividendos` já foi executado no dia.

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
══════════════════════════════════════════════════════
```

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

Pipeline completo de análise de um ativo — 8 etapas em sequência. O mais pesado e completo do sistema.

**Etapas:**

| Etapa | Agente | O que entrega |
|-------|--------|---------------|
| 0 | Scripts | Coleta Brapi + Yahoo macro + consenso de analistas |
| 1 | Market Researcher | Contexto macro, setor, catalisadores do dia |
| 2 | Earnings Reviewer | Revisão do resultado mais recente (QoQ, YoY, qualidade) |
| 3 | Model Builder | DCF com premissas explícitas (WACC, g, FCL projetado) |
| 4 | Valuation Reviewer | Crítica ao DCF + múltiplos + consenso de sell-side + veredicto BARATO/JUSTO/CARO |
| 5 | Quant | Sharpe, volatilidade, drawdown, beta, correlação com carteira |
| 6 | Risk Engineer | VaR, CVaR, stress test, circuit breakers |
| 7 | Portfolio Manager | Decisão final: COMPRAR / AGUARDAR / EVITAR + sizing + stop |

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

> Salvo em: `vault/01-ativos/TICKER/analise-TICKER-YYYY-MM-DD.md`

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

**Não é uma recomendação de compra** — é uma sugestão de onde focar a análise do dia.

**Critérios usados:**

- Alinhamento com a alocação alvo do IPS (qual classe está sub-alocada?)
- Contexto macro favorável para qual setor?
- Ativos da watchlist com análise recente que podem ter melhorado de patamar

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
├── 00-portfolio/        → carteira.md, ips.md, historico-trades.md
├── 01-ativos/TICKER/    → tese, análise completa, DCF, earnings, equity research
├── 02-relatorios/
│   ├── diarios/         → morning-call, snapshot
│   ├── semanais/        → relatorio-semanal
│   ├── mensais/         → relatorio-mensal
│   └── revisoes/        → revisar-carteira
├── 03-macro/            → notas de cenário macro
├── 04-knowledge/        → documentos indexados na base RAG
└── 05-risk/             → snapshots de risco
```
