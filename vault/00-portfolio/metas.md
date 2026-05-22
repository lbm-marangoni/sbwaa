---
tags: [portfolio, metas, objetivos]
cssclasses: [node-portfolio]
atualizado: 2026-05-22
---

# Metas Financeiras

> Este arquivo é lido pelo comando `/metas` e pelo `/morning-call`.
> Os agentes de análise (Market Researcher, PM, etc.) **não leem este arquivo** —
> as metas são puramente informativas e não influenciam nenhuma decisão de investimento.
>
> Edite os valores diretamente aqui. Para metas livres, atualize o campo `atual`
> manualmente conforme for acumulando.

---

## Renda Passiva Mensal

> Calculado automaticamente a partir dos dividendos reais da carteira (DPA × cotas).

```
alvo_mensal: 3000        # R$/mês — meta de renda passiva recorrente
data_alvo: 2028-12-31    # opcional — deixe vazio se não tiver prazo
```

---

## Reserva de Emergência

> Calculado automaticamente: soma dos ativos de tipo renda-fixa e tesouro na carteira.

```
alvo: 50000              # R$ total mantido em RF + TD
data_alvo:               # opcional
```

---

## Patrimônio Total

> Calculado automaticamente: valor total da carteira (todas as classes).

```
alvo: 500000             # R$ total investido
data_alvo: 2030-12-31    # opcional
```

---

## Metas Livres

> Atualize o campo `atual` manualmente conforme for acumulando para cada meta.
> O campo `classe` indica em qual classe do IPS o capital está sendo guardado
> (ex: renda-fixa, tesouro). Deixe vazio se não estiver segmentado.

```yaml
metas_livres:
  - nome: "Viagem Europa"
    alvo: 15000
    atual: 0              # atualizar manualmente
    data_alvo: 2027-06-30
    classe: renda-fixa    # onde o dinheiro está guardado (opcional)
    notas: ""

  # Para adicionar mais metas, copie o bloco acima e edite os valores.
  # Exemplo:
  # - nome: "Entrada Imóvel"
  #   alvo: 80000
  #   atual: 12000
  #   data_alvo: 2029-01-01
  #   classe: tesouro
  #   notas: "TD IPCA+ 2029"
```

---

## Links

- [[ips]] — Investment Policy Statement (alocação alvo e limites de risco)
- [[carteira]] — Posições atuais e P&L
