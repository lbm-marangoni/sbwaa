# SBWAA — Workflow Operacional

> Rotinas de uso do sistema por cadência e por fluxo oportunístico.
> Para referência de comandos e sintaxe: [`GUIA-COMANDOS.md`](GUIA-COMANDOS.md)

**Versão: v2.12.0**

---

## Filosofia operacional

O SBWAA não é para acompanhar cotação minuto a minuto. É para tomar **menos decisões, mas melhores** — com dados estruturados, análise de risco e contexto macro sempre atualizados.

Cada cadência tem um objetivo diferente:
- **Diária** → saber se o ambiente mudou e se há algo urgente
- **Semanal** → controle de performance e risco
- **Mensal** → decisões de portfólio com visão completa
- **Trimestral** → absorver resultados e recalibrar
- **Anual** → revisar a estratégia e o IPS

Os fluxos oportunísticos não têm calendário — são gatilhados por eventos.

---

## Conceitos fundamentais

### Carteira vs Watchlist

| Conceito | Definição | Localização |
|----------|-----------|-------------|
| **Carteira** | Ativos que você **possui** — posição ativa com quantidade e custo médio | `vault/00-portfolio/carteira.md` |
| **Watchlist** | Ativos **analisados mas não comprados** — tese existe, aguardando gatilho ou timing | `vault/01-ativos/{TICKER}/` (sem entrada na carteira) |

Um ativo entra na watchlist quando você rodou `/tese` ou `/analisar` e o PM emitiu AGUARDAR — ou COMPRAR mas você ainda não executou. Sai da watchlist quando entra na carteira ou quando o veredicto vira EVITAR.

### Quando usar cada comando de análise

| Situação | Comando correto | Pré-requisito |
|----------|----------------|---------------|
| Ativo **novo** — nunca analisou | `/tese TICKER` | Nenhum |
| Tese favorável, quer análise completa | `/analisar TICKER` | Nenhum |
| Ativo na **watchlist** com análise < 60 dias | `/pm TICKER` | Análise em `vault/01-ativos/TICKER/` |
| Ativo na **carteira** com análise < 60 dias | `/pm TICKER` | Análise em `vault/01-ativos/TICKER/` |
| Qualquer ativo com análise **≥ 60 dias** | `/analisar TICKER` | Cache stale — /pm usaria dados desatualizados |
| **Capital novo — distribuir entre múltiplos ativos** | `/pm` ou `/pm 700` | ≥ 1 ativo com análise em `vault/01-ativos/` |
| Comparar dois candidatos | `/comparar A B` | Nenhum |
| Sugestão baseada no macro do dia | `/investimento-do-dia` | `/morning-call` rodou |

> **Regra dos 60 dias:** `/pm` pressupõe análise recente no vault. Com análise > 60 dias, os dados de valuation, earnings e risco podem estar desatualizados — use `/analisar` para recalibrar tudo antes de qualquer decisão.

---

## Calendário de referência rápida

| Comando | Diário | Semanal | Mensal | Trimestral | Anual |
|---------|:------:|:-------:|:------:|:----------:|:-----:|
| `/morning-call` | ✅ | | | | |
| `/snapshot` | ✅ | | | | |
| `/knowledge --coletar-rss` | ✅ | | | | |
| `/carteira` | ○ | ✅ | ✅ | ✅ | ✅ |
| `/dividendos` | | ✅ | ✅ | | |
| `/watchlist --rever` | | ✅ | ✅ | | |
| `/risco-carteira` | | ✅ | ✅ | ✅ | ✅ |
| `/relatorio-semanal` | | ✅ | | | |
| `/rebalancear` | | ✅ | ✅ | ✅ | ✅ |
| `/stress-test` | | | ✅ | ✅ | ✅ |
| `/simulacao` | | | ✅ | | ✅ |
| `/otimizar-expansao` | | | ✅ | ✅ | ✅ |
| `/watchlist` | | | ✅ | ✅ | ✅ |
| `/relatorio-mensal` | | | ✅ | | ✅ |
| `/revisar-carteira` | | | ✅ | ✅ | ✅ |
| `/earnings TICKER` | | | | ✅ | |
| `/ips --editar` | | | | | ✅ |

✅ = obrigatório | ○ = opcional se quiser ver P&L do dia

---

## Cadência Diária

### Pré-abertura — O que você precisa saber antes de olhar os preços (5–15 min)

