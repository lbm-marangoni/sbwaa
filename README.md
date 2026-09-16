# SBWAA
### Investment Research & Portfolio Decision-Support System

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![Investment Research](https://img.shields.io/badge/Investment-Research-0D1E35)
![Portfolio Analysis](https://img.shields.io/badge/Portfolio-Analysis-0D1E35)
![AI Assisted](https://img.shields.io/badge/AI-Assisted-0D1E35)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

---

## Overview

**SBWAA** is a personal investment research and portfolio decision-support system designed to connect:

**company analysis → valuation → portfolio context → decision support → monitoring**

within a single structured workflow.

The project was built around a simple question:

> How can an individual investor organize the different stages of an investment process — research, valuation, macro context, risk, portfolio construction and monitoring — into one coherent system?

Rather than treating each analysis independently, SBWAA connects different parts of the investment process through a modular architecture supported by **Python, financial data, AI-assisted research and a persistent investment knowledge base**.

The system is not intended to replace investment judgment.

Its purpose is to **organize information, structure analysis, challenge assumptions and improve the consistency of the decision-making process**.

---

# Investment Framework

SBWAA is structured around three core layers.

## 1. Company Analysis

The first layer focuses on understanding the underlying asset.

The workflow can incorporate:

- financial statement analysis
- business model and industry research
- competitive positioning
- earnings analysis
- macroeconomic and sector context
- valuation through DCF and market multiples
- investment thesis development
- identification of risks and catalysts

The goal is not simply to produce a price target, but to build a structured view of:

**what drives the business, what the market may be pricing, what could change the thesis and where the main risks lie.**

---

## 2. Portfolio Thinking

An investment idea is evaluated not only in isolation, but also in the context of the portfolio.

SBWAA incorporates portfolio-level analysis such as:

- return and volatility
- correlation
- beta
- drawdown
- diversification
- allocation
- portfolio constraints
- risk limits
- stress scenarios
- position sizing context
- benchmark comparison

The portfolio layer is also connected to an **Investment Policy Statement (IPS)** containing allocation targets and risk constraints.

This allows the system to distinguish between:

> “Is this asset attractive?”

and

> “Does this asset improve the portfolio?”

---

## 3. Investment Judgment

The final layer focuses on structuring the decision itself.

SBWAA combines research outputs, valuation, portfolio context, risk and existing investment theses to support decisions such as:

- investigate further
- initiate or increase a position
- maintain exposure
- reduce exposure
- exit
- wait for a better entry point

The purpose is not to automate conviction.

Instead, the system creates a **repeatable decision process** where assumptions, evidence and previous decisions can be reviewed over time.

---

# Investment Workflow

```text
                MARKET & MACRO CONTEXT
                         │
                         ▼
                 COMPANY RESEARCH
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
       FUNDAMENTALS                 EARNINGS
            │                         │
            └────────────┬────────────┘
                         ▼
                     VALUATION
                         │
                         ▼
                 INVESTMENT THESIS
                         │
                         ▼
                 PORTFOLIO CONTEXT
          risk • allocation • correlation
                         │
                         ▼
                  DECISION SUPPORT
                         │
                         ▼
                MONITORING & REVIEW
                         │
                         ▼
                INVESTMENT JOURNAL
```

The central idea is that each stage produces information used by the next one.

Research therefore becomes a continuous process rather than a collection of disconnected analyses.

---

# System Architecture

At a high level, SBWAA combines four components:

```text
┌─────────────────────────────────────────────┐
│                 DATA INPUTS                 │
│                                             │
│ Market data • Fundamentals • News • Macro  │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│              RESEARCH LAYER                 │
│                                             │
│ Company • Sector • Earnings • Valuation    │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│             PORTFOLIO LAYER                 │
│                                             │
│ Risk • Allocation • IPS • Stress Testing   │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│              DECISION LAYER                 │
│                                             │
│ Thesis • Monitoring • Review • Decisions   │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│            KNOWLEDGE SYSTEM                 │
│                                             │
│ Obsidian • Reports • History • Research    │
└─────────────────────────────────────────────┘
```

Python handles data collection, portfolio calculations, risk analysis, automation and system orchestration.

AI-assisted components support research synthesis, valuation review, earnings analysis and structured decision workflows.

The resulting research is stored in a persistent knowledge base so previous assumptions and decisions remain available for future review.

---

# Research Modules

The current architecture contains specialized components for different stages of the investment process.

| Module | Role |
|---|---|
| **Market & Company Research** | Macro environment, sector analysis, competitors and market context |
| **Earnings Review** | Revenue, margins, guidance and quarterly performance |
| **Valuation** | DCF and market-multiple analysis |
| **Valuation Review** | Challenges assumptions and reviews valuation outputs |
| **Quant & Data** | Returns, volatility, beta and correlation |
| **Econometrics** | Additional statistical and time-series analysis |
| **Portfolio Risk** | VaR, CVaR, drawdown, stress testing and portfolio limits |
| **Portfolio Decision Support** | Integrates research, valuation, portfolio context and existing theses |

These modules were implemented as specialized AI-assisted agents in the current version of the system.

The investment process remains the organizing layer above them.

---

# Portfolio & Risk Analysis

SBWAA includes tools for studying the portfolio beyond individual security selection.

Examples include:

### Risk metrics

- Value at Risk
- Conditional Value at Risk
- volatility
- Sharpe ratio
- beta
- maximum drawdown
- correlation analysis

### Portfolio analysis

- asset allocation
- diversification
- benchmark comparison
- allocation deviations versus IPS
- portfolio expansion analysis
- efficient-frontier experiments

### Stress testing

The system can simulate different market scenarios and estimate their potential effect on the portfolio.

These tools are used as **decision inputs**, rather than mechanical trading rules.

---

# Fundamental Research

Individual assets can be analyzed through a structured research workflow.

A complete analysis can combine:

```text
Company
   ↓
Industry
   ↓
Financial Performance
   ↓
Competitive Position
   ↓
Earnings
   ↓
Valuation
   ↓
Risks & Catalysts
   ↓
Investment Thesis
   ↓
Portfolio Context
```

Research outputs are stored so that the original assumptions can later be compared with actual developments.

This makes the system useful not only for generating investment ideas, but also for studying **how those ideas evolve over time**.

---

# Investment Knowledge Base

SBWAA uses an Obsidian-based research vault to maintain a persistent history of investment work.

```text
vault/
│
├── portfolio/
│   ├── positions
│   ├── IPS
│   ├── trades
│   └── goals
│
├── assets/
│   └── ticker/
│       ├── thesis
│       ├── valuation
│       ├── earnings
│       └── decision history
│
├── reports/
│   ├── daily
│   ├── weekly
│   └── monthly
│
├── macro/
│
├── decisions/
│
└── risk/
```

Analyses are linked across the vault, creating a connected research history rather than isolated files.

This structure allows previous:

- theses
- valuation assumptions
- earnings reviews
- portfolio decisions
- risk snapshots

to be revisited later.

---

# Monitoring & Automation

SBWAA also includes automated workflows for maintaining the research environment.

Typical scheduled tasks include:

### Before market hours

```text
Market data update
        ↓
News collection
        ↓
Portfolio snapshot
        ↓
Risk metrics
        ↓
Alerts
        ↓
Morning research briefing
```

### End of day

```text
Market close data
        ↓
Portfolio update
        ↓
Performance analysis
        ↓
Risk snapshot
        ↓
Monitoring alerts
```

### Weekly / Monthly

The system can generate recurring portfolio reports covering:

- portfolio performance
- risk
- thesis monitoring
- macro context
- upcoming events
- potential areas requiring further research

Automation is executed locally through the operating system scheduler.

---

# Example Workflows

## Researching a Company

```text
/analisar WEGE3
```

The workflow can combine:

```text
Company research
      ↓
Industry analysis
      ↓
Earnings
      ↓
Valuation
      ↓
Risk review
      ↓
Portfolio context
      ↓
Structured decision output
```

---

## Reviewing an Existing Position

```text
/pm TICKER
```

The system retrieves the existing research history and combines it with updated information before generating a structured review.

---

## Portfolio Review

```text
/revisar-carteira
```

The portfolio workflow reviews current positions in the context of:

- investment thesis
- valuation
- portfolio allocation
- portfolio risk
- IPS limits

---

## Risk Analysis

```text
/risco-carteira
```

Produces a portfolio-level risk snapshot with metrics such as volatility, beta, drawdown and other risk measures.

---

# Selected Capabilities

SBWAA currently includes workflows for:

**Investment Research**

`company research` · `sector analysis` · `earnings` · `valuation` · `investment theses`

**Portfolio Analysis**

`allocation` · `correlation` · `risk` · `stress testing` · `portfolio constraints`

**Monitoring**

`watchlists` · `alerts` · `earnings calendar` · `daily snapshots`

**Reporting**

`morning briefings` · `weekly reviews` · `monthly reviews`

**Data & Automation**

`market data` · `fundamentals` · `news collection` · `scheduled workflows`

---

# Technology

The project currently uses:

### Core

- Python
- Pandas
- NumPy
- financial market data APIs
- Windows Task Scheduler

### Research & Knowledge

- AI-assisted research workflows
- Obsidian
- local research vault
- RAG-based document retrieval

### Analysis

- fundamental analysis
- valuation workflows
- portfolio analytics
- risk metrics
- statistical analysis

Technology is intentionally treated as **infrastructure for the investment process**, rather than the objective of the project itself.

---

# Repository Structure

```text
sbwaa/
│
├── sbwaa.py
│
├── interface/
│
├── scripts/
│   ├── data/
│   ├── alerts/
│   ├── risk/
│   └── automation/
│
├── .claude/
│   └── agents/
│
├── knowledge/
│
├── prompts/
│
├── docs/
│
└── vault/
```

The repository separates:

- investment logic
- data pipelines
- research workflows
- automation
- knowledge storage
- user interface

into independent components.

---

# Running the Project

## Requirements

- Python 3.11+
- Windows
- PowerShell
- Claude Code for AI-assisted workflows
- Obsidian recommended for research visualization

Clone the repository:

```powershell
git clone https://github.com/lbm-marangoni/sbwaa.git
cd sbwaa
```

Create the environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Check the system:

```powershell
python sbwaa.py /status
```

Available commands can be viewed with:

```powershell
python sbwaa.py /help
```

---

# Privacy

Personal portfolio information is intentionally separated from the public repository.

Portfolio positions, average prices, personal allocation data and other private investment records are excluded from version control.

The public repository contains the system architecture and implementation without exposing the owner's personal portfolio.

---

# Project Philosophy

SBWAA began as an attempt to build better tools for managing a personal investment portfolio.

Over time, the project evolved into an experiment in **investment process design**.

The most important question became less:

> “Can I automate this analysis?”

and more:

> **“What information should actually influence an investment decision, and how should those pieces interact?”**

This led to the development of a system that combines:

**company analysis**

+

**portfolio thinking**

+

**investment judgment**

with technology acting as the connecting layer.

---

# What I Learned

Building SBWAA required thinking about more than code.

The project involved designing how different areas of investing interact:

- how macro conditions affect companies
- how company research becomes an investment thesis
- how valuation affects expected return
- how an attractive asset can still be inappropriate for a portfolio
- how risk should influence position sizing
- how assumptions should be monitored after an investment is made
- how previous decisions can be reviewed to improve future ones

The project therefore became both a technical system and a practical laboratory for developing a more structured investment process.

---

# Current Status

SBWAA is an ongoing personal research project.

The current implementation covers a broad range of investment workflows, but many modules remain experimental and continue to evolve as the underlying investment framework becomes more rigorous.

Future development is focused less on adding features and more on improving:

- financial modeling quality
- fundamental research depth
- valuation methodology
- portfolio construction
- decision documentation
- post-investment review

---

# Disclaimer

SBWAA is a personal educational and research project.

Nothing generated by the system should be interpreted as financial advice, an investment recommendation or a substitute for independent analysis.

Models, valuation outputs, risk estimates and AI-generated research may contain errors and should always be independently reviewed.

---

## Author

**Lucas Marangoni**

Economics @ FAAP  
Performance & Insights @ Bradesco  
Research @ FAAP Finance

Asset Management • Equity Research • Investment Analysis

[LinkedIn](https://www.linkedin.com/in/lbm-marangoni)
