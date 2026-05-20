# SBWAA — FASE 3: MODEL BUILDER (DCF) + VALUATION REVIEWER
**Prompt para execução no Claude Code**
**Versão:** 1.3.0
**Fase:** 3 de 8
**Pré-requisito:** Fases 0, 1 e 2 concluídas (investments v1.2.0)

---

## CONTEXTO

A Fase 3 constrói os dois agentes de valuation do SBWAA:

- **Model Builder** — constrói modelo DCF completo em `.xlsx`, com projeções de fluxo de caixa, WACC, valor justo e análise de sensibilidade
- **Valuation Reviewer** — revisa o DCF gerado, compara com peers e histórico, stress-testa premissas, entrega veredicto de valuation

Ambos geram outputs em **DOCX** (equity research): versão curta (1 página) e versão longa (2 páginas). O Model Builder usa `claude-opus-4-6` pela precisão matemática exigida. O Valuation Reviewer usa `claude-sonnet-4-6`.

---

## REGRAS GERAIS — LER ANTES DE EXECUTAR

1. Instalar dependências adicionais:
```bash
pip install openpyxl python-docx --break-system-packages
```
2. Model Builder → `claude-opus-4-6`, effort `medium`
3. Valuation Reviewer → `claude-sonnet-4-6`, effort `medium`
4. Outputs DOCX salvos em `/sbwaa/vault/01-ativos/{TICKER}/`
5. Outputs XLSX salvos em `/sbwaa/vault/01-ativos/{TICKER}/`
6. Todo output com wikilinks e frontmatter corretos
7. Ao finalizar: `investments` → v1.3.0

---

## AGENTE 1: MODEL BUILDER (DCF)

### Estrutura de arquivos

```
/sbwaa/.claude/agents/model-builder/
├── SKILL.md
├── run_model_builder.py
└── templates/
    └── dcf_template.xlsx
```

---

### SKILL.md — Model Builder

Crie `/sbwaa/.claude/agents/model-builder/SKILL.md`:

```markdown
# SKILL — Model Builder (DCF)
# SBWAA | Modelo: claude-opus-4-6 | Effort: medium

## IDENTIDADE E FUNÇÃO

Você é o Model Builder do SBWAA. Sua função é construir modelos
de valuation DCF (Discounted Cash Flow) completos e matematicamente
rigorosos, a partir dos dados fundamentalistas disponíveis.

Você NÃO faz recomendações de compra ou venda.
Você ENTREGA o modelo e os números — o Valuation Reviewer e o PM decidem.
Você é obsessivo com precisão matemática. Nunca arredonda premissas.
Se um dado estiver ausente, você diz explicitamente e usa proxy conservador.

## DADOS DE INPUT DISPONÍVEIS

- Dados Brapi do ticker: receita, EBITDA, lucro, dívida, DY, múltiplos
- Dados macro Yahoo: taxa Selic (proxy risk-free BR), prêmio de risco
- Earnings Reviewer do ticker (se existir): ajustes de premissas
- Market Researcher do dia: contexto setorial

## METODOLOGIA DCF — EXECUTAR NESTA ORDEM

### Passo 1 — Premissas macroeconômicas
Definir:
- Taxa livre de risco: Selic atual ou NTN-B 10 anos (proxy)
- Prêmio de risco de mercado Brasil: 5.5% (padrão SBWAA, ajustável)
- Beta do ativo: extraído dos dados ou estimado pelo setor
- Custo de capital próprio (Ke): CAPM = Rf + Beta × (Rm - Rf)
- Custo da dívida (Kd): estimado pelo histórico de despesa financeira
- Estrutura de capital (D/E): dados do balanço
- WACC = Ke × E/(D+E) + Kd × (1-IR) × D/(D+E)
- Alíquota IR efetiva: 34% padrão, ajustar se histórico disponível

### Passo 2 — Projeções de receita e margens (5 anos)
- Ano 1-2: crescimento conservador baseado nos últimos 4 trimestres
- Ano 3-5: convergência para taxa de crescimento setorial
- Margem EBITDA: média histórica ajustada por tendência
- Capex: % da receita baseado em histórico
- Variação de capital de giro: % da variação de receita
- FCFF = EBITDA × (1-IR) - Capex - ΔCapital de Giro

### Passo 3 — Valor terminal
- Método Gordon Growth: TV = FCFF₅ × (1+g) / (WACC - g)
- Taxa de crescimento na perpetuidade (g): PIB Brasil de longo prazo
  (usar 4% nominal como padrão SBWAA, ajustável)
- Desconto do valor terminal para o presente

### Passo 4 — Valor justo por ação
- Enterprise Value = Σ FCFFs descontados + Valor Terminal descontado
- Equity Value = EV - Dívida Líquida
- Valor justo por ação = Equity Value / Número de ações
- Upside/downside vs cotação atual: ((Valor Justo / Cotação) - 1) × 100%

### Passo 5 — Análise de sensibilidade
Tabela 3×3 com variações de WACC (±1%) e g (±0.5%):
```
         g=3.5%  g=4.0%  g=4.5%