O objetivo não é ver quanto subiu ou desceu — é entender se o ambiente mudou e se há algo que exige ação hoje. O modelo de camadas evita escalar para análise pesada sem necessidade.

---

**Camada 1 — Briefing (obrigatório, 5 min)**

```
/morning-call
```

O que olhar:
- **Alertas ativos:** ativo da carteira disparou alerta de queda/alta ou correlação?
- **Macro adverso:** juros, câmbio, commodity afetando seu setor principal?
- **Eventos do dia:** resultado, COPOM, Fed, inflação?
- **Oportunidade setorial:** macro favorece uma classe de ativo hoje?

Se nenhum alerta e macro estável → encerrar aqui. Camadas 2 e 3 só se necessário.

---

**Camada 2 — Triagem por ativo (se Camada 1 identificou algo, 5 min)**

```
Alerta em TICKER específico?
  → Ativo na carteira/watchlist + análise < 60 dias → /pm TICKER
  → Análise ≥ 60 dias                               → /tese TICKER  (mais rápido que /analisar)
  → Ativo nunca analisado                           → /tese TICKER

Macro sugere oportunidade setorial, sem ativo claro?
  → /investimento-do-dia [categoria]    (ex: /investimento-do-dia fii)
```

Se /tese ou /pm retornar EVITAR ou AGUARDAR sem urgência → encerrar aqui.

---

**Camada 3 — Análise completa (se Camada 2 confirmar oportunidade real)**

```
/tese retornou COMPRAR ou tese forte?   → /analisar TICKER
/pm retornou AUMENTAR com margem clara? → avaliar /rebalancear
Macro mudou estruturalmente?            → /mundo-economico → /revisar-carteira
```

---

**2. Snapshot diário (obrigatório, 1 min)**

```powershell
! python sbwaa.py /snapshot
```

Salva o estado do dia em `vault/02-relatorios/diarios/`. Sem ação necessária — é dado histórico para relatórios semanais e mensais. Rodar mesmo em dias sem evento.

---

### Pós-fechamento — Alimentar a base (3 min, opcional)

```powershell
! python sbwaa.py /knowledge --coletar-rss
```

Indexa notícias do dia (Valor Econômico, InfoMoney, BCB, Bloomberg, Reuters). O próximo `/morning-call` ou `/analisar` encontra contexto mais atualizado na RAG.

---

## Cadência Semanal

### Sexta (fechamento) ou domingo (revisão) — 20–30 min

Objetivo: verificar se a semana mudou o posicionamento e identificar o que precisa de atenção na semana seguinte. Só escalar para análise por ativo se as métricas indicarem necessidade.

---

**Camada 1 — Dados e métricas (obrigatório, 5 min)**

```powershell
! python sbwaa.py /carteira         # P&L, concentração, dividendos recebidos
! python sbwaa.py /risco-carteira   # Sharpe, VaR, circuit breakers
! python sbwaa.py /dividendos       # ex-dates nos próximos 15 dias
```

O que olhar:
- Circuit breaker disparado? → ir direto para Fluxo 3 (Circuit Breaker)
- Algum ativo chegou perto do limite de concentração (> 18%)?
- Ex-date relevante nos próximos 15 dias? → não vender sem verificar Yield on Cost
- Sharpe caindo há 3 semanas? → anotar para /revisar-carteira na sessão

Se métricas OK e sem anomalia → Camada 2 suficiente, pular Camada 3.

---

**Camada 2 — Relatório e ativos defasados (10 min)**

```
/relatorio-semanal
```

P&L da semana, Sharpe, drawdown, outlook. Ler antes de avançar — o relatório mostra padrões que as métricas brutas não mostram.

```powershell
! python sbwaa.py /watchlist --rever
```

Lista ativos com análise > 45 dias. Para cada um:
```
Houve evento relevante desde a última análise?
  → Sim + análise < 60 dias  → /pm TICKER           (Camada 3)
  → Sim + análise ≥ 60 dias  → /analisar TICKER     (Camada 3)
  → Não + em carteira < 60d  → /pm TICKER           (Camada 3, baixa prioridade)
  → Não + em carteira ≥ 60d  → /analisar TICKER     (Camada 3)
  → Não + só na watchlist    → aguardar, não escalar
```

Se nenhum ativo sinalizado → encerrar aqui.

---

**Camada 3 — Ação nos ativos sinalizados + rebalanceamento (se necessário)**

Para cada ativo sinalizado na Camada 2:
```
/pm TICKER          (análise < 60d)
/analisar TICKER    (análise ≥ 60d ou evento relevante)
```

