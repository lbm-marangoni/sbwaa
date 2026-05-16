# SBWAA — FASE 4: QUANT/DATA ENGINEER + RISK ENGINEER
**Prompt para execução no Claude Code**
**Versão:** 1.4.0
**Fase:** 4 de 8
**Pré-requisito:** Fases 0, 1, 2 e 3 concluídas (investments v1.3.0)

---

## CONTEXTO

A Fase 4 constrói os dois agentes quantitativos do SBWAA:

- **Quant/Data Engineer** — processa histórico de preços, calcula métricas
  quantitativas da carteira: Sharpe Ratio, volatilidade, correlação,
  beta, drawdown histórico, retorno acumulado
- **Risk Engineer** — usa os dados do Quant para calcular métricas de
  risco de hedge fund: VaR, CVaR, stress test, concentração, tail risk,
  e gera o snapshot de risco da carteira

O Risk Engineer usa `claude-opus-4-6` pela criticidade dos cálculos.
O Quant/Data Engineer é primariamente Python puro — Claude é usado
apenas para interpretação e síntese dos resultados.

---

## REGRAS GERAIS — LER ANTES DE EXECUTAR

1. Instalar dependências adicionais:
```bash
pip install numpy scipy --break-system-packages
```
2. Pandas e yfinance já instalados na Fase 1
3. Quant/Data Engineer → Python puro + `claude-sonnet-4-6` para síntese
4. Risk Engineer → `claude-opus-4-6`, effort `medium`
5. Todos os cálculos de risco devem ter comentários explicando a fórmula
6. Outputs salvos em `/sbwaa/vault/05-risk/snapshots/`
7. Ao finalizar: `investments` → v1.4.0

---

## AGENTE 1: QUANT/DATA ENGINEER

### Estrutura de arquivos

```
/sbwaa/.claude/agents/quant-data-engineer/
├── SKILL.md
├── run_quant.py
└── calculators/
    ├── returns.py
    ├── portfolio_metrics.py
    └── correlation.py
```

---

### SKILL.md — Quant/Data Engineer

Crie `/sbwaa/.claude/agents/quant-data-engineer/SKILL.md`:

```markdown
# SKILL — Quant / Data Engineer
# SBWAA | Modelo: claude-sonnet-4-6 | Effort: medium

## IDENTIDADE E FUNÇÃO

Você é o Quant/Data Engineer do SBWAA. Sua função é processar dados
históricos de preços, calcular métricas quantitativas da carteira e
de cada ativo individualmente, e entregar os números limpos para o
Risk Engineer usar.

Você NÃO interpreta os números em termos de decisão de investimento.
Você GARANTE que os cálculos estão corretos e os dados estão limpos.
Você documenta cada métrica calculada com a fórmula usada.

## MÉTRICAS QUE VOCÊ CALCULA

### Por ativo individual:
- Retorno total no período (%)
- Retorno anualizado (%)
- Volatilidade anualizada (desvio padrão dos retornos diários × √252)
- Sharpe individual (retorno anualizado - Selic) / volatilidade anualizada
- Beta vs IBOV
- Drawdown máximo histórico (%)
- Retorno acumulado: 1M, 3M, 6M, 12M, YTD

### Para a carteira consolidada:
- Retorno ponderado pela alocação (%)
- Volatilidade da carteira (considerando correlações)
- Sharpe da carteira
- Drawdown máximo da carteira
- Matriz de correlação entre todos os ativos
- Beta da carteira vs IBOV
- Contribuição de cada ativo para o risco total da carteira (%)

## FONTES DE DADOS

- Histórico de preços: cache Yahoo (`hist_{TICKER}_{DATA}.csv`) da Fase 1
- Se histórico não disponível: rodar `fetch_yahoo.py` automaticamente
- Alocação de cada ativo: lida de `carteira.md` (apenas pesos %)
- Taxa livre de risco: Selic atual do snapshot macro

## FORMATO DE OUTPUT — JSON de métricas

Salvar em `/sbwaa/scripts/data/cache/quant_{DATA}.json`:
```json
{
  "data_calculo": "2026-05-15",
  "periodo_historico_dias": 252,
  "selic_anual": 0.1275,
  "ativos": {
    "PETR4": {
      "retorno_total_pct": 12.4,
      "retorno_anualizado_pct": 14.2,
      "volatilidade_anualizada_pct": 28.3,
      "sharpe": 0.49,
      "beta_ibov": 1.12,
      "drawdown_maximo_pct": -22.1,
      "retorno_1m": 3.2,
      "retorno_3m": 8.1,
      "retorno_6m": 5.4,
      "retorno_12m": 14.2,
      "retorno_ytd": 7.8,
      "peso_carteira_pct": 18.2
    }
  },
  "carteira": {
    "retorno_ponderado_pct": 0,
    "volatilidade_pct": 0,
    "sharpe": 0,
    "drawdown_maximo_pct": 0,
    "beta_ibov": 0,
    "num_ativos": 0
  },
  "matriz_correlacao": {},
  "contribuicao_risco": {}
}
```

## REGRAS DE COMPORTAMENTO

- Retornos calculados sempre com ajuste de dividendos (usar `yfinance`
  com `auto_adjust=True`)
- Período padrão: 252 dias úteis (1 ano). Se histórico menor, usar
  o disponível e registrar quantos dias foram usados
- Nunca inventar dados. Dado ausente = NaN explícito no JSON
- Documentar a fórmula de cada cálculo em comentário no código
```