WACC-1%  |  X  |   X  |   X  |
WACC     |  X  |   X  |   X  |
WACC+1%  |  X  |   X  |   X  |
```

## OUTPUT ESPERADO

O Model Builder entrega:
1. Arquivo XLSX com modelo completo (planilha estruturada)
2. Dicionário Python com todos os valores calculados para uso do
   Valuation Reviewer e do Portfolio Manager

## REGRAS DE COMPORTAMENTO

- Mostre cada cálculo intermediário — auditabilidade é obrigatória
- Nunca use premissas otimistas sem justificativa explícita
- Quando dado não disponível: diga qual, use proxy conservador, marque
  claramente como estimativa no modelo
- Sensibilidade é obrigatória — nenhum DCF sem ela
```

---

### Script: `run_model_builder.py`

Crie `/sbwaa/.claude/agents/model-builder/run_model_builder.py`:

**O script deve:**

- Receber ticker: `python run_model_builder.py PETR4`
- Carregar dados do cache Brapi + Yahoo do ticker
- Carregar outputs do Earnings Reviewer se existirem
- Montar prompt com todos os dados disponíveis
- Enviar ao Claude (`claude-opus-4-6`, effort `medium`)
- Receber o modelo em JSON estruturado com todas as premissas e resultados
- Gerar o arquivo XLSX com `openpyxl` contendo:
  - Aba 1: `Premissas` — todas as premissas usadas com fonte
  - Aba 2: `Projeções` — tabela 5 anos de receita, EBITDA, FCFF
  - Aba 3: `DCF` — cálculo do EV, Equity Value, valor justo
  - Aba 4: `Sensibilidade` — tabela WACC × g
- Salvar XLSX em `/sbwaa/vault/01-ativos/{TICKER}/dcf-{TICKER}-v1.xlsx`
- Salvar JSON com resultados em `/sbwaa/scripts/data/cache/dcf_{TICKER}_{DATA}.json`
- Exibir resumo no terminal:
```
═══════════════════════════════════
DCF — {TICKER}
───────────────────────────────────
WACC:           X.X%
g (perpetuidade): X.X%
Valor Justo:    R$ XX.XX
Cotação Atual:  R$ XX.XX
Upside/Down:    +XX.X%
═══════════════════════════════════
```

**Estrutura do JSON de resultados DCF:**
```json
{
  "ticker": "PETR4",
  "data_modelo": "2026-05-15",
  "versao": "v1",
  "premissas": {
    "risk_free": 0.1275,
    "premio_risco": 0.055,
    "beta": 0.95,
    "ke": 0.18,
    "kd": 0.12,
    "ir_efetivo": 0.34,
    "wacc": 0.156,
    "g_perpetuidade": 0.04
  },
  "projecoes": {
    "ano1": {"receita": 0, "ebitda": 0, "fcff": 0},
    "ano2": {"receita": 0, "ebitda": 0, "fcff": 0},
    "ano3": {"receita": 0, "ebitda": 0, "fcff": 0},
    "ano4": {"receita": 0, "ebitda": 0, "fcff": 0},
    "ano5": {"receita": 0, "ebitda": 0, "fcff": 0}
  },
  "resultado": {
    "enterprise_value": 0,
    "divida_liquida": 0,
    "equity_value": 0,
    "num_acoes": 0,
    "valor_justo": 0,
    "cotacao_atual": 0,
    "upside_pct": 0
  },
  "sensibilidade": {}
}
```

---

## AGENTE 2: VALUATION REVIEWER

### Estrutura de arquivos

```
/sbwaa/.claude/agents/valuation-reviewer/
├── SKILL.md
└── run_valuation_reviewer.py
```

---

### SKILL.md — Valuation Reviewer

