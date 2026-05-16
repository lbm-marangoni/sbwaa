# SBWAA — FASE 6: COMANDOS + HEARTBEAT + ALERTAS
**Prompt para execução no Claude Code**
**Versão:** 1.6.0
**Fase:** 6 de 8
**Pré-requisito:** Fases 0–5 concluídas (investments v1.5.0)

---

## CONTEXTO

A Fase 6 transforma o SBWAA de um conjunto de scripts em um **sistema
operacional financeiro pessoal**. São três entregas:

1. **Comandos slash** — interface unificada para todos os agentes via
   terminal, com um único ponto de entrada (`sbwaa.py`)
2. **Heartbeat** — processo automático agendado que roda diariamente
   sem intervenção do usuário
3. **Alertas** — sistema de triggers por evento que notifica quando
   algo relevante acontece na carteira ou no mercado

Modelo: `claude-sonnet-4-6` para comandos diários e heartbeat.
O heartbeat não cria análises profundas — ele monitora e alerta.
Análises profundas são acionadas manualmente via `/analisar`.

---

## REGRAS GERAIS — LER ANTES DE EXECUTAR

1. Nenhum agente novo é criado nesta fase — apenas orquestração
2. O ponto de entrada único é `/sbwaa/sbwaa.py` — todos os comandos
   passam por ele
3. Heartbeat usa cron (Linux/Mac) ou Task Scheduler (Windows)
4. Alertas são exibidos no terminal e salvos no vault — sem push
   notifications externas (privacidade)
5. Ao finalizar: `investments` → v1.6.0 e `heartbeat` → v1.0.0

---

## PARTE 1 — PONTO DE ENTRADA: `sbwaa.py`

Crie `/sbwaa/sbwaa.py` — o arquivo principal do sistema:

```python
#!/usr/bin/env python3
"""
SBWAA — Second Brain Wealth + Asset + Assessor Individual
Ponto de entrada único para todos os comandos.

Uso:
    python sbwaa.py /analisar PETR4
    python sbwaa.py /carteira
    python sbwaa.py /morning-call
    python sbwaa.py /help
"""

import sys
import os
import argparse
from datetime import datetime

# Mapa de comandos → scripts
COMANDOS = {
    "/analisar":             "agents/portfolio-manager/run_analisar.py",
    "/pm":                   "agents/portfolio-manager/run_pm.py",
    "/decidir":              "agents/portfolio-manager/run_pm.py",
    "/morning-call":         "commands/morning_call.py",
    "/mundo-economico":      "commands/mundo_economico.py",
    "/investimento-do-dia":  "commands/investimento_do_dia.py",
    "/carteira":             "commands/carteira.py",
    "/adicionar":            "scripts/data/add_ativo.py",
    "/risco-carteira":       "commands/risco_carteira.py",
    "/relatorio-semanal":    "commands/relatorio_semanal.py",
    "/relatorio-mensal":     "commands/relatorio_mensal.py",
    "/dividendos":           "commands/dividendos.py",
    "/stress-test":          "commands/stress_test.py",
    "/rebalancear":          "commands/rebalancear.py",
    "/comparar":             "commands/comparar.py",
    "/earnings":             "agents/earnings-reviewer/run_earnings_reviewer.py",
    "/tese":                 "commands/tese.py",
    "/ips":                  "commands/ips.py",
    "/help":                 None,  # tratado internamente
    "/status":               None,  # tratado internamente
}

def exibir_help():
    print("""
═══════════════════════════════════════════════════════
SBWAA — Comandos disponíveis
═══════════════════════════════════════════════════════

ANÁLISE
  /analisar [TICKER]           Pipeline completo (8 agentes)
  /tese [TICKER]               Research + DCF + PM (rápido)
  /earnings [TICKER]           Só Earnings Reviewer
  /comparar [TICKER1] [TICKER2] Análise lado a lado
  /pm [TICKER]                 PM direto (requer análise prévia)

PORTFÓLIO
  /carteira                    Snapshot completo da carteira
  /adicionar [TKR] [TIPO] [QTD] [PREÇO]  Adicionar ativo
  /risco-carteira              VaR, CVaR, Sharpe, drawdown
  /rebalancear                 Sugestão de ajuste vs IPS
  /dividendos                  Calendário e histórico
  /ips                         Exibir/atualizar perfil

DIÁRIO
  /morning-call                Briefing pré-abertura
  /mundo-economico             Macro do dia
  /investimento-do-dia         Oportunidade do dia

RELATÓRIOS
  /relatorio-semanal           P&L e performance da semana
  /relatorio-mensal            Relatório completo do mês
  /stress-test [CENÁRIO]       Simular choque na carteira

SISTEMA
  /status                      Status do sistema e versões
  /help                        Este menu

═══════════════════════════════════════════════════════
""")

def exibir_status():
    # Ler VERSION.md e exibir versões de todos os módulos
    versao_path = os.path.join(os.path.dirname(__file__), "VERSION.md")
    print("\n═══════════════════════════════════════════════")
    print("SBWAA — Status do Sistema")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("═══════════════════════════════════════════════")
    if os.path.exists(versao_path):
        with open(versao_path) as f:
            print(f.read())
    print("═══════════════════════════════════════════════\n")

def main():
    if len(sys.argv) < 2:
        exibir_help()
        return

    comando = sys.argv[1].lower()
    args = sys.argv[2:]

    if comando == "/help":
        exibir_help()
        return

    if comando == "/status":
        exibir_status()
        return

    if comando not in COMANDOS:
        print(f"\n❌ Comando '{comando}' não reconhecido.")
        print("   Use /help para ver todos os comandos disponíveis.\n")
        return

    script = COMANDOS[comando]
    script_path = os.path.join(os.path.dirname(__file__), ".claude", script)

    # Ajuste para scripts fora de .claude/
    if not os.path.exists(script_path):
        script_path = os.path.join(os.path.dirname(__file__), script)

    if not os.path.exists(script_path):
        print(f"\n❌ Script não encontrado: {script}")
        print("   Verifique se a fase correspondente foi concluída.\n")
        return

    cmd = f"python {script_path} {' '.join(args)}"
    os.system(cmd)

if __name__ == "__main__":
    main()
```

---

## PARTE 2 — COMANDOS INDIVIDUAIS

Criar pasta `/sbwaa/.claude/commands/` e os seguintes scripts:

---

### `/morning-call` → `commands/morning_call.py`

**Função:** Briefing completo pré-abertura. Roda os dados do dia e
sintetiza o que importa antes do mercado abrir.

**O script deve:**
- Rodar `market_snapshot.py` para dados atualizados
- Rodar `run_market_researcher.py` para contexto macro
- Verificar se há earnings de ativos da carteira no dia (via Brapi)
- Verificar agenda econômica do dia (COPOM, IPCA, PIB, payroll US)
  usando dados do Yahoo Finance e cache
- Gerar output no terminal E salvar em vault

**Output no terminal:**
```
═══════════════════════════════════════════════
SBWAA — Morning Call | {DATA} | {HORA}
═══════════════════════════════════════════════

🌍 MACRO GLOBAL
  S&P 500:   X.XXX  (+X.X%)    DXY:      XXX.X  (+X.X%)
  NASDAQ:    X.XXX  (+X.X%)    Petróleo: $XX.X  (+X.X%)
  IBOV fut:  X.XXX  (+X.X%)    BRL/USD:  X.XX   (+X.X%)
  Juros 10Y: X.XX%  (+Xbps)    Ouro:     $X.XXX (+X.X%)

📅 AGENDA DO DIA
  {lista de eventos macro agendados com horário}

📋 EARNINGS HOJE (ativos da carteira)
  {lista ou "Nenhum earnings de ativos da carteira hoje"}

📊 CARTEIRA — PRÉ-ABERTURA
  {tabela com ativos, cotação fechamento anterior, variação pré}

💡 FOCO DO DIA (Market Researcher)
  {2-3 linhas do que monitorar hoje}

⚡ ALERTAS ATIVOS
  {circuit breakers ou alertas pendentes}

═══════════════════════════════════════════════
Gerado em {HORA} | Cache: {status}
```

