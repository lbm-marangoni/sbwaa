# SBWAA — Workflow Operacional

> Rotinas de uso do sistema por cadência e por fluxo oportunístico.
> Para referência de comandos e sintaxe: [`GUIA-COMANDOS.md`](GUIA-COMANDOS.md)

**Versão: v2.8.0**

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
| `/otimizar-expansao` | | | ✅ | ✅ | ✅ |
| `/watchlist` | | | ✅ | ✅ | ✅ |
| `/relatorio-mensal` | | | ✅ | | ✅ |
| `/revisar-carteira` | | | ✅ | ✅ | ✅ |
| `/earnings TICKER` | | | | ✅ | |
| `/ips --editar` | | | | | ✅ |

✅ = obrigatório | ○ = opcional se quiser ver P&L do dia

---

## Cadência Diária

### Pré-abertura — O que você precisa saber antes de olhar os preços (5–10 min)

O objetivo não é ver quanto subiu ou desceu — é entender se o ambiente mudou desde ontem e se há algo que exige ação hoje.

---

**1. Briefing completo**

```
/morning-call
```

O que olhar no output:
- **Alertas ativos:** algum ativo da carteira disparou alerta de queda/alta ou correlação?
- **Macro adverso:** juros, câmbio, commodity afetando seu setor principal?
- **Eventos do dia:** resultado, COPOM, Fed, dado de inflação?

Árvore de ação:
```
Alerta em TICKER específico?
  → Sim: rodar /pm TICKER antes de decidir qualquer coisa
  → Não: continuar

Macro mudou muito? (juros, câmbio, commodity fora da banda histórica)
  → Sim: rodar /mundo-economico em seguida
  → Não: briefing suficiente
```

---

**2. Snapshot diário**

```powershell
! python sbwaa.py /snapshot
```

Salva o estado do dia em `vault/02-relatorios/diarios/`. Sem ação necessária — é dado histórico para os relatórios semanais e mensais usarem. Rodar mesmo em dias sem evento.

---

### Pós-fechamento — Alimentar a base (3 min, opcional)

Não é obrigatório diariamente, mas melhora a qualidade das análises ao longo do tempo.

```powershell
! python sbwaa.py /knowledge --coletar-rss
```

Indexa notícias do dia dos feeds configurados (Valor Econômico, InfoMoney, BCB, Bloomberg, Reuters). O próximo `/morning-call` ou `/analisar` vai encontrar contexto mais atualizado na RAG.

---

## Cadência Semanal

### Sexta (fechamento) ou domingo (revisão) — 20–30 min

Objetivo: verificar se a semana mudou o posicionamento e identificar o que precisa de atenção na semana seguinte.

---

**1. Situação da carteira**

```powershell
! python sbwaa.py /carteira
```

O que olhar:
- P&L total e por ativo. Qual divergiu mais da semana?
- Algum ativo chegou perto do limite de concentração (20%)?
- Dividendos recebidos na semana?

---

**2. Risco e métricas quantitativas**

```powershell
! python sbwaa.py /risco-carteira
```

O que olhar: Sharpe estável ou caindo? VaR dentro do limite do IPS? Circuit breakers todos OK? Fronteira eficiente: ajuste sugerido > 5% em algum ativo?

Árvore de ação:
```
Circuit breaker disparado?
  → Sim: ir para Fluxo — Circuit Breaker (seção abaixo)
  → Não: continuar

Sharpe < 0.3 por 3 semanas seguidas?
  → Sim: incluir /revisar-carteira na próxima sessão semanal
  → Não: continuar

Fronteira eficiente sugere ajuste > 5% num ativo?
  → Sim: anotar para /rebalancear discutir com o IPS
  → Não: continuar
```

---

**3. Próximos dividendos**

```powershell
! python sbwaa.py /dividendos
```

O que olhar: algum ex-date importante nos próximos 15 dias? Se sim, não vender esse ativo antes do ex-date sem verificar o impacto no Yield on Cost.

---

**4. Ativos defasados**

```powershell
! python sbwaa.py /watchlist --rever
```

Lista ativos com análise > 45 dias. Para cada um, avaliar:
```
Houve evento relevante desde a última análise?
  → Sim: rodar /pm TICKER (rápido) ou /analisar TICKER (completo)
  → Não + ativo em carteira: /pm TICKER basta para manter o frescor
  → Não + só na watchlist: aguardar evento ou próxima rotina mensal
```

