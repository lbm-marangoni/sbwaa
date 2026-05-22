# SBWAA — Second Brain Wealth + Asset + Assessor Individual

> Sistema multi-agente de gestão de portfólio e análise de ativos financeiros.
> Operação 100% local. Dados 100% privados. Motor de IA: Claude Code.

**Versão:** v2.8.8 | **Python:** 3.11+ | **Plataforma:** Windows (PowerShell)

---

## O que é

SBWAA é um sistema pessoal que combina 8 agentes de IA especializados, pipeline de dados de mercado, base de conhecimento RAG (ativa em todos os agentes) e painel visual para análise e gestão de portfólio de investimentos.

O sistema opera em dois modos:
- **Claude Code** (padrão) — sem API key, comandos de IA rodam diretamente no chat
- **API** — com `ANTHROPIC_API_KEY` configurada, agentes executam via subprocess

---

## Pré-requisitos

| Ferramenta | Versão mínima | Obrigatório |
|------------|---------------|-------------|
| Python | 3.11+ | Sim |
| Claude Code | qualquer | Sim |
| PowerShell | 5.1+ | Sim (Windows) |
| Obsidian | qualquer | Não (vault funciona sem) |

**Instalar Claude Code:**
```powershell
npm install -g @anthropic-ai/claude-code
```
Ou baixe o instalador em: https://claude.ai/download

---

## Instalação

### 1. Clonar o repositório

```powershell
git clone https://github.com/SEU_USUARIO/sbwaa.git
cd sbwaa
```

### 2. Criar ambiente virtual (recomendado)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

> Se o PowerShell bloquear a execução de scripts, rode antes:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### 3. Instalar dependências

```powershell
pip install -r requirements.txt
```

### 4. Configurar API key (opcional — só para Modo API)

```powershell
Copy-Item ".env.template" ".env"
notepad ".env"    # substituir 'sua_chave_aqui' pela ANTHROPIC_API_KEY
```

Sem API key, todos os comandos locais funcionam. Comandos de IA rodam no chat do Claude Code.

### 5. Criar os arquivos do seu portfólio

O sistema gerencia três arquivos em `vault/00-portfolio/`. Eles não vêm no repositório pois contêm dados pessoais — você os cria ao registrar seus primeiros ativos:

```powershell
# UTF-8 no terminal (rodar uma vez por sessão no Windows)
$env:PYTHONUTF8 = "1"

# Verificar se o sistema está ok
python sbwaa.py /status

# Adicionar seu primeiro ativo (cria os arquivos automaticamente)
python sbwaa.py /adicionar --ticker PETR4 --tipo acao-on --quantidade 100 --preco-medio 38.50 --setor energia
```

Os arquivos criados serão:
- `vault/00-portfolio/carteira.md` — posições e cotações
- `vault/00-portfolio/historico-trades.md` — log de operações
- `vault/00-portfolio/decisoes.md` — log de decisões do PM

### 6. Configurar o IPS (Investment Policy Statement)

O IPS define suas metas de alocação e limites de risco. Crie o arquivo manualmente:

```powershell
python sbwaa.py /ips --editar
```

Estrutura mínima do `vault/00-portfolio/ips.md`:

```markdown
# IPS — Investment Policy Statement

## Perfil
- Horizonte: longo prazo (10+ anos)
- Tolerância a risco: moderada

## Alocação alvo
| Classe       | Alvo % | Mín % | Máx % |
|--------------|--------|--------|--------|
| Ações        | 40     | 30     | 50     |
| FIIs         | 35     | 25     | 45     |
| ETFs Intl    | 15     | 10     | 25     |
| Renda Fixa   | 10     | 5      | 20     |

## Limites de risco
- VaR diário 95%: máx 2%
- Drawdown máximo: 18%
- Concentração máxima por ativo: 20%
```

---

## Primeiros passos após instalar

```powershell
# Ver todos os comandos disponíveis
python sbwaa.py /help

# Snapshot de mercado (IBOV, S&P500, câmbio, juros)
python sbwaa.py /snapshot

# Ver posições da carteira com P&L atualizado
python sbwaa.py /carteira

# Ver watchlist + veredictos e frescor das análises
python sbwaa.py /watchlist

# Risco: VaR, CVaR, Sharpe, Fronteira Eficiente Markowitz
python sbwaa.py /risco-carteira

# Fronteira dual: carteira vs carteira + watchlist (candidatos MELHORA/NEUTRO/PIORA)
python sbwaa.py /otimizar-expansao

# Abrir painel visual (customtkinter)
python sbwaa.py /ui
```

**No chat do Claude Code** (abrir a pasta do projeto no Claude Code):

```
/morning-call          # briefing pré-abertura com macro + alertas
/analisar PETR4        # pipeline completo de análise (8 agentes, 10 etapas)
/tese VALE3            # análise rápida com DCF e veredicto do PM
/revisar-carteira      # PM revisa todas as posições: MANTER/AUMENTAR/REDUZIR/SAIR
/rebalancear           # desvios vs IPS e sugestão de ajuste de alocação
```

**Workflow operacional completo** (cadências diária, semanal, mensal, trimestral, anual):

→ [`docs/SBWAA-WORKFLOW.md`](docs/SBWAA-WORKFLOW.md)

---

## Configuração guiada (Setup Wizard)

Após clonar e instalar as dependências, cole o prompt abaixo no chat do Claude Code com a pasta do projeto aberta. Ele mapeia tudo que precisa ser configurado manualmente e conduz um formulário interativo — uma pergunta por vez.

