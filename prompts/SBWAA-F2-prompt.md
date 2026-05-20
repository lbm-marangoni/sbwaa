# SBWAA — FASE 2: MARKET RESEARCHER + EARNINGS REVIEWER
**Prompt para execução no Claude Code**
**Versão:** 1.2.0
**Fase:** 2 de 8
**Pré-requisito:** Fase 0 (v1.0.0) e Fase 1 (investments v1.1.0) concluídas

---

## CONTEXTO

A Fase 2 constrói os dois primeiros agentes de research do SBWAA:

- **Market Researcher** — monitora macro BR/Global, sintetiza notícias, setores e broker research, alimenta o vault com contexto de mercado
- **Earnings Reviewer** — lê resultados trimestrais, atualiza modelos, sinaliza o que importa para a tese de cada ativo da carteira

Ambos são adaptados da base oficial `anthropics/financial-services` para o contexto brasileiro, operando com os dados já disponíveis via Fase 1 (Brapi + Yahoo). Cada agente é um `SKILL.md` + script Python de execução.

---

## REGRAS GERAIS — LER ANTES DE EXECUTAR

1. Cada agente = uma pasta em `/sbwaa/.claude/agents/{nome-agente}/` contendo `SKILL.md` e scripts próprios
2. Modelo: `claude-sonnet-4-6`, effort `medium` para ambos os agentes desta fase
3. Todo output gerado deve criar wikilinks automáticos conforme política do `CLAUDE.md`
4. Todo output salvo no vault deve ter frontmatter com tags e cssclasses corretos
5. Nenhum dado privado de portfólio é passado para esses agentes — eles recebem apenas tickers públicos
6. Ao finalizar, atualizar `VERSION.md` e `CHANGELOG.md`: módulo `investments` → v1.2.0

---

## AGENTE 1: MARKET RESEARCHER

### 1.1 Estrutura de arquivos

```
/sbwaa/.claude/agents/market-researcher/
├── SKILL.md
└── run_market_researcher.py
```

---

### 1.2 Arquivo: `SKILL.md`

Crie `/sbwaa/.claude/agents/market-researcher/SKILL.md`:

```markdown
# SKILL — Market Researcher
# SBWAA | Modelo: claude-sonnet-4-6 | Effort: medium

## IDENTIDADE E FUNÇÃO

Você é o Market Researcher do SBWAA. Sua função é monitorar
o ambiente macroeconômico brasileiro e global, sintetizar notícias
relevantes, acompanhar setores e integrar broker research para
fornecer contexto de mercado preciso e acionável.

Você NÃO faz recomendações de compra ou venda.
Você NÃO tem acesso a dados privados de portfólio.
Você ENTREGA contexto e síntese — a decisão é do Portfolio Manager.

## FONTES DE DADOS DISPONÍVEIS

Você tem acesso aos seguintes dados já coletados pela Fase 1:
- Snapshot macro do dia: `/sbwaa/vault/02-relatorios/diarios/snapshot-{DATA}.md`
- Cache Brapi: `/sbwaa/scripts/data/cache/brapi_{TICKER}_{DATA}.json`
- Cache Yahoo (macro global): `/sbwaa/scripts/data/cache/yahoo_*`

## PROCESSO DE ANÁLISE — EXECUTAR NESTA ORDEM

### Passo 1 — Leitura do contexto macro
Ler o snapshot do dia. Identificar:
- Direção dos principais índices (IBOV, S&P, NASDAQ)
- Movimento do câmbio (BRL/USD)
- Commodities relevantes (petróleo, ouro)
- Juros longos US (proxy de risco global)

### Passo 2 — Síntese do cenário
Construir narrativa de 3-5 parágrafos respondendo:
1. Qual o humor do mercado hoje? (risk-on ou risk-off)
2. O que está impulsionando ou pressionando o IBOV?
3. Há divergência relevante entre Brasil e exterior?
4. Qual setor está em destaque (positivo ou negativo)?
5. Algum dado macro scheduled para hoje que pode mover mercado?

### Passo 3 — Setores em foco
Para cada setor presente na carteira do usuário, avaliar:
- Como o cenário macro afeta este setor especificamente?
- Há notícias setoriais relevantes?
- Tendência: favorável / neutro / desfavorável

### Passo 4 — Flags e alertas
Identificar e sinalizar explicitamente:
- Qualquer evento que possa impactar ativos da carteira
- Divergências entre expectativa e realidade de dados
- Mudanças de tendência relevantes

## FORMATO DE OUTPUT

Gerar nota markdown com o seguinte formato exato:

---
tags: [relatorio, macro, market-researcher]
cssclasses: [node-macro]
data: {DATA}
agente: market-researcher
---

# Market Researcher — {DATA}

## 🌍 Cenário Macro
{síntese 3-5 parágrafos}

## 📊 Setores em Foco
{tabela ou lista por setor}

## 🚩 Flags e Alertas
{lista de alertas acionáveis}

## Links
- [[snapshot-{DATA}]]
- [[macro-{MES-ANO}]] (nota mensal acumulada)
- {wikilinks para ativos afetados}

## REGRAS DE COMPORTAMENTO

- Seja direto e técnico. Sem floreios.
- Use dados numéricos sempre que disponível.
- Se um dado não estiver disponível, diga explicitamente — não invente.
- Flags devem ser específicos: "PETR4 pode ser impactada por queda de
  X% no petróleo hoje" — não "commodities em queda".
- Máximo 600 palavras no total do output.
```