---

**5. Relatório da semana**

```
/relatorio-semanal
```

P&L da semana, Sharpe, drawdown e outlook. Salvo em `vault/02-relatorios/semanais/`. Ler o output: houve regressão vs semana anterior em alguma métrica-chave?

---

**6. Verificar rebalanceamento**

```
/rebalancear
```

O que olhar:
- Alguma classe de ativo saiu da banda do IPS (mínimo/máximo)?
- Candidato da watchlist classificado MELHORA que ainda não está em carteira?
- Fronteira eficiente + IPS indicam ajuste viável?

Árvore de ação:
```
Desvio vs IPS > 5% numa classe?
  → Sim: anotar ação (aportar/reduzir) para executar na semana
  → Não: aguardar

Candidato MELHORA na watchlist?
  → Com análise recente (<60d): /pm TICKER para ver se o veredicto mantém
  → Sem análise ou >60d: agendar /analisar TICKER no próximo mês
```

---

## Cadência Mensal

### Primeiro fim de semana do mês — 60–90 min

Objetivo: decisões de portfólio com visão completa — performance, risco, otimização e revisão de cada posição.

---

**Bloco 1 — Dados (15 min)**

Rodar tudo antes de abrir qualquer comando de IA. Os agentes vão usar esses caches.

```powershell
# Atualizar carteira e proventos
! python sbwaa.py /carteira
! python sbwaa.py /dividendos

# Métricas de risco + fronteira eficiente
! python sbwaa.py /risco-carteira

# Stress test completo (todos os cenários históricos)
! python sbwaa.py /stress-test

# Fronteira eficiente expandida com watchlist
! python sbwaa.py /otimizar-expansao

# Watchlist completa (carteira + ativos analisados)
! python sbwaa.py /watchlist
```

O que notar antes de continuar:
- `/risco-carteira`: circuit breakers OK? Sharpe do mês?
- `/stress-test`: no pior cenário histórico, qual seria o impacto?
- `/otimizar-expansao`: há candidatos MELHORA na watchlist que o scipy colocaria no portfólio?

---

**Bloco 2 — Relatório (10 min)**

```
/relatorio-mensal
```

Performance completa com benchmarks (IBOV, CDI). Gera `.md` e `.docx` em `vault/02-relatorios/mensais/`. Ler antes de tomar qualquer decisão — o relatório mostra padrões que a visão semanal não captura.

---

**Bloco 3 — Revisão do PM (20–30 min)**

```
/revisar-carteira
```

O PM recebe tudo (carteira, IPS, quant, risk, análises por ativo, cache de expansão) e emite MANTER / AUMENTAR / REDUZIR / SAIR para cada posição, com sizing alvo e prioridades imediatas.

O que olhar no output:
- Quais posições receberam REDUZIR ou SAIR? → ir para Fluxo de Saída
- Quais receberam AUMENTAR? → verificar banda do IPS antes de executar
- Seção "Oportunidades da Watchlist": candidatos MELHORA com análise disponível?
- Alertas de IPS: alguma violação iminente?

---

**Bloco 4 — Plano de ajuste (10 min)**

```
/rebalancear
```

Consolida: desvio vs IPS + fronteira eficiente + candidatos da watchlist. Gera plano concreto de ajuste (o que comprar, o que reduzir, em que ordem).

---

**Bloco 5 — Ação nos ativos sinalizados**

Para cada ativo que o `/revisar-carteira` sinalizou:

```
Análise existe e tem < 60 dias?
  → /pm TICKER    (decisão atualizada com cache existente)

Análise ausente ou > 60 dias?
  → /analisar TICKER    (pipeline completo — 10 etapas, 8 agentes)

Ativo da watchlist candidato MELHORA + análise recente?
  → /comparar TICKER TICKER_SIMILAR    (avaliar vs o que já tem)
  → /pm TICKER    (veredicto final antes de decidir entrada)
```

---

## Cadência Trimestral — Época de resultados

### Janeiro, abril, julho, outubro — 2–3h distribuídas ao longo de 2 semanas

Objetivo: absorver os resultados trimestrais e recalibrar o portfólio com dados fundamentalistas novos.

A temporada de resultados é o momento em que teses se confirmam ou quebram. O risco de não agir é tão alto quanto o de agir errado.

---

**Fase 1 — Coleta de resultados (ao longo da semana do resultado)**

Para cada ativo em carteira com resultado disponível:

```
/earnings TICKER
```