Para o IPS especificamente, o fluxo é mais cuidadoso: explica cada métrica com benchmarks de mercado brasileiro, faz perguntas qualitativas sobre o seu perfil e só sugere números depois de entender suas respostas.

```
Quero configurar o SBWAA do zero.

Antes de começar, leia os arquivos de configuração do sistema
(.env.template, knowledge/sources/sources.json,
scripts/alerts/check_alerts.py e CLAUDE.md) para mapear tudo
que pode ser configurado manualmente.

Depois conduza um formulário interativo comigo — uma pergunta
por vez, aguardando minha resposta antes de avançar — cobrindo
nesta ordem:

1. API Key — modo Claude Code (padrão, sem key) vs modo API
   (agentes autônomos via subprocess, precisa de ANTHROPIC_API_KEY)

2. Feeds RSS — fontes de notícias da base de conhecimento:
   quais manter, quais adicionar, volume por coleta e idioma

3. Thresholds de alerta — revise comigo os valores atuais de
   queda/alta de ativo e correlação, explicando o que cada um
   dispara antes de perguntar se quero ajustar

4. IPS completo — para este item seja mais cuidadoso:
   explique cada métrica com contexto e benchmarks de mercado
   brasileiro (IBOV histórico, CDI, volatilidade típica por
   classe), faça perguntas qualitativas sobre meu perfil antes
   de sugerir qualquer número. Cubra em sequência: horizonte de
   investimento, alocação alvo por classe (% alvo + mín + máx),
   VaR máximo diário 95%, drawdown máximo tolerado e
   concentração máxima por ativo.

Ao final de cada etapa, salve as configurações nos arquivos
corretos. Para o IPS, gere o vault/00-portfolio/ips.md completo.
```

---

## Estrutura do projeto

```
sbwaa/
├── sbwaa.py                  ← ponto de entrada de todos os comandos
├── requirements.txt
├── .env.template
├── CLAUDE.md                 ← políticas globais e roteamento de agentes
├── VERSION.md
├── CHANGELOG.md
│
├── docs/                     ← documentação do projeto
│   ├── GUIA-COMANDOS.md      ← referência completa de comandos, flags e exemplos
│   ├── SBWAA-WORKFLOW.md     ← workflow operacional: 6 cadências + fluxos oportunísticos
│   ├── SBWAA-REFERENCIA.md   ← campos, mockups de output e comportamento esperado
│   ├── SBWAA-MASTER-BLUEPRINT.md
│   └── SBWAA-LOGO.md
│
├── interface/                ← painel visual (customtkinter)
│   ├── ui.py
│   └── splash.py
│
├── .claude/
│   ├── agents/               ← 8 agentes especializados (SKILL.md + runner)
│   │   └── quant-data-engineer/calculators/optimization.py  ← Fronteira Eficiente (Markowitz)
│   └── commands/             ← scripts dos comandos locais
│
├── scripts/
│   ├── data/                 ← fetch Brapi (BR), Yahoo Finance (macro), optimize_expansao.py
│   ├── alerts/               ← 8 tipos de alerta automático
│   └── heartbeat/            ← processo diário automatizado
│
├── knowledge/                ← base RAG (ChromaDB + sentence-transformers)
├── prompts/                  ← histórico de prompts de construção do sistema
├── _standby/                 ← código arquivado (interface Streamlit legada)
│
└── vault/                    ← notas Obsidian
    ├── 00-portfolio/         ← carteira, IPS, trades (dados pessoais — não versionados)
    ├── 01-ativos/            ← teses, DCFs e earnings por ticker
    ├── 02-relatorios/        ← diários, semanais e mensais
    ├── 03-macro/             ← notas do Market Researcher
    ├── 04-knowledge/         ← sínteses RAG
    └── 05-risk/              ← snapshots de risco quantitativo
```

---

## Os 8 agentes

| Agente | Modelo | Função |
|--------|--------|--------|
| Market Researcher | Sonnet | Análise macro, setorial e posicionamento |
| Earnings Reviewer | Sonnet | Revisão de resultados trimestrais |
| Model Builder | Opus | Construção de DCF e modelos de valuation |
| Valuation Reviewer | Sonnet | Revisão crítica do modelo, equity research |
| Quant / Data Eng. | Sonnet | Sharpe, VaR, correlação, métricas quant |
| Econometrician | Sonnet | GARCH, beta dinâmico, Fama-French 3F, macro BCB, drawdown avançado |
| Risk Engineer | Opus | VaR, CVaR, stress tests, circuit breakers |
| Portfolio Manager | Opus | Decisão final: COMPRAR / AGUARDAR / EVITAR |

---

## Segurança

- Dados de portfólio (posições, preço médio, patrimônio) **nunca saem do vault local**
- APIs externas recebem apenas tickers públicos, datas e parâmetros de mercado
- Sizing do PM é calculado localmente — a API recebe apenas pesos percentuais
- Arquivos pessoais estão no `.gitignore` e nunca são versionados

Política completa: [`CLAUDE.md`](CLAUDE.md) — seção Security Policy.

---

## Referência de comandos

Documentação completa de todos os comandos, flags e exemplos de uso:

→ [`docs/GUIA-COMANDOS.md`](docs/GUIA-COMANDOS.md)

---

## Compatibilidade

- **Windows 10/11** — testado, PowerShell nativo
- **macOS / Linux** — compatível (substituir comandos PowerShell por equivalentes bash)
- **Obsidian** — opcional, mas recomendado para visualizar o vault com graph view
