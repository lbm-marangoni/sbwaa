---
description: Sugestão de rebalanceamento da carteira vs metas do IPS
---

# /rebalancear

## Passo 1 — Coletar dados

```powershell
$env:PYTHONUTF8 = "1"; cd "C:\Users\lbmma\Downloads\Local\SBWAA"
python scripts/data/update_carteira.py
```

Leia:
- `vault/00-portfolio/carteira.md` — posições e pesos atuais
- `vault/00-portfolio/ips.md` — alocação alvo por classe e bandas

## Passo 2 — Análise de Rebalanceamento

Leia `.claude/agents/portfolio-manager/SKILL.md`.

**Alocação Atual vs Alvo**

| Classe | Alvo % | Mín % | Máx % | Atual % | Desvio | Status |
|--------|--------|--------|--------|---------|--------|--------|
| Ações BR | | | | | | |
| FIIs | | | | | | |
| Renda Fixa | | | | | | |
| ETFs Intl | | | | | | |
| Tesouro Direto | | | | | | |

Status: ✅ OK / ⚠️ Fora da banda / 🚨 Violação do IPS

**Ações Sugeridas**

Para cada classe fora da banda:
- O que fazer (aportar / reduzir / aguardar aporte)
- Quanto (em % do portfólio ou R$ normalizados)
- Qual ativo dentro da classe priorizar e por quê

**Regras do IPS a respeitar:**
- Não sugerir alavancagem nem derivativos
- Concentração máxima por ativo: 20%
- Só sugerir redução se desvio for > 5% do alvo

**Observação final:** rebalanceamento é sugestão — decisão final é sempre do investidor.

Não salva arquivo — resposta direta no chat.
