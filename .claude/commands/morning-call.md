---
description: Briefing diário pré-abertura — macro, carteira e alertas sem API key
---

# /morning-call

Execute o morning call do dia.

## Passo 1 — Atualizar dados

```powershell
$env:PYTHONUTF8 = "1"; cd "C:\Users\lbmma\Downloads\Local\SBWAA"
python scripts/data/fetch_yahoo.py --macro
python scripts/data/market_snapshot.py
python scripts/data/update_carteira.py
python scripts/alerts/check_alerts.py
```

## Passo 2 — Ler contexto

Leia todos estes arquivos:
- Todos os `scripts/data/cache/yahoo_*.json` do dia (macro global)
- `vault/02-relatorios/diarios/snapshot-YYYY-MM-DD.md` (snapshot gerado acima)
- `vault/00-portfolio/carteira.md` (posições e P&L atual)
- `vault/00-portfolio/ips.md` (limites do investidor)
- `vault/00-portfolio/metas.md` (metas financeiras — para o bloco de metas)
- `logs/alerts.log` se existir (alertas ativos)

## Passo 3 — Gerar Morning Call

Leia `.claude/agents/market-researcher/SKILL.md` e produza o briefing com:

### Macro Global
Tabela com: IBOV, S&P500, Nasdaq, DXY, BRL/USD, petróleo, ouro, juros EUA 10Y.
Para cada um: cotação atual, variação % do dia, contexto em 1 linha.

### Cenário do Dia
2-3 parágrafos curtos: o que move o mercado hoje, riscos e oportunidades no horizonte.

### Impacto na Carteira
Como o cenário macro do dia afeta cada posição em `vault/00-portfolio/carteira.md`.
Mostre apenas posições que têm exposição relevante ao cenário do dia.

### Alertas Ativos
Se houver alertas no `logs/alerts.log` com CRÍTICO ou ALTO, liste aqui.

### Alertas Econométricos
Ler os arquivos `scripts/data/cache/econometria_{TICKER}_*.json` mais recentes para cada ativo em carteira. Exibir **apenas** se houver pelo menos um sinal crítico — omitir a seção silenciosamente se tudo estiver normal:

| Ticker | Sinal | Detalhe |
|--------|-------|---------|
| TICK1  | ⚠️ GARCH ALTA | Persistência 0.97 — choques demoram X dias para dissipar |
| TICK2  | ⚠️ Corr instável | Correlação >0.80 com TICK3 — diversificação comprometida |
| TICK3  | ⚠️ Beta crescente | Beta subiu de 0.X para 0.X em 60d — ativo mais arriscado |

Sinais que disparam alerta: GARCH regime=ALTA, correlação rolling >0.80 com instabilidade, beta dinâmico tendência=crescente com delta >0.20, Calmar <0.5.

### Metas — Resumo Compacto

Ler `vault/00-portfolio/metas.md` e exibir uma linha de status por meta. Destacar com ⚠️ qualquer milestone recém-atingido (25 / 50 / 75 / 100%) ou meta em risco de prazo.

```
📊 Metas: Renda Passiva ████████░░░░░░░ XX% | Reserva ████████████░░░ XX% | Patrimônio ████░░░░░░░░░░░ XX%
{metas livres com nome abreviado e % — ex: Viagem Europa ██░░░░░░░░░░░░░ 14%}
```

Se `metas.md` não existir ou não tiver metas configuradas: omitir esta seção silenciosamente.

### Ponto de Atenção do Dia
1 único insight acionável: um ativo, setor ou evento específico para monitorar hoje.

## Passo 4 — Salvar

Salve em `vault/02-relatorios/diarios/morning-call-YYYY-MM-DD.md` com wikilinks para os ativos mencionados e `[[carteira]]`, `[[ips]]`.