Após rodar o PM nos sinalizados:
```
/rebalancear
```
```
Desvio vs IPS > 5% numa classe?
  → Sim: plano concreto de ajuste para a semana
  → Não: aguardar

Candidato MELHORA na watchlist com análise recente?
  → /pm TICKER para confirmar veredicto antes de entrar
  → Análise ≥ 60d: agendar /analisar TICKER no próximo mês
```

---

## Cadência Mensal

### Primeiro fim de semana do mês — 60–90 min

Objetivo: decisões de portfólio com visão completa. O modelo de camadas garante que análise por ativo só ocorre quando o relatório e a revisão identificam necessidade real.

---

**Camada 1 — Dados completos (15 min, obrigatório)**

Rodar tudo antes de abrir qualquer comando de IA:

```powershell
! python sbwaa.py /carteira           # P&L, posições, proventos
! python sbwaa.py /dividendos         # calendário de proventos
! python sbwaa.py /risco-carteira     # Sharpe, VaR, circuit breakers, fronteira
! python sbwaa.py /stress-test        # impacto nos cenários históricos extremos
! python sbwaa.py /simulacao          # Monte Carlo 10 anos com parâmetros atuais
! python sbwaa.py /otimizar-expansao  # fronteira eficiente expandida com watchlist
! python sbwaa.py /watchlist          # lista completa: carteira + analisados
```

Sinaleiros que determinam o que escalar:
- Circuit breaker disparado → Fluxo 3 imediatamente, antes de continuar
- Sharpe do mês abaixo de 0.3 → priorizar /revisar-carteira (Camada 2)
- `/otimizar-expansao` mostra candidato MELHORA → anotar para Camada 3
- Stress test: impacto pior cenário > 20%? → revisar concentração (Camada 2)

---

**Camada 2 — Relatório e revisão do PM (20–30 min)**

```
/relatorio-mensal
```

Performance com benchmarks (IBOV, CDI). Ler antes de qualquer decisão — o relatório mostra padrões que a visão semanal não captura.

```
/revisar-carteira
```

PM recebe tudo (carteira, IPS, quant, risk, análises, cache de expansão) e emite MANTER / AUMENTAR / REDUZIR / SAIR por posição.

O que olhar no output:
- REDUZIR ou SAIR em algum ativo? → Fluxo 4 (Saída)
- AUMENTAR em algum ativo? → verificar banda IPS, anotar para Camada 3
- Candidatos MELHORA na watchlist com análise disponível? → Camada 3
- Violação iminente de IPS? → Camada 3 prioritária

Se `/revisar-carteira` retornar tudo MANTER e sem candidatos → ir direto para /rebalancear e encerrar.

---

**Camada 3 — Ação por ativo + plano de ajuste (conforme sinalizado na Camada 2)**

Para cada ativo sinalizado pelo `/revisar-carteira`:
```
Análise < 60 dias?  → /pm TICKER
Análise ≥ 60 dias?  → /analisar TICKER    (pipeline completo)

Candidato MELHORA na watchlist com análise recente?
  → /comparar TICKER TICKER_SIMILAR    (avaliar vs posição existente)
  → /pm TICKER                         (veredicto final antes de entrar)

Candidato MELHORA sem análise ou análise > 60d?
  → /analisar TICKER                   (não entrar sem análise atualizada)
```

```
/rebalancear
```

Consolida: desvio vs IPS + fronteira eficiente + candidatos + decisões da Camada 3. Gera plano concreto (o que comprar, o que reduzir, em que ordem).

---

## Cadência Trimestral — Época de resultados

### Janeiro, abril, julho, outubro — 2–3h distribuídas ao longo de 2 semanas

Objetivo: absorver os resultados trimestrais e recalibrar o portfólio. A temporada é o momento em que teses se confirmam ou quebram — o modelo de camadas evita recalibrar tudo de uma vez sem saber o que realmente mudou.

---

**Camada 1 — Coleta e triagem dos resultados (ao longo da semana do resultado)**

Para cada ativo em carteira ou watchlist com resultado disponível:

```
/earnings TICKER
```

O que olhar: receita, EBITDA, lucro vs guidance, dívida, dividendo — acima, dentro ou abaixo do esperado?

