---
description: Revisão completa de todas as posições em carteira — PM emite MANTER/AUMENTAR/REDUZIR/SAIR para cada ativo
---

# /revisar-carteira

> **Como funciona:** o PM recebe toda a carteira de uma vez (posições, IPS, quant, risk + arquivos de análise de cada ativo) e produz o painel consolidado em uma única chamada. Não chama `/pm` nem `/analisar` em loop — é uma visão panorâmica rápida. Se após a revisão um ativo específico precisar de atenção mais profunda, aí você roda `/pm TICKER` ou `/analisar TICKER` naquele ativo individualmente.

## Passo 1 — Atualizar dados

```powershell
$env:PYTHONUTF8 = "1"; cd "C:\Users\lbmma\Downloads\Local\SBWAA"
python scripts/data/update_carteira.py
python .claude/agents/quant-data-engineer/run_quant.py
python .claude/agents/risk-engineer/run_risk_engineer.py
```

## Passo 2 — Coletar contexto da carteira

Leia:
- `vault/00-portfolio/carteira.md` — todas as posições, pesos e P&L atual
- `vault/00-portfolio/ips.md` — perfil de risco, limites e alocação alvo
- `scripts/data/cache/quant_*.json` — métricas quantitativas (arquivo mais recente)
- `scripts/data/cache/risk_*.json` — métricas de risco (arquivo mais recente)
- `scripts/data/cache/optim_expansao_*.json` — análise de expansão com watchlist (se disponível)
  Use para adicionar seção "Oportunidades da Watchlist" ao final do painel, listando os
  candidatos MELHORA que ainda não estão em carteira.

## Passo 3 — Coletar análises existentes por ativo

Para cada ativo em `vault/00-portfolio/carteira.md`, leia os arquivos em `vault/01-ativos/TICKER/` — priorize os mais recentes (tese, análise completa, equity research, DCF). Se a pasta não existir ou estiver vazia, marque como "Sem análise".

## Passo 4 — Revisão pelo Portfolio Manager

Leia `.claude/agents/portfolio-manager/SKILL.md`.

Você é o PM revisando toda a carteira de uma vez. Para cada posição, emita um veredicto independente com base no que existe de análise + dados de mercado atuais.

### Painel de Revisão (tabela obrigatória)

| Ticker | Peso Atual | Ação | Sizing Alvo | Análise | Justificativa |
|--------|-----------|------|-------------|---------|---------------|

**Ação:** MANTER / AUMENTAR / REDUZIR / SAIR

**Sizing Alvo:** % do portfólio que deveria ter neste ativo (vs peso atual)

**Análise:** data da última análise disponível ou "Sem análise"

**Justificativa:** 1 linha direta. Sem "depende", sem diplomatismo.

---

### Prioridades Imediatas

Liste as **3 ações mais urgentes** da carteira toda (pode ser de ativos diferentes). Ordene por urgência.

### O que não mudar

Liste os ativos que estão bem posicionados e não precisam de intervenção agora. 1 linha cada, com razão.

### Alertas de IPS

Se alguma posição viola ou está próxima de violar os limites do IPS (concentração máxima, VaR, alocação por classe), liste aqui com a violação específica.

### Métricas HF da Carteira

Exibir o bloco de métricas HF conforme Passo 4 do SKILL do PM.

### Oportunidades da Watchlist (se cache de expansão disponível)

Se `optim_expansao_*.json` existir, adicione esta seção:

| Ticker | Sharpe Próprio | ΔSharpe | Peso Ótimo | Status | Análise Disponível |
|--------|---------------|---------|-----------|--------|-------------------|

Liste apenas os classificados como MELHORA. Para cada um, indique se já existe análise
em `vault/01-ativos/TICKER/` (e o frescor) — se sim, o PM pode emitir um veredicto
rápido; se não, indicar `/analisar TICKER`.

### Próximos Passos Sugeridos

Para cada ativo que recebeu AUMENTAR / REDUZIR / SAIR ou que tem confiança baixa, indique qual comando usar a seguir:

| Ticker | Ação | Próximo Passo | Motivo |
|--------|------|---------------|--------|
| ... | ... | `/pm TICKER` ou `/analisar TICKER` | ... |

Critério:
- **`/pm TICKER`** → análise existe e tem menos de 60 dias; só precisa de decisão atualizada
- **`/analisar TICKER`** → análise ausente, desatualizada (>60 dias) ou houve evento relevante desde a última análise (resultado, mudança de gestão, macro)

---

**Regras:**
- Se não houver análise em `vault/01-ativos/TICKER/`: ação = "Sem análise — rodar /analisar TICKER" e não emitir veredicto
- Se a análise existir mas estiver desatualizada (>60 dias): sinalizar com ⚠️ e emitir veredicto com confiança reduzida
- Não sugerir alavancagem nem derivativos
- Tom: gestor sênior, cirúrgico. Cada linha deve ter propósito.

## Passo 5 — Salvar

Crie a pasta `vault/02-relatorios/revisoes/` se não existir.

Salve em `vault/02-relatorios/revisoes/revisao-carteira-YYYY-MM-DD.md` com:
- Frontmatter: `tags: [relatorio, revisao-carteira]`, `data:`, `agente: portfolio-manager`
- Todo o conteúdo gerado acima
- Wikilinks para cada ativo mencionado, `[[carteira]]` e `[[ips]]`