O que olhar por ativo:
- Receita, EBITDA, lucro líquido: acima/abaixo do guidance?
- Dívida: aumentou? Qual impacto no valuation do DCF?
- Guidance revisado: para cima ou para baixo?

Árvore de ação por resultado:
```
Resultado bem acima do esperado (surpresa positiva > 10%)?
  → /analisar TICKER    (recalibrar DCF e valuation completo)
  → Se PM confirmar COMPRAR: avaliar aumento de posição no /rebalancear

Resultado dentro do esperado (variação < 10%)?
  → /pm TICKER    (decisão atualizada com novo contexto)
  → Tese se mantém? Sizing alvo continua?

Resultado muito abaixo do esperado (surpresa negativa > 10%)?
  → /analisar TICKER    (revisão completa — tese pode ter quebrado)
  → Se PM emitir EVITAR ou SAIR: ir para Fluxo de Saída

Guidance cortado ou suspensão de dividendos?
  → /analisar TICKER    (obrigatório — mudança estrutural)
```

Para candidatos da watchlist com resultado disponível:

```
/earnings TICKER    (contexto fundamentalista do candidato)
/tese TICKER        (se o resultado for interessante — tese rápida)
/analisar TICKER    (se a tese justificar pipeline completo)
```

---

**Fase 2 — Recalibração do portfólio (após coletar todos os resultados)**

```powershell
! python sbwaa.py /risco-carteira     # risco com novos fundamentos
! python sbwaa.py /stress-test        # re-calibrar: beta mudou?
! python sbwaa.py /otimizar-expansao  # fronteira com watchlist atualizada
```

```
/revisar-carteira    # PM com todos os earnings já nos arquivos do vault
/rebalancear         # plano de ajuste pós-temporada
```

---

**Fase 3 — Pesquisa de expansão**

A temporada de resultados é o melhor momento para identificar candidatos novos — os relatórios estão frescos e o contexto fundamentalista está no pico de informação.

```
/investimento-do-dia    # o sistema sugere com base no IPS + macro + resultados recentes
/tese TICKER            # candidatos descobertos na temporada
/comparar A B           # comparar com o que já está em carteira ou watchlist
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

**Gatilho:** você ouviu, leu ou alguém mencionou um ativo que você não conhecia.

O risco aqui é gastar horas analisando algo que o PM vai descartar em 5 minutos. Fazer em camadas.

**Camada 1 — Triagem rápida (5 min)**

```
/investimento-do-dia    # o sistema já está sugerindo algo parecido?
/tese TICKER            # tese rápida: Research + DCF + PM (15–20 min de processamento)
```

Árvore de decisão pós-tese:
```
PM emitiu COMPRAR ou BARATO?
  → Continuar para camada 2

PM emitiu AGUARDAR?
  → Adicionar à watchlist (pasta vault/01-ativos/TICKER/ já foi criada)
  → Definir trigger para rever: "quando EBITDA crescer X%" ou "quando preço cair Y%"
  → Encerrar por agora

PM emitiu EVITAR?
  → Registrar motivo no vault e encerrar pesquisa
  → Não gastar mais tempo neste ativo
```

**Camada 2 — Comparação e posicionamento (10 min)**

```
/comparar TICKER TICKER_SIMILAR    # vs algo que já tenho ou analiso na watchlist
```

O que olhar: valuation relativo, qualidade, risco. O novo ativo é melhor ou complementar ao que já existe?

**Camada 3 — Análise completa (se a tese e a comparação forem favoráveis)**

```
/analisar TICKER    # pipeline completo: 8 agentes, 10 etapas (~30 min)
```

Pós-análise:
```
PM confirma COMPRAR?
  → Verificar IPS: a classe tem espaço? Concentração OK?
  → Verificar /otimizar-expansao: o ativo melhora a fronteira?
  → Se tudo OK: python sbwaa.py /adicionar --ticker X ...

PM volta para AGUARDAR?
  → Ativo fica na watchlist com análise completa
  → Aparece em /watchlist e em /revisar-carteira com análise atualizada
```

---

### Fluxo 2 — Evento relevante

#### Resultado trimestral (earnings)

```
/earnings TICKER
```

Árvore de ação:
```
Surpresa > 10% para cima ou para baixo?
  → /analisar TICKER    (recalibração completa)
  → Se tese quebrou: ir para Fluxo de Saída