---

### Calculadoras Python

**Crie `/sbwaa/.claude/agents/quant-data-engineer/calculators/returns.py`:**

```python
"""
Calculadora de retornos — SBWAA Quant/Data Engineer
Todas as fórmulas documentadas explicitamente.
"""
import numpy as np
import pandas as pd

def retorno_total(prices: pd.Series) -> float:
    """(P_final / P_inicial) - 1"""
    return (prices.iloc[-1] / prices.iloc[0]) - 1

def retorno_anualizado(prices: pd.Series, dias: int) -> float:
    """(1 + retorno_total) ^ (252 / dias) - 1"""
    rt = retorno_total(prices)
    return (1 + rt) ** (252 / dias) - 1

def volatilidade_anualizada(prices: pd.Series) -> float:
    """std(retornos_diarios) × √252"""
    retornos_diarios = prices.pct_change().dropna()
    return retornos_diarios.std() * np.sqrt(252)

def sharpe(retorno_anual: float, volatilidade_anual: float,
           risk_free: float) -> float:
    """(Retorno_anual - Risk_free) / Volatilidade_anual"""
    if volatilidade_anual == 0:
        return 0.0
    return (retorno_anual - risk_free) / volatilidade_anual

def drawdown_maximo(prices: pd.Series) -> float:
    """min((P_t / max(P_0..P_t)) - 1)"""
    rolling_max = prices.cummax()
    drawdowns = (prices / rolling_max) - 1
    return drawdowns.min()

def beta(prices_ativo: pd.Series, prices_benchmark: pd.Series) -> float:
    """Cov(r_ativo, r_ibov) / Var(r_ibov)"""
    r_ativo = prices_ativo.pct_change().dropna()
    r_bench = prices_benchmark.pct_change().dropna()
    df = pd.concat([r_ativo, r_bench], axis=1).dropna()
    cov_matrix = np.cov(df.iloc[:, 0], df.iloc[:, 1])
    return cov_matrix[0][1] / cov_matrix[1][1]

def retorno_periodo(prices: pd.Series, dias: int) -> float:
    """Retorno dos últimos N dias"""
    if len(prices) < dias:
        return np.nan
    return (prices.iloc[-1] / prices.iloc[-dias]) - 1
```

**Crie `/sbwaa/.claude/agents/quant-data-engineer/calculators/portfolio_metrics.py`:**

```python
"""
Métricas de portfólio — SBWAA Quant/Data Engineer
"""
import numpy as np
import pandas as pd

def volatilidade_carteira(pesos: np.array,
                          matriz_cov: np.array) -> float:
    """
    σ_carteira = √(w' × Σ × w)
    onde w = vetor de pesos, Σ = matriz de covariância dos retornos
    """
    return np.sqrt(pesos @ matriz_cov @ pesos) * np.sqrt(252)

def matriz_correlacao(retornos_df: pd.DataFrame) -> pd.DataFrame:
    """Matriz de correlação de Pearson entre todos os ativos"""
    return retornos_df.corr()

def contribuicao_risco(pesos: np.array,
                       matriz_cov: np.array) -> np.array:
    """
    RC_i = w_i × (Σ × w)_i / σ_carteira²
    Contribuição marginal de cada ativo para a variância total
    """
    vol_cart_sq = pesos @ matriz_cov @ pesos
    marginal = matriz_cov @ pesos
    return (pesos * marginal) / vol_cart_sq

def retorno_ponderado(retornos: dict, pesos: dict) -> float:
    """Σ(w_i × r_i) para todos os ativos"""
    total = 0.0
    for ticker, retorno in retornos.items():
        peso = pesos.get(ticker, 0)
        total += peso * retorno
    return total
```