Sinaleiro por resultado:
```
Surpresa positiva > 10% (resultado bem acima)?  → marcar para Camada 2: /analisar
Resultado dentro do esperado (< 10% desvio)?    → marcar para Camada 2: /pm
Surpresa negativa > 10% (resultado abaixo)?     → marcar para Camada 2: /analisar
Guidance cortado ou dividendo suspenso?         → Camada 2: /analisar (obrigatório)
```

Para candidatos da watchlist: mesmo fluxo — `/earnings TICKER` primeiro para decidir se vale escalar.

---

**Camada 2 — Decisão por ativo (conforme sinalizado na Camada 1)**

```
Surpresa positiva ou dentro do esperado + análise < 60 dias?
  → /pm TICKER    (veredicto atualizado — tese se mantém? sizing alvo continua?)

Surpresa positiva + quer recalibrar DCF?
  → /analisar TICKER    (pipeline completo com earnings novos)

Surpresa negativa > 10% ou guidance cortado?
  → /analisar TICKER    (revisão completa — tese pode ter quebrado)
  → Se PM emitir EVITAR ou SAIR: ir para Fluxo 4

Candidato da watchlist com resultado interessante?
  → /tese TICKER    (triagem rápida antes de comprometer pipeline)
  → Se tese favorável: /analisar TICKER
```

---

**Camada 3 — Recalibração do portfólio (após todos os earnings coletados)**

```powershell
! python sbwaa.py /risco-carteira     # risco com novos fundamentos incorporados
! python sbwaa.py /stress-test        # beta dos ativos mudou com os resultados?
! python sbwaa.py /otimizar-expansao  # fronteira eficiente com watchlist atualizada
```

```
/revisar-carteira    # PM com todos os earnings já no vault
/rebalancear         # plano de ajuste pós-temporada
```

---

**Bônus — Pesquisa de expansão (temporada é o melhor momento)**

A temporada de resultados é quando o contexto fundamentalista está no pico de informação. Bom momento para identificar candidatos novos — mas só após concluir a Camada 3.

```
/investimento-do-dia    # sugestão baseada no IPS + macro + resultados recentes
/tese TICKER            # candidatos descobertos na temporada
/comparar A B           # comparar candidato vs posição existente
```

---

## Cadência Anual

### Dezembro — meio período

Objetivo: revisar se a estratégia ainda faz sentido, recalibrar o IPS e posicionar o portfólio para o ano seguinte.

---

**Bloco 1 — Revisão do IPS**

```powershell
! python sbwaa.py /ips --editar
```

Perguntas a responder antes de editar:
- Meu horizonte de investimento mudou?
- Minha tolerância a risco (VaR, drawdown) ainda faz sentido com o patrimônio atual?
- As alocações alvo (% por classe) ainda refletem minha estratégia?
- O limite de concentração por ativo (20%) está adequado?

Após editar o IPS, rodar `/rebalancear` imediatamente — qualquer mudança nas bandas vai gerar novos desvios.

---

**Bloco 2 — Dados e relatório anual**

```powershell
! python sbwaa.py /carteira
! python sbwaa.py /dividendos
! python sbwaa.py /stress-test          # impacto dos cenários históricos com o portfólio atual
! python sbwaa.py /risco-carteira       # métricas do ano inteiro
! python sbwaa.py /otimizar-expansao    # fronteira com watchlist — revisão anual
! python sbwaa.py /watchlist            # o que analisei esse ano?
```

```
/relatorio-mensal    # dezembro funciona como relatório anual — benchmark 12m, CDI vs IBOV
```

---

**Bloco 3 — Decisões de portfólio**

```
/revisar-carteira    # PM com visão anual — manter, aumentar, reduzir ou sair
/rebalancear         # plano de ajuste para o início do próximo ano
```

Para cada ativo em watchlist há mais de 6 meses sem entrar em carteira:
```
Veredicto ainda COMPRAR mas não entrou?
  → /pm TICKER    — rever o motivo: preço, momento, ou IPS?
  → Decisão: manter na watchlist com critério claro, ou descartar?

Veredicto virou AGUARDAR ou EVITAR?
  → Remover da watchlist ativa — mover para vault/01-ativos/TICKER/ como "descartado"
```

---

## Fluxos Oportunísticos

### Fluxo 1 — Ativo novo descoberto

**Gatilho:** você ouviu, leu ou alguém mencionou um ativo que não conhecia.

O risco é gastar 30min de pipeline em algo que o PM descarta em 5. Fazer em camadas — só escalando quando a camada anterior confirmar.

---

**Camada 1 — Triagem rápida (5 min)**