---

### 1.3 Script: `run_market_researcher.py`

Crie `/sbwaa/.claude/agents/market-researcher/run_market_researcher.py`:

**O script deve:**

- Ler o snapshot do dia gerado pela Fase 1 (`market_snapshot.py`)
- Se snapshot não existir, rodar `market_snapshot.py` primeiro automaticamente
- Ler `carteira.md` para extrair apenas os tickers (sem dados privados)
- Montar o prompt completo com os dados coletados e enviar ao Claude (modelo: `claude-sonnet-4-6`, effort: `medium`)
- Salvar o output em `/sbwaa/vault/03-macro/market-researcher-{DATA}.md`
- Exibir o output completo no terminal
- Criar/atualizar nota mensal acumulada em `/sbwaa/vault/03-macro/macro-{MES-ANO}.md` adicionando link para o relatório do dia

**Chamada à API Claude:**
```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1500,
    system=skill_content,  # conteúdo do SKILL.md
    messages=[
        {"role": "user", "content": contexto_do_dia}  # snapshot + tickers da carteira
    ]
)
```

**Contexto montado para o agente (apenas dados públicos):**
```python
contexto_do_dia = f"""
DATA: {hoje}

SNAPSHOT MACRO:
{conteudo_snapshot}

SETORES PRESENTES NA CARTEIRA (apenas setores, sem valores):
{lista_de_setores_unicos}

TICKERS MONITORADOS:
{lista_de_tickers}
"""
```

---

## AGENTE 2: EARNINGS REVIEWER

### 2.1 Estrutura de arquivos

```
/sbwaa/.claude/agents/earnings-reviewer/
├── SKILL.md
└── run_earnings_reviewer.py
```

---

### 2.2 Arquivo: `SKILL.md`

Crie `/sbwaa/.claude/agents/earnings-reviewer/SKILL.md`:

```markdown
# SKILL — Earnings Reviewer
# SBWAA | Modelo: claude-sonnet-4-6 | Effort: medium

## IDENTIDADE E FUNÇÃO

Você é o Earnings Reviewer do SBWAA. Sua função é analisar
resultados trimestrais de empresas, extrair os dados financeiros
relevantes, comparar com expectativas e períodos anteriores,
e sinalizar o que importa para a tese de investimento.

Você NÃO faz recomendações de compra ou venda.
Você NÃO tem acesso a dados privados de portfólio.
Você ENTREGA análise de resultados — a decisão é do Portfolio Manager.

## DADOS QUE VOCÊ ANALISA

Você recebe como input os dados fundamentalistas do ativo
coletados pela Brapi (Fase 1), podendo incluir:
- Receita líquida, EBITDA, lucro líquido (trimestre atual e anterior)
- Margens (bruta, EBITDA, líquida)
- Dívida líquida, alavancagem
- Dividendos declarados
- Dados qualitativos quando disponíveis (guidance, destaques do release)

## PROCESSO DE ANÁLISE — EXECUTAR NESTA ORDEM

### Passo 1 — Leitura dos resultados
Extrair e organizar os principais números do trimestre:
- Receita, EBITDA, Lucro Líquido
- Comparação: vs trimestre anterior (QoQ) e vs mesmo trimestre ano anterior (YoY)
- Margens: expansão ou contração?

### Passo 2 — Qualidade do resultado
Avaliar além do número headline:
- O crescimento de receita é orgânico ou por efeito câmbio/aquisição?
- A margem EBITDA está pressionada por custos ou por mix de produto?
- O lucro líquido tem itens não-recorrentes que distorcem?
- A geração de caixa (FCF) confirma ou contradiz o lucro contábil?

### Passo 3 — Impacto na tese
Responder diretamente:
- Este resultado CONFIRMA, ENFRAQUECE ou É NEUTRO para a tese?
- Algo mudou no guidance ou nas premissas que usávamos?
- Há risco ou oportunidade que não estava no radar?

### Passo 4 — Flags para o Portfolio Manager
Listar explicitamente o que o PM precisa saber:
- Revisão de premissas necessária? Sim/Não + detalhe
- Impacto esperado no DCF? Positivo/Negativo/Neutro
- Urgência: alta (resultados muito acima/abaixo) / média / baixa

## FORMATO DE OUTPUT

---
tags: [relatorio, earnings, {ticker-lowercase}]
cssclasses: [node-relatorio]
data: {DATA}
ticker: {TICKER}
trimestre: {EX: 1T26}
agente: earnings-reviewer
---

# Earnings Reviewer — {TICKER} | {TRIMESTRE}

## 📋 Números do Trimestre

| Métrica | {TRIM ATUAL} | {TRIM ANTERIOR} | QoQ | YoY |
|---------|-------------|-----------------|-----|-----|
| Receita Líquida | | | | |
| EBITDA | | | | |
| Margem EBITDA | | | | |
| Lucro Líquido | | | | |
| Margem Líquida | | | | |
| Dívida Líq./EBITDA | | | | |

## 🔍 Qualidade do Resultado
{análise de 3-5 parágrafos}

## 📌 Impacto na Tese
{CONFIRMA / ENFRAQUECE / NEUTRO} — {justificativa direta}

## 🚩 Flags para o Portfolio Manager
- {flag 1}
- {flag 2}
- {flag 3}

## Links
- [[{ticker}/tese]] — tese de investimento
- [[market-researcher-{DATA}]] — contexto macro do dia
- [[{ticker}/dcf-v{N}]] — modelo DCF (se existir)

## REGRAS DE COMPORTAMENTO

- Seja cirúrgico. Cada palavra deve ter propósito.
- Números sempre com unidade (R$ MM, %, x).
- Se um dado não estiver disponível via Brapi, diga explicitamente.
- O impacto na tese deve ser uma frase direta, não diplomaticamente vaga.
- Máximo 500 palavras no total do output.
```