**Salvar em:** `vault/02-relatorios/diarios/morning-call-{DATA}.md`

---

### `/mundo-economico` → `commands/mundo_economico.py`

**Função:** Notícias e dados macro do dia. Usa o Market Researcher
focado apenas em macro — sem análise de ativos específicos.

**Output:**
- Índices globais atualizados
- Câmbio e commodities
- 3-5 temas macro mais relevantes do dia
- Impacto estimado para carteiras Brasil

**Salvar em:** `vault/03-macro/mundo-economico-{DATA}.md`

---

### `/investimento-do-dia` → `commands/investimento_do_dia.py`

**Função:** Identifica 1-2 oportunidades de investimento compatíveis
com o perfil do usuário (IPS), baseado nos dados do dia.

**O script deve:**
- Carregar IPS do usuário (perfil, limites, alocação alvo)
- Identificar classes de ativo com underweight vs IPS
- Cruzar com dados macro do dia (setor favorecido?)
- Usar `claude-sonnet-4-6` para sugerir 1-2 ativos a explorar
  (NÃO é recomendação de compra — é sugestão para o `/analisar`)

**Output:**
```
═══════════════════════════════════════════════
SBWAA — Investimento do Dia | {DATA}
═══════════════════════════════════════════════

Com base no seu IPS e no cenário de hoje:

🎯 EXPLORAR: {TICKER1}
   Tipo: {tipo} | Setor: {setor}
   Por quê hoje: {1-2 linhas de contexto}
   → Execute: python sbwaa.py /analisar {TICKER1}

🎯 EXPLORAR: {TICKER2} (se houver)
   ...

⚠️  Esta sugestão é ponto de partida para análise,
    não recomendação de compra. Use /analisar para
    a análise completa antes de qualquer decisão.
═══════════════════════════════════════════════
```

---

### `/carteira` → `commands/carteira.py`

**Função:** Snapshot completo e atualizado da carteira.

**O script deve:**
- Rodar `update_carteira.py` para cotações atualizadas
- Exibir tabela completa com todos os ativos
- Exibir resumo com patrimônio, P&L total, variação do dia
- Mostrar alocação atual vs alvo do IPS com status

**Output:**
```
═══════════════════════════════════════════════
SBWAA — Carteira | {DATA} {HORA}
═══════════════════════════════════════════════

POSIÇÕES
Ticker  Tipo        Qtd   P.Médio  P.Atual  P&L(R$)  P&L(%)  Aloc%
──────────────────────────────────────────────────────────────────
PETR4  🟦 AÇÃO PN   100   36.00    38.50   +250     +6.9%   8.2%
...

RESUMO
  Patrimônio Total:  R$ XX.XXX
  Total Investido:   R$ XX.XXX
  P&L Total:         R$ XX.XXX (+X.X%)
  Variação Hoje:     R$ XXX (+X.X%)

ALOCAÇÃO vs IPS
  Classe        Atual%   Alvo%   Status
  Ações BR       XX%      XX%    ✅/⚠️/🔴
  FIIs           XX%      XX%    ✅/⚠️/🔴
  ...

═══════════════════════════════════════════════
```

---

### `/risco-carteira` → `commands/risco_carteira.py`

**Função:** Snapshot rápido de risco. Roda Quant + Risk Engineer
e exibe métricas HF no terminal.

