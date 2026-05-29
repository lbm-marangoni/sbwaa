---
tags: [apresentacao, sbwaa, sistema]
cssclasses: [node-apresentacao]
versao: v2.19.0
atualizado: 2026-05-29
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
| `/adicionar TICKER` | Registra nova posição com custo médio, quantidade e data |
| `/vender TICKER` | Registra venda parcial ou total |
| `/metas` | Dashboard de metas financeiras: renda passiva, patrimônio, reserva, metas livres |

### Risco e Quantitativo

| Comando | O que entrega |
|---------|--------------|
| `/risco-carteira` | VaR, CVaR, Sharpe, Beta, Drawdown, Circuit Breakers, Fronteira Eficiente Markowitz |
| `/snapshot` | Versão rápida do risco — salva no vault sem análise completa |
| `/stress-test` | Simula 6 cenários de crise: -20%, +5% juros, crash crypto, recessão, deflação, guerra |
| `/simulacao` | Monte Carlo + backtest histórico + projeção de patrimônio com aportes |
| `/otimizar-expansao` | Compara fronteira atual vs fronteira expandida com a watchlist — identifica quais ativos melhoram o portfólio |

### Análise de Ativos

| Comando | O que entrega |
|---------|--------------|
| `/tese TICKER` | Análise rápida: macro, setor, DCF simplificado, decisão PM |
| `/analisar TICKER` | Pipeline completo: 8 agentes, DCF, earnings, risco, valuation, decisão PM fundamentada |
| `/earnings TICKER` | Análise de resultado trimestral: receita, margem, EBITDA, guidance vs consenso |
| `/comparar A B` | Análise lado a lado de dois ativos — qual o melhor ponto de entrada |
| `/investimento-do-dia` | Sugestão de 1–2 ativos para explorar com base no macro do dia |

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
| `/morning-call` | Briefing pré-mercado: macro global, Brasil, carteira, alertas, oportunidades do dia |
| `/mundo-economico` | Análise macro profunda: Fed, Copom, câmbio, commodities, impacto na carteira |
| `/relatorio-semanal` | P&L da semana, métricas de risco, performance vs benchmark, outlook |
| `/relatorio-mensal` | Relatório completo: performance, análise de risco, revisão de teses, next steps |

### Base de Conhecimento

| Comando | O que entrega |
|---------|--------------|
| `/knowledge` | Consulta a base RAG local com notícias e documentos indexados |
| `/knowledge --coletar-rss` | Coleta feeds de Valor Econômico, InfoMoney, Bloomberg, Reuters, BCB |
| `/ips` | Exibe ou edita a Política de Investimentos — os limites que o sistema respeita |
| `/watchlist` | Lista todos os ativos analisados com veredicto, frescor e preço-alvo |

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
   └── /morning-call       → Claude gera briefing completo no vault

17:00 — Seg a Sex
   ├── Market Snapshot EOD → fechamento do mercado
   ├── Check Alerts EOD    → alertas do fechamento
   └── /snapshot           → risk snapshot no vault

08:00 — Domingo
   └── /relatorio-semanal  → relatório semanal completo

08:00 — 1° fim de semana do mês
   └── /relatorio-mensal   → relatório mensal completo
```

### Notificação ao concluir

O sistema envia uma **toast notification do Windows** ao terminar cada slot, informando quantas tarefas passaram e quais falharam — sem abrir nada, sem spam.

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
  └── Abre o vault / terminal
       └── Lê o morning call que o sistema gerou às 07:45
            ├── Nenhum alerta → dia normal, nada a fazer
            └── Alerta presente?
                 ├── Circuit breaker (VaR ou drawdown) → /risco-carteira → /rebalancear
                 ├── Ativo caiu >5%                    → /pm TICKER → decidir
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
| Automação diária sem intervenção | ✅ | ❌ | Parcial |
| 100% local — dados privados nunca saem | ✅ | ✅ | ❌ |
| Vault navegável com histórico de teses | ✅ | ❌ | ❌ |
| Modo aporte — distribui capital entre ativos | ✅ | Manual | ❌ |
| Stress test em cenários de crise | ✅ | ❌ | Raro |
| Custo recorrente de dados | R$ 0 | R$ 0 | R$ 30–200/mês |

---

## Estado Atual — v2.12.0

- **25+ comandos** operacionais
- **8 agentes** especializados
- **3 slots automatizados** via Task Scheduler
- **Pipeline de dados próprio** — sem dependência de APIs pagas
- **11 templates Obsidian** para padronizar todo output
- **Base RAG local** com feeds de 5+ fontes financeiras

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
