---
description: Decisão do Portfolio Manager para um ativo já analisado — ou Modo Aporte multi-ativo
---

# /pm $ARGUMENTS

## ROTEAMENTO — ler antes de qualquer coisa

Analisar `$ARGUMENTS` e rotear para o modo correto:

| Caso | Condição | Modo |
|------|----------|------|
| A | `$ARGUMENTS` vazio ou em branco | **Modo Aporte** (interativo completo) |
| B | `$ARGUMENTS` é apenas um número (ex: `700`, `1500.50`) | **Modo Aporte** com valor pré-preenchido |
| C | `$ARGUMENTS` é um ticker de ativo (letras+números, ex: `MXRF11`) | **Modo Análise** (fluxo original) |

---

## MODO APORTE (Casos A e B)

> Ativar quando `$ARGUMENTS` está vazio OU é apenas um valor numérico.

O PM distribui capital entre múltiplos ativos da watchlist, com base nas análises existentes e no IPS.

**Se Caso B:** o valor de `$ARGUMENTS` é o valor do aporte em R$ — pular a pergunta do Passo 1 e usar esse valor diretamente.

### Passo A1 — Ler contexto da carteira

Ler antes de fazer qualquer pergunta:
- `vault/00-portfolio/carteira.md` — posição atual, patrimônio total, pesos
- `vault/00-portfolio/ips.md` — perfil, limites de risco, alocação alvo por classe
- `vault/00-portfolio/watchlist.md` — ativos monitorados (se existir)
- `vault/01-ativos/` — listar subpastas existentes (= ativos com análise disponível)
- `scripts/data/cache/risk_*.json` — métricas de risco (mais recente)

### Passo A2 — Perguntas interativas

Fazer as perguntas **uma de cada vez**, aguardando resposta antes de continuar.

**Pergunta 1 — Valor** (pular se Caso B):
> **Quanto deseja aportar no total? (R$)**
> Informe o valor em reais (ex: 700, 1500.50).

**Pergunta 2 — Classe de ativos:**
> **Em qual classe deseja aportar?**
> a) Ações | b) FIIs | c) ETFs | d) Renda Fixa | e) Múltiplas classes | f) PM decide

**Pergunta 3 — Número de ativos:**
> **Quantos ativos deseja incluir no aporte?**
> a) 1 | b) 2 | c) 3 | d) PM decide (baseado no sizing ótimo)

**Pergunta 4 — Restrições:**
> **Alguma restrição para este aporte?**
> Ex: "não quero XPML11", "só ativos que já tenho na carteira", "sem ações agora" — ou **nenhuma**.

### Passo A3 — RF Oportunidade

Ler `vault/00-portfolio/rf-oportunidade.md`, extrair `saldo_bruto` e `data_deposito` do bloco ```yaml```.
Se `saldo_bruto > 0` e `data_deposito != "—"`:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 RF OPORTUNIDADE — CAIXINHA NUBANK
────────────────────────────────────────────────────
  Saldo bruto:          R$ X.XXX,XX
  Rendimento est.*:     R$ X.XX  (N dias)
  IOF estimado:         R$ X.XX  ✅ zerado / ⚠️ XX%
  IR estimado*:         R$ X.XX  (XX,X%)
  Líquido disponível:   R$ X.XXX,XX
