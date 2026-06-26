---
tags: [apresentacao, sbwaa, sistema]
cssclasses: [node-apresentacao]
versao: v2.22.0
atualizado: 2026-06-26
---

# SBWAA — Second Brain Wealth + Asset + Assessor Individual

> **Sistema de inteligência financeira pessoal, 100% local, construído sobre IA.**
> Substitui o que antes exigia planilhas, ferramentas pagas e horas de pesquisa manual —
> por decisões estruturadas, análise de risco quantitativa e automação diária.

---

## O Problema

O investidor individual enfrenta uma assimetria real de recursos em relação a gestoras e fundos:

- Não tem acesso a ferramentas institucionais de risco (VaR, CVaR, Markowitz)
- Faz análise de ativos de forma esporádica e sem metodologia consistente
- Perde contexto macro relevante por falta de tempo ou de fluxo de informação organizado
- Toma decisões de portfólio sem visão integrada de risco, valuation e fundamentos
- Não tem registro estruturado das teses de investimento — e repete erros por isso

O resultado é uma carteira gerida por intuição, não por processo.

---

## A Solução

O SBWAA é um **sistema operacional de investimentos pessoais** que funciona localmente, sem APIs pagas, sem enviar dados financeiros para terceiros. Ele combina:

- **8 agentes de IA especializados** que executam análises de nível institucional
- **Pipeline de dados próprio** que coleta preços, fundamentals e notícias automaticamente
- **Vault estruturado** (Obsidian) onde todo o conhecimento fica organizado e conectado
- **Automação diária** que roda antes de você acordar, sem você precisar pedir

> [!tip] Filosofia central
> O SBWAA não é para acompanhar cotação minuto a minuto.
> É para **tomar menos decisões, mas melhores** — com dados estruturados, análise de risco e contexto macro sempre atualizados.

---

## Arquitetura em Alto Nível

```
┌─────────────────────────────────────────────────────────────┐
│                        ENTRADA                              │
│   Task Scheduler  ·  Terminal  ·  UI Desktop (Tkinter)      │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  SBWAA CORE (sbwaa.py)                      │
│         Roteador de comandos · Pipeline de execução         │
└──┬────────────────┬──────────────────┬──────────────────────┘
   │                │                  │
   ▼                ▼                  ▼
Scripts Python   Agentes IA        Knowledge Base
(dados, risco,   (análise,         (ChromaDB · RAG
 alertas,        decisão PM,        local · notícias
 simulação)      valuation,         indexadas)
                 earnings)
   │                │                  │
   └────────────────┴──────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────────┐
│                   VAULT OBSIDIAN                            │
│   Portfólio · Análises · Relatórios · Decisões · Macro      │
└─────────────────────────────────────────────────────────────┘
```

---

## Os 8 Agentes

Cada agente é especializado em uma disciplina. Eles colaboram entre si — a análise de um alimenta a decisão de outro.

| Agente | Função | Quando atua |
|--------|--------|-------------|
| 🔍 **Market Researcher** | Análise macro, setor, posicionamento competitivo, notícias | `/analisar`, `/morning-call` |
| 📊 **Quant / Data Engineer** | Métricas quantitativas: Sharpe, Beta dinâmico, correlação, GARCH | Automático diário |
| ⚠️ **Risk Engineer** | VaR, CVaR, drawdown, circuit breakers, fronteira Markowitz | `/risco-carteira`, `/snapshot` |
| 🧮 **Model Builder (DCF)** | Valuation por fluxo de caixa descontado, múltiplos, preço-alvo | `/analisar`, `/tese` |
| 📈 **Valuation Reviewer** | Revisão crítica do DCF, comparação por múltiplos de mercado | `/analisar` |
| 📋 **Earnings Reviewer** | Análise de resultados trimestrais, receita, margens, guidance | `/earnings` |
| 📐 **Econometrician** | GARCH, fator modelo, beta rolling, correlação dinâmica | Pipeline automático |
| 💼 **Portfolio Manager** | Decisão final: COMPRAR / MANTER / REDUZIR / SAIR / AGUARDAR / EVITAR | `/pm`, `/analisar` |

> [!note] O PM é o árbitro
> O Portfolio Manager é o último agente a falar. Ele lê o output de todos os outros e emite a decisão fundamentada — com preço-alvo, horizonte e justificativa.

---

## Comandos — O que o Sistema Faz

Os comandos se dividem em dois grupos: **locais** (Python puro, instantâneos) e **IA** (disparam os agentes).

### Gestão da Carteira