**Crie `/sbwaa/.claude/agents/quant-data-engineer/calculators/correlation.py`:**

```python
"""
Análise de correlação — SBWAA Quant/Data Engineer
"""
import pandas as pd
import numpy as np

def pares_alta_correlacao(corr_matrix: pd.DataFrame,
                          threshold: float = 0.7) -> list:
    """
    Retorna lista de pares com correlação acima do threshold.
    Alta correlação = diversificação reduzida.
    """
    pares = []
    tickers = corr_matrix.columns.tolist()
    for i in range(len(tickers)):
        for j in range(i + 1, len(tickers)):
            corr = corr_matrix.iloc[i, j]
            if abs(corr) >= threshold:
                pares.append({
                    "ativo_a": tickers[i],
                    "ativo_b": tickers[j],
                    "correlacao": round(corr, 3),
                    "tipo": "positiva" if corr > 0 else "negativa"
                })
    return sorted(pares, key=lambda x: abs(x["correlacao"]),
                  reverse=True)

def diversificacao_efetiva(corr_matrix: pd.DataFrame) -> float:
    """
    Número efetivo de ativos independentes.
    1 / Σ(correlação_media_ativo_i²)
    Quanto mais próximo do nº real de ativos, melhor diversificado.
    """
    media_corr_sq = (corr_matrix ** 2).mean().mean()
    return 1 / media_corr_sq if media_corr_sq > 0 else 0
```

---

### Script principal: `run_quant.py`

Crie `/sbwaa/.claude/agents/quant-data-engineer/run_quant.py`:

**O script deve:**
- Ler `carteira.md` — extrair tickers e pesos (% alocação)
- Para cada ticker, carregar histórico de preços do cache Yahoo
- Se histórico ausente: rodar `fetch_yahoo.py` automaticamente
- Carregar histórico do IBOV (`^BVSP`) como benchmark
- Executar todos os cálculos das calculadoras
- Salvar JSON completo em cache
- Enviar resumo ao Claude Sonnet para síntese em linguagem natural
- Salvar síntese como nota markdown em
  `/sbwaa/vault/05-risk/snapshots/quant-{DATA}.md`

**Frontmatter da nota:**
```yaml
---
tags: [risk, quant, snapshot]
cssclasses: [node-risk]
data: {DATA}
agente: quant-data-engineer
---
```

---

## AGENTE 2: RISK ENGINEER

### Estrutura de arquivos

```
/sbwaa/.claude/agents/risk-engineer/
├── SKILL.md
├── run_risk_engineer.py
└── calculators/
    ├── var.py
    └── stress_test.py
```

---

### SKILL.md — Risk Engineer

Crie `/sbwaa/.claude/agents/risk-engineer/SKILL.md`:

