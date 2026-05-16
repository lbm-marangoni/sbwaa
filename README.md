# SBWAA — Second Brain Wealth + Asset + Assessor Individual

> Sistema multi-agente de gestão de portfólio e análise de ativos financeiros.
> Operação 100% local. Dados 100% privados. Motor de IA: Claude Code.

**Versão:** v2.2.3 | **Python:** 3.11+ | **Plataforma:** Windows (PowerShell)

---

## O que é

SBWAA é um sistema pessoal que combina 7 agentes de IA especializados, pipeline de dados de mercado, base de conhecimento RAG e painel visual para análise e gestão de portfólio de investimentos.

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

# Abrir painel visual (customtkinter)
python sbwaa.py /ui
```

**No chat do Claude Code** (abrir a pasta do projeto no Claude Code):

```
/morning-call          # briefing pré-abertura com macro + alertas
/analisar PETR4        # pipeline completo de análise (8 etapas, ~15 min)
/tese VALE3            # análise rápida com DCF e veredicto do PM
```

---

## Estrutura do projeto

```
sbwaa/
├── sbwaa.py                  ← ponto de entrada de todos os comandos
├── ui.py                     ← painel visual (customtkinter)
├── requirements.txt
├── .env.template
├── CLAUDE.md                 ← políticas globais e roteamento de agentes
├── GUIA-COMANDOS.md          ← referência completa de todos os comandos
├── VERSION.md
├── CHANGELOG.md
│
├── .claude/
│   ├── agents/               ← 7 agentes especializados (SKILL.md + runner)
│   └── commands/             ← scripts dos comandos locais
│
├── scripts/
│   ├── data/                 ← fetch Brapi (BR) e Yahoo Finance (macro)
│   ├── alerts/               ← 8 tipos de alerta automático
│   └── heartbeat/            ← processo diário automatizado
│
├── knowledge/                ← base RAG (ChromaDB + sentence-transformers)
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

## Os 7 agentes

| Agente | Modelo | Função |
|--------|--------|--------|
| Market Researcher | Sonnet | Análise macro, setorial e posicionamento |
| Earnings Reviewer | Sonnet | Revisão de resultados trimestrais |
| Model Builder | Opus | Construção de DCF e modelos de valuation |
| Valuation Reviewer | Sonnet | Revisão crítica do modelo, equity research |
| Quant / Data Eng. | Sonnet | Sharpe, VaR, correlação, métricas quant |
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

→ [`GUIA-COMANDOS.md`](GUIA-COMANDOS.md)

---

## Compatibilidade

- **Windows 10/11** — testado, PowerShell nativo
- **macOS / Linux** — compatível (substituir comandos PowerShell por equivalentes bash)
- **Obsidian** — opcional, mas recomendado para visualizar o vault com graph view
