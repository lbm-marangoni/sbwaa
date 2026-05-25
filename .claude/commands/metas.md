---
description: Dashboard de metas financeiras — progresso de renda passiva, reserva, patrimônio e metas livres
---

# /metas

Exibe o dashboard completo de progresso das metas financeiras definidas em `vault/00-portfolio/metas.md`.

## Passo 1 — Coletar dados

```powershell
$env:PYTHONUTF8 = "1"; cd "C:\Users\lbmma\Downloads\Local\SBWAA"
python scripts/data/update_carteira.py
```

Leia:
- `vault/00-portfolio/metas.md` — definição das metas e valores-alvo
- `vault/00-portfolio/carteira.md` — posições atuais para cálculo automático
- `scripts/data/cache/fundamentals_*.json` mais recentes — cotações atualizadas

## Passo 2 — Calcular progresso de cada meta

### Renda Passiva Mensal
- Calcular dividendo mensal estimado por ativo: DPA_anualizado / 12 × quantidade de cotas/ações
- Somar todos os ativos → renda_passiva_atual (R$/mês)
- Progresso = renda_passiva_atual / alvo_mensal × 100%
- Se `data_alvo` preenchida: calcular meses restantes e projeção de quando atingirá o alvo baseado no crescimento implícito atual

### Reserva de Emergência
- Somar o valor atual de todos os ativos com tipo `renda-fixa` e `tesouro` em carteira
- Progresso = soma / alvo × 100%

### Patrimônio Total
- Usar o patrimônio total da carteira (soma de todos os ativos a valor de mercado)
- Progresso = patrimônio_atual / alvo × 100%
- Se `data_alvo` preenchida: calcular projeção com CAGR implícito dos últimos 12 meses (se disponível) ou informar que projeção requer histórico

### Metas Livres
- Usar o campo `atual` de cada meta (atualizado manualmente pelo usuário)
- Progresso = atual / alvo × 100%
- Se `data_alvo` preenchida: calcular quantos meses restam e se o ritmo atual (atual / meses decorridos) é suficiente para chegar no prazo

## Passo 3 — Gerar dashboard

Formato obrigatório:

```
══════════════════════════════════════════════════════════
METAS FINANCEIRAS — {DATA}
══════════════════════════════════════════════════════════

💰 RENDA PASSIVA MENSAL
   Alvo: R$ X.XXX/mês | Atual: R$ X.XXX/mês
   ████████░░░░░░░ XX%
   {🎯 META ATINGIDA! | ⚠️ Marco: XX% | → Projeção: MMM/AAAA}

🏦 RESERVA DE EMERGÊNCIA
   Alvo: R$ XX.XXX | Atual: R$ XX.XXX (RF + TD)
   ██████████░░░░░ XX%
   {status e projeção se houver data_alvo}

📈 PATRIMÔNIO TOTAL
   Alvo: R$ XXX.XXX | Atual: R$ XXX.XXX
   ████░░░░░░░░░░░ XX%
   {status e projeção se houver data_alvo}

──────────────────────────────────────────────────────────
METAS LIVRES
──────────────────────────────────────────────────────────

🎯 {Nome da Meta}
   Alvo: R$ XX.XXX | Atual: R$ XX.XXX | Prazo: MMM/AAAA
   ███████░░░░░░░░ XX%
   {status: no prazo / em risco / concluída}

══════════════════════════════════════════════════════════
```

**Regras de formatação da barra de progresso:**
- Barra de 15 caracteres: `█` para preenchido, `░` para vazio
- Milestones destacados: 25%, 50%, 75%, 100%
- Se progresso > 100%: mostrar 100% preenchido + "✅ SUPERADA (+XX%)"

**Status de projeção (quando `data_alvo` preenchida):**
- "no prazo" → ritmo atual é suficiente para atingir até a data
- "em risco" → ritmo atual insuficiente — informar o déficit mensal necessário
- "META ATINGIDA!" → progresso ≥ 100%

**Milestones — destacar sempre que o progresso cruzar:**
- 25% → `⭐ Marco 25% atingido`
- 50% → `⭐⭐ Metade do caminho`
- 75% → `⭐⭐⭐ Reta final`
- 100% → `🎯 META ATINGIDA!`

## Regras gerais

- Não salva arquivo — resposta direta no chat
- Não faz nenhuma recomendação de investimento
- Não lê nem referencia análises de ativos
- Se `metas.md` não existir ou estiver vazio: informar que o arquivo precisa ser configurado em `vault/00-portfolio/metas.md`
- Se algum campo estiver zerado ou vazio: calcular o que for possível e indicar "configure em metas.md" para os campos ausentes