- Roda `run_quant.py` + `run_risk_engineer.py`
- Exibe o bloco de métricas HF completo
- Exibe circuit breakers e alertas ativos
- Salva snapshot em `vault/05-risk/snapshots/`

---

### `/relatorio-semanal` → `commands/relatorio_semanal.py`

**Função:** Relatório de performance da semana.

**Conteúdo:**
- P&L da semana por ativo (R$ e %)
- Patrimônio início vs fim da semana
- Melhor e pior ativo da semana
- Dividendos recebidos na semana
- Sharpe e volatilidade da semana
- Comparação vs IBOV na semana
- Resumo macro da semana (links para morning-calls)
- Top 3 eventos que moveram a carteira

**Salvar em:** `vault/02-relatorios/semanais/semana-{ANO}-W{NUM}.md`
**Também gerar DOCX** com o mesmo conteúdo.

---

### `/relatorio-mensal` → `commands/relatorio_mensal.py`

**Função:** Relatório completo do mês. Versão expandida do semanal.

**Conteúdo adicional:**
- Atribuição de retorno por ativo (quanto cada um contribuiu)
- Evolução do Sharpe, VaR e drawdown ao longo do mês
- Comparação vs IBOV, CDI e IPCA no mês e no ano
- Dividendos recebidos no mês + yield on cost por ativo
- Revisão de teses: o que mudou nas análises do mês?
- Próximos eventos relevantes (earnings, vencimentos, COPOM)

**Salvar em:** `vault/02-relatorios/mensais/relatorio-{ANO}-{MES}.md`
**Também gerar DOCX.**

---

### `/dividendos` → `commands/dividendos.py`

**Função:** Calendário de dividendos e histórico de proventos.

**Output:**
- Próximos dividendos de ativos da carteira (próximos 60 dias)
- Dividendos recebidos nos últimos 12 meses por ativo
- Yield on cost atual por ativo
- Total de proventos recebidos no ano

---

### `/stress-test` → `commands/stress_test.py`

**Função:** Roda stress test de cenário específico ou todos.

**Uso:**
```bash
python sbwaa.py /stress-test                  # todos os cenários
python sbwaa.py /stress-test covid-2020       # cenário específico
python sbwaa.py /stress-test custom -30       # choque customizado -30%
```

---

### `/rebalancear` → `commands/rebalancear.py`

**Função:** PM analisa alocação atual vs IPS e sugere ajustes.

**Output:**
- Desvios por classe de ativo vs alvo do IPS
- Sugestão do PM: o que reduzir, o que aumentar
- Impacto estimado no Sharpe e VaR após rebalanceamento
- Atenção: sugestão, não ordem — usuário decide

---

### `/tese` → `commands/tese.py`

**Função:** Versão rápida do `/analisar` — Research + DCF + PM.
Pula Quant e Risk Engineer (usa cache existente).

**Uso:**
```bash
python sbwaa.py /tese PETR4
python sbwaa.py /tese PETR4 --completo    # força versão longa
```

---

### `/ips` → `commands/ips.py`

**Função:** Exibir ou atualizar IPS do usuário.

```bash
python sbwaa.py /ips           # exibe IPS atual formatado
python sbwaa.py /ips --editar  # abre ips.md no editor padrão
```

---

## PARTE 3 — HEARTBEAT AUTOMÁTICO

### Script: `scripts/heartbeat/heartbeat.py`

**Função:** Processo automático que roda diariamente sem intervenção.
Monitora a carteira, verifica alertas e prepara o morning-call.

```python
"""
SBWAA — Heartbeat Diário
Roda automaticamente. Não requer interação.
Agendado via cron (Linux/Mac) ou Task Scheduler (Windows).

Execução recomendada: 07h15 em dias úteis (antes da abertura)
"""
```