| Comando | O que entrega |
|---------|--------------|
| `/carteira` | Posições atualizadas, P&L, alocação por classe, barras visuais, projeção de metas |
| `/dividendos` | Proventos recebidos, DY ponderado, renda mensal, próximas datas ex |
| `/adicionar TICKER` | Registra nova posição com custo médio, quantidade e data; suporte a RF/TD com indexador, taxa e vencimento; ativos USD com conversão automática BRL/USD |
| `/vender TICKER` | Registra venda parcial ou total; para RF/TD/DEB/CRI-CRA: calcula IR regressivo (22,5%→15%) e IOF automático; P&L exibido em bruto e líquido |
| `/metas` | Dashboard de metas financeiras: renda passiva, patrimônio, reserva, metas livres |
| `/oportunidade` | Gerencia RF de curto prazo (Caixinha/RDB): saldo bruto, IOF estimado, IR estimado, líquido disponível para aporte; integrado ao PM |

### Risco e Quantitativo

| Comando | O que entrega |
|---------|--------------|
| `/risco-carteira` | VaR, CVaR, Sharpe, Beta, Drawdown, Circuit Breakers, Fronteira Eficiente Markowitz |
| `/snapshot` | Versão rápida do risco — salva no vault sem análise completa |
| `/stress-test` | Simula 8 cenários de crise: -20%, +5% juros, crash crypto, recessão, deflação, guerra, câmbio +20%, crise fiscal BR; breakdown FX para carteiras com exposição USD |
| `/simulacao` | Monte Carlo + backtest histórico + projeção de patrimônio com aportes; `--real` plota curva de equity real vs IBOV e CDI |
| `/otimizar-expansao` | Compara fronteira atual vs fronteira expandida com a watchlist — identifica quais ativos melhoram o portfólio |
| `/correlacao` | Heatmap de correlações da carteira: tabela ASCII colorida no terminal + PNG dark mode + nota Obsidian com pares de alta correlação e métricas de diversificação |
| `/performance` | Benchmark local: retorno da carteira vs IBOV, CDI e IPCA para MTD/YTD/12m; alpha, beta, Sharpe, tracking error, decomposição por classe |
| `/alerta` | Gerencia alertas de preço extraídos automaticamente das análises do vault; histórico de disparos em `alertas-historico.md`; verificação a cada 60 min no pregão |

### Análise de Ativos

| Comando | O que entrega |
|---------|--------------|
| `/tese TICKER` | Análise rápida: macro, setor, DCF simplificado, decisão PM; extrai preços-alvo automaticamente para o sistema de alertas |
| `/analisar TICKER [TICKER2...]` | Pipeline completo: 8 agentes, DCF, earnings, risco, valuation, decisão PM fundamentada; aceita múltiplos tickers em batch com tabela comparativa ao final |
| `/earnings TICKER` | Análise de resultado trimestral: receita, margem, EBITDA, guidance vs consenso |
| `/earning-calendar` | Calendário de resultados dos próximos 90 dias: datas confirmadas (ações via yfinance) e estimadas (FIIs por calendário CVM); alertas automáticos em D-7 e D-1 |
| `/comparar A B` | Análise lado a lado de dois ativos — qual o melhor ponto de entrada |
| `/investimento-do-dia [categoria]` | Sugestão de 1–2 ativos para explorar com base no macro do dia; filtra por categoria: fii, acao, etf, rf, td |

### Decisão de Portfólio

| Comando | O que entrega |
|---------|--------------|
| `/pm TICKER` | Portfolio Manager emite decisão estruturada para ativo com análise existente |
| `/pm 700` | **Modo Aporte** — distribui R$ 700 (qualquer valor) entre múltiplos ativos elegíveis da watchlist |
| `/revisar-carteira` | PM revisa todas as posições: MANTER / AUMENTAR / REDUZIR / SAIR para cada ativo |
| `/rebalancear` | Sugere rebalanceamento da carteira vs metas do IPS + fronteira eficiente |

### Macro e Relatórios

| Comando | O que entrega |
|---------|--------------|
| `/morning-call` | Briefing pré-mercado: macro global, Brasil, carteira, alertas, oportunidades do dia; inclui resumo compacto de metas e alertas econométricos críticos |
| `/mundo-economico` | Análise macro profunda: Fed, Copom, câmbio, commodities, impacto na carteira |
| `/fluxo-caixa` | Projeção de renda passiva mês a mês (12 meses): dividendos periódicos por ticker, valorização estimada de RF/TD/DEB/CRI-CRA líquida de IR; alerta vs meta de renda |
| `/relatorio-semanal` | P&L da semana, métricas de risco, performance vs benchmark, outlook |
| `/relatorio-mensal` | Relatório completo: performance, análise de risco, revisão de teses, next steps |