────────────────────────────────────────────────────
  Aporte solicitado:    R$ X.XXX,XX  ✅ / ⚠️ insuficiente
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  * CDI 14,75% a.a. — IR realizado apenas no resgate.
```

- IOF: 96%→0% dias 1–30 sobre rendimentos; 0% após D30
- IR: 22,5% ≤180d · 20% 181–360d · 17,5% 361–720d · 15% >720d
- Alertar se `dias < 30` (IOF incide) e se saldo insuficiente.
- Se arquivo ausente ou saldo zero: omitir silenciosamente.

### Passo A4 — Seleção dos ativos e distribuição

Com base nas análises disponíveis em `vault/01-ativos/` e nas restrições informadas:

1. **Verificar quais ativos têm análise** — listar arquivos em `vault/01-ativos/*/pm-decisao-*.md` ou `*/tese*.md`
2. **Se um ativo da watchlist não tiver análise:** avisar o usuário e oferecer rodar `/analisar TICKER` antes de continuar
3. **Ranquear** os ativos elegíveis por adequação ao IPS, upside estimado e déficit de alocação vs alvo
4. **Distribuir o capital** entre os N ativos selecionados, respeitando:
   - Concentração máxima: 20% por ativo
   - VaR da carteira: ≤ 2%
   - Sizing por ativo conforme IPS

Exibir o plano de distribuição:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PLANO DE APORTE — PM
────────────────────────────────────────────────────
Total a aportar:  R$ X.XXX,XX

  TICKER1  [Tipo]  R$ X.XXX  (XX%)  — sizing: XX% → XX% após
  TICKER2  [Tipo]  R$ X.XXX  (XX%)  — sizing: XX% → XX% após
  TICKER3  [Tipo]  R$ X.XXX  (XX%)  — sizing: XX% → XX% após

Concentração max após:  XX,X%  ✅ / ⚠️
VaR estimado após:      X,X%   ✅ / ⚠️
Status IPS:             ✅ APROVADO / ⚠️ ACIMA DO IDEAL / 🚨 VIOLA IPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Passo A5 — Confirmação e registro

Perguntar:
> **Confirma este plano de aporte? (sim / ajustar / cancelar)**

Se **ajustar**: perguntar o que mudar e refazer A4.
Se **cancelar**: encerrar sem registrar.
Se **sim**: para cada ativo do plano, acrescentar linha em `vault/00-portfolio/decisoes.md` e salvar `vault/01-ativos/TICKER/pm-decisao-TICKER-YYYY-MM-DD.md`.

Se houver RF Oportunidade: informar o comando para registrar a movimentação:
`python sbwaa.py /oportunidade --retirar X.XX --destino TICKERS`

---

## MODO ANÁLISE (Caso C)

> Ativar quando `$ARGUMENTS` é um ticker de ativo.

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
4. **Nível de entrada:** escrever obrigatoriamente como `**Nível de entrada:** R$ XX.XX` (preço máximo aceitável para entrada). Se for condicional a evento: `**Nível de entrada:** aguardar {evento/condição}`.
5. **Stop / Revisão:** escrever obrigatoriamente em duas linhas: `**Stop:** R$ XX.XX` e `**Condição de revisão:** {motivo}`. Se não houver stop de preço: `**Stop:** — sem stop de preço`.
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

### Etapa B1 — RF Oportunidade (executar após receber o valor)

Ler `vault/00-portfolio/rf-oportunidade.md`, extrair `saldo_bruto` e `data_deposito`
do bloco ```yaml```. Se `saldo_bruto > 0` e `data_deposito != "—"`:

Calcular e exibir antes do bloco C:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 RF OPORTUNIDADE — CAIXINHA NUBANK
────────────────────────────────────────────────────
  Saldo bruto:          R$ X.XXX,XX
  Rendimento est.*:     R$ X.XX  (N dias)
  IOF estimado:         R$ X.XX  ✅ zerado / ⚠️ XX%
  IR estimado*:         R$ X.XX  (XX,X%)
  Líquido disponível:   R$ X.XXX,XX
────────────────────────────────────────────────────
  Aporte solicitado:    R$ X.XXX,XX  ✅ / ⚠️ insuficiente
────────────────────────────────────────────────────
  Movimentação:
    − R$ X.XXX,XX  RF Oportunidade
    + R$ X.XXX,XX  $ARGUMENTS
  Saldo bruto após:     R$ X.XXX,XX
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  * CDI 14,75% a.a. — IR realizado apenas no resgate.
```

- IOF: 96%→0% dias 1-30 sobre rendimentos; 0% após D30
- IR: 22,5% ≤180d · 20% 181-360d · 17,5% 361-720d · 15% >720d
- Alertar se `dias < 30` (IOF incide) e se saldo insuficiente.
- Se arquivo ausente ou saldo zero: omitir silenciosamente.
- Após confirmação final: `python sbwaa.py /oportunidade --retirar X.XX --destino $ARGUMENTS`

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

## Passo 4 — Registrar alertas de preço

Após salvar os arquivos do passo anterior, executar:

```powershell
$env:PYTHONUTF8 = "1"; python scripts/alerts/extract_targets.py --ticker $ARGUMENTS
```

> Se $ARGUMENTS for vazio (Modo Aporte), executar para cada ticker do plano de aporte confirmado.
> Se o comando falhar: ignorar silenciosamente e prosseguir.

---

## Passo 5 — Salvar em decisoes.md

Acrescente **uma linha** na tabela de `vault/00-portfolio/decisoes.md` com os dados da decisão. (Renumerado de Passo 4 para Passo 5 — conteúdo inalterado.)

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