```
/investimento-do-dia    # o sistema já está sugerindo algo parecido?
/tese TICKER            # tese rápida: Research + DCF + PM (~15 min)
```

```
PM emitiu COMPRAR?      → continuar para Camada 2
PM emitiu AGUARDAR?     → watchlist com trigger definido, encerrar aqui
PM emitiu EVITAR?       → registrar motivo no vault, não escalar
```

---

**Camada 2 — Comparação (10 min)**

```
/comparar TICKER TICKER_SIMILAR    # vs ativo já em carteira ou watchlist
```

O ativo novo é melhor, pior ou complementar ao que já existe? Se pior ou redundante → encerrar aqui, não vale o pipeline completo.

---

**Camada 3 — Análise completa (se Camada 1 e 2 forem favoráveis)**

```
/analisar TICKER    # pipeline completo: 8 agentes, 10 etapas
```

```
PM confirma COMPRAR?
  → Verificar IPS: a classe tem espaço? Concentração OK?
  → /otimizar-expansao: o ativo melhora a fronteira eficiente?
  → Se tudo OK: python sbwaa.py /adicionar --ticker X ...

PM volta para AGUARDAR?
  → Watchlist com análise completa — aparece em /watchlist e /revisar-carteira
```

---

### Fluxo 2 — Evento relevante

#### Resultado trimestral (earnings)

**Camada 1 — Coletar e classificar**
```
/earnings TICKER
```
Surpreendeu (> 10% desvio)? Guidance cortado? → escalar para Camada 2.
Dentro do esperado? → /pm TICKER direto (Camada 2 leve).

**Camada 2 — Decisão por ativo**
```
Surpresa ou guidance cortado?  → /analisar TICKER
Dentro do esperado, < 60d?     → /pm TICKER
Se PM emitir SAIR/EVITAR       → Fluxo 4
```

**Camada 3 — Impacto no portfólio (só se Camada 2 mudar veredicto)**
```
/rebalancear    # sizing alvo mudou? ajustar posição
```

---

#### COPOM, Fed ou mudança macro relevante

**Camada 1 — Entender o choque**
```
/mundo-economico
/morning-call
```
O choque é passageiro ou estrutural? Afeta diretamente ativos em carteira? Se impacto restrito → encerrar aqui.

**Camada 2 — Quantificar impacto**
```powershell
! python sbwaa.py /stress-test custom -15    # choque estimado no portfólio
```
```
Juros subiram além do esperado?
  → /pm para FIIs em carteira (taxa de desconto muda o valuation)
  → Checar se RF/TD está abaixo do mínimo IPS → /rebalancear

Câmbio disparou (BRL fraco)?
  → ETFs internacionais: checar concentração (valorizam em BRL)
  → /pm para exportadoras em carteira (PETR4, VALE3)

Risco político/fiscal aumentou?
  → /stress-test custom -20
  → /pm para ativos de alta correlação com risco Brasil
```

**Camada 3 — Revisão completa (se choque estrutural)**
```
/revisar-carteira    # PM reposiciona com novo contexto macro
/rebalancear         # ajuste defensivo ou oportunista
```

---

#### Queda expressiva num ativo (> 8% em 1 dia)

**Camada 1 — Diagnóstico rápido (2 min)**
```powershell
! python sbwaa.py /risco-carteira    # impacto no VaR e concentração
```
Qual é a causa aparente? Notícia fundamentalista, macro, resultado, contágio?

**Camada 2 — Triagem por ativo**
```
Ativo em carteira/watchlist + análise < 60d?  → /pm TICKER
Análise ≥ 60d ou ativo novo?                  → /tese TICKER
```
Se /pm ou /tese retornar MANTER → encerrar. A queda foi ruído.

**Camada 3 — Revisão completa (se Camada 2 indicar problema real)**
```
Causa fundamentalista grave (fraude, perda de contrato, downgrade)?
  → /analisar TICKER    (urgente — independente da idade da análise)

Resultado trimestral muito abaixo?
  → /earnings TICKER → /analisar TICKER

PM emite SAIR?  → Fluxo 4
```

---

#### Crise sistêmica ou queda generalizada (mercado > 5% em 1 dia)

**Camada 1 — Entender o cenário**
```powershell
! python sbwaa.py /stress-test       # todos os cenários históricos de uma vez
! python sbwaa.py /risco-carteira    # VaR atual
```
```
/mundo-economico    # o que está acontecendo
```
VaR dentro do limite? Drawdown OK? → se sim, não agir ainda. Monitorar.

