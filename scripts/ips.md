---
tags: [portfolio, ips, perfil]
cssclasses: [node-portfolio]
atualizado: 2026-05-16
---

# IPS — Investment Policy Statement

## Perfil do Investidor

- **Horizonte:** 10–30 anos (acumulação para independência financeira)
- **Tolerância ao risco:** Moderado-Arrojado
- **Objetivo principal:** Equilíbrio crescimento + renda (DY elevado via FIIs, crescimento via ações)
- **Restrições:** Sem derivativos, alavancagem ou ativos exóticos

## Alocação Alvo

| Classe          | Alvo (%) | Mín (%) | Máx (%) |
|-----------------|----------|---------|---------|
| Ações BR        | 25       | 20      | 30      |
| FIIs            | 35       | 30      | 40      |
| Renda Fixa      | 20       | 15      | 25      |
| ETFs Internac.  | 8        | 3       | 13      |
| Tesouro Direto  | 12       | 7       | 17      |

> Renda Fixa serve como: reserva de oportunidade + metas de liquidez (viagens, compras planejadas).
> Tesouro Direto IPCA+ reservado para acumulação de longo prazo / aposentadoria.
> Banda de rebalanceamento: ±5% do alvo → sistema sugere ajuste quando ultrapassado.

## Limites de Risco

- **VaR máximo (95%, 1 dia):** 2%
- **Drawdown máximo tolerado:** 18%
- **Concentração máxima por ativo:** 20%

## Metas Financeiras

As metas de longo prazo são definidas separadamente em [[metas]] e **não influenciam as decisões de análise** — servem apenas como painel de acompanhamento pessoal.

| Meta | Arquivo | Calculado por |
|------|---------|---------------|
| Renda passiva mensal | [[metas]] | Automático (dividendos da carteira) |
| Reserva de emergência | [[metas]] | Automático (saldo RF + TD) |
| Patrimônio total | [[metas]] | Automático (valor total da carteira) |
| Metas livres (viagens, etc.) | [[metas]] | Manual (campo `atual` no arquivo) |

> Para ver o progresso: `/metas` (dashboard completo) ou `/morning-call` (resumo diário compacto).

## Notas de Calibração

- VaR 2%: calibrado para alertar apenas em stress real — portfólio esperado (~10-12% vol anual) gera VaR ~1.0-1.3%/dia em condições normais
- Drawdown 18%: acionaria em crise severa tipo COVID-2020 (~-16%) mas não em volatilidade normal
- Concentração 20%: mínimo de 5 posições com peso relevante; alertas automáticos se uma posição crescer além por apreciação
- FIIs 35% alvo: DY esperado 8-10% a.a., volatilidade menor que ações (~12% a.a.), proteção implícita a inflação via aluguéis