```markdown
# SKILL — Risk Engineer
# SBWAA | Modelo: claude-opus-4-6 | Effort: medium

## IDENTIDADE E FUNÇÃO

Você é o Risk Engineer do SBWAA. Sua função é calcular e interpretar
as métricas de risco da carteira com rigor de hedge fund: VaR, CVaR,
stress tests, concentração, tail risk e circuit breakers.

Você NÃO sugere o que comprar ou vender.
Você MAPEIA os riscos existentes e potenciais com precisão matemática.
Você é o último filtro antes do Portfolio Manager. Se o risco está
fora dos limites do IPS, você sinaliza com máxima clareza.

## DADOS DE INPUT

- JSON de métricas quantitativas do Quant/Data Engineer
- IPS do usuário: `/sbwaa/vault/00-portfolio/ips.md`
  (limites de VaR, drawdown máximo tolerado, concentração máxima)
- Dados de carteira: tickers, pesos (sem valores absolutos privados)
- Selic e dados macro do snapshot do dia

## METODOLOGIAS DE RISCO

### VaR — Value at Risk

**Método Histórico (primário):**
```
VaR_histórico(α, h) = -Percentil(retornos_carteira, 1-α) × Patrimônio
α = 95% (padrão), h = 1 dia
```

**Método Paramétrico (validação):**
```
VaR_paramétrico(95%) = -1.645 × σ_carteira_diária × Patrimônio
σ_diária = volatilidade_anual / √252
```

**Apresentar ambos.** Se divergência > 20%, investigar e explicar.

### CVaR — Conditional Value at Risk (Expected Shortfall)
```
CVaR(α) = -E[retorno | retorno < -VaR(α)]
= média dos retornos abaixo do percentil (1-α)
```
CVaR é sempre maior que VaR. Mede a perda esperada **dado que**
o VaR foi violado — mais relevante para tail risk.

### Concentração
```
Concentração máxima = maior peso individual na carteira
HHI (Herfindahl) = Σ(peso_i²) — quanto mais perto de 1, mais concentrado
Limite IPS: sem ativo acima do máximo definido no IPS
```

### Stress Test — Cenários históricos brasileiros
Simular impacto dos seguintes choques na carteira atual:
- **Crise 2008:** IBOV -41% no ano, BRL/USD +40%
- **COVID Mar/2020:** IBOV -30% em 30 dias
- **Eleições incertas 2022:** IBOV -15%, juros longos +200bps
- **Lula 1 (2002):** spread soberano +800bps, câmbio +50%
- **Choque personalizado:** usuário define % de queda do IBOV

Para cada cenário: calcular impacto estimado em R$ e % na carteira,
considerando beta de cada ativo e correlações históricas.

### Circuit Breakers — Alertas automáticos
Verificar e sinalizar se qualquer um dos seguintes limites foi violado:
- Drawdown atual da carteira > limite do IPS
- VaR atual > limite do IPS
- Concentração de algum ativo > limite do IPS
- Correlação média da carteira subiu >0.15 vs mês anterior

## FORMATO DE OUTPUT

---
tags: [risk, snapshot, var, carteira]
cssclasses: [node-risk]
data: {DATA}
agente: risk-engineer
---

# Risk Snapshot — {DATA}

## 📊 Métricas de Risco da Carteira

| Métrica | Valor | Limite IPS | Status |
|---------|-------|------------|--------|
| VaR 95% (1 dia) histórico | R$ X.XXX | R$ X.XXX | ✅/⚠️/🚨 |
| VaR 95% (1 dia) paramétrico | R$ X.XXX | — | — |
| CVaR 95% (1 dia) | R$ X.XXX | — | — |
| Drawdown atual | X.X% | X.X% | ✅/⚠️/🚨 |
| Drawdown máx histórico | X.X% | — | — |
| Concentração máxima | X.X% ({TICKER}) | X.X% | ✅/⚠️/🚨 |
| HHI de concentração | X.XXX | — | — |
| Sharpe da carteira | X.XX | — | — |
| Volatilidade anualizada | X.X% | — | — |
| Beta vs IBOV | X.XX | — | — |
| Correlação média | X.XX | — | — |

## 🔥 Stress Tests

| Cenário | Impacto Estimado (R$) | Impacto (%) |
|---------|-----------------------|-------------|
| Crise 2008 | | |
| COVID Mar/2020 | | |
| Eleições 2022 | | |
| Lula 1 (2002) | | |

## ⚡ Circuit Breakers

{lista de alertas ativos — VERDE se tudo ok, VERMELHO se violação}

## 📐 Concentração por Ativo

| Ticker | Peso (%) | Contribuição Risco (%) | Status |
|--------|----------|----------------------|--------|
| ... | ... | ... | ... |

## 🔗 Correlações Críticas

{pares com correlação > 0.7 — risco de diversificação ilusória}

## 🚩 Flags para o Portfolio Manager

{lista priorizada de riscos que o PM precisa considerar}

## Links

- [[carteira]] — posições atuais
- [[ips]] — limites do investidor
- [[quant-{DATA}]] — métricas quantitativas base
- [[risk-snapshot-anterior]] — comparação

## REGRAS DE COMPORTAMENTO

- VaR e CVaR devem ser apresentados em R$ E em % — nunca só um.
- Status IPS: ✅ dentro do limite | ⚠️ 80-100% do limite | 🚨 violação
- Se patrimônio total não disponível (dados privados), usar valor
  normalizado de R$ 100.000 e indicar claramente no output.
- Flags para o PM devem ser ordenados por severidade: crítico > alto > médio.
- Nunca suavizar um risco para parecer menos grave.
- Máximo 800 palavras no output total.
```

