---
description: Análise rápida de ativo — Research + DCF + decisão do PM sem API key
---

# /tese $ARGUMENTS

Análise rápida (3 etapas) para **$ARGUMENTS**. Mais veloz que /analisar, sem Quant/Risk detalhado.

## Passo 1 — Coletar dados

```powershell
$env:PYTHONUTF8 = "1"; cd "C:\Users\lbmma\Downloads\Local\SBWAA"
python scripts/data/fetch_fundamentals.py $ARGUMENTS
python scripts/data/fetch_investidor10.py $ARGUMENTS
python scripts/data/fetch_yahoo.py --macro
```

Leia o cache gerado: `scripts/data/cache/fundamentals_$ARGUMENTS_*.json` (campos `_i10_*` já enriquecidos) e os `yahoo_*.json` do dia.

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

Verificar antes de emitir o veredicto: **$ARGUMENTS já está na carteira?**
- **Não está** → Modo A: COMPRAR / AGUARDAR / EVITAR
- **Já está** → Modo B: AUMENTAR / MANTER / REDUZIR / SAIR
  Mostrar: `Posição atual: X.X% | P&L: +/-XX% → peso alvo: Y.Y%`

Emita:
- **Veredicto:** [conforme o modo acima]
- **Sizing:** % do portfólio (Modo A: aporte sugerido; Modo B: peso atual → alvo)
- **Gatilho:** preço ou evento, se AGUARDAR
- **Razão principal:** 1 frase objetiva com dado concreto

## Passo 4 — Salvar

Salve em `vault/01-ativos/$ARGUMENTS/tese-rapida-$ARGUMENTS-YYYY-MM-DD.md` usando o template `vault/_templates/tese-ativo.md` como base. Preencher TODAS as seções.

```markdown
---
tags: [ativo, tese, {tipo-lowercase}]
ticker: {TICKER}
tipo: {label do tipo conforme CLAUDE.md — ex: 🟩 FII}
setor: {setor}
data: {YYYY-MM-DD}
status: ativa
---

# Tese — {TICKER}

## Por que este ativo
{Setor/posição competitiva, vantagem, por que hoje — 3-5 linhas}

## Catalisadores
- {catalisador 1}
- {catalisador 2}
- {macro relevante}

## Riscos principais
- {risco 1}
- {risco 2}

## Preço teto / Nível de entrada
- **Método:** Gordon Growth / DCF simplificado / Graham / Bazin
- **Premissas:** taxa X%, g X%
- **Valor justo (base):** R$ XX,XX — upside +/-X%
- **Valor justo (pessimista):** R$ XX,XX
- **Preço teto (Graham/Bazin 8%):** R$ XX,XX
- **Preço chão (Bazin 12%):** R$ XX,XX (apenas FII)
- **Veredicto PM:** COMPRAR / AGUARDAR / EVITAR — sizing X%
- **Gatilho:** {preço ou evento se AGUARDAR}

## Condição de saída
- {stop de tese — preço, resultado, evento}

## Links
- [[carteira]]
- [[ips]]
```