**Camada 2 — Verificar posições expostas**
```
/pm TICKER    # para cada ativo com maior contribuição ao risco
```
PM confirma MANTER? → aguardar. PM emite REDUZIR ou SAIR? → Camada 3.

**Camada 3 — Ação estruturada (não agir no calor sem isso)**
```
/revisar-carteira    # PM em modo de crise: o que sai, o que fica, o que reduz
/rebalancear         # plano concreto de redução de risco ou reposicionamento
```

Regras em crise:
- Não vender tudo sem passar pelo PM — o sistema existe para isso
- Não comprar o ativo que mais caiu sem /analisar TICKER novo
- Se VaR violou o IPS: redução de risco é obrigatória antes de qualquer compra

---

### Fluxo 3 — Circuit breaker / drawdown

**Gatilho:** `/risco-carteira` mostra algum circuit breaker disparado.

---

#### 🚨 VaR 95% > 2% (limite do IPS violado)

**Camada 1 — Quantificar**
```powershell
! python sbwaa.py /stress-test    # exposição nos cenários extremos
```
Qual ativo tem maior contribuição ao risco? (`contribuicao_risco` no output)

**Camada 2 — Triagem por ativo**
```
/pm TICKER    # para o ativo de maior contribuição — ainda é válido manter?
```
PM confirma MANTER? → reduzir parcialmente mesmo assim (VaR viola IPS).
PM emite REDUZIR/SAIR? → executar.

**Camada 3 — Execução e confirmação**
```powershell
! python sbwaa.py /vender --ticker X --quantidade Y
! python sbwaa.py /risco-carteira    # confirmar VaR voltou abaixo de 2%
```
```
/rebalancear    # onde alocar o capital liberado
```

---

#### ⚠️ Drawdown > 12% (aproximando do limite de 18%)

**Camada 1 — Contexto**
```
/mundo-economico    # setorial, macro ou idiossincrático?
```

**Camada 2 — Posicionamento defensivo**
```
/revisar-carteira    # PM em modo defensivo: o que reduz, o que fica
```

Regra enquanto drawdown > 12%: nenhum aporte em renda variável. Capital novo vai para TD/RF até drawdown < 10%.

---

#### ⚠️ Concentração > 18% num ativo (limite: 20%)

**Camada 1 — Verificar se ainda faz sentido manter**
```
/pm TICKER    # atualizar veredicto com concentração elevada
```

**Camada 2 — Se PM não emitir SAIR**
- Congelar aportes neste ativo até concentração < 15%
- Próximo aporte: classe/ativo com maior desvio negativo vs IPS

---

#### ⚠️ Correlação média > 0.75

Sinal de que o portfólio está virando um só ativo — quando um cai, todos caem.

**Camada 1 — Identificar candidatos descorrelacionados**
```powershell
! python sbwaa.py /otimizar-expansao    # candidatos da watchlist com correlação < 0.5
```

**Camada 2 — Avaliar entrada**
```
Candidato MELHORA com análise < 60d?  → /pm TICKER
Candidato sem análise ou > 60d?       → /tese TICKER → /analisar se justificar
```

```
/rebalancear    # plano de diversificação com fronteira eficiente
```

---

### Fluxo 4 — Saída de posição

**Gatilho:** `/revisar-carteira` emitiu SAIR, evento fundamentalista grave ou necessidade de liquidez.

---

**Camada 1 — Confirmação (nunca vender sem isso)**

```
/pm TICKER    # ainda é SAIR? tese quebrou ou é timing?
```

O que verificar antes de executar:
- Há ex-date de dividendo nos próximos 15 dias? Se sim, pode valer aguardar
- P&L realizado: impacto relevante no total do portfólio?
- A causa é fundamentalista (quebra de tese) ou técnica (preço, timing)?

Se /pm confirmar MANTER ou REDUZIR parcialmente → ajustar plano antes de executar.

---

**Camada 2 — Execução**

```powershell
! python sbwaa.py /vender --ticker TICKER --quantidade X --preco Y
! python sbwaa.py /carteira          # confirmar saída e novo P&L total
! python sbwaa.py /risco-carteira    # como mudou o risco?
```

---

**Camada 3 — Realocação do capital (não alocar no mesmo dia se > 5% do portfólio)**

```
/rebalancear    # onde o capital faz mais sentido agora
```