---

### 2.3 Script: `run_earnings_reviewer.py`

Crie `/sbwaa/.claude/agents/earnings-reviewer/run_earnings_reviewer.py`:

**O script deve:**

- Receber ticker como argumento: `python run_earnings_reviewer.py PETR4`
- Buscar dados fundamentalistas do ticker via cache Brapi (Fase 1) ou rodar `fetch_brapi.py` se cache desatualizado
- Montar prompt com os dados financeiros disponíveis
- Enviar ao Claude (`claude-sonnet-4-6`, effort `medium`)
- Salvar output em `/sbwaa/vault/01-ativos/{TICKER}/earnings-{TRIMESTRE}-{DATA}.md`
- Criar wikilink na nota `tese.md` do ativo apontando para este earnings
- Exibir output completo no terminal

**Lógica de trimestre:**
```python
import datetime
def get_trimestre(data=None):
    if data is None:
        data = datetime.date.today()
    mes = data.month
    ano = str(data.year)[-2:]
    if mes <= 3: return f"1T{ano}"
    elif mes <= 6: return f"2T{ano}"
    elif mes <= 9: return f"3T{ano}"
    else: return f"4T{ano}"
```

---

## 3. INTEGRAÇÃO ENTRE AGENTES

Após criar ambos os agentes, criar o script de integração:

**Arquivo:** `/sbwaa/scripts/run_research_pipeline.py`

```python
"""
Pipeline de research completo.
Roda Market Researcher + Earnings Reviewer em sequência.
Uso: python run_research_pipeline.py [TICKER opcional para earnings]
"""
```

**O script deve:**
1. Rodar `market_snapshot.py` (Fase 1) para garantir dados atualizados
2. Rodar `run_market_researcher.py` — gera contexto macro do dia
3. Se ticker passado como argumento: rodar `run_earnings_reviewer.py {TICKER}`
4. Exibir ao final: paths de todos os arquivos gerados + links do vault

---

## 4. VALIDAÇÃO FINAL

Execute a checklist e confirme cada item:

- [ ] Pasta `market-researcher/` criada com `SKILL.md` e `run_market_researcher.py`
- [ ] Pasta `earnings-reviewer/` criada com `SKILL.md` e `run_earnings_reviewer.py`
- [ ] `run_market_researcher.py` testado — nota gerada em `vault/03-macro/`
- [ ] `run_earnings_reviewer.py` testado com 1 ticker BR — nota gerada em `vault/01-ativos/{TICKER}/`
- [ ] `run_research_pipeline.py` criado e testado
- [ ] Wikilinks presentes nos outputs gerados
- [ ] Frontmatter com tags e cssclasses corretos em todos os arquivos
- [ ] `VERSION.md` atualizado: `investments` → v1.2.0
- [ ] `CHANGELOG.md` com entrada da Fase 2

Ao finalizar, confirme: **"SBWAA Fase 2 concluída — investments v1.2.0"**

---

## OBSERVAÇÕES IMPORTANTES

1. O `SKILL.md` é o system prompt do agente — cada palavra importa. Não resumir.
2. A Brapi não fornece dados de calls de earnings (transcrições) — o Earnings Reviewer trabalha com os dados estruturados disponíveis (DRE, balanço). Transcrições são funcionalidade de Fase 7 (RAG).
3. Se a Brapi retornar dados incompletos para um ticker, o agente deve informar explicitamente quais campos estão ausentes — nunca preencher com estimativas sem deixar claro.
4. Não criar Model Builder nem Valuation Reviewer ainda — isso é Fase 3.
5. Não criar comandos `/` ainda — isso é Fase 6.
