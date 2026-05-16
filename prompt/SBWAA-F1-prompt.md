# SBWAA — FASE 1: PIPELINE DE DADOS
**Prompt para execução no Claude Code**
**Versão:** 1.1.0
**Fase:** 1 de 8
**Pré-requisito:** Fase 0 concluída (v1.0.0)

---

## CONTEXTO

A Fase 0 criou a base estrutural do SBWAA. A Fase 1 constrói o **pipeline de dados**: os scripts Python responsáveis por buscar cotações, dados fundamentalistas e informações de mercado das APIs públicas (Brapi e Yahoo Finance), e por popular/atualizar os arquivos do vault automaticamente.

Nenhum dado privado (patrimônio, quantidade, custo médio) sai do vault local. As APIs recebem apenas tickers públicos.

---

## REGRAS GERAIS — LER ANTES DE EXECUTAR

1. Instalar dependências com `pip install --break-system-packages` ou `pip install` em venv
2. Todos os scripts ficam em `/sbwaa/scripts/data/`
3. Nenhum script loga ou transmite dados de portfólio para fora
4. Todo script deve ter tratamento de erro com mensagens claras em português
5. Ao final de cada script, atualizar `VERSION.md` e `CHANGELOG.md` (módulo `investments` → MINOR bump: v1.0.0 → v1.1.0)
6. Testar cada script individualmente antes de prosseguir

---

## DEPENDÊNCIAS

Instale as seguintes bibliotecas Python:

```bash
pip install requests yfinance pandas python-dotenv --break-system-packages
```

---

## 1. SCRIPT: `fetch_brapi.py`

**Caminho:** `/sbwaa/scripts/data/fetch_brapi.py`