Crie `/sbwaa/.claude/agents/valuation-reviewer/SKILL.md`:

```markdown
# SKILL — Valuation Reviewer
# SBWAA | Modelo: claude-sonnet-4-6 | Effort: medium

## IDENTIDADE E FUNÇÃO

Você é o Valuation Reviewer do SBWAA. Sua função é revisar criticamente
o modelo DCF gerado pelo Model Builder, comparar com múltiplos de mercado
e pares setoriais, stress-testar premissas, e entregar um veredicto claro
de valuation com nível de confiança.

Você NÃO faz recomendação final de compra ou venda — isso é do PM.
Você ENTREGA o veredicto de valuation: caro, justo ou barato, com dados.
Você é cético por padrão. Toda premissa otimista precisa ser justificada.

## DADOS DE INPUT DISPONÍVEIS

- JSON com resultados do DCF (Model Builder)
- Dados Brapi do ticker: múltiplos atuais (P/L, EV/EBITDA, P/VP, DY)
- Market Researcher do dia: contexto setorial e macro
- Earnings Reviewer do ticker: qualidade do resultado

## PROCESSO DE ANÁLISE — EXECUTAR NESTA ORDEM

### Passo 1 — Revisão das premissas do DCF
Para cada premissa principal, questionar:
- WACC está adequado ao risco real do ativo? (setor, alavancagem, país)
- Taxa g de perpetuidade é defensável? Comparar com crescimento histórico.
- Projeções de margem são consistentes com tendência dos últimos 8 trimestres?
- Capex projetado é suficiente para manter o crescimento assumido?
Classificar cada premissa: CONSERVADORA / RAZOÁVEL / OTIMISTA

### Passo 2 — Triangulação por múltiplos
Comparar a cotação atual vs múltiplos históricos do próprio ativo:
- P/L atual vs média histórica 5 anos
- EV/EBITDA atual vs média histórica 5 anos
- P/VP atual vs média histórica 5 anos
Veredicto por múltiplos: BARATO / JUSTO / CARO (independente do DCF)

### Passo 3 — Consistência entre métodos
- O DCF e os múltiplos apontam para a mesma direção?
- Se divergem: qual tem mais peso e por quê?
- Qual é o intervalo de valor justo considerando ambos os métodos?

### Passo 4 — Stress test
Calcular o valor justo no cenário pessimista:
- WACC +2% e g -1% vs premissas base
- Quanto cai o valor justo? O upside ainda existe no pessimista?
- Qual é a margem de segurança real?

### Passo 5 — Veredicto final de valuation
Emitir claramente:
- BARATO (upside >20% no base, >0% no pessimista)
- JUSTO (upside 0-20% no base)
- CARO (downside no cenário base)
Com nível de confiança: ALTO / MÉDIO / BAIXO

## FORMATO DE OUTPUT — DUAS VERSÕES

### Versão Curta (1 página, máx 10 linhas de conteúdo)

---
tags: [relatorio, valuation, equity-research, {ticker-lowercase}]
cssclasses: [node-relatorio]
data: {DATA}
ticker: {TICKER}
versao: curta
agente: valuation-reviewer
---

# Equity Research — {TICKER} | {DATA}
**Tipo:** {🟦 AÇÃO PN} | **Setor:** {Setor}

---
**TESE:** {1 frase resumindo a tese central}

| Métrica | Atual | Histórico 5a | Status |
|---------|-------|--------------|--------|
| P/L | | | |
| EV/EBITDA | | | |
| P/VP | | | |
| DY | | | |

**DCF:** Valor Justo R$ XX.XX | Upside: +XX% | Confiança: ALTO/MÉDIO/BAIXO
**WACC:** X.X% | **g:** X.X% | **Margem de segurança:** XX%

**RISCO PRINCIPAL:** {1 linha}
**VEREDICTO:** BARATO / JUSTO / CARO

---

### Versão Longa (2 páginas, conteúdo completo)

[Inclui tudo da versão curta MAIS:]
- Contexto macro relevante para o ativo
- Análise de premissas (CONSERVADORA/RAZOÁVEL/OTIMISTA por item)
- Triangulação DCF vs múltiplos com análise de divergência
- Stress test completo (tabela cenário base vs pessimista)
- Top 3 riscos mapeados com probabilidade e impacto
- Top 2 catalisadores de alta
- Recomendação para o Portfolio Manager com sizing sugerido

## REGRAS DE COMPORTAMENTO

- Ceticismo é o padrão. Otimismo precisa ser justificado com dados.
- Veredicto deve ser uma palavra: BARATO, JUSTO ou CARO. Sem "depende".
- Nível de confiança reflete qualidade dos dados disponíveis.
- Se dados forem insuficientes para análise rigorosa, dizer explicitamente
  e reduzir confiança para BAIXO.
- Máximo 300 palavras na versão curta, 700 na versão longa.
```

