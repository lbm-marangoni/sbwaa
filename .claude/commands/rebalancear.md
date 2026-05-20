---
description: Sugestão de rebalanceamento da carteira vs metas do IPS + fronteira eficiente
---

# /rebalancear

## Passo 1 — Coletar dados

```powershell
$env:PYTHONUTF8 = "1"; cd "C:\Users\lbmma\Downloads\Local\SBWAA"
python scripts/data/update_carteira.py
python .claude/agents/quant-data-engineer/run_quant.py
```

Leia:
- `vault/00-portfolio/carteira.md` — posições e pesos atuais
- `vault/00-portfolio/ips.md` — alocação alvo por classe e bandas
- Cache quant mais recente em `scripts/data/cache/quant_YYYY-MM-DD.json`
  — campos relevantes: `otimizacao.max_sharpe`, `otimizacao.min_vol`,
    `otimizacao.ajustes_sugeridos`, `otimizacao.ganho_sharpe_potencial`,
    `pares_alta_correlacao`, `contribuicao_risco`
- Cache de expansão (se disponível) em `scripts/data/cache/optim_expansao_YYYY-MM-DD.json`
  — campos: `fronteira_base`, `fronteira_expandida`, `ganho_sharpe_expansao`,
    `candidatos` (ranking watchlist com classificação MELHORA/NEUTRO/PIORA)

## Passo 2 — Análise de Rebalanceamento

Leia `.claude/agents/portfolio-manager/SKILL.md`.

**Alocação Atual vs Alvo (IPS)**

| Classe | Alvo % | Mín % | Máx % | Atual % | Desvio | Status |
|--------|--------|--------|--------|---------|--------|--------|
| Ações BR | | | | | | |
| FIIs | | | | | | |
| Renda Fixa | | | | | | |
| ETFs Intl | | | | | | |
| Tesouro Direto | | | | | | |

Status: ✅ OK / ⚠️ Fora da banda / 🚨 Violação do IPS

**Ações Sugeridas (desvio vs IPS)**

Para cada classe fora da banda:
- O que fazer (aportar / reduzir / aguardar aporte)
- Quanto (em % do portfólio ou R$ normalizados)
- Qual ativo dentro da classe priorizar e por quê

**Posição na Fronteira Eficiente**

Use os dados de `otimizacao` do cache quant para apresentar:
- Sharpe atual vs Max Sharpe possível (e o ganho potencial)
- Volatilidade atual vs Min Vol possível
- Top 3–5 ajustes de peso sugeridos para aproximar do portfólio Max Sharpe,
  com conflito ou alinhamento vs IPS explicitado para cada um
- Se o ajuste de otimização conflitar com o IPS (ex: concentraria demais
  num ativo), alertar e sugerir alternativa dentro das bandas

**Correlações e diversificação**

- Pares com correlação > 0.7 (leia `pares_alta_correlacao` do cache)
- Qual par mais reduz diversificação real e o que fazer a respeito

**Candidatos da watchlist (se cache de expansão disponível)**

Se `optim_expansao_YYYY-MM-DD.json` existir:
- Liste os candidatos classificados MELHORA com ticker, delta Sharpe e peso sugerido
- Destaque o ganho potencial de Sharpe ao incluir os melhores (vs fronteira base)
- Sinalize se algum candidato MELHORA já foi analisado recentemente (frescor) — esses
  são os mais prontos para uma decisão; os sem análise recente pedem /analisar primeiro

**Regras do IPS a respeitar:**
- Não sugerir alavancagem nem derivativos
- Concentração máxima por ativo: 20%
- Só sugerir redução se desvio for > 5% do alvo
- Otimização é referência quantitativa — decisão final respeita sempre o IPS

**Observação final:** rebalanceamento é sugestão — decisão final é sempre do investidor.

Não salva arquivo — resposta direta no chat.