```
Capital > 5% do portfólio?
  → Aguardar 24h — decidir com o sistema, não no calor da saída
  → /otimizar-expansao    (candidato da watchlist para absorver?)
  → /rebalancear          (classe com maior desvio negativo vs IPS)

Capital < 5%?
  → Direcionar para a classe mais distante do alvo IPS
  → Ou TD/RF curto se não houver oportunidade clara no momento
```

---

### Fluxo 6 — Aporte de capital novo

**Gatilho:** você tem um valor para investir e não sabe exatamente o quê comprar ou como distribuir.

---

**Camada 1 — Verificar candidatos disponíveis**

```powershell
! python sbwaa.py /watchlist    # ver ativos com veredicto COMPRAR / AUMENTAR e frescor
```

Identifique quantos ativos têm análise suficiente (✅ ≤ 45d, idealmente via `/analisar`).

---

**Camada 2 — PM Modo Aporte**

```
/pm        → PM faz as perguntas (valor, classe, nº de ativos, restrições)
/pm 700    → atalho com valor pré-definido
```

O PM:
1. Escaneia `vault/01-ativos/` + carteira → filtra COMPRAR/AUMENTAR
2. Ranqueia por: gap de IPS da classe, frescor, presença de /analisar
3. Distribui o capital entre os N ativos selecionados
4. Valida a distribuição e emite justificativa por ativo

**Se faltar análise nos candidatos:**

```
PM informa quais ativos estão sem análise suficiente.
  → [S] PM roda /analisar automaticamente e retoma o fluxo
  → [N] Continua com os candidatos disponíveis
```

---

**Camada 3 — Ajuste e confirmação**

Após receber a sugestão do PM:
- Campo livre: "sem XPML11", "quero mais em ações", "e se eu colocasse 1200?"
- PM recalcula e apresenta nova tabela sem reiniciar o fluxo
- Ao encerrar: decisão salva em `vault/00-portfolio/pm-aporte-YYYY-MM-DD.md`

---

**Diferença vs `/rebalancear`:**

| Aspecto | `/pm` (modo aporte) | `/rebalancear` |
|---------|---------------------|----------------|
| Dinheiro | Capital novo entrando | Redistribuição do existente |
| Vendas | Não — só compras | Pode envolver vendas |
| Gatilho | "Tenho R$X para investir" | "Carteira desviou do IPS" |

---

### Fluxo 5 — Novo documento / pesquisa para indexar

**Gatilho:** você tem um PDF de resultado, relatório de corretora, tese de casa de análise ou paper.

---

**Camada 1 — Indexar**

```powershell
! python sbwaa.py /knowledge --adicionar "C:\caminho\relatorio.pdf"
```

Após indexar, o documento fica disponível para todos os agentes via RAG (`/analisar`, `/tese`, `/pm`, `/revisar-carteira`). Não é necessário fazer mais nada — o sistema recupera os trechos relevantes automaticamente.

---

**Camada 2 — Verificar se o conteúdo muda alguma análise ativa**

```powershell
! python sbwaa.py /knowledge --buscar "tema do documento"    # o que foi indexado?
```

```
O documento traz dado novo sobre um ativo em carteira ou watchlist?
  → Sim + análise < 60d: /pm TICKER    (PM vai encontrar o novo contexto na RAG)
  → Sim + análise ≥ 60d: /analisar TICKER    (recalibrar com o novo conteúdo)
  → Não: indexação suficiente, nenhuma ação adicional
```

---

Casos de uso comuns:
```powershell
! python sbwaa.py /knowledge --adicionar "C:\downloads\petr4-3t24.pdf"
! python sbwaa.py /knowledge --adicionar "C:\downloads\vale3-tese-xp.pdf"
! python sbwaa.py /knowledge --adicionar "C:\downloads\resultados-3t24\"  # pasta inteira
! python sbwaa.py /knowledge --status
! python sbwaa.py /knowledge --listar
```

---

## Tabela de decisão — Quando usar cada comando de análise

