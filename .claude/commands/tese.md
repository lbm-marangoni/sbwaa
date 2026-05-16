---
description: Análise rápida de ativo — Research + DCF + decisão do PM sem API key
---

# /tese $ARGUMENTS

Análise rápida (3 etapas) para **$ARGUMENTS**. Mais veloz que /analisar, sem Quant/Risk detalhado.

## Passo 1 — Coletar dados

```powershell
$env:PYTHONUTF8 = "1"; cd "C:\Users\lbmma\Downloads\Local\SBWAA"
python scripts/data/fetch_brapi.py $ARGUMENTS
python scripts/data/fetch_yahoo.py --macro
```

Leia o cache gerado: `scripts/data/cache/brapi_$ARGUMENTS_*.json` e os `yahoo_*.json` do dia.

## Passo 2 — Research + Valuation

Leia `.claude/agents/market-researcher/SKILL.md`, `.claude/agents/model-builder/SKILL.md` e `.claude/agents/valuation-reviewer/SKILL.md`.

Produza em sequência:

**Research (5 bullets):** setor, posição competitiva, catalisadores, riscos, macro relevante.

**Valuation:**
- Múltiplos atuais vs histórico e peers (P/L, P/VP, EV/EBITDA ou P/FFO para FIIs)
- Preço-alvo simplificado com método escolhido e premissas explícitas
- Upside/downside vs cotação atual: **X%**
- Margem de segurança presente? Sim/Não

## Passo 3 — Decisão do Portfolio Manager

Leia `.claude/agents/portfolio-manager/SKILL.md`, `vault/00-portfolio/ips.md` e `vault/00-portfolio/carteira.md`.

Emita:
- **Veredicto:** COMPRAR / AGUARDAR / EVITAR
- **Sizing sugerido:** % do portfólio, se COMPRAR
- **Gatilho de entrada:** preço ou evento específico, se AGUARDAR
- **Razão principal:** 1 frase objetiva

## Passo 4 — Salvar

Salve em `vault/01-ativos/$ARGUMENTS/tese-rapida-$ARGUMENTS-YYYY-MM-DD.md` com wikilinks.
