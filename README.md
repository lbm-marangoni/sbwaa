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