Resultado dentro do esperado?
  → /pm TICKER    (decisão atualizada)
  → Sizing alvo mudou? Se sim, ver /rebalancear
```

#### COPOM, Fed ou mudança macro relevante

```
/mundo-economico
/morning-call
```

Após entender o impacto:
```powershell
! python sbwaa.py /stress-test custom -15    # impacto no portfólio com choque estimado
```

```
/revisar-carteira    # PM reposiciona com o novo contexto macro
/rebalancear         # ajuste defensivo ou oportunista dependendo do cenário
```

Árvore de ação por cenário macro:
```
Juros subiram mais do que o esperado?
  → Renda fixa e tesouro ficam mais atrativos → ver /otimizar-expansao
  → FIIs tendem a sofrer → /pm para os FIIs em carteira
  → Checar banda de alocação: RF/TD está abaixo do mínimo do IPS?

Câmbio disparou (BRL fraco)?
  → ETFs internacionais se valorizam em BRL → checar concentração
  → Exportadoras (PETR4, VALE3) tendem a beneficiar → /pm nesses ativos

Risco político/fiscal aumentou?
  → /stress-test custom -20 para estimar
  → /revisar-carteira com foco em ativos de alta correlação com risco Brasil
```

#### Queda expressiva num ativo (> 8% em 1 dia)

```powershell
! python sbwaa.py /risco-carteira    # ver impacto no VaR e concentração
```

```
/pm TICKER    # reavalia: a tese quebrou ou é ruído de mercado?
```

Árvore de ação:
```
Queda por notícia fundamentalista grave (perda de contrato, fraude, downgrade)?
  → /analisar TICKER    (revisão completa urgente)
  → Se PM emitir SAIR: ir para Fluxo de Saída imediatamente

Queda por movimento técnico, macro ou contagio setorial sem mudança de fundamento?
  → /pm TICKER confirma posição → manter ou aumentar se IPS permitir
  → Ver /otimizar-expansao: o ativo ainda aparece no portfólio ótimo?

Queda por resultado trimestral abaixo do esperado?
  → /earnings TICKER primeiro, depois /pm TICKER
  → Decidir se é revisão de tese ou ajuste de preço
```

#### Crise sistêmica ou queda generalizada

Quando o mercado cai > 5% em 1 dia ou há evento de cauda (banco quebrou, default soberano, etc.):

```powershell
! python sbwaa.py /stress-test         # todos os cenários históricos de uma vez
! python sbwaa.py /risco-carteira      # VaR em tempo real
```

```
/mundo-economico      # entender o que está acontecendo
/revisar-carteira     # PM em modo de crise: o que sai, o que fica, o que reduz
/rebalancear          # plano concreto — não agir no calor do momento sem isso
```

O que não fazer em crise:
- Não vender tudo sem passar pelo PM — o sistema existe exatamente para isso
- Não comprar mais do ativo que mais caiu sem nova análise (/analisar TICKER)
- Não ignorar o VaR — se violou o limite do IPS, redução de risco é obrigatória

---

### Fluxo 3 — Circuit breaker / drawdown

**Gatilho:** `/risco-carteira` mostra algum circuit breaker disparado.

```powershell
! python sbwaa.py /risco-carteira
```

#### 🚨 VaR 95% > 2% (limite do IPS violado)

```powershell
! python sbwaa.py /stress-test    # quantificar exposição nos cenários extremos
```

```
/revisar-carteira    # PM em modo de redução de risco
/rebalancear         # priorizar redução do ativo com maior contribuição ao risco
```

Sequência de ação:
1. Identificar no `/risco-carteira` qual ativo tem maior contribuição ao risco (`contribuicao_risco`)
2. `/pm TICKER` nesse ativo — confirmar se ainda é válido manter
3. Se confirmar redução: `/vender --ticker X --quantidade Y` parcialmente
4. Rodar `/risco-carteira` novamente para confirmar VaR voltou abaixo de 2%

#### ⚠️ Drawdown > 12% (aproximando do limite de 18%)

```
/mundo-economico     # entender contexto: é setorial, macro ou idiossincrático?
/revisar-carteira    # PM em modo defensivo
```

Regra: não aumentar posição em nenhum ativo enquanto drawdown > 12%. Aportes vão para Tesouro/Renda Fixa até drawdown < 10%.

#### ⚠️ Concentração > 18% num ativo (limite: 20%)

```
/pm TICKER    # ativo concentrado — atualizar veredicto
```

- Não comprar mais deste ativo até concentração cair abaixo de 15%
- Próximo aporte vai para a classe/ativo mais distante do alvo IPS

#### ⚠️ Correlação média > 0.75

Sinal de que o portfólio está "virando um só ativo" — quando um cai, todos caem junto.

```powershell
! python sbwaa.py /otimizar-expansao    # candidatos descorrelacionados da watchlist
```

```
/rebalancear    # ver sugestão de diversificação com dados de fronteira eficiente
```

Candidatos da watchlist classificados MELHORA com correlação < 0.5 são a prioridade.

---

### Fluxo 4 — Saída de posição

**Gatilho:** `/revisar-carteira` emitiu SAIR, ou evento fundamentalista grave, ou necessidade de liquidez.

**Antes de vender — confirmação**

```
/pm TICKER    # confirmação final: ainda é SAIR?
```

O que olhar:
- A tese quebrou (fundamento), ou é uma decisão de timing/preço?
- Há ex-date de dividendo nos próximos 15 dias? Se sim, verificar se vale aguardar.
- Qual o P&L realizado? Impacto no total do portfólio?

**Executar a venda**

```powershell
! python sbwaa.py /vender --ticker TICKER --quantidade X --preco Y
! python sbwaa.py /carteira    # confirmar saída e novo P&L total
! python sbwaa.py /risco-carteira    # como mudou o risco do portfólio?
```

**Alocar o capital liberado**

```
/rebalancear    # onde o capital liberado faz mais sentido
```

Árvore de alocação pós-saída:
```
Capital liberado é relevante (> 5% do portfólio)?
  → /rebalancear    (direciona para a classe mais distante do alvo)
  → /otimizar-expansao    (ver se há candidato na watchlist para absorver)
  → Não alocar no mesmo dia — aguardar 24h para tomar a decisão com o sistema