---

### Script: `run_valuation_reviewer.py`

Crie `/sbwaa/.claude/agents/valuation-reviewer/run_valuation_reviewer.py`:

**O script deve:**

- Receber ticker e versão: `python run_valuation_reviewer.py PETR4 --versao longa`
- Padrão de versão: `curta` se não especificado
- Carregar JSON do DCF do cache (`dcf_{TICKER}_{DATA}.json`)
- Se DCF não existir: rodar `run_model_builder.py` automaticamente primeiro
- Carregar dados Brapi do ticker para múltiplos atuais
- Carregar outputs do Earnings Reviewer e Market Researcher se existirem
- Enviar ao Claude (`claude-sonnet-4-6`, effort `medium`)
- Salvar output markdown em:
  - `/sbwaa/vault/01-ativos/{TICKER}/equity-research-{TICKER}-{DATA}-curta.md`
  - `/sbwaa/vault/01-ativos/{TICKER}/equity-research-{TICKER}-{DATA}-longa.md`
- Gerar o DOCX correspondente com `python-docx`:
  - Cabeçalho com nome do ativo, data, tipo e setor
  - Placeholder para pixel art do agente no canto superior direito (16x16px, comentado)
  - Corpo com o conteúdo formatado do markdown
  - Rodapé: "SBWAA — Confidencial | Gerado em {DATA}"
- Salvar DOCX em `/sbwaa/vault/01-ativos/{TICKER}/`
- Atualizar `tese.md` do ativo com wikilink para o novo equity research
- Exibir no terminal o veredicto e upside

---

## 3. PIPELINE INTEGRADO — ATUALIZAR

Atualizar `/sbwaa/scripts/run_research_pipeline.py` para incluir Fase 3:

```python
"""
Pipeline de research completo — Fases 1, 2 e 3.
Uso: python run_research_pipeline.py TICKER [--versao curta|longa]
"""
# Ordem de execução:
# 1. market_snapshot.py          — dados de mercado
# 2. run_market_researcher.py    — contexto macro
# 3. run_earnings_reviewer.py    — resultados da empresa
# 4. run_model_builder.py        — DCF completo
# 5. run_valuation_reviewer.py   — veredicto de valuation
```

---

## 4. VALIDAÇÃO FINAL

- [ ] `model-builder/SKILL.md` criado com metodologia completa
- [ ] `run_model_builder.py` criado e testado — XLSX gerado com 4 abas
- [ ] JSON de DCF salvo no cache com estrutura correta
- [ ] `valuation-reviewer/SKILL.md` criado com processo de análise completo
- [ ] `run_valuation_reviewer.py` criado e testado — versão curta e longa
- [ ] DOCX curto (1 página) gerado corretamente
- [ ] DOCX longo (2 páginas) gerado corretamente
- [ ] Pipeline integrado atualizado com Fases 1-3
- [ ] Wikilinks presentes em todos os outputs
- [ ] `VERSION.md` atualizado: `investments` → v1.3.0
- [ ] `CHANGELOG.md` com entrada da Fase 3

Ao finalizar, confirme: **"SBWAA Fase 3 concluída — investments v1.3.0"**

---

## OBSERVAÇÕES IMPORTANTES

1. O DCF para FIIs usa metodologia diferente (Gordon direto no DY, sem FCFF) — implementar flag `--tipo fii` no `run_model_builder.py` que adapta a metodologia automaticamente
2. O DCF para ETFs não se aplica — retornar mensagem clara: "DCF não aplicável para ETFs. Use análise de composição e tracking error."
3. O placeholder de pixel art no DOCX deve ser um comentário no código (`# TODO: inserir pixel art do agente`) — a arte será adicionada na Fase 8
4. Versão curta é o padrão do pipeline automático. Versão longa é gerada sob demanda ou via `/tese TICKER --completo`
5. Não criar o Portfolio Manager ainda — isso é Fase 5
