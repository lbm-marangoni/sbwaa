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

Salve em `vault/01-ativos/$ARGUMENTS/tese-rapida-$ARGUMENTS-YYYY-MM-DD.md` usando o template `vault/_templates/tese-ativo.md` como base. Preencher TODAS as seções do template. Não criar seções extras fora do template.

Regras obrigatórias para a seção **Preço Teto / Nível de Entrada**:
- Usar vírgula como separador decimal (R$ XX,XX — padrão BR)
- `**Preço teto (Bazin DY 8% / Graham):** R$ XX,XX` — se não aplicável, indicar N/A com justificativa
- `**Preço chão (Bazin DY 12%):** R$ XX,XX` — somente FII
- `**Valor justo (base):** R$ XX,XX — upside +X%`
- `**Valor justo (pessimista):** R$ XX,XX — downside -X%`

## Passo 5 — Registrar alertas de preço

Após salvar a tese, executar:

```powershell
$env:PYTHONUTF8 = "1"; python scripts/alerts/extract_targets.py --ticker $ARGUMENTS
```

> Se o comando falhar: ignorar silenciosamente e prosseguir.