**Função:** Busca cotações, dados fundamentalistas e dividendos de ativos brasileiros via Brapi (https://brapi.dev). API gratuita, sem chave obrigatória para uso básico.

**O script deve:**

- Receber uma lista de tickers como argumento (ex: `python fetch_brapi.py PETR4 VALE3 MXRF11`)
- Para cada ticker, buscar:
  - Cotação atual, variação do dia (%), volume
  - P/L, EV/EBITDA, P/VP, Dividend Yield, ROE, Dívida Líquida/EBITDA
  - Últimos 3 dividendos pagos (data + valor)
  - Setor e subsetor
- Retornar os dados como dicionário Python e salvar em `/sbwaa/scripts/data/cache/brapi_{TICKER}_{DATA}.json`
- Nunca receber ou transmitir: quantidade de cotas, preço médio, patrimônio
- Exibir no terminal um resumo limpo por ticker ao finalizar

**Endpoint base Brapi:**
```
https://brapi.dev/api/quote/{TICKER}?modules=summaryProfile,defaultKeyStatistics,financialData,balanceSheetHistory
```

**Estrutura do JSON de saída por ticker:**
```json
{
  "ticker": "PETR4",
  "tipo": "acao-pn",
  "nome": "Petrobras PN",
  "setor": "Energia",
  "cotacao": 38.50,
  "variacao_dia_pct": -1.2,
  "volume": 45000000,
  "pl": 4.2,
  "ev_ebitda": 3.1,
  "pvp": 1.8,
  "dy": 12.4,
  "roe": 28.5,
  "divida_liquida_ebitda": 0.9,
  "dividendos_recentes": [
    {"data": "2026-03-15", "valor": 1.20},
    {"data": "2025-12-15", "valor": 0.95},
    {"data": "2025-09-15", "valor": 1.10}
  ],
  "fonte": "brapi",
  "atualizado_em": "2026-05-15T08:00:00"
}
```

---

## 2. SCRIPT: `fetch_yahoo.py`

**Caminho:** `/sbwaa/scripts/data/fetch_yahoo.py`

**Função:** Busca dados de ETFs internacionais, macroeconomia (índices globais, câmbio, commodities) e histórico de preços via Yahoo Finance (biblioteca `yfinance`).

**O script deve:**

- Receber lista de tickers Yahoo como argumento (ex: `python fetch_yahoo.py VT IVV BOVA11 BRL=X CL=F`)
- Para cada ticker, buscar:
  - Cotação atual e variação do dia
  - Histórico de preços dos últimos 252 dias úteis (1 ano)
  - Para ETFs: AUM, expense ratio, benchmark
  - Para câmbio (BRL=X, EUR=X): taxa atual
  - Para commodities (CL=F petróleo, GC=F ouro): preço atual
- Salvar em `/sbwaa/scripts/data/cache/yahoo_{TICKER}_{DATA}.json`
- Salvar histórico de preços em `/sbwaa/scripts/data/cache/hist_{TICKER}_{DATA}.csv`

**Tickers padrão a monitorar sempre (macro global):**
```python
MACRO_TICKERS = {
    "IBOV": "^BVSP",
    "SP500": "^GSPC",
    "NASDAQ": "^IXIC",
    "DXY": "DX-Y.NYB",
    "BRL_USD": "BRL=X",
    "PETROLEO_WTI": "CL=F",
    "OURO": "GC=F",
    "JUROS_US_10Y": "^TNX"
}
```

**Estrutura do JSON de saída:**
```json
{
  "ticker_yahoo": "^BVSP",
  "nome": "IBOVESPA",
  "tipo": "indice",
  "cotacao_atual": 138500,
  "variacao_dia_pct": 0.8,
  "moeda": "BRL",
  "historico_disponivel": true,
  "fonte": "yahoo_finance",
  "atualizado_em": "2026-05-15T08:00:00"
}
```

---

## 3. SCRIPT: `update_carteira.py`

**Caminho:** `/sbwaa/scripts/data/update_carteira.py`

**Função:** Lê as posições em `carteira.md`, busca cotações atualizadas via Brapi/Yahoo, calcula P&L, e reescreve a tabela de posições no arquivo com os dados atualizados. **Este script é o único que acessa dados privados (quantidade e preço médio) — e nunca os transmite para fora.**

**O script deve:**

- Ler `/sbwaa/vault/00-portfolio/carteira.md` e extrair a tabela de posições
- Para cada ativo com ticker, quantidade e preço médio preenchidos:
  - Buscar cotação atual (Brapi para BR, Yahoo para internacionais)
  - Calcular: Preço Atual, P&L em R$, P&L em %, Valor atual da posição
  - Calcular % de alocação de cada ativo no portfólio total
- Reescrever a tabela no `carteira.md` com os valores atualizados
- Atualizar o bloco "Resumo" com: Patrimônio Total, Total Investido, P&L Total, data/hora da última atualização
- Gerar wikilinks automáticos: cada ticker na tabela vira `[[01-ativos/TICKER/tese]]` se o arquivo existir

**Formato da tabela atualizada em `carteira.md`:**
```markdown
| Ticker | Tipo | Setor | Qtd | Preço Médio | Preço Atual | Valor (R$) | P&L (R$) | P&L (%) | Alocação (%) |
|--------|------|-------|-----|-------------|-------------|------------|----------|---------|--------------|
| [[PETR4\|PETR4]] | 🟦 AÇÃO PN | Energia | 100 | 36.00 | 38.50 | 3.850 | +250 | +6.9% | 8.2% |
```

---

## 4. SCRIPT: `add_ativo.py`

**Caminho:** `/sbwaa/scripts/data/add_ativo.py`

**Função:** Implementa o comando `/adicionar`. Adiciona um novo ativo à `carteira.md` e cria a estrutura de pasta e nota base do ativo no vault.

**O script deve receber os seguintes argumentos:**
```bash
python add_ativo.py --ticker PETR4 --tipo acao-pn --quantidade 100 --preco-medio 36.00 --setor energia
```

**Tipos válidos:** `acao-on`, `acao-pn`, `fii`, `etf-br`, `etf-intl`, `renda-fixa`, `tesouro`, `debenture`, `cri-cra`

**Ao executar, o script deve:**

1. Validar se o ticker existe na Brapi ou Yahoo antes de adicionar
2. Adicionar linha na tabela de `carteira.md`
3. Adicionar entrada em `historico-trades.md` com data, operação=COMPRA, qtd, preço
4. Criar pasta `/sbwaa/vault/01-ativos/{TICKER}/`
5. Criar nota base `/sbwaa/vault/01-ativos/{TICKER}/tese.md` com o frontmatter correto:

```markdown
---
tags: [ativo, {tipo}, {ticker-lowercase}]
cssclasses: [node-{tipo}]
ticker: {TICKER}
tipo: {tipo}
setor: {setor}
status: aguardando-analise
---

# {TICKER} — Tese de Investimento

> Análise pendente. Execute `/analisar {TICKER}` para gerar.

## Links
- [[carteira]] — posição atual
- [[ips]] — adequação ao perfil
```

6. Confirmar no terminal: `"✅ {TICKER} adicionado à carteira. Pasta criada em vault/01-ativos/{TICKER}/"`

---

## 5. SCRIPT: `market_snapshot.py`

**Caminho:** `/sbwaa/scripts/data/market_snapshot.py`

**Função:** Gera um snapshot diário do mercado (macro global + ativos da carteira) e salva como nota no vault. Este é o dado base que os agentes de análise vão consumir.

**O script deve:**

- Buscar todos os tickers macro (IBOV, SP500, NASDAQ, DXY, BRL/USD, petróleo, ouro, juros US 10Y)
- Buscar cotações de todos os ativos presentes em `carteira.md`
- Gerar nota `/sbwaa/vault/02-relatorios/diarios/snapshot-{DATA}.md` com o seguinte formato:

```markdown
---
tags: [relatorio, snapshot, diario]
cssclasses: [node-relatorio]
data: {DATA}
---

# Market Snapshot — {DATA}

## Macro Global
| Indicador | Valor | Variação |
|-----------|-------|----------|
| IBOVESPA  | ...   | ...%     |
| S&P 500   | ...   | ...%     |
| NASDAQ    | ...   | ...%     |
| DXY       | ...   | ...%     |
| BRL/USD   | ...   | ...%     |
| Petróleo  | ...   | ...%     |
| Ouro      | ...   | ...%     |
| Juros US 10Y | ... | ...%  |

## Carteira — Posições Hoje
| Ticker | Preço Atual | Variação Dia | P&L Total |
|--------|-------------|--------------|-----------|
| ...    | ...         | ...          | ...       |

## Links
- [[carteira]] — posição completa
- [[snapshot-{DATA-1}]] — dia anterior
```

---

## 6. PASTA DE CACHE

Crie a pasta `/sbwaa/scripts/data/cache/` e adicione ao `.gitignore`:
```
scripts/data/cache/
```

O cache evita chamadas desnecessárias à API. Cada arquivo de cache tem validade de 4 horas — se o arquivo existe e tem menos de 4h, reutilizar sem nova chamada.

---

## 7. VALIDAÇÃO FINAL

Execute a checklist abaixo e confirme cada item:

- [ ] `fetch_brapi.py` criado e testado com ao menos 1 ticker BR
- [ ] `fetch_yahoo.py` criado e testado com ao menos 1 ticker + macro global
- [ ] `update_carteira.py` criado e funcionando (mesmo com tabela vazia)
- [ ] `add_ativo.py` criado — testar adicionando 1 ativo fictício e removendo depois
- [ ] `market_snapshot.py` criado e gerando nota no vault corretamente
- [ ] Pasta `/cache/` criada e no `.gitignore`
- [ ] `VERSION.md` atualizado: módulo `investments` → v1.1.0
- [ ] `CHANGELOG.md` com entrada da Fase 1

Ao finalizar, confirme no terminal: **"SBWAA Fase 1 concluída — investments v1.1.0"**

---

## OBSERVAÇÕES IMPORTANTES

1. A Brapi pode ter rate limit no plano gratuito — adicionar `time.sleep(0.5)` entre chamadas de múltiplos tickers
2. Yahoo Finance pode falhar em tickers BR com sufixo `.SA` — testar ambos: `PETR4` e `PETR4.SA`
3. Não criar agentes ainda — isso é Fase 2
4. O `update_carteira.py` nunca deve sobrescrever quantidade e preço médio — apenas atualiza cotação atual e cálculos derivados
5. Todos os valores monetários em R$ com 2 casas decimais, percentuais com 1 casa decimal