### Base de Conhecimento

| Comando | O que entrega |
|---------|--------------|
| `/knowledge` | Consulta a base RAG local com notícias e documentos indexados |
| `/knowledge --coletar-rss` | Coleta feeds de Valor Econômico, InfoMoney, Bloomberg, Reuters, BCB |
| `/ips` | Exibe ou edita a Política de Investimentos — os limites que o sistema respeita |
| `/watchlist` | Lista todos os ativos analisados com veredicto, frescor e preço-alvo |
| `/cache` | Dashboard de status do cache por tipo (cotação, fundamentais, macro, dividendos, modelos); limpa stale automaticamente ou por tipo; TTL configurável via `.env` |
| `/att-info-system` | Fecha a sessão de trabalho: detecta versão, atualiza CHANGELOG, bump de versão em todos os docs, git commit + push + GitHub Release |

---

## Automação — O Sistema Trabalha Enquanto Você Dorme

A partir da v2.12.0, o SBWAA tem um **sistema de automação local** que roda via Windows Task Scheduler, sem abrir nenhuma janela, sem precisar de interação.

### O que roda automaticamente

```
07:45 — Seg a Sex
   ├── RSS Collector       → atualiza base de notícias
   ├── Market Snapshot     → preços e variações
   ├── Quant Metrics       → Sharpe, Vol, Beta da carteira
   ├── Risk Engineer       → VaR, drawdown, circuit breakers
   ├── Check Alerts        → verifica violações e dividendos próximos
   ├── /morning-call       → Claude gera briefing completo no vault
   └── Auto Flag           → cria flag que ativa o slot de teses

08:30 — Seg a Sex (somente após morning automático)
   └── Tese Trigger        → extrai tickers do morning call e roda /tese em cada um;
                             salva tese_queue com veredictos e comandos sugeridos

10:00–17:00 — Seg a Sex (a cada 60 min, janela de pregão)
   └── Check Preços-Alvo   → verifica alertas de preço da watchlist; dispara toast
                             e registra em vault/05-risk/alertas-historico.md

17:00 — Seg a Sex
   ├── Market Snapshot EOD → fechamento do mercado
   ├── Update Carteira EOD → snapshot diário de P&L em vault/02-relatorios/diarios/
   ├── Performance Build   → benchmark vs IBOV/CDI/IPCA atualizado
   ├── Check Alerts EOD    → alertas do fechamento
   └── /snapshot           → risk snapshot no vault

08:00 — Domingo
   ├── Fluxo de Caixa      → projeção de renda passiva atualizada (12 meses)
   └── /relatorio-semanal  → relatório semanal completo

08:00 — 1° fim de semana do mês
   ├── Earnings Calendar   → atualiza calendário de resultados da carteira
   └── /relatorio-mensal   → relatório mensal completo
```

### Notificação ao concluir

O sistema envia uma **toast notification do Windows** ao terminar cada slot, informando quantas tarefas passaram e quais falharam — sem abrir nada, sem spam.

### Banner de alertas na UI

Ao abrir o painel, `startup_check.py` verifica se há ativos com sinal **COMPRAR** na fila de teses do dia. Se houver, um **banner persistente** aparece no topo da interface com: ticker, tipo de ativo, status (carteira/watchlist/novo) e comando sugerido (`/pm` ou `/analisar`). Botão de copiar por linha. Fecha para a sessão mas reaparece no próximo boot enquanto a fila for do dia.

> [!important] PC em sleep/hibernate
> O Task Scheduler está configurado com `WakeToRun = true` — acorda o PC do sleep para rodar as tarefas. Se o PC estiver completamente desligado, as tarefas rodam no próximo boot (`StartWhenAvailable = true`).

---

## Vault Obsidian — O Cérebro Persistente

Todo output do sistema é salvo no vault — uma base de conhecimento estruturada que cresce com o tempo.

```
vault/
├── 00-portfolio/       → carteira.md, ips.md, metas.md, historico-trades.md
├── 01-ativos/          → uma pasta por ticker: tese, DCF, earnings, PM decisions
├── 02-relatorios/      → morning calls, semanais, mensais, dividendos, risco
├── 03-macro/           → notas de análise macroeconômica
├── 04-decisoes/        → registro de todas as decisões do PM
├── 05-risk/            → snapshots de risco e alertas
└── _templates/         → 11 templates Obsidian para padronizar notas
```

Cada nota usa **wikilinks automáticos** — a tese de um ativo linka para o DCF, earnings, risk snapshot e notas macro relacionadas. O vault se torna uma rede navegável de conhecimento financeiro.

