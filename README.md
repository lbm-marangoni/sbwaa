# SBWAA — Second Brain Wealth + Asset + Assessor Individual

> Sistema multi-agente de gestão de portfólio e análise de ativos financeiros.
> Operação 100% local. Dados 100% privados. Motor de IA: Claude Code.

![Version](https://img.shields.io/badge/versão-v2.23.0-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Platform](https://img.shields.io/badge/plataforma-Windows-lightgrey)
![License](https://img.shields.io/badge/licença-privado-red)

---

## O que é

SBWAA é um **sistema operacional de investimentos pessoais** que roda inteiramente no seu computador. Combina 8 agentes de IA especializados, pipeline de dados de mercado, base de conhecimento RAG local e automação diária via Task Scheduler — sem enviar nenhum dado financeiro para fora da sua máquina.

### O que resolve

| Sem o SBWAA | Com o SBWAA |
|-------------|-------------|
| Análise de ativos esporádica, sem metodologia | Pipeline completo: macro → DCF → earnings → risco → decisão do PM |
| Risco calculado na intuição | VaR, CVaR, Sharpe, Fronteira Eficiente Markowitz, stress tests |
| Teses de investimento perdidas em planilhas | Vault Obsidian estruturado: teses, DCFs, earnings, decisões linkados |
| Aporte decidido no impulso | Modo Aporte: PM distribui capital entre ativos elegíveis com justificativa |
| Horas gastas lendo notícias | Morning call automático às 07:45 com macro, alertas e oportunidades |

---

## Funcionalidades

### 25+ comandos organizados em 6 categorias

| Categoria | Comandos |
|-----------|----------|
| **Carteira** | `/carteira`, `/dividendos`, `/adicionar`, `/vender`, `/metas` |
| **Risco** | `/risco-carteira`, `/snapshot`, `/stress-test`, `/simulacao`, `/otimizar-expansao` |
| **Análise** | `/tese`, `/analisar`, `/earnings`, `/comparar`, `/investimento-do-dia` |
| **Decisão PM** | `/pm TICKER`, `/pm 700` (modo aporte), `/revisar-carteira`, `/rebalancear` |
| **Macro** | `/morning-call`, `/mundo-economico`, `/relatorio-semanal`, `/relatorio-mensal` |
| **Sistema** | `/watchlist`, `/ips`, `/knowledge`, `/snapshot`, `/status` |

### 8 agentes especializados

| Agente | Modelo | Função |
|--------|--------|--------|
| Market Researcher | Sonnet | Macro, setor, competidores, notícias do dia |
| Earnings Reviewer | Sonnet | Resultado trimestral: receita, margens, guidance vs consenso |
| Model Builder | Opus | DCF, múltiplos, preço-alvo |
| Valuation Reviewer | Sonnet | Revisão crítica do modelo, equity research |
| Quant / Data Eng. | Sonnet | Sharpe, Beta, correlação, métricas quantitativas |
| Econometrician | Sonnet | GARCH, beta dinâmico, Fama-French 3F, macro BCB, drawdown avançado |
| Risk Engineer | Opus | VaR, CVaR, circuit breakers, Fronteira Eficiente |
| Portfolio Manager | Opus | Decisão final: COMPRAR / MANTER / REDUZIR / SAIR / AGUARDAR / EVITAR |

### Automação diária (v2.13.0)

Três slots via Windows Task Scheduler — roda silenciosamente, sem abrir janela:

```
07:45 seg–sex  →  RSS + snapshot + quant + risk + alertas + /morning-call
17:00 seg–sex  →  snapshot EOD + alertas + /snapshot
08:00 sáb–dom  →  /relatorio-semanal (dom) + /relatorio-mensal (1° fds do mês)
```

- **PC em sleep**: `WakeToRun` acorda o computador automaticamente
- **PC desligado**: `StartWhenAvailable` roda na próxima inicialização
- **Notificação**: toast Windows ao concluir cada slot

### Outputs Obsidian

Cada comando gera notas `.md` estruturadas no vault com wikilinks automáticos entre teses, DCFs, earnings, snapshots de risco e notas macro.

`/carteira` — barras visuais `█░`, callouts `[!warning]`/`[!danger]` por desvio do IPS  
`/dividendos` — relatório de proventos com DY ponderado e renda mensal  
`/risco-carteira` — métricas HF, circuit breakers, Fronteira Markowitz  
`/stress-test` — 6 cenários de crise com ícones por severidade  

---

## Pré-requisitos

| Ferramenta | Versão | Obrigatório |
|------------|--------|-------------|
| Python | 3.11+ | ✅ |
| Claude Code | qualquer | ✅ |
| PowerShell | 5.1+ | ✅ |
| Obsidian | qualquer | Recomendado |

**Instalar Claude Code:**
```powershell
npm install -g @anthropic-ai/claude-code
```

---

## Instalação

```powershell
# 1. Clonar
git clone https://github.com/lbm-marangoni/sbwaa.git
cd sbwaa

# 2. Ambiente virtual
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Dependências
pip install -r requirements.txt

# 4. Verificar instalação
$env:PYTHONUTF8 = "1"
python sbwaa.py /status
```

> Se o PowerShell bloquear scripts: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

---

## Configuração inicial

### Portfólio

Os arquivos de portfólio ficam em `vault/00-portfolio/` e **não vêm no repositório** (dados pessoais). São criados automaticamente ao registrar o primeiro ativo:

```powershell
python sbwaa.py /adicionar --ticker PETR4 --tipo acao-on --quantidade 100 --preco-medio 38.50 --setor energia
```

### IPS (Investment Policy Statement)

O IPS define metas de alocação e limites de risco que o sistema respeita em todas as decisões:

```powershell
python sbwaa.py /ips --editar
```

### Automação

```powershell
# Instala as 3 tarefas no Task Scheduler (WakeToRun ativado)
python scripts/automation/setup_scheduler.py --instalar

# Verificar status
python scripts/automation/setup_scheduler.py --status

# Testar agora
python scripts/automation/setup_scheduler.py --testar morning
```

### Setup guiado (opcional)

Para uma configuração completa assistida por IA, abra o projeto no Claude Code e cole:

```
Quero configurar o SBWAA do zero. Leia .env.template,
knowledge/sources/sources.json, scripts/alerts/check_alerts.py
e CLAUDE.md, depois conduza um formulário interativo comigo —
uma pergunta por vez — cobrindo: modo de operação, feeds RSS,
thresholds de alerta e IPS completo.
```

---

## Uso rápido

### Comandos locais (Python puro)

```powershell
python sbwaa.py /carteira          # posições, P&L, alocação visual
python sbwaa.py /risco-carteira    # VaR, Sharpe, Markowitz
python sbwaa.py /stress-test       # 6 cenários de crise
python sbwaa.py /dividendos        # proventos e DY
python sbwaa.py /watchlist         # ativos monitorados com frescor
python sbwaa.py /otimizar-expansao # quais ativos melhoram o portfólio
python sbwaa.py /simulacao         # Monte Carlo + backtest
python sbwaa.py /metas             # dashboard de metas financeiras
python sbwaa.py /help              # todos os comandos
```

### Comandos de IA (no chat do Claude Code)

```
/morning-call              # briefing pré-abertura: macro + carteira + alertas
/analisar PETR4            # pipeline completo: 8 agentes, DCF, earnings, risco, decisão PM
/tese VALE3                # análise rápida com veredicto
/pm PETR4                  # decisão do PM para ativo com análise existente
/pm 700                    # modo aporte: distribui R$ 700 entre elegíveis
/revisar-carteira          # PM revisa todas as posições
/rebalancear               # desvios vs IPS + sugestão de ajuste
/earnings WEGE3            # análise de resultado trimestral
/relatorio-semanal         # P&L + risco + outlook da semana
```

---

## Estrutura do projeto

```
sbwaa/
├── sbwaa.py                    ← ponto de entrada de todos os comandos
├── CLAUDE.md                   ← políticas globais e roteamento de agentes
├── requirements.txt
│
├── docs/
│   ├── GUIA-COMANDOS.md        ← sintaxe, flags e exemplos de todos os comandos
│   ├── SBWAA-WORKFLOW.md       ← cadências diária/semanal/mensal/trimestral/anual
│   ├── SBWAA-REFERENCIA.md     ← campos, mockups de output, comportamento esperado
│   ├── SBWAA-APRESENTACAO.md   ← visão geral do sistema para apresentações
│   └── SBWAA-MASTER-BLUEPRINT.md
│
├── interface/
│   ├── ui.py                   ← painel visual (customtkinter)
│   └── splash.py
│
├── .claude/
│   └── agents/                 ← 8 agentes (market-researcher, earnings-reviewer,
│                                  model-builder, valuation-reviewer, quant-data-engineer,
│                                  econometrician, risk-engineer, portfolio-manager)
│
├── scripts/
│   ├── data/                   ← fetch_fundamentals, fetch_yahoo, fetch_investidor10,
│   │                              market_snapshot, optimize_expansao, simulacao_carteira
│   ├── alerts/                 ← check_alerts (8 tipos: VaR, drawdown, variação, dividendos...)
│   ├── heartbeat/              ← heartbeat.py legado (execução manual)
│   └── automation/             ← dispatcher modular: main.py, runner.py, notifier.py,
│                                  launcher.vbs, setup_scheduler.py
│
├── knowledge/                  ← base RAG (ChromaDB + sentence-transformers)
│
└── vault/                      ← notas Obsidian (dados pessoais — não versionados)
    ├── 00-portfolio/           ← carteira, IPS, trades, metas, decisoes
    ├── 01-ativos/              ← teses, DCFs, earnings por ticker
    ├── 02-relatorios/          ← morning calls, semanais, mensais, dividendos
    ├── 03-macro/               ← notas do Market Researcher
    ├── 04-decisoes/            ← histórico de decisões do PM
    ├── 05-risk/                ← snapshots de risco e alertas
    └── _templates/             ← 11 templates Obsidian
```

---

## Segurança e privacidade

- Posições, preço médio, patrimônio e dados pessoais **nunca saem do vault local**
- APIs externas recebem apenas: tickers públicos, datas e parâmetros de mercado
- `vault/00-portfolio/`, `scripts/data/cache/`, `knowledge/.chromadb/` no `.gitignore`
- Logs ficam exclusivamente em `logs/` local

Política completa: [`CLAUDE.md`](CLAUDE.md) — seção Security Policy.

---

## Documentação

| Documento | Conteúdo |
|-----------|----------|
| [`docs/GUIA-COMANDOS.md`](docs/GUIA-COMANDOS.md) | Referência completa: sintaxe, flags, exemplos |
| [`docs/SBWAA-WORKFLOW.md`](docs/SBWAA-WORKFLOW.md) | Workflow operacional: 6 cadências + fluxos oportunísticos |
| [`docs/SBWAA-REFERENCIA.md`](docs/SBWAA-REFERENCIA.md) | Campos, mockups de output e comportamento esperado |
| [`docs/SBWAA-APRESENTACAO.md`](docs/SBWAA-APRESENTACAO.md) | Visão geral do sistema: problema, solução, features |
| [`docs/SBWAA-MASTER-BLUEPRINT.md`](docs/SBWAA-MASTER-BLUEPRINT.md) | Guia completo de reconstrução do sistema do zero |
| [`docs/SBWAA-GLOSSARIO.md`](docs/SBWAA-GLOSSARIO.md) | ~80 termos técnicos: métricas quant, agentes, comandos |
| [`CHANGELOG.md`](CHANGELOG.md) | Histórico completo de versões |

---

## Compatibilidade

- **Windows 10/11** — testado, PowerShell nativo
- **macOS / Linux** — compatível (substituir comandos PowerShell por equivalentes bash; Task Scheduler → cron)
- **Obsidian** — recomendado para visualizar o vault com graph view e templates