| Situação | Comando | Pré-requisito |
|----------|---------|---------------|
| Ativo novo — nunca analisou | `/tese TICKER` | Nenhum |
| Tese favorável, quer aprofundar | `/analisar TICKER` | Nenhum |
| Carteira/watchlist, análise **< 60 dias** | `/pm TICKER` | Análise em vault/01-ativos/ |
| Carteira/watchlist, análise **≥ 60 dias** | `/analisar TICKER` | — dados stale |
| Resultado trimestral dentro do esperado | `/earnings TICKER` → `/pm TICKER` | Análise < 60d |
| Resultado muito fora do esperado | `/earnings TICKER` → `/analisar TICKER` | — |
| Ativo caiu muito — ativo novo | `/tese TICKER` | Nenhum |
| Ativo caiu muito — já na carteira/watchlist | `/pm TICKER` (se < 60d) ou `/analisar TICKER` | — |
| Morning call sugere setor, não ativo | `/investimento-do-dia [categoria]` | morning-call rodou |
| Quer comparar dois ativos | `/comparar A B` | Nenhum |
| Macro mudou — impacto na carteira | `/mundo-economico` → `/revisar-carteira` | — |
| Época de resultados (trimestral) | `/earnings` por ativo → `/revisar-carteira` | — |
| Fim de mês — visão completa | `/risco-carteira` → `/revisar-carteira` → `/rebalancear` | — |
| VaR violado | `/stress-test` → `/revisar-carteira` → `/rebalancear` | — |
| Candidatos da watchlist | `/otimizar-expansao` | quant cache do dia |
| **Capital novo — não sabe onde alocar** | `/pm` ou `/pm 700` | ≥ 1 ativo analisado em vault/01-ativos/ |

---

## Outputs visuais — Relatórios .md no Vault

Além do output no terminal, os comandos abaixo salvam relatórios formatados em Obsidian:

| Comando | Arquivo gerado | Modo |
|---------|---------------|------|
| `/carteira` | `vault/00-portfolio/carteira.md` — seções `📊 Alocação por Classe` e `📈 Posições — Detalhes Visuais` appendadas automaticamente | Sobreescrito a cada `/carteira` |
| `/dividendos` | `vault/02-relatorios/dividendos.md` | Sobreescrito — estado atual |
| `/risco-carteira` | `vault/02-relatorios/risco-carteira.md` | Sobreescrito — estado atual |
| `/stress-test` | `vault/02-relatorios/stress-test.md` | Sobreescrito — estado atual |
| `/watchlist` | `vault/02-relatorios/watchlist-YYYY-MM-DD.md` | **Datado** — mantém histórico de snapshots |

**Por que sobreescrever vs datar:**
- Comandos de **estado atual** (`/risco-carteira`, `/stress-test`, `/dividendos`): sobreescrito — o arquivo sempre reflete o momento mais recente, sem acúmulo de arquivos.
- `/watchlist` é **datado** porque o universo de ativos analisados muda com tempo — o histórico tem valor para ver a evolução da watchlist.
- Relatórios de período (`/relatorio-semanal`, `/relatorio-mensal`) já eram datados e continuam assim.

**Formatação Obsidian usada:**
- `> [!info]` — informação contextual
- `> [!warning]` — desvio do IPS (gap 5–10%)
- `> [!danger]` — violação crítica (gap > 10%, concentração > 20%)
- `> [!tip]` — circuit breakers OK, status positivo
- Barras `█░` (20 chars) — alocação visual por classe e por ativo

---

## Dicas operacionais

**Usar o `!` no chat do Claude Code**

Qualquer comando local pode ser executado diretamente no chat sem sair da conversa:

```
! python sbwaa.py /carteira
! python sbwaa.py /risco-carteira
! python sbwaa.py /otimizar-expansao
```

O output aparece na conversa. Útil para combinar um comando local com um slash command de IA na mesma sessão — por exemplo: rodar `/risco-carteira`, ver o output, e em seguida digitar `/revisar-carteira` com o PM já contextualizando o risco visto.

---

**Sequência típica numa sessão produtiva**

```
! python sbwaa.py /carteira               # contexto atual
! python sbwaa.py /risco-carteira         # onde estou no risco
/revisar-carteira                         # PM com visão completa
/rebalancear                              # plano de ação
```

---

**Cache e TTL**

Os agentes de cálculo (Quant, Risk) salvam cache JSON com data no nome. Quando `/revisar-carteira` e `/rebalancear` pedem para rodar `run_quant.py` e `run_risk_engineer.py`, é porque o cache de hoje ainda não existe. Se já rodou o `/risco-carteira` mais cedo no dia, o cache está lá — não precisa rodar de novo.

---

**Ordem importa**

```
/otimizar-expansao precisa que /risco-carteira (ou run_quant.py) já rodou
/revisar-carteira  lê os caches de quant, risk e otimizacao — rodar os três antes
/rebalancear       mesma coisa
/relatorio-mensal  lê snapshots diários — quanto mais /snapshot você rodou, melhor
```