---

## Segurança e Privacidade

> [!important] 100% local — nenhum dado financeiro sai do seu computador

- Posições, custo médio, patrimônio e dados pessoais nunca são enviados a APIs externas
- APIs externas recebem apenas: tickers públicos, datas e parâmetros de mercado
- O vault fica no seu disco — não sincroniza com nenhum servidor por padrão
- Logs ficam exclusivamente em `/logs/` local
- O `.gitignore` bloqueia `vault/00-portfolio/` e `knowledge/raw/` do git

---

## Workflow — Como o Sistema é Usado na Prática

O fluxo de trabalho tem dois eixos: o **calendário fixo** (o que roda automaticamente ou por hábito) e os **fluxos oportunísticos** (gatilhados por eventos de mercado ou decisões).

### Fluxo Diário — O que você faz em 5–10 minutos

```
Acorda
  └── Abre o painel ou vault
       ├── Banner de COMPRAR? (tese_trigger rodou às 08:30)
       │    ├── Sim → copiar comando sugerido (/pm ou /analisar) e executar
       │    └── Não → continuar
       └── Lê o morning call que o sistema gerou às 07:45
            ├── Nenhum alerta → dia normal, nada a fazer
            └── Alerta presente?
                 ├── Circuit breaker (VaR ou drawdown) → /risco-carteira → /rebalancear
                 ├── Ativo caiu >5%                    → /pm TICKER → decidir
                 ├── Alerta de preço-alvo disparado     → /alerta --historico → revisar
                 └── Dividendo próximo                 → /dividendos → conferir
```

### Fluxo Semanal — Revisão de 20–30 minutos (domingo)

```
Ler /relatorio-semanal  (gerado automaticamente sábado/domingo)
  ├── Performance OK e sem alertas → /watchlist --rever  (ver o que está defasado)
  │    └── Ativo com análise > 45 dias → /analisar TICKER
  └── Performance abaixo do esperado → /rebalancear → /pm (decidir ajuste)
```

### Fluxo de Análise de Ativo — Do zero à decisão

```
Ativo novo?
  └── /tese TICKER  (análise rápida — 5 min)
       ├── EVITAR → não entra na watchlist
       └── Tese favorável → /analisar TICKER  (análise completa — 15 min)
            └── Agentes rodam: Macro → Quant → DCF → Earnings → Risk → PM
                 ├── AGUARDAR → fica na watchlist, /pm quando gatilho surgir
                 ├── COMPRAR  → /pm TICKER para confirmar preço e tamanho
                 └── /adicionar TICKER para registrar a entrada
```

### Fluxo de Aporte — Onde colocar capital novo

```
Tem capital para aportar?
  └── /pm 700  (ou qualquer valor)
       ├── PM lê o IPS, a carteira atual e os ativos da watchlist
       ├── Calcula gap de alocação vs metas
       ├── Filtra ativos elegíveis (análise < 60d, veredicto ≥ AGUARDAR)
       └── Distribui o capital com justificativa por ativo
            └── Você executa na corretora e roda /adicionar para registrar
```

### Fluxo Oportunístico — Eventos de mercado

```
Evento relevante surgiu (queda de mercado, notícia macro, resultado trimestral)?
  ├── Queda do mercado  → /stress-test  → ver impacto real na carteira
  ├── Notícia macro     → /mundo-economico  → interpretar impacto nos ativos
  ├── Resultado trimestral → /earnings TICKER  → avaliar vs expectativa
  └── "Qual o melhor ativo agora?" → /investimento-do-dia  → sugestão contextualizada
```

> [!tip] A regra dos 60 dias
> O Portfolio Manager (`/pm`) pressupõe que a análise do ativo no vault está atualizada.
> Com análise **acima de 60 dias**, o sistema exige `/analisar` antes de emitir decisão —
> fundamentos, preço e contexto macro podem ter mudado.

---

## Stack Técnica

| Camada | Tecnologia |
|--------|-----------|
| IA / Agentes | Claude Code (Anthropic) — via subscription, sem API key separada |
| Linguagem | Python 3.13 |
| Base de conhecimento | ChromaDB (vetorial local) + RSS feeds |
| Vault / outputs | Obsidian (Markdown) |
| Dados de mercado | Yahoo Finance (yfinance), Brapi, Investidor10 (scraping) |
| Automação | Windows Task Scheduler + launcher VBS silencioso |
| UI desktop | CustomTkinter (painel visual opcional) |
| Quantitativo | NumPy, SciPy, statsmodels (GARCH, fator modelo, Monte Carlo) |