Capital pequeno (< 5%)?
  → Direcionar para a classe com maior desvio negativo vs IPS
  → Ou manter em caixa/renda fixa curta se não houver oportunidade clara
```

---

### Fluxo 5 — Novo documento / pesquisa para indexar

**Gatilho:** você tem um PDF de resultado, relatório de corretora, tese de casa de análise, paper acadêmico.

```powershell
! python sbwaa.py /knowledge --adicionar "C:\caminho\relatorio.pdf"
```

Após indexar, o documento fica disponível para todos os agentes de IA que consultam a RAG (`/analisar`, `/tese`, `/pm`, `/revisar-carteira`). Não é necessário fazer nada mais — o sistema recupera automaticamente os trechos relevantes.

Casos de uso comuns:
```powershell
# Relatório trimestral da empresa
! python sbwaa.py /knowledge --adicionar "C:\downloads\petr4-3t24.pdf"

# Tese de casa de análise
! python sbwaa.py /knowledge --adicionar "C:\downloads\vale3-tese-xp.pdf"

# Pasta inteira de relatórios
! python sbwaa.py /knowledge --adicionar "C:\downloads\resultados-3t24\"

# Verificar o que está indexado
! python sbwaa.py /knowledge --status
! python sbwaa.py /knowledge --listar

# Buscar contexto manualmente antes de analisar
! python sbwaa.py /knowledge --buscar "valuation petróleo Brasil upstream"
```

---

## Tabela de decisão — Quando usar cada comando de análise

| Situação | Comando |
|----------|---------|
| Ouviu falar num ativo novo | `/tese TICKER` primeiro |
| Tese boa, quer aprofundar | `/analisar TICKER` |
| Resultado trimestral saiu | `/earnings TICKER` → `/pm TICKER` |
| Resultado muito fora do esperado | `/earnings TICKER` → `/analisar TICKER` |
| Ativo caiu muito — checar tese | `/pm TICKER` |
| Quer comparar dois ativos | `/comparar A B` |
| Já tem análise, quer só a decisão | `/pm TICKER` |
| Macro mudou — impacto na carteira | `/mundo-economico` → `/revisar-carteira` |
| Quer sugestão baseada no IPS | `/investimento-do-dia` |
| Época de resultados (trimestral) | `/earnings` por ativo → `/revisar-carteira` |
| Fim de mês — visão completa | `/risco-carteira` → `/revisar-carteira` → `/rebalancear` |
| VaR violado | `/stress-test` → `/revisar-carteira` → `/rebalancear` |
| Quero ver candidatos da watchlist | `/otimizar-expansao` |

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