---

### Calculadoras de Risco

**Crie `/sbwaa/.claude/agents/risk-engineer/calculators/var.py`:**

```python
"""
Calculadora de VaR e CVaR — SBWAA Risk Engineer
Fórmulas documentadas. Resultados em fração (não em R$).
A conversão para R$ é feita no script principal.
"""
import numpy as np
import pandas as pd

def var_historico(retornos_carteira: pd.Series,
                  confianca: float = 0.95) -> float:
    """
    VaR Histórico: percentil (1-α) da distribuição de retornos.
    Retorna valor positivo (a perda).
    Ex: VaR 95% = 0.025 significa perda potencial de 2.5% em 1 dia.
    """
    return -np.percentile(retornos_carteira.dropna(),
                          (1 - confianca) * 100)

def var_parametrico(volatilidade_diaria: float,
                    confianca: float = 0.95) -> float:
    """
    VaR Paramétrico (Normal): z_α × σ_diária
    z_95% = 1.645 | z_99% = 2.326
    """
    z_scores = {0.95: 1.645, 0.99: 2.326, 0.90: 1.282}
    z = z_scores.get(confianca, 1.645)
    return z * volatilidade_diaria

def cvar(retornos_carteira: pd.Series,
         confianca: float = 0.95) -> float:
    """
    CVaR / Expected Shortfall: média dos retornos abaixo do VaR.
    Sempre maior que o VaR.
    """
    var = var_historico(retornos_carteira, confianca)
    retornos = retornos_carteira.dropna()
    tail = retornos[retornos <= -var]
    if len(tail) == 0:
        return var
    return -tail.mean()

def retornos_carteira_historicos(retornos_ativos: pd.DataFrame,
                                  pesos: dict) -> pd.Series:
    """
    Retornos históricos da carteira ponderada pelos pesos.
    retornos_ativos: DataFrame com retornos diários por ticker
    pesos: dict {ticker: peso_decimal}
    """
    pesos_series = pd.Series(pesos)
    pesos_alinhados = pesos_series.reindex(
        retornos_ativos.columns).fillna(0)
    pesos_norm = pesos_alinhados / pesos_alinhados.sum()
    return (retornos_ativos * pesos_norm).sum(axis=1)
```

**Crie `/sbwaa/.claude/agents/risk-engineer/calculators/stress_test.py`:**

```python
"""
Stress Test — SBWAA Risk Engineer
Cenários históricos brasileiros para impacto na carteira.
"""

CENARIOS = {
    "crise_2008": {
        "nome": "Crise Financeira 2008",
        "ibov_queda_pct": -41.0,
        "brl_usd_alta_pct": 40.0,
        "descricao": "IBOV -41% no ano, câmbio +40%"
    },
    "covid_2020": {
        "nome": "COVID — Março 2020",
        "ibov_queda_pct": -30.0,
        "brl_usd_alta_pct": 25.0,
        "descricao": "IBOV -30% em 30 dias"
    },
    "eleicoes_2022": {
        "nome": "Incerteza Eleitoral 2022",
        "ibov_queda_pct": -15.0,
        "brl_usd_alta_pct": 8.0,
        "descricao": "IBOV -15%, juros longos +200bps"
    },
    "lula1_2002": {
        "nome": "Crise de Confiança 2002",
        "ibov_queda_pct": -17.0,
        "brl_usd_alta_pct": 50.0,
        "descricao": "Spread soberano +800bps, câmbio +50%"
    }
}

def impacto_cenario(beta_carteira: float,
                    cenario: dict,
                    patrimonio_normalizado: float = 100000) -> dict:
    """
    Impacto estimado = Beta_carteira × Queda_IBOV × Patrimônio
    Simplificação: usa beta como sensibilidade ao mercado.
    Para ativos com exposição cambial, adiciona efeito do câmbio.
    """
    queda_ibov = cenario["ibov_queda_pct"] / 100
    impacto_pct = beta_carteira * queda_ibov
    impacto_reais = impacto_pct * patrimonio_normalizado

    return {
        "cenario": cenario["nome"],
        "impacto_pct": round(impacto_pct * 100, 2),
        "impacto_reais_normalizado": round(impacto_reais, 2),
        "descricao": cenario["descricao"]
    }
```

