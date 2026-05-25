---
description: Revisão de resultados trimestrais de um ativo
---

# /earnings $ARGUMENTS

Revisão de earnings para **$ARGUMENTS**.

## Passo 1 — Coletar dados

```powershell
$env:PYTHONUTF8 = "1"; cd "C:\Users\lbmma\Downloads\Local\SBWAA"
python scripts/data/fetch_fundamentals.py $ARGUMENTS
```

Leia `scripts/data/cache/fundamentals_$ARGUMENTS_*.json`.

## Passo 2 — Análise

Leia `.claude/agents/earnings-reviewer/SKILL.md` e produza:

**Resultado do Trimestre**
- Receita líquida: R$ X bi (+/-Y% a/a)
- EBITDA ajustado: R$ X bi, margem Y%
- Lucro líquido: R$ X bi (+/-Y% a/a)
- FCL: R$ X bi
- Dívida líquida / EBITDA: X×

**Qualidade dos Resultados**
- Recorrente ou com itens extraordinários?
- Tendência: acelerando / estável / deteriorando
- Surpresa vs estimativas: positiva / em linha / negativa

**Pontos de Atenção**
- Máximo 3 bullets com os fatos mais relevantes do trimestre

**Impacto no Valuation**
- Precisaria rever o DCF? Em qual direção?

## Passo 3 — Salvar

Salve em `vault/01-ativos/$ARGUMENTS/earnings-$ARGUMENTS-YYYY-MM-DD.md` com wikilinks.
