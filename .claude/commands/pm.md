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
- `scripts/data/cache/brapi_$ARGUMENTS_*.json` — dados fundamentalistas atuais

## Instrução

Leia `.claude/agents/portfolio-manager/SKILL.md` e emita a decisão com:

1. **VEREDICTO:** COMPRAR / AGUARDAR / EVITAR (em destaque)
2. **Tese em 3 bullets:** por que este veredicto agora
3. **Sizing:** % sugerido do portfólio, posição atual vs alvo
4. **Nível de entrada:** preço máximo aceitável ou gatilho de evento
5. **Stop / Revisão:** condição que invalidaria a tese
6. **Adequação ao IPS:** confirmar que a operação respeita todos os limites

Seja direto. Nenhuma análise de ativo vale mais do que a adequação ao perfil do investidor.

## Passo 3 — Salvar em decisoes.md

Acrescente **uma linha** na tabela de `vault/00-portfolio/decisoes.md` com os dados da decisão:

| YYYY-MM-DD | $ARGUMENTS | {Tipo do ativo} | {VEREDICTO} | {Sizing sugerido % ou R$} | Sim/Não | [[pm-decisao-$ARGUMENTS-YYYY-MM-DD]] |

Regras:
- Use data ISO (YYYY-MM-DD) com a data de hoje
- **Não apague linhas existentes** — apenas acrescente no final da tabela
- "Sizing OK" = Sim se a operação respeitou todos os limites do IPS, Não caso contrário
- Se o veredicto for EVITAR, inserir a linha mesmo assim (para histórico)
- Criar pasta `vault/01-ativos/$ARGUMENTS/` se não existir
- Salvar também em `vault/01-ativos/$ARGUMENTS/pm-decisao-$ARGUMENTS-YYYY-MM-DD.md` com:
  - Frontmatter: `tags: [pm-decisao, {ticker}]`, `data:`, `veredicto:`, `ticker:`
  - O output completo dos passos 1-2 acima
  - Wikilinks para `[[carteira]]`, `[[ips]]` e os arquivos de análise lidos