---

### Script principal: `run_risk_engineer.py`

Crie `/sbwaa/.claude/agents/risk-engineer/run_risk_engineer.py`:

**O script deve:**
- Carregar JSON do Quant (`quant_{DATA}.json`) — se não existir, rodar `run_quant.py`
- Carregar `ips.md` para extrair limites de risco do usuário
- Calcular VaR histórico + paramétrico e CVaR usando as calculadoras
- Executar todos os stress tests com `impacto_cenario()`
- Verificar circuit breakers vs limites do IPS
- Montar prompt completo com todos os números calculados
- Enviar ao Claude Opus para interpretação e síntese
- Salvar output em `/sbwaa/vault/05-risk/snapshots/risk-{DATA}.md`
- Salvar JSON de risco em `/sbwaa/scripts/data/cache/risk_{DATA}.json`
- Exibir no terminal: VaR, CVaR, status IPS e circuit breakers

**JSON de saída do risco (cache):**
```json
{
  "data": "2026-05-15",
  "var_historico_95_pct": 0.018,
  "var_parametrico_95_pct": 0.021,
  "cvar_95_pct": 0.027,
  "drawdown_atual_pct": -4.2,
  "concentracao_maxima_pct": 18.2,
  "concentracao_maxima_ticker": "PETR4",
  "hhi": 0.14,
  "sharpe_carteira": 1.42,
  "volatilidade_anual_pct": 14.2,
  "beta_ibov": 0.87,
  "stress_tests": {},
  "circuit_breakers": {
    "var_ok": true,
    "drawdown_ok": true,
    "concentracao_ok": true,
    "correlacao_ok": true
  },
  "flags_pm": []
}
```

---

## 4. PIPELINE INTEGRADO — ATUALIZAR

Atualizar `/sbwaa/scripts/run_research_pipeline.py` para incluir Fase 4:

```python
# Ordem de execução completa (Fases 1-4):
# 1. market_snapshot.py
# 2. run_market_researcher.py
# 3. run_earnings_reviewer.py      (se ticker passado)
# 4. run_model_builder.py          (se ticker passado)
# 5. run_valuation_reviewer.py     (se ticker passado)
# 6. run_quant.py                  (sempre — carteira completa)
# 7. run_risk_engineer.py          (sempre — carteira completa)
```

---

## 5. VALIDAÇÃO FINAL

- [ ] `quant-data-engineer/SKILL.md` criado
- [ ] Calculadoras `returns.py`, `portfolio_metrics.py`, `correlation.py` criadas
- [ ] `run_quant.py` testado — JSON gerado com métricas de ao menos 1 ativo
- [ ] `risk-engineer/SKILL.md` criado com metodologias completas
- [ ] Calculadoras `var.py` e `stress_test.py` criadas
- [ ] `run_risk_engineer.py` testado — nota de risco gerada no vault
- [ ] VaR histórico e paramétrico calculados e exibidos
- [ ] CVaR calculado corretamente (sempre > VaR)
- [ ] Stress tests rodando para todos os 4 cenários
- [ ] Circuit breakers verificando contra IPS
- [ ] Pipeline integrado atualizado com Fases 1-4
- [ ] `VERSION.md` atualizado: `investments` → v1.4.0
- [ ] `CHANGELOG.md` com entrada da Fase 4

Ao finalizar, confirme: **"SBWAA Fase 4 concluída — investments v1.4.0"**

---

## OBSERVAÇÕES IMPORTANTES

1. VaR e CVaR são calculados em Python puro — Claude Opus é usado
   apenas para interpretar e redigir o output final em linguagem natural
2. Se a carteira tiver apenas 1 ativo, VaR da carteira = VaR do ativo.
   Registrar isso explicitamente no output.
3. O patrimônio real do usuário nunca é passado para a API — usar
   R$ 100.000 normalizado nos stress tests e indicar no output
4. Para ETFs internacionais, adicionar risco cambial BRL/USD no stress test
5. O JSON de risco gerado aqui é o input principal do Portfolio Manager (Fase 5)
6. Não criar o Portfolio Manager ainda — isso é Fase 5