---

## Cadência Operacional — Quanto Tempo Exige

| Frequência | Tempo estimado | O que fazer |
|------------|---------------|-------------|
| **Diária** | 5–10 min | Ler o morning call que o sistema gerou. Agir se houver alerta. |
| **Semanal** | 20–30 min | Ler o relatório semanal. `/watchlist --rever`. Decidir `/pm` se houver candidato. |
| **Mensal** | 60–90 min | Relatório mensal, `/revisar-carteira`, `/rebalancear`, `/stress-test`. |
| **Trimestral** | 2–3h | Época de resultados: `/earnings` nos ativos da carteira, recalibrar DCFs. |
| **Anual** | 1 sessão | Revisar IPS, `/simulacao`, recalibrar metas. |

> O sistema faz o trabalho pesado automaticamente — você entra apenas para decidir e ajustar.

---

## Diferenciais

| Característica | SBWAA | Planilha | App de Investimentos |
|---------------|-------|----------|---------------------|
| Análise quantitativa de risco (VaR, Markowitz) | ✅ | ❌ | Raro |
| Decisão de portfólio com IA fundamentada | ✅ | ❌ | ❌ |
| Análise de ativos com DCF + múltiplos | ✅ | Manual | ❌ |
| Contexto macro integrado às decisões | ✅ | ❌ | ❌ |
| Econometria aplicada (GARCH, Fama-French, beta dinâmico) | ✅ | ❌ | ❌ |
| Automação diária sem intervenção (5 slots) | ✅ | ❌ | Parcial |
| Tese automática pós-morning com alertas de COMPRAR | ✅ | ❌ | ❌ |
| Alertas de preço com histórico navegável | ✅ | Manual | Parcial |
| Motor tributário IR/IOF por tipo de ativo | ✅ | Manual | Raro |
| P&L histórico diário + curva de equity real | ✅ | Manual | Parcial |
| Benchmark automático vs IBOV/CDI/IPCA | ✅ | Manual | Parcial |
| Suporte a ativos internacionais (USD) com exposição cambial | ✅ | Manual | Parcial |
| 100% local — dados privados nunca saem | ✅ | ✅ | ❌ |
| Vault navegável com histórico de teses | ✅ | ❌ | ❌ |
| Modo aporte — distribui capital entre ativos | ✅ | Manual | ❌ |
| Stress test em cenários de crise | ✅ | ❌ | Raro |
| Custo recorrente de dados | R$ 0 | R$ 0 | R$ 30–200/mês |

---

## Estado Atual — v2.22.0

- **35+ comandos** operacionais
- **8 agentes** especializados (+ Econometrician: GARCH, beta dinâmico, Fama-French 3 fatores, macro regression)
- **5 slots automatizados** via Task Scheduler (morning, tese, alerta, eod, weekend)
- **Pipeline de dados próprio** — sem dependência de APIs pagas; scraping Investidor10, Yahoo Finance, BCB SGS, Brapi
- **11 templates Obsidian** para padronizar todo output
- **Base RAG local** com feeds de 5+ fontes financeiras
- **Motor tributário completo** — IR regressivo e IOF para RF/TD/DEB/CRI-CRA; IR renda variável por classe; P&L líquido em todos os relatórios
- **Cache centralizado com TTL por tipo** — cotação 15min, macro 60min, dividendos 6h, fundamentais/histórico 24h; configurável via `.env`
- **P&L histórico diário** — snapshot automático às 17h; curva de equity real vs IBOV e CDI com `/simulacao --real`
- **Suporte a ativos internacionais (USD)** — conversão automática BRL/USD na entrada e no P&L; exposição cambial separada em USD direto vs indireto
- **Sistema de alertas de preço** — preços-alvo extraídos automaticamente das análises; verificação horária no pregão; histórico navegável no vault

---

## Roadmap — Próximas Evoluções

- [ ] Integração com corretoras via Open Finance para sync automático da carteira
- [ ] Dashboard web local (FastAPI + React) como alternativa à UI Tkinter
- [ ] Alertas por WhatsApp/Telegram além das notificações Windows
- [ ] Backtesting de estratégias de alocação com dados históricos longos
- [ ] Multi-portfólio — gerenciar mais de uma carteira separadamente
- [ ] Modo colaborativo — compartilhar análises sem expor posições

---

*Documento gerado e mantido automaticamente pelo SBWAA.*
*Atualizado a cada nova feature, remoção ou alteração relevante.*
*[[VERSION]] · [[CHANGELOG]] · [[SBWAA-MASTER-BLUEPRINT]]*