**O heartbeat deve:**
1. Verificar se é dia útil (segunda a sexta, fora de feriados BR)
2. Rodar `market_snapshot.py` — atualizar dados do dia
3. Rodar `run_quant.py` — calcular métricas atualizadas da carteira
4. Rodar `run_risk_engineer.py` — verificar circuit breakers
5. Se qualquer circuit breaker ativo → registrar alerta em `alerts.log`
6. Verificar earnings do dia para ativos da carteira
7. Gerar `morning-call` automaticamente e salvar no vault
8. Registrar execução em `logs/heartbeat.log`

**Nunca fazer no heartbeat:**
- Análises profundas (DCF, PM decision) — são sob demanda
- Chamar Claude para análise de ativos específicos — apenas snapshot
- Gastar tokens desnecessariamente — usar cache ao máximo

---

### Script: `scripts/heartbeat/schedule_heartbeat.py`

**Função:** Configura o agendamento automático do heartbeat.

```python
"""
Configura o cron job (Linux/Mac) ou Task Scheduler (Windows)
para o heartbeat rodar automaticamente.

Uso: python schedule_heartbeat.py --instalar
     python schedule_heartbeat.py --remover
     python schedule_heartbeat.py --status
"""
import platform
import subprocess
import os

def instalar_cron():
    """Linux/Mac: adiciona entrada no crontab"""
    sbwaa_path = os.path.abspath("scripts/heartbeat/heartbeat.py")
    log_path = os.path.abspath("logs/heartbeat.log")
    # Roda às 07h15 de segunda a sexta
    cron_entry = f"15 7 * * 1-5 python {sbwaa_path} >> {log_path} 2>&1"
    # Instrução: exibir o comando para o usuário adicionar manualmente
    print(f"\nAdicione a seguinte linha ao seu crontab (crontab -e):")
    print(f"\n{cron_entry}\n")

def instalar_windows():
    """Windows: instrução para Task Scheduler"""
    print("\nNo Windows, configure o Task Scheduler:")
    print("1. Abrir 'Agendador de Tarefas'")
    print("2. Criar Tarefa Básica")
    print(f"3. Programa: python")
    print(f"4. Argumentos: {os.path.abspath('scripts/heartbeat/heartbeat.py')}")
    print("5. Gatilho: Diariamente às 07:15")
    print("6. Executar apenas em dias úteis\n")

def main():
    sistema = platform.system()
    if sistema in ["Linux", "Darwin"]:
        instalar_cron()
    elif sistema == "Windows":
        instalar_windows()
    else:
        print(f"Sistema {sistema} não suportado automaticamente.")
        print("Configure manualmente para rodar heartbeat.py às 07h15.")

if __name__ == "__main__":
    main()
```

---

## PARTE 4 — SISTEMA DE ALERTAS

### Script: `scripts/alerts/check_alerts.py`

**Função:** Verifica condições de alerta e registra quando ativas.
Chamado pelo heartbeat e pode ser chamado manualmente.

**Alertas implementados:**

```python
ALERTAS = {
    "queda_ativo": {
        "descricao": "Ativo da carteira caiu > X% no dia",
        "threshold_pct": 5.0,  # configurável no IPS
        "severidade": "ALTO"
    },
    "alta_ativo": {
        "descricao": "Ativo da carteira subiu > X% no dia",
        "threshold_pct": 7.0,
        "severidade": "MÉDIO"
    },
    "circuit_breaker_var": {
        "descricao": "VaR da carteira violou limite do IPS",
        "severidade": "CRÍTICO"
    },
    "circuit_breaker_drawdown": {
        "descricao": "Drawdown atual violou limite do IPS",
        "severidade": "CRÍTICO"
    },
    "circuit_breaker_concentracao": {
        "descricao": "Ativo ultrapassou concentração máxima do IPS",
        "severidade": "ALTO"
    },
    "earnings_amanha": {
        "descricao": "Ativo da carteira tem earnings amanhã",
        "severidade": "MÉDIO"
    },
    "dividendo_proximo": {
        "descricao": "Data ex-dividendo de ativo da carteira em 5 dias",
        "severidade": "BAIXO"
    },
    "correlacao_subiu": {
        "descricao": "Correlação média da carteira subiu > 0.15 vs mês anterior",
        "severidade": "MÉDIO"
    }
}
```

