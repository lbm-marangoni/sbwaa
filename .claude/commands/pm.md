---
description: Decisão do Portfolio Manager para um ativo já analisado
---

# /pm $ARGUMENTS

Decisão final do Portfolio Manager para **$ARGUMENTS**.

Pressupõe que análise prévia já existe em `vault/01-ativos/$ARGUMENTS/`.

## Contexto a ler

Leia todos estes arquivos antes de responder:
- `vault/01-ativos/$ARGUMENTS/` — todos os `.md` existentes (tese, earnings, DCF, equity research)
- `vault/00-portfolio/carteira.md` — posição atual e pesos
- `vault/00-portfolio/ips.md` — perfil, limites de risco e alocação alvo
- `scripts/data/cache/risk_*.json` — métricas de risco da carteira (arquivo mais recente)
- `scripts/data/cache/quant_*.json` — métricas quantitativas (arquivo mais recente)
- `scripts/data/cache/fundamentals_$ARGUMENTS_*.json` — dados fundamentalistas atuais

## Instrução

Leia `.claude/agents/portfolio-manager/SKILL.md` e emita a decisão com:

1. **VEREDICTO:** COMPRAR / AGUARDAR / EVITAR (em destaque)
2. **Tese em 3 bullets:** por que este veredicto agora
3. **Sizing:** % sugerido do portfólio, posição atual vs alvo
4. **Nível de entrada:** preço máximo aceitável ou gatilho de evento
5. **Stop / Revisão:** condição que invalidaria a tese
6. **Adequação ao IPS:** confirmar que a operação respeita todos os limites

Seja direto. Nenhuma análise de ativo vale mais do que a adequação ao perfil do investidor.

## Passo 3 — Fluxo de Aporte (interativo)

Execute este fluxo **somente se o veredicto for COMPRAR, AUMENTAR ou MANTER**.
Se for AGUARDAR, EVITAR, REDUZIR ou SAIR: pular direto para o Passo 4.

---

### Etapa A — Intenção

Perguntar ao usuário:

> **Deseja realizar um aporte em $ARGUMENTS agora?**
> Responda **sim** para continuar ou **não** para encerrar.

Se **não**: registrar `aporte_planejado: —` e ir direto ao Passo 4.

---

### Etapa B — Valor do aporte

Se **sim**, perguntar:

> **Quanto deseja aportar em $ARGUMENTS? (R$)**
> Informe o valor em reais (ex: 1000, 2500.50).

---

### Etapa C — Validação do PM

Com o valor informado (`V`), calcular:

1. **Patrimônio de referência:** ler `vault/00-portfolio/carteira.md` → campo `Patrimônio Total`.
   - Se patrimônio = 0 ou carteira vazia: usar R$ 100.000 como base normalizada e indicar isso.
2. **% do portfólio resultante:** `V / Patrimônio × 100`
3. **Sizing sugerido em R$:** `sizing_pct_sugerido × Patrimônio / 100`
4. **VaR estimado após aporte:** se disponível em `risk_*.json`, recalcular proporcionalmente.
5. **Concentração resultante:** posição atual + V / Patrimônio.

Exibir o bloco de validação:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VALIDAÇÃO DE APORTE — $ARGUMENTS
────────────────────────────────────────────
Sizing sugerido (PM):  X,X% → R$ X.XXX
Você quer aportar:     X,X% → R$ X.XXX
Concentração após:     X,X% (limite IPS: 20%)
VaR estimado após:     X,X% (limite IPS: 2%)
────────────────────────────────────────────
Status: ✅ APROVADO / ⚠️ ACIMA DO IDEAL / 🚨 VIOLA IPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Regras de status:**
- ✅ APROVADO: aporte ≤ sizing sugerido E concentração ≤ 20% E VaR ≤ 2%
- ⚠️ ACIMA DO IDEAL: aporte > sizing sugerido mas não viola limites do IPS
- 🚨 VIOLA IPS: concentração > 20% OU VaR > 2%

---

### Etapa D — Confirmação (somente se ⚠️ ou 🚨)

Se status for ⚠️ ou 🚨, perguntar:

> **O aporte de R$ X.XXX está {acima do sizing ideal / em violação do IPS}.**
> Escolha:
> - **a)** Prosseguir mesmo assim com R$ X.XXX
> - **b)** Ajustar para o sizing sugerido de R$ X.XXX
> - **c)** Cancelar

Se **c)**: registrar `aporte_planejado: cancelado` e ir ao Passo 4.

Registrar a escolha final do usuário em `aporte_planejado`.

---

### Etapa E — Resumo do aporte decidido

Exibir confirmação final:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
APORTE REGISTRADO — $ARGUMENTS
────────────────────────────────────────────
Valor:      R$ X.XXX
% portfólio: X,X%
Sizing OK:  Sim / Não
────────────────────────────────────────────
Próximo passo: execute a ordem na sua corretora.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Passo 4 — Salvar em decisoes.md

Acrescente **uma linha** na tabela de `vault/00-portfolio/decisoes.md` com os dados da decisão:

| YYYY-MM-DD | $ARGUMENTS | {Tipo do ativo} | {VEREDICTO} | {Sizing sugerido %} | {Aporte planejado R$ ou —} | Sim/Não | [[pm-decisao-$ARGUMENTS-YYYY-MM-DD]] |

Regras:
- Use data ISO (YYYY-MM-DD) com a data de hoje
- **Não apague linhas existentes** — apenas acrescente no final da tabela
- "Sizing OK" = Sim se aporte respeitou limites do IPS, Não se violou, — se não houve aporte
- Se o veredicto for EVITAR/AGUARDAR, inserir a linha mesmo assim (para histórico); aporte = —
- Criar pasta `vault/01-ativos/$ARGUMENTS/` se não existir
- Salvar também em `vault/01-ativos/$ARGUMENTS/pm-decisao-$ARGUMENTS-YYYY-MM-DD.md` com:
  - Frontmatter: `tags: [pm-decisao, {ticker}]`, `data:`, `veredicto:`, `ticker:`, `aporte_planejado:`
  - O output completo dos passos 1-3 acima (incluindo bloco de validação de aporte se houve)
  - Wikilinks para `[[carteira]]`, `[[ips]]` e os arquivos de análise lidos