**Formato do log de alertas** em `logs/alerts.log`:
```
[2026-05-15 07:16:43] CRÍTICO | circuit_breaker_var | VaR atual 2.8% > limite IPS 2.5%
[2026-05-15 07:16:43] ALTO    | queda_ativo         | PETR4 -6.2% no dia
[2026-05-15 07:16:43] MÉDIO   | earnings_amanha     | VALE3 divulga 1T26 amanhã
```

**Exibição de alertas no terminal** (quando há alertas ativos):
```
═══════════════════════════════════════════════
⚡ ALERTAS SBWAA — {DATA} {HORA}
═══════════════════════════════════════════════
🚨 CRÍTICO  VaR atual (2.8%) > limite IPS (2.5%)
            → Execute: python sbwaa.py /risco-carteira

⚠️  ALTO    PETR4 caiu 6.2% hoje
            → Execute: python sbwaa.py /analisar PETR4

ℹ️  MÉDIO   VALE3 divulga earnings amanhã
            → Execute: python sbwaa.py /earnings VALE3
═══════════════════════════════════════════════
```

**Salvar alerta no vault:** cada alerta CRÍTICO ou ALTO gera nota em
`vault/05-risk/snapshots/alerta-{DATA}-{HORA}.md`

---

## PARTE 5 — VALIDAÇÃO FINAL

- [ ] `sbwaa.py` criado como ponto de entrada único
- [ ] `/help` exibe menu completo e formatado
- [ ] `/status` exibe versões de todos os módulos
- [ ] Todos os 14 comandos criados em `commands/`
- [ ] `/morning-call` testado — output completo no terminal + vault
- [ ] `/carteira` testado — tabela e resumo exibidos corretamente
- [ ] `/risco-carteira` testado — métricas HF exibidas
- [ ] `/investimento-do-dia` testado — sugestão gerada
- [ ] `/mundo-economico` testado — macro do dia exibida
- [ ] `/stress-test` testado com todos os cenários e custom
- [ ] `/relatorio-semanal` testado — DOCX gerado
- [ ] `heartbeat.py` criado e testado manualmente
- [ ] `schedule_heartbeat.py` criado — instruções de cron exibidas
- [ ] `check_alerts.py` criado com todos os 8 tipos de alerta
- [ ] Log de alertas sendo escrito em `logs/alerts.log`
- [ ] Alertas CRÍTICO/ALTO sendo salvos no vault
- [ ] `VERSION.md` atualizado: `investments` → v1.6.0,
      `heartbeat` → v1.0.0
- [ ] `CHANGELOG.md` com entrada da Fase 6

Ao finalizar, confirme: **"SBWAA Fase 6 concluída — investments v1.6.0 | heartbeat v1.0.0"**

---

## OBSERVAÇÕES IMPORTANTES

1. `sbwaa.py` deve funcionar de qualquer diretório — usar `os.path`
   com caminhos absolutos relativos ao `__file__`

2. O heartbeat é leve por design — estimativa de 500-1.000 tokens
   por execução diária, sem análises profundas

3. Os alertas não enviam notificações externas (e-mail, SMS, push)
   — ficam em log local e vault. Notificações externas violam a
   política de privacidade do SBWAA

4. `/relatorio-semanal` e `/relatorio-mensal` podem demorar 2-3 min
   — informar o usuário com mensagem de progresso

5. Comandos que não têm dados suficientes (carteira vazia, IPS não
   preenchido) devem informar explicitamente o que falta e como
   resolver — nunca travar silenciosamente

6. Não criar interface visual ainda — isso é Fase 8
   Não criar RAG ainda — isso é Fase 7
