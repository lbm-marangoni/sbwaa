# SBWAA — CHANGELOG

---

## [2.19.0] — 2026-05-29 — /EARNING-CALENDAR: CALENDÁRIO DE RESULTADOS

### Added
- **`scripts/data/earnings_calendar.py`** — calendário de resultados trimestrais:
  - **Ações (AÇÃO ON/PN)**: tenta `yfinance.calendar['Earnings Date']` → se vazio, usa `earnings_dates` histórico + 91 dias (`tipo: estimado`)
  - **FIIs**: estimativa baseada no calendário CVM (~45 dias após fechamento do trimestre); datas fixas: 15/02, 15/05, 15/08, 15/11 (`tipo: estimado-fii`)
  - ETFs, RF, TD, DEB, CRI/CRA: ignorados
  - Cria automaticamente `vault/01-ativos/TICKER/earnings-TICKER-TRIMESTRE.md` (stub com template) se não existir
  - Salva `vault/00-portfolio/earnings-calendar.json` (lido pelo check_alerts)
  - Salva `vault/00-portfolio/earnings-calendar.md` (visualização Obsidian com wikilinks)
  - Output terminal: tabela dos próximos 90 dias com status confirmado/estimado

- **`scripts/alerts/check_alerts.py`** — `verificar_earnings_proximos()` implementada:
  - Lê `earnings-calendar.json`
  - Dispara `earnings_semana` (MÉDIO) no exato D-7 antes do resultado
  - Dispara `earnings_amanha` (ALTO) no exato D-1 — não dispara em dias intermediários
  - `earnings_semana` adicionado ao `ALERTAS_CONFIG` e `SEVERIDADE_ACAO`
  - `earnings_amanha` atualizado de MÉDIO para ALTO (lembrete mais urgente)

### Changed
- **`scripts/automation/tasks.py`** — `earnings_calendar` adicionado ao `MONTHLY_TASKS` (antes de `relatorio_mensal`)
- **`sbwaa.py`** — `/earning-calendar` em `COMANDOS_LOCAIS` + bloco no `/help`

---

## [2.18.0] — 2026-05-29 — SUPORTE A ATIVOS INTERNACIONAIS USD

### Added
- **`fetch_yahoo.py`** — nova função `buscar_brl_usd()`: retorna cotação BRL/USD via `BRL=X`

### Changed
- **`add_ativo.py`** — suporte a ativos USD-listed (tipo `etf-intl`):
  - Detecta `moeda: USD` via yfinance após validar o ticker
  - Busca BRL/USD automaticamente e converte PM: `$450 USD × 5.50 = R$ 2.475`
  - Armazena no vault note: `moeda: USD`, `pm_usd: 450.00`, `brl_usd_entrada: 5.50`
  - Flag `--moeda` implícita: se yfinance retorna USD, conversão é automática
  - Para B3 ETF INTL (moeda BRL): comportamento inalterado

- **`update_carteira.py`** — nova infraestrutura FX:
  - `_ler_moeda_ativo(ticker)`: lê `moeda:` do frontmatter de `vault/01-ativos/TICKER/tese.md`
  - `cotacao_intl(ticker, moeda)`: se `moeda=USD`, converte yfinance USD × BRL/USD atual
  - BRL/USD cacheado uma vez por execução (sem chamadas redundantes)
  - Nova `_exibir_fx_exposicao()`: exibe e salva seção `## 💱 Exposição Cambial` em carteira.md
    - Separa USD direto (ativos NYSE/NASDAQ) vs USD indireto (B3 ETF INTL como IVVB11)
    - Mostra BRL/USD atual, valor em USD, sensibilidade +10% e -10% câmbio

- **`stress_test.py` (calculators)** — corrigido e ampliado:
  - `impacto_cenario()`: agora usa `brl_usd_alta_pct` (estava definido mas NUNCA aplicado)
  - Nova componente FX: `peso_intl_direto × brl_usd_alta × 1.0` + `peso_intl_indireto × brl_usd_alta × 0.92`
  - FX é POSITIVO para carteira (USD assets sobem em BRL quando BRL enfraquece)
  - 2 novos cenários: `brl_usd_mais_20` (câmbio +20% isolado) e `crise_fiscal_br` (IBOV -25%, câmbio +30%)

- **`stress_test.py` (command)** — novo display e lógica:
  - `calcular_peso_intl()`: lê carteira.md + vault notes para derivar `peso_ind` e `peso_dir`
  - `exibir_stress()`: quando há exposição FX, exibe 3 colunas: Mercado% | Câmbio% | Total%
  - Exibe resumo de exposição USD ao final
  - `custom` scenario agora também recebe `peso_intl` para FX breakdown correto

---

## [2.17.0] — 2026-05-29 — /CORRELACAO: HEATMAP + FIX QUANT PIPELINE

### Added
- **`scripts/data/correlacao.py`** — heatmap de correlações da carteira:
  - Lê `quant_YYYY-MM-DD.json`; se vazio/ausente, roda `run_quant.py` inline (subprocess)
  - **Terminal**: tabela ASCII com ANSI colors (verde < 0.40 | amarelo 0.40–0.70 | vermelho ≥ 0.70)
  - **PNG**: heatmap matplotlib dark theme em `vault/02-relatorios/correlacao-YYYY-MM-DD.png`
    - N×N matriz com valores anotados + borda vermelha nos pares ≥ threshold
    - Coluna extra IBOV à direita com correlação de cada ativo
    - Colormap RdBu_r (red=+1, blue=-1, white=0)
  - **Obsidian**: `vault/02-relatorios/correlacao-YYYY-MM-DD.md` com `![[png]]`, tabela de pares, matriz completa com wikilinks, métricas de diversificação
  - Flag `--threshold` (default 0.70)
- **`sbwaa.py`** — `/correlacao` em `COMANDOS_LOCAIS` + bloco CORRELAÇÃO no `/help`

### Fixed
- **`run_quant.py` — `extrair_carteira()`** — dois bugs corrigidos:
  1. `elif dentro: break` → `elif dentro and stripped: break` — linhas em branco dentro da tabela não quebravam mais o loop prematuramente (causa raiz do cache vazio)
  2. Agora lê a coluna Tipo e filtra `TIPOS_RF_SKIP` + `TICKERS_ESPECIAIS_SKIP` (RF-OPRT, CDB001, etc.) — evita falhas em yfinance que tornavam `historicos = {}`
- **`run_quant.py` — `main()`** — `sys.exit(1)` quando `historicos` vazio substituído por save gracioso de JSON parcial (não derruba o slot morning)
- **`run_quant.py` — métricas por ativo`** — novo campo `correlacao_ibov` calculado para cada ativo (correlação direta com retornos do IBOV, não beta)

---

## [2.16.0] — 2026-05-29 — /FLUXO-CAIXA: PROJEÇÃO DE RENDA PASSIVA

### Added
- **`scripts/data/fluxo_caixa.py`** — projeção de renda passiva mês a mês (12 meses):
  - **Seção A — Renda Periódica** (ações, FIIs, ETFs): tabela calendário mês × ticker
    - Pagamentos históricos recebidos (✅), declarados futuros (📢), projetados por frequência (~)
    - Frequência detectada automaticamente (mensal/trimestral/semestral/anual) via histórico Brapi/yfinance
    - Declarados têm prioridade sobre projetados para evitar duplicatas
  - **Seção B — Valorização RF/TD/DEB/CRI-CRA** (separada): crescimento mensal estimado
    - Bruto: PM × qtd × taxa_mensal (CDI/IPCA/PRE via indexador+taxa de tese.md)
    - Líquido: bruto − IR estimado (alíquota regressiva pelo prazo de holding em cada mês)
    - CRI/CRA: IR isento explicitamente; IOF = zero (posições ativas > 30 dias)
  - **Alerta vs meta**: lê `alvo_mensal` de `vault/00-portfolio/metas.md`; alerta ⚠️ se < meta
  - Output: `vault/00-portfolio/fluxo-caixa.md` com wikilinks `[[TICKER]]` para cada ativo
  - Importa funções de `dividendos.py` (sem duplicar lógica de fetch/análise)
- **`scripts/automation/tasks.py`** — `fluxo_caixa_build` no slot WEEKEND (toda semana, domingo)
- **`sbwaa.py`** — `/fluxo-caixa` em `COMANDOS_LOCAIS` + bloco FLUXO DE CAIXA no `/help`

---

## [2.15.1] — 2026-05-29 — PERSISTÊNCIA DE P&L HISTÓRICO

### Added
- **`update_carteira.py`** — salva `vault/02-relatorios/diarios/YYYY-MM-DD.json` a cada execução:
  - `patrimonio_total`, `total_investido`, `pl_total_rs`, `pl_total_pct`
  - `por_classe`: valor_rs e peso_pct por classe de ativo
  - `posicoes`: detalhe completo por ticker (qtd, pm, preco_atual, valor_rs, pl_rs, pl_pct, peso_pct)
  - Campo `estimado: true` marca posições RF sem cotação em bolsa
  - Arquivo sobrescrevido se rodar mais de uma vez no mesmo dia (versão mais recente do dia)

- **RF Estimation** em `update_carteira.py` — posições RF/TD/DEB/CRI-CRA recebem preço estimado:
  - CDI-linked: `selic_acum_mes` (BCB série 4189) composta desde `data_entrada`; multiplicador % do CDI
  - IPCA-linked: `ipca_mensal` (série 433) + spread anual
  - PRE: taxa fixa anual pro-rata
  - Fallback: PM × qtd se BCB indisponível ou `data_entrada` ausente em `tese.md`
  - BCB cache carregado uma vez por execução (até 7 dias de cache)

- **`simulacao_carteira.py --real`** — novo modo de curva de equity real:
  - Lê todos os JSONs de `vault/02-relatorios/diarios/YYYY-MM-DD.json`
  - Normaliza patrimônio_total a base 100 no primeiro ponto
  - Plota Carteira vs IBOV vs CDI com retornos anotados e alpha vs cada benchmark
  - Salva `logs/simulacao/equity_real_YYYY-MM-DD.png`
  - Exibe resumo no terminal (retorno, alpha vs IBOV e CDI, n° de snapshots)
  - Compatível com `--no-graficos`; se < 2 snapshots, exibe aviso e continua

- **`scripts/automation/tasks.py`** — nova task `update_carteira_eod` no slot EOD:
  - Roda após `market_snapshot_eod`, antes de `performance_build`
  - Garante snapshot diário às 17h sem intervenção manual

### Changed
- Slot EOD agora tem 4 tasks: market_snapshot → update_carteira → performance_build → /snapshot

---

## [2.15.0] — 2026-05-29 — /PERFORMANCE: BENCHMARK AUTOMÁTICO

### Added
- **`scripts/data/performance.py`** — benchmark local sem IA:
  - Retorno da carteira vs IBOV, CDI, IPCA para MTD / YTD / 12m
  - Carteira ponderada por capital investido (qtd × PM); RF estimada por indexador/taxa de tese.md
  - CDI e IPCA via BCB SGS (cache local fetch_bcb.py; auto-fetch se cache > 7 dias)
  - IBOV via yfinance (`^BVSP`)
  - Alpha vs IBOV e vs CDI (excesso de retorno simples)
  - Beta vs IBOV, Tracking Error, Sharpe, Volatilidade, Max Drawdown (base: 12m)
  - Série diária do portfólio construída por posição (equity via yfinance + RF via CDI diário)
  - Decomposição de retorno MTD por classe (Ações BR, FIIs, ETFs, RF, TD)
  - Salva snapshot mensal em `vault/02-relatorios/performance-historico.json`
  - Cada execução atualiza o snapshot do mês corrente (sem duplicar)
  - RF com `indexador=CDI`: `retorno = CDI_periodo × taxa%`; IPCA+spread; PRE taxa fixa
- **`scripts/automation/tasks.py`** — nova task `performance_build` no slot EOD
- **`sbwaa.py`** — `/performance` em `COMANDOS_LOCAIS` + bloco PERFORMANCE no `/help`

---

## [2.14.1] — 2026-05-29 — /VENDER RF/TD: IR REGRESSIVO + IOF + RESGATE PARCIAL

### Changed
- **`scripts/data/vender_ativo.py`** — reescrito para suportar RF/TD/DEB/CRI-CRA:
  - Nova flag `--valor X` para resgate por valor total bruto (em vez de `--preco` por unidade)
  - Nova flag `--data-entrada YYYY-MM-DD` como override da data da aplicação
  - Leitura automática de `data_entrada` do frontmatter de `vault/01-ativos/TICKER/tese.md`
  - Cálculo automático de IR regressivo (22,5%→15%) e IOF (96%→0%) para RF/TD/DEB via `calculos_tributarios.py`
  - CRI/CRA: IR isento para PF (Lei 12.431/2011) — exibido explicitamente
  - DEB: aviso sobre verificar se é incentivada (isenção) no extrato
  - Resgate parcial funciona com `--quantidade 0.6 --valor 3300` (60% de uma posição com qtd=1)
  - P&L exibido em bruto e líquido separadamente para RF
  - Rótulo de unidade corrigido: "ações" → "unidades" (RF/DEB/CRI-CRA) / "títulos" (TD)
  - P&L histórico registrado como "X% bruto / Y% líq." para RF
- **`sbwaa.py`** — bloco `/vender` no `/help` atualizado com sintaxe RF e exemplos

---

## [2.14.0] — 2026-05-29 — /ALERTA: MONITOR DE PREÇOS BIDIRECIONAL

### Added
- **`scripts/alerts/extract_targets.py`** — parser automático de vault/01-ativos/:
  - Extrai preços de teto, alvo, valor justo, chão, nível de entrada, stop e downside pessimista
  - Lê frontmatter (`preco-alvo:`) e corpo do markdown com regex padronizada
  - Prioridade de leitura: analise > pm-decisao > tese-rapida > tese
  - Deduplica por tipo (o arquivo mais recente vence por tipo de alerta)
  - Flags: `--ticker TICKER` (individual) e `--todos` (reprocessar toda a vault)
  - Salva em `vault/00-portfolio/alertas.json`

- **`scripts/alerts/alerta_cmd.py`** — CLI para gerenciar alertas:
  - `--listar`: alertas ativos agrupados por ticker
  - `--historico`: histórico com contagem de não lidos/lidos
  - `--verificar`: dispara check_alerts agora (fora do scheduler)
  - `--remover TICKER`: remove alertas de um ticker

- **`vault/05-risk/alertas-historico.md`** — criado automaticamente no primeiro disparo:
  - Formato Obsidian checkbox: `- [ ]` (não lido) / `- [x]` (lido)
  - Novos alertas inseridos no topo (ancoragem via comentário HTML)
  - Contém: timestamp, severidade, ticker, cotação vs alvo, ação sugerida

- **Novo slot Task Scheduler `SBWAA_Alerta`** — seg–sex a cada 60 min:
  - Horário: 10:00–17:00 (controle de pregão em main.py, não no scheduler)
  - Roda `check_alerts.py` (incluindo verificação de preços-alvo)
  - Custo: ~20–30s por execução, 0 tokens Claude

### Changed
- **`scripts/alerts/check_alerts.py`** — três extensões:
  - Nova `verificar_precos_alvo()`: compara cotação yfinance com alertas.json; remove one-shot ao disparar
  - Nova `adicionar_ao_historico()`: appenda alertas disparados em alertas-historico.md
  - Nova `_notificar()`: toast Windows via notifier.py para severidade CRÍTICO/ALTO
  - `verificar_alertas()` agora chama `verificar_precos_alvo()`
  - `main()` agora chama `adicionar_ao_historico()` e `_notificar()`

- **`scripts/automation/tasks.py`** — novo `ALERTA_TASKS` com task `check_precos_alvo`
- **`scripts/automation/main.py`** — novo `elif slot == "alerta"` com guard de dia útil e horário
- **`scripts/automation/setup_scheduler.py`** — `SBWAA_Alerta` adicionado à lista; `--testar` aceita `alerta`
- **`sbwaa.py`** — `/alerta` adicionado a `COMANDOS_LOCAIS`; bloco `ALERTAS DE PREÇO` no `/help`
- **`vault/_templates/pm-decisao.md`** — `## Nível de entrada` e `## Stop / Revisão` agora têm linhas padrão parseable (`**Nível de entrada:** R$ —` e `**Stop:** R$ —`)
- **`.claude/commands/pm.md`** — Passo 4 (novo): roda `extract_targets.py --ticker` após salvar; instrução de formato obrigatório para Nível de entrada e Stop. Passo de decisoes.md renumerado para Passo 5
- **`.claude/commands/tese.md`** — Passo 5 (novo): roda `extract_targets.py --ticker`; instrução de formato para seção Preço Teto
- **`.claude/commands/analisar.md`** — Etapa 10 (nova): roda `extract_targets.py` para cada ticker; instrução de preenchimento do frontmatter `preco-alvo:`

---

## [2.13.2] — 2026-05-29 — COMANDO /att-info-system

### Added
- **`.claude/commands/att-info-system.md`** — novo slash command de fechamento de sessão completo:
  - Fase 1: leitura de estado (VERSION.md, git log, git diff, git status, versões de todos os docs)
  - Fase 2: diagnóstico automático — detecta se é MAJOR/MINOR/PATCH ou só sync de docs
  - Fase 3: CHANGELOG — cria entrada se ausente, complementa se incompleta
  - Fase 4: atualizações mecânicas de versão em todos os docs (README, GUIA-COMANDOS, REFERENCIA, WORKFLOW, APRESENTACAO, MASTER-BLUEPRINT, LOGO, sbwaa.py)
  - Fase 5: atualizações de conteúdo — sbwaa.py /help, ui.py botões, GUIA-COMANDOS, REFERENCIA, WORKFLOW, APRESENTACAO, MASTER-BLUEPRINT
  - Fase 6: verificação de segurança git (bloqueia vault/00-portfolio/, .env, caches privados)
  - Fase 7: ciclo git completo — add seletivo, commit, push, gh release create (MINOR/MAJOR obrigatório; PATCH conforme criticidade)
  - Fase 8: relatório final compacto do que foi feito
- **`sbwaa.py`** — `/att-info-system` adicionado ao dict `COMANDOS_IA` e ao `/help` (bloco SISTEMA)
- **`docs/GUIA-COMANDOS.md`** e **`docs/SBWAA-REFERENCIA.md`** — documentação do novo comando

---

## [2.13.1] — 2026-05-29 — FIX /pm MODO APORTE

### Fixed
- **`.claude/commands/pm.md`** — GUARD bloqueava `/pm` sem argumentos; substituído por roteamento A/B/C:
  - Caso A (`$ARGUMENTS` vazio): dispara Modo Aporte interativo completo (5 passos)
  - Caso B (`$ARGUMENTS` é número): Modo Aporte com valor pré-preenchido (pula pergunta de valor)
  - Caso C (`$ARGUMENTS` é ticker): fluxo de análise original mantido intacto

---

## [2.13.0] — 2026-05-29 — MOTOR TRIBUTÁRIO + RF OPORTUNIDADE

### Added
- **`scripts/data/calculos_tributarios.py`** — motor tributário completo:
  - IOF regressivo (Decreto 6.306/2007): 96%→0% dias 1-30, sobre rendimentos
  - IR RF regressivo (Lei 11.033/2004): 22,5%→20%→17,5%→15% por prazo
  - IR renda variável: ações (15% swing / 20% day / isenção R$20k), FIIs (20% ganho / isento dividendos), ETF BR/Intl (15%)
  - `bloco_rf_oportunidade()`: formata bloco de aporte para o PM com bruto/IOF/IR/líquido
  - `tabela_ir_por_classe()`: tabela markdown de referência tributária por tipo de ativo

- **`vault/00-portfolio/rf-oportunidade.md`** — arquivo de controle da Caixinha Nubank:
  - Saldo bruto + data depósito (bloco YAML machine-readable)
  - Tabela de estimativa tributária atualizada automaticamente
  - Histórico de movimentações (depósitos e retiradas para aportes)
  - Referência de IOF/IR do RDB 100% CDI

- **`scripts/data/rf_oportunidade.py`** — script de gerenciamento da RF Oportunidade:
  - `--saldo`: exibe bruto, rendimento, IOF, IR, líquido disponível
  - `--depositar X`: registra depósito
  - `--retirar X --destino TICKER`: registra retirada para aporte
  - `--atualizar-saldo X --data-deposito YYYY-MM-DD`: sincroniza com saldo real
  - `--checar-aporte X`: exibe bloco de validação para o PM

- **`/oportunidade`** — novo comando local em `sbwaa.py`

### Changed
- **`portfolio-manager/SKILL.md`** — Passo 5 (Fluxo de Aporte) reformulado:
  - Novo Passo B1: lê `rf-oportunidade.md` e exibe bloco com saldo bruto, IOF estimado, IR estimado, líquido disponível e movimentação proposta
  - Alerta automático quando IOF incide (< 30 dias) e quando saldo é insuficiente
  - Instrução de registro pós-confirmação via `/oportunidade --retirar`

- **`vault/00-portfolio/ips.md`** — adicionada seção "Tributação por Classe" com tabela completa de IR/IOF por tipo de ativo; nota sobre RF Oportunidade no bucket RF

- **`vault/00-portfolio/carteira.md`** — adicionada seção "RF Circulante — Oportunidade" com referência ao arquivo; Resumo passa a distinguir patrimônio de investimentos vs. Oportunidade

- **Templates de relatório** — P&L líquido estimado adicionado em todos:
  - `snapshot-diario.md`: colunas P&L bruto / P&L líq. est. / IR alíq.
  - `semana.md`: colunas P&L bruto / P&L líq. est. + tabela dividendos bruto/líquido
  - `mensal.md`: colunas P&L bruto / P&L líq. est. + seção Dividendos do Mês com IR

- **`earnings.md`**: DPA marcado como "bruto" com nota de isenção de IR para FIIs

- **`sbwaa.py`**: versão → v2.13.0; comando `/oportunidade` adicionado ao help

### Versões de módulo
- `investments` → **v1.21.0** (RF Oportunidade + motor tributário)

---

## [2.12.0] — 2026-05-27 — AUTOMATION LAYER: TASK SCHEDULER LOCAL

### Added
- **`scripts/automation/` — nova camada de automação modular:**
  - `tasks.py` — registro declarativo de tarefas por slot (morning/eod/weekend)
  - `runner.py` — executor unificado: `run_python()` + `run_claude()` via `claude -p` não-interativo
  - `notifier.py` — toast notification Windows via PowerShell/NotifyIcon (sem pacotes externos)
  - `main.py` — dispatcher principal com `--slot` e `--dry-run`; lógica de dia útil, feriados BR, 1° fds do mês
  - `setup_scheduler.py` — instala/remove/testa tarefas reais no Task Scheduler via `schtasks.exe`; ativa WakeToRun + StartWhenAvailable automaticamente
  - `launcher.vbs` — lança Python sem janela de console (necessário para Task Scheduler silencioso)

- **3 slots de execução agendados:**
  - `morning` (seg–sex 07:45): RSS → market_snapshot → quant → risk → alertas → `/morning-call`
  - `eod` (seg–sex 17:00): market_snapshot EOD → alertas EOD → `/snapshot`
  - `weekend` (sáb–dom 08:00): `/relatorio-semanal` (domingos) + `/relatorio-mensal` (1° fds do mês)

- **PC desligado:** `WakeToRun` acorda o PC do sleep/hibernate; `StartWhenAvailable` roda tarefa perdida no próximo boot

### Changed
- Módulo `heartbeat` → **v2.0.0**: antigo `heartbeat.py` mantido para execução manual; novo sistema o supersede no agendamento
- Global → **v2.12.0**

---

## [2.11.2] — 2026-05-27 — VARREDURA COMPLETA DE TESTES + CORREÇÕES DE ROBUSTEZ

### Fixed
- **`diagnostico.py`** — UnicodeEncodeError no Windows: adicionado setup UTF-8 no topo (os.environ PYTHONUTF8, sys.stdout.reconfigure)
- **`gerar_relatorio_testes.py`** — UnicodeEncodeError ao imprimir VERSION.md com emojis: adicionado setup UTF-8; contagens atualizadas (7→8 agentes, 13→14 comandos)
- **`sbwaa.py /help`** — versão exibida desatualizada: `v2.11.0` → `v2.11.1` (e agora → v2.11.2)
- **`optimize_expansao.py`** — conflito de módulo `calculators` quando stress_test carregado antes no mesmo processo: adicionado cache clearing antes do import

### Verificado / Testado (55/55 OK)
- Sintaxe Python: 68 arquivos — 0 erros
- Calculadoras Quant + Risk: todos os testes passam
- Módulos Econometrician (GARCH, Beta Dinâmico, Fator Modelo, Drawdown Avançado, Rolling Corr): OK
- Comandos: `/stress-test`, `/watchlist`, `/ips`, `/snapshot`, `/knowledge`, `/status`, `/help`: todos OK
- Cache JSON: 116 arquivos — 0 inválidos
- Vault .md: 20 arquivos — 0 frontmatters quebrados
- Portfolio files: carteira.md, ips.md, historico-trades.md, metas.md — todos presentes
- Docs: VERSION, CHANGELOG, README, GUIA-COMANDOS, SBWAA-LOGO — todos em v2.11.2

---

## [2.11.1] — 2026-05-26 — OUTPUTS VISUAIS OBSIDIAN + DESPOLUÇÃO DE COMANDOS

### Added
- **`carteira.md` — seções visuais embutidas** (Option B — append após `## Resumo`):
  - `## 📊 Alocação por Classe`: tabela com % atual, alvo IPS, gap e barra `█░` (20 chars)
  - `## 📈 Posições — Detalhes Visuais`: % total da carteira, % dentro da classe, barra por ativo
  - Callouts Obsidian: `> [!warning]` (gap 5–10%), `> [!danger]` (gap > 10% ou concentração > 20%)
  - Regeneradas automaticamente a cada execução de `/carteira` (substituição via regex)
- **`vault/02-relatorios/dividendos.md`** — relatório Obsidian completo de proventos:
  - Frontmatter com tags, data, DY ponderado, renda mensal
  - Seções: Resumo de Renda, Próximos Pagamentos, Pagos no ano (tabela completa), Total desde entrada, YoC, links
  - Sobreescrito a cada `/dividendos`
- **`vault/02-relatorios/risco-carteira.md`** — snapshot Obsidian de risco:
  - Métricas: Sharpe, Vol, VaR, CVaR, Drawdown, Beta, Correlação, Concentração
  - Circuit Breakers com callouts (`[!tip]`/`[!danger]`)
  - Fronteira eficiente Markowitz com tabela de ajustes sugeridos
  - Sobreescrito a cada `/risco-carteira`
- **`vault/02-relatorios/stress-test.md`** — snapshot Obsidian de stress test:
  - Todos os cenários com ícones por severidade (🟢/🟡/🔴/⛔)
  - Callout destacando pior cenário
  - Circuit breakers de referência
  - Sobreescrito a cada `/stress-test`
- **`vault/02-relatorios/watchlist-YYYY-MM-DD.md`** — snapshot **datado** da watchlist:
  - Frontmatter com data e nº de ativos
  - Tabela completa com veredictos, frescor e preços-alvo
  - Mantém histórico — não sobreescreve datas anteriores
- **`SBWAA-WORKFLOW.md`** — nova seção "Outputs visuais" documentando todos os arquivos gerados, modo (sobreescrito vs datado) e formatação Obsidian usada
- Formatação Obsidian padronizada: callouts `[!info/warning/danger/tip]`, barras `█░`, emoji headers

### Changed
- **`dividendos.py`** terminal slimado: Seção 2 (pagos no ano) exibe apenas top 3 + total; Seção 3 (total histórico) movida para o .md; Seção 4 (YoC) mantida compacta; pointer `📄 Relatório completo` adicionado
- **`carteira.py`**: pointer `📄 Visão visual completa: vault/00-portfolio/carteira.md` ao final
- **`watchlist.py`**: pointer `📄 Snapshot salvo` com path do arquivo gerado
- **`risco_carteira.py`** e **`stress_test.py`**: pointer `📄 Relatório completo` ao final
- `investments`: v1.20.0 → **v1.20.1**
- Global → **v2.11.1**

---

## [2.11.0] — 2026-05-25 — MODO APORTE NO /PM

### Added
- **`/pm` sem ticker → Modo Aporte interativo** — PM distribui capital novo entre múltiplos ativos da watchlist/carteira:
  - Perguntas sequenciais: valor (R$), classe de ativo, nº de ativos, campo livre de restrições
  - Atalho `/pm 700` pula a pergunta de valor e entra direto nas demais
  - Seleção automática de candidatos: varre `vault/01-ativos/` + carteira, filtra COMPRAR/AUMENTAR, ranqueia por score (gap IPS, frescor, completude)
  - Distribuição de capital: 60% igualitário + 40% ponderado por gap de IPS da classe
  - Cotas estimadas calculadas localmente pelo preço atual (cache ou carteira)
  - Validação pelo PM (claude-opus-4-6): ajuste de pesos, justificativa por ativo, alertas de IPS
  - Loop de ajuste: campo livre para refinar sugestão sem reiniciar o fluxo
  - Salva `vault/00-portfolio/pm-aporte-YYYY-MM-DD.md` + linha em `decisoes.md`
- **Auto-reflow após /analisar**: quando candidatos insuficientes, PM lista pendentes, oferece executar `/analisar` via subprocess e **retoma automaticamente** com os mesmos parâmetros ao concluir
- `run_pm.py`: `ticker` agora é argumento opcional (nargs="?") — `argparse` não quebra mais sem ticker

### Changed
- `run_pm.py`: imports adicionados (`subprocess`, `date` de datetime)
- `investments`: v1.19.3 → **v1.20.0**
- Global → **v2.11.0**

---

## [2.10.4] — 2026-05-25 — GLOSSÁRIO TÉCNICO SBWAA

### Added
- **`docs/SBWAA-GLOSSARIO.md`** — guia de referência de todos os termos e siglas técnicas do sistema em português:
  - 11 seções cobrindo ~80+ termos: sistema SBWAA, agentes do pipeline, mercado financeiro BR, tipos de ativo, indicadores fundamentalistas, valuation, risco e métricas quantitativas, econometria, macro global, termos operacionais e conceitos de investimento

### Changed
- Global → **v2.10.4**

---

## [2.10.3] — 2026-05-25 — FLUXO INTERATIVO DE APORTE EM /PM E /ANALISAR

### Added
- **Fluxo de aporte interativo** em `/pm` (Passo 3) e `/analisar` (Etapa 8b):
  - **A** — "Deseja aportar agora?" → Não: encerra | Sim: continua
  - **B** — "Quanto deseja aportar?" (R$)
  - **C** — Validação do PM: sizing sugerido vs planejado, concentração após, VaR estimado após; status ✅/⚠️/🚨
  - **D** — Confirmação adicional se acima do ideal ou em violação do IPS (a/b/c)
  - **E** — Bloco de confirmação final + registro do `aporte_planejado` no frontmatter do pm-decisao
- Campo `aporte_planejado` adicionado ao frontmatter de `pm-decisao-*.md` e à tabela `decisoes.md`
- PM SKILL.md: Passo 5 reescrito para refletir fluxo interativo (antes era "quando solicitado via script")

### Changed
- `investments`: v1.19.2 → **v1.19.3**
- Global → **v2.10.3**

---

## [2.10.2] — 2026-05-25 — INVESTIDOR10: SCRAPING DE DADOS COMPLEMENTARES

### Added
- **`scripts/data/fetch_investidor10.py`** — scraping do Investidor10 como fonte complementar:
  - FIIs: P/VP, DY 12m, vacância, VPA por cota, DPA último, DPA anualizado (12m), dividendos mensais (últimos 24), patrimônio líquido, número de cotas/cotistas, taxa de administração, segmento, liquidez diária
  - Ações: P/L, P/VP, LPA, VPA, DY, ROE, EV/EBITDA, margens (EBITDA/líquida/bruta), payout, liquidez diária
  - Enriquece automaticamente `fundamentals_{TICKER}.json` com campos `_i10_*` para rastreabilidade de fonte
  - Cache com TTL 4h (`investidor10_{TICKER}_{DATA}.json`)
- `/analisar` e `/tese` — `fetch_investidor10.py` adicionado à ETAPA 0 (Preparação)

### Changed
- `investments`: v1.19.1 → **v1.19.2**
- Global → **v2.10.2**

---

## [2.10.1] — 2026-05-25 — YAHOO FINANCE: SUBSTITUIÇÃO DO BRAPI + TEMPLATES ENRIQUECIDOS

### Added
- **`scripts/data/fetch_fundamentals.py`** — substitui `fetch_brapi.py` por Yahoo Finance (`yfinance`). Sem API key necessária. Mesmo formato de saída (`fundamentals_{TICKER}_{DATA}.json`). Suporte a ações BR (`.SA`) e FIIs. Normalização de DY (Yahoo retorna % em vez de decimal para alguns ativos BR).
- **`vault/_templates/equity-research.md`** enriquecido com: Premissas como tabela classificada, Stress Test (3 cenários), Preço Teto/Chão completo (Graham + Bazin), Precificação do Mercado com consenso, Top 3 Riscos, Catalisadores, Para o Portfolio Manager
- **`vault/_templates/earnings.md`** enriquecido com: Números do Trimestre (QoQ/YoY), Resultados vs Estimativa, Tendência 4 trimestres, Flags para o Portfolio Manager
- **`vault/_templates/pm-decisao.md`** enriquecido com: justificativa paragrafos, Síntese da Equipe (tabela 6 agentes), Portfólio Métricas HF (bloco ASCII)
- **`vault/_templates/tese-ativo.md`** enriquecido com: Valuation Simplificado (tabela completa)

### Fixed
- **Bazin DY** nos templates: corrigido de 6% (errado) para 8% (padrão SBWAA)
- **Referências Brapi** em todos os SKILL.md, comandos e scripts ativos substituídas por `fetch_fundamentals`/Yahoo Finance
- **`earnings-reviewer/SKILL.md`** limpado: referências a "Brapi" substituídas por "Yahoo Finance"

### Changed
- Todos os comandos (`.claude/commands/`) atualizados: `fetch_brapi.py` → `fetch_fundamentals.py`; cache `brapi_*` → `fundamentals_*`
- `investments`: v1.19.0 → **v1.19.1**
- Global → **v2.10.1**

---

## [2.10.0] — 2026-05-25 — VAULT OBSIDIAN: TEMPLATES + SAVING + RISK SNAPSHOTS

### Added
- **`vault/_templates/`** — 11 templates Obsidian prontos para uso via Insert Template:
  `tese-ativo`, `analise-ativo`, `earnings`, `equity-research`, `pm-decisao`,
  `snapshot-diario`, `morning-call`, `macro-mundo`, `risk-snapshot`, `semana`, `mensal`
- **`/pm` Passo 3** — após emitir veredicto, agora salva automaticamente:
  - Linha na tabela de `vault/00-portfolio/decisoes.md` (histórico permanente de decisões)
  - Arquivo `vault/01-ativos/{TICKER}/pm-decisao-{TICKER}-YYYY-MM-DD.md` com frontmatter estruturado
- **`/relatorio-semanal` Passo 4** — gera risk snapshot semanal em `vault/05-risk/snapshots/risk-YYYY-MM-DD.md`
  com tabela de métricas vs limites IPS (VaR, CVaR, drawdown, concentração, circuit breakers)
- **Obsidian `app.json`** — configurado `templateFolder: "_templates"` (plugin Templates agora funciona)
- **`graph.json` `#screening`** — cor amarelo-claro (rgb 16761095) adicionada ao color group do graph view

### Changed
- **`workspace.json`** — removidas 30+ referências a arquivos inexistentes (`lastOpenFiles` limpo)
- `investments`: v1.18.5 → **v1.19.0**
- `interface`: v2.4.0 → **v2.5.0**
- Global → **v2.10.0** (MINOR bump — novas funcionalidades)

---

## [2.9.0] — 2026-05-25 — REBRANDING PAINEL + 6 FEATURES DE UI

### Added
- **Rebranding completo** do painel (`interface/ui.py`): estética terminal financeiro com paleta ciano (#00D4FF), fundo profundo (#09090F), fontes Consolas
- **Sidebar** com navegação por página (Portfólio / Análise / Mercado / Relatórios / Knowledge)
- **Header live**: IBOV, BRL/USD, SELIC, PATRIMÔNIO, PROVENTOS + relógio em tempo real
- **Toast notifications**: feedback visual no canto superior direito (sem poluir o output)
- **Distinção visual local vs IA**: botões cinza (local) vs ciano com tag `[IA]` (clipboard)
- `/watchlist --rever` — botão na seção de Ações Rápidas em Portfólio
- `/ips --editar` — botão IA junto ao IPS em Ações Rápidas
- **Simulação MC com flags opcionais**: campos `--patrimonio`, `--aporte` e checkbox `--no-graficos` em seção dedicada em Portfólio
- `/status` — botão no rodapé da sidebar (acesso rápido)
- **RF fields no form de Adicionar**: Indexador (combo CDI/IPCA/Selic/PRE/IGPM), Taxa (%) e Vencimento — repassados como flags ao `/adicionar`
- **Investimento do Dia com categoria**: combobox `qualquer/fii/acao/etf-br/etf-intl/rf/td` na página Mercado
- **`/analisar` Etapa 9**: outputs separados por tipo — específicos do ativo em `vault/01-ativos/{TICKER}/` (earnings, valuation, pm-decisao, consolidado), geral em `vault/02-relatorios/diarios/` (market-researcher)

### Changed
- `interface`: v2.3.1 → **v2.4.0**
- Global → **v2.9.0** (MINOR bump — nova funcionalidade)

---

## [2.8.9] — 2026-05-22 — /ADICIONAR COM CAMPOS DE RENDA FIXA

### Added
- `add_ativo.py`: flags opcionais para RF/TD/DEB/CRI-CRA:
  - `--nome "CDB XP 110% CDI"` — nome legível do produto
  - `--indexador CDI|IPCA|Selic|PRE|IGPM` — indexador da remuneração
  - `--taxa "110%"` — taxa (110% CDI, +6% IPCA, 13.5% prefixado)
  - `--vencimento YYYY-MM-DD` — data de vencimento
  - `--setor` vira **emissor** para RF (XP, BTG, Nubank, Tesouro Nacional...)
- Auto-skip de validação de API para tipos off-exchange (renda-fixa, tesouro, debenture, cri-cra) — nunca têm cotação em bolsa
- Nota do ativo (`tese.md`) gerada com frontmatter estruturado (`indexador`, `taxa`, `vencimento`, `emissor`) e tabela de detalhes em vez de "análise pendente"
- `/help` do `sbwaa.py` atualizado com flags RF e dois exemplos completos

### Changed
- `investments`: v1.18.4 → **v1.18.5**
- Global → **v2.8.9**

---

## [2.8.8] — 2026-05-22 — RENDA PASSIVA REAL + BARRA DE PROGRESSO NAS METAS

### Fixed
- **Renda Passiva**: yield calculado de `total_no_ano / patrimônio` (correto e anualizado) em vez de `total_recebido / patrimônio` (acumulado histórico distorcido pelo tempo de carteira)
- **Renda atual**: `total_no_ano / 12` = renda mensal estimada real dos dividendos deste ano — antes não existia, usava só projeção

### Added
- Barra de progresso `[###---]` em todas as metas: patrimônio, renda passiva e metas livres
- Linha "Atual: R$X/mes [barra] XX%" na renda passiva — mostra onde está hoje vs alvo
- Linha "Atual: [barra] XX%" no patrimônio e nas metas livres

### Changed
- `investments`: v1.18.3 → **v1.18.4**
- Global → **v2.8.8**

---

## [2.8.7] — 2026-05-22 — PROJECAO DE METAS NO /CARTEIRA

### Added
- `carteira.py`: seção **METAS — PROJECAO** ao final do output do `/carteira`, logo após a projeção geral
- `parse_metas()`: lê `vault/00-portfolio/metas.md` e extrai patrimônio alvo, renda passiva alvo e metas livres
- `_anos_para_atingir_mc()`: MC iterativo (1k sims, tracking anual) que retorna o ano em que P50 cruza o alvo com aporte mensal
- `_fmt_projecao()`: formata resultado de projeção com status vs prazo (OK / ATENCAO + anos de diferença)
- `exibir_projecao_metas()`: renderiza projeção por tipo de meta:
  - **Patrimônio Total**: analítico sem aporte (`ln(meta/P) / drift_anual`) + MC com aporte
  - **Renda Passiva**: estima patrimônio necessário via yield (proventos/patrimônio ou default 6% a.a.) → mesmo MC
  - **Metas Livres**: projeção linear `faltam / aporte_mensal` em meses, com status vs `data_alvo`

### Changed
- `investments`: v1.18.2 → **v1.18.3**
- Global → **v2.8.7**

---

## [2.8.6] — 2026-05-22 — PROJECAO COM APORTE HISTORICO NO /CARTEIRA

### Added
- `carteira.py`: `calcular_aporte_medio()` — lê `historico-trades.md`, agrupa compras por mês (YYYY-MM) e retorna média mensal + n_meses de histórico
- `carteira.py`: projeção agora exibe **dois cenários** lado a lado:
  - *Sem aportes adicionais*: P10/P50/P90 para 10/20/30 anos
  - *Mantendo aporte médio de R$ X/mes*: P10/P50/P90 + coluna "Ganho vs sem" (diferença das medianas)
  - Se sem histórico de aportes: mensagem orientativa + cenário base mantido
- `carteira.py`: `_mc_finais()` — Monte Carlo unificado com suporte a aporte mensal (loop diário quando aporte > 0, vetorizado quando = 0)

### Changed
- `investments`: v1.18.1 → **v1.18.2**
- Global → **v2.8.6**

---

## [2.8.5] — 2026-05-22 — /SIMULACAO + PROJECAO INTEGRADA AO /CARTEIRA

### Added
- `scripts/simulacao_carteira.py`: análise quantitativa de longo prazo
  - **Parte B (Backtest)**: 5 anos histórico com proxies IPS (BOVA11/KNRI11/IVVB11/CDI/IPCA+5%), vs IBOVESPA e CDI; painel triplo: retorno acumulado, rolling 12m, drawdown
  - **Parte A (Monte Carlo)**: GBM com correção Itô (drift = μ − σ²/2), 10k simulações, fan chart P5/P25/P50/P75/P95, suporte a `--aporte` mensal
  - `--no-graficos`: modo terminal sem geração de PNGs
  - Salva `logs/simulacao/params_cache.json` com μ e σ anualizados para consumo pelo `/carteira`
  - Gráficos dark mode em `logs/simulacao/backtest_YYYY-MM-DD.png` e `montecarlo_YYYY-MM-DD.png`
- `/carteira` (`carteira.py`): seção **PROJECAO DE LONGO PRAZO** ao final do output
  - Lê `params_cache.json`; roda Monte Carlo rápido em processo (5k sims, sem rede)
  - Exibe P10 / P50 / P90 para 10, 20 e 30 anos com patrimônio real da carteira
  - Carteira vazia: mostra projeção com R$ 10.000 de exemplo
  - Sem cache: instrui executar `/simulacao` primeiro
- `sbwaa.py`: `/simulacao` adicionado a `COMANDOS_LOCAIS`; help atualizado
- `requirements.txt`: `matplotlib>=3.9.0` adicionado

### Changed
- `investments`: v1.18.0 → **v1.18.1**
- Global → **v2.8.5**

---

## [2.8.4] — 2026-05-22 — FIX UI: PROJECT_ROOT + /METAS REGISTRADO

### Fixed
- `interface/ui.py`: `PROJECT_ROOT` corrigido de `.parent` para `.parent.parent` — comandos do painel apontavam para `interface/sbwaa.py` (inexistente) em vez do root do projeto
- `sbwaa.py`: `/metas` adicionado ao dict `COMANDOS_IA` — estava documentado no `/help` e no painel mas não era roteado, causando "Comando não reconhecido"

### Changed
- `interface`: v2.3.0 → **v2.3.1**
- Global → **v2.8.4**

---

## [2.8.3] — 2026-05-22 — ECONOMETRICIAN EXPANDIDO + VEREDICTOS CONTEXTUAIS EM TODOS OS COMANDOS

### Added
- `run_pm.py`: `carregar_econometria()` — lê cache `econometria_{TICKER}_{DATA}.json` (janela de 8 dias); dados passados ao PM no bloco ECONOMETRICIAN do prompt
- `run_pm.py`: `montar_prompt_sizing_reducao()` — parecer de sizing para REDUZIR (venda parcial) e SAIR (saída total); PM calcula peso atual → novo peso e impacto em VaR/Sharpe
- `.claude/commands/rebalancear.md`: leitura de caches econométricos por ativo; tabela "Sinais Econométricos por Ativo" com regras de incorporação (GARCH ALTA → REDUZIR, Calmar < 0.5 → REDUZIR, corr instável → diversificação em risco, sinais positivos → reforçam MANTER/AUMENTAR)
- `.claude/commands/revisar-carteira.md`: leitura de caches econométricos por ativo; PM instruído a usar sempre Modo B (todos os ativos já estão na carteira) e incorporar bullets "Para o PM" do Econometrician
- `.claude/commands/morning-call.md`: seção "Alertas Econométricos" — exibe apenas alertas críticos (GARCH ALTA, beta crescente, correlação instável); omite silenciosamente se tudo normal

### Changed
- `run_pm.py`: detecção automática de Modo A vs Modo B — lê carteira e calcula peso atual + P&L; exibe "[Modo A]" ou "[Modo B]" no startup; passa `posicao_atual` ao prompt
- `run_pm.py`: fluxo interativo adaptado por veredicto — COMPRAR/AUMENTAR pergunta "quanto alocar"; REDUZIR pergunta "quanto vender"; SAIR confirma saída total; MANTER registra sem sizing
- `run_pm.py`: `extrair_veredicto()` reconhece os 7 veredictos: AUMENTAR/MANTER/REDUZIR/SAIR/COMPRAR/AGUARDAR/EVITAR
- `run_pm.py`: `montar_prompt_pm()` aceita `posicao_atual` e `econometria`; inclui bloco "MODO B" e bloco "ECONOMETRICIAN" no prompt; instrução de veredicto adaptada ao modo
- `.claude/commands/tese.md`: Passo 3 com detecção Modo A/B — verifica se ativo está na carteira antes de emitir veredicto
- `.claude/commands/watchlist.py`: `VEREDICTO_COR` expandido com ícones para AUMENTAR (📈), MANTER (🔒), REDUZIR (📉), SAIR (🚪)

- `investments`: v1.17.2 → **v1.18.0**
- Global → **v2.8.3**

---

## [2.8.2] — 2026-05-22 — PM: VEREDICTOS CONTEXTUAIS PARA POSIÇÕES EXISTENTES

### Changed
- `.claude/agents/portfolio-manager/SKILL.md`: Passo 2 agora detecta explicitamente se o ativo já está na carteira (posição atual, P&L, data de entrada). Passo 3 dividido em dois modos:
  - **Modo A** (não está na carteira): COMPRAR / AGUARDAR / EVITAR — comportamento anterior preservado
  - **Modo B** (já está na carteira): AUMENTAR / MANTER / REDUZIR / SAIR — com critérios específicos para cada veredicto e instrução de mostrar posição atual → posição alvo (X.X% → Y.Y%)
- Output template: frontmatter aceita os 7 veredictos; cabeçalho do Modo B inclui linha de contexto com posição atual, P&L e data de entrada; sizing em Modo B mostra transição de peso

- `investments`: v1.17.1 → **v1.17.2**
- Global → **v2.8.2**

---

## [2.8.1] — 2026-05-22 — INTEGRAÇÃO PM↔ECONOMETRICIAN + BUGS

### Fixed
- `.claude/agents/econometrician/modules/dynamic_beta.py`: `_tendencia_beta` comparava `validos[-1] - validos[0]` (252d - 60d), produzindo "crescente" quando o beta caiu de 1.1 para 0 — corrigido para `validos[0] - validos[-1]` (recente - antigo)
- `.claude/agents/econometrician/modules/factor_model.py`: yfinance imprimia HTTP 404 no stderr ao tentar SMLL11.SA (delisted) — suprimido com redirecionamento temporário de sys.stderr na função `_baixar_precos`

### Changed
- `.claude/agents/portfolio-manager/SKILL.md`:
  - `econometria_{TICKER}_{DATA}.json` adicionado à lista de inputs obrigatórios com instrução de leitura dos bullets "Para o Portfolio Manager"
  - Critérios de COMPRAR / AGUARDAR / EVITAR expandidos com sinais econométricos: regime GARCH, tendência de beta, alpha Fama-French, correlação rolling, Calmar Ratio
  - Linha do Econometrician adicionada à tabela `## Síntese da Equipe` do output template
- `.claude/commands/analisar.md`: Etapa 8 (PM) expandida — instrução explícita de ler o cache econometria e incorporar os bullets do Econometrician; requisito de ao menos 1 bullet na justificativa referenciando dado econométrico

- `investments`: v1.17.0 → **v1.17.1**
- Global → **v2.8.1**

---

## [2.8.0] — 2026-05-22 — AGENTE ECONOMETRICIAN

### Added
- `.claude/agents/econometrician/run_econometrician.py`: script principal do agente — baixa 3 anos de preços via yfinance, executa 6 módulos em sequência e salva `scripts/data/cache/econometria_{TICKER}_{DATA}.json`
- `.claude/agents/econometrician/modules/garch_model.py`: GARCH(1,1) via biblioteca `arch`; entrega vol condicional anualizada, regime (BAIXA/NORMAL/ELEVADA/ALTA), persistência (α+β), half-life de choques; fallback para rolling std se `arch` não instalado
- `.claude/agents/econometrician/modules/dynamic_beta.py`: beta dinâmico por rolling OLS em janelas de 60d/126d/252d e full; detecta tendência (crescente/decrescente/estável)
- `.claude/agents/econometrician/modules/factor_model.py`: Fama-French 3 fatores com proxies brasileiros (SMLL11, BOVA11, DIVO11, IVVB11); alpha anualizado com p-valor e significância; R² ajustado
- `.claude/agents/econometrician/modules/macro_regression.py`: regressão múltipla dos retornos mensais do ativo vs Δselic, IPCA, ΔBRL/USD e IBC-Br (dados BCB SGS); identifica driver principal
- `.claude/agents/econometrician/modules/rolling_stats.py`: correlação rolling (60d/252d) entre o ativo analisado e todos os ativos da carteira; classifica estabilidade (ESTAVEL/MODERADA/INSTAVEL); alertas automáticos para corr > 0.80
- `.claude/agents/econometrician/modules/advanced_drawdown.py`: Calmar Ratio, Ulcer Index, Pain Index, tempo médio de recuperação, duração máxima de drawdown, número de períodos de DD
- `.claude/agents/econometrician/SKILL.md`: prompt de interpretação do agente Econometrician — traduz métricas em insights para o Portfolio Manager sem repetir o que o Quant já calculou
- `scripts/data/fetch_bcb.py`: fetcher de dados macro do BCB SGS (Selic/11, IPCA/433, BRL-USD/1, IBC-Br/24363, etc.); salva `scripts/data/cache/bcb_{DATA}.json`
- `requirements.txt`: `arch>=6.0.0` adicionado

### Changed
- `.claude/commands/analisar.md`: Econometrician inserido como **Etapa 6**; `fetch_bcb.py` adicionado à Etapa 0; Pipeline Manager renumerado de 7→8; Salvar Output renumerado de 8→9
- `CLAUDE.md`: Econometrician adicionado à tabela de model routing (claude-sonnet-4-6, medium)
- `investments`: v1.16.0 → **v1.17.0**
- Global → **v2.8.0**

---

## [2.7.0] — 2026-05-22 — SISTEMA DE METAS FINANCEIRAS

### Added
- `vault/00-portfolio/metas.md`: arquivo de configuração das metas financeiras — renda passiva mensal, reserva de emergência, patrimônio total e metas livres com data. Agentes de análise não leem este arquivo
- `.claude/commands/metas.md`: novo comando `/metas` — dashboard completo com barra de progresso por meta, cálculo automático (dividendos reais / saldo RF+TD / patrimônio total), projeção de prazo, alertas de milestone (25/50/75/100%) e status "no prazo / em risco"
- `vault/00-portfolio/ips.md`: nova seção "Metas Financeiras" linkando para `metas.md` e explicando a separação entre IPS (decisões) e metas (informativo)
- `.claude/commands/morning-call.md`: novo bloco "Metas — Resumo Compacto" adicionado ao briefing diário — uma linha por meta com barra de progresso e alertas de milestone

### Changed
- `interface/ui.py`: botão "Metas" adicionado à aba Portfólio (linha 2); versão atualizada para v2.7.0
- `sbwaa.py`: `/metas` e `/investimento-do-dia [categoria]` adicionados ao `/help`; versão atualizada
- `docs/SBWAA-REFERENCIA.md`: `/metas` adicionado ao índice e com seção completa (campos, mockup de output)
- `investments`: v1.15.2 → **v1.16.0**
- `interface`: v2.2.1 → **v2.3.0**
- Global → **v2.7.0**

---

## [2.6.2] — 2026-05-22 — /INVESTIMENTO-DO-DIA COM FILTRO DE CATEGORIA

### Changed
- `.claude/commands/investimento-do-dia.md`: aceita argumento opcional de categoria — `fii`, `acao`, `etf`, `etf-br`, `etf-intl`, `rf`, `td`. Sem argumento: comportamento padrão inalterado. Com argumento: restringe sugestões ao tipo correspondente
- `docs/SBWAA-REFERENCIA.md`: `/investimento-do-dia` atualizado com sintaxe e tabela de categorias
- `investments`: v1.15.1 → **v1.15.2**
- Global → **v2.6.2**

---

## [2.6.1] — 2026-05-22 — /ANALISAR EM BATCH: MÚLTIPLOS TICKERS

### Changed
- `.claude/commands/analisar.md`: aceita 1 ou mais tickers separados por espaço (`/analisar PETR4 VALE3 XPML11`). Em batch: pipeline completo e isolado por ticker em sequência, output individual normal para cada um, tabela comparativa de veredictos ao final com prioridade de aporte
- `docs/SBWAA-REFERENCIA.md`: `/analisar` atualizado com nova sintaxe, modo batch e mockup da tabela comparativa
- `docs/GUIA-COMANDOS.md`: `/analisar` atualizado com nova sintaxe e descrição do modo batch
- `investments`: v1.15.0 → **v1.15.1**
- Global → **v2.6.1**

---

## [2.6.0] — 2026-05-22 — PREÇO TETO/CHÃO: GRAHAM (AÇÕES) + BAZIN (FIIS) NO VALUATION REVIEWER

### Added
- `.claude/agents/valuation-reviewer/SKILL.md`: novo **Passo 5 — Preço Teto / Chão** no pipeline do Valuation Reviewer, entre o stress test e a precificação do mercado (passos anteriores renumerados para 6 e 7)
  - **Ações (Graham):** Preço Teto = √(22,5 × LPA × VPA); margens de segurança a 10%, 15% e 20%; comparação com DCF; não aplicável se LPA ou VPA negativos
  - **FIIs (Bazin adaptado):** Preço Teto = DPA_anualizado / 8%; Preço Chão = DPA_anualizado / 12%; DY real vs cotação atual; status ZONA DE COMPRA FORTE / ZONA DE COMPRA / ACIMA DO TETO
- Versão curta: linha de preço teto/chão adicionada ao bloco de valuation
- Versão longa: nova seção `## 📐 Preço Teto / Chão` com tabela completa por tipo de ativo

### Changed
- `docs/SBWAA-REFERENCIA.md`: etapa 4 do `/analisar` atualizada para refletir novo entregável
- `investments`: v1.14.0 → **v1.15.0**
- Global → **v2.6.0**

---

## [2.5.3] — 2026-05-20 — AUDITORIA DOCS: SBWAA-REFERENCIA, BLUEPRINT E UI

### Fixed
- `docs/SBWAA-REFERENCIA.md`: versão atualizada de v2.4.1 para v2.5.3; `/otimizar-expansao` adicionado ao índice e com seção completa (campos, classificação, mockup de output); mockup do `/risco-carteira` atualizado com bloco de Fronteira Eficiente
- `docs/SBWAA-MASTER-BLUEPRINT.md`: versão e data do cabeçalho atualizados (v2.4.1 → v2.5.3, 2026-05-19 → 2026-05-20); Seção 3 com `optimization.py` na estrutura de pastas; Seção 10 com `/otimizar-expansao` na tabela de comandos; Seção 16 "Estado Atual" com versões e histórico completo até v2.5.3; "Uso diário típico" com `/risco-carteira`, `/watchlist`, `/otimizar-expansao` e link para SBWAA-WORKFLOW.md
- `interface/ui.py`: versão no header atualizada de v2.4.1 para v2.5.3; botão "Otimizar Expansão" adicionado ao Portfolio tab

### Changed
- `interface`: v2.2.0 → **v2.2.1**
- Global → **v2.5.3**

---

## [2.5.2] — 2026-05-20 — SBWAA-WORKFLOW.MD: WORKFLOW OPERACIONAL COMPLETO

### Added
- `docs/SBWAA-WORKFLOW.md`: workflow operacional completo separado do GUIA-COMANDOS — 6 cadências (diária/semanal/mensal/trimestral/anual + pós-fechamento), 5 fluxos oportunísticos (ativo novo, evento relevante, circuit breaker/drawdown, saída de posição, knowledge base), árvores de decisão por situação, tabela de calendário de comandos, tabela de decisão rápida "quando usar cada comando de análise" e dicas operacionais de encadeamento de comandos
- `CLAUDE.md`: `docs/SBWAA-WORKFLOW.md` adicionado ao mapa de pastas, à tabela de docs obrigatórios e ao checklist de encerramento de sessão (etapa 8, renumerando as seguintes)

### Changed
- `docs/GUIA-COMANDOS.md`: seção "Rotinas de uso sugeridas" substituída por link para SBWAA-WORKFLOW.md + tabela de resumo rápido
- Global → **v2.5.2**

---

## [2.5.1] — 2026-05-20 — /OTIMIZAR-EXPANSAO: FRONTEIRA EFICIENTE COM WATCHLIST

### Added
- `scripts/data/optimize_expansao.py`: script local que compara duas fronteiras eficientes — carteira atual (base) vs carteira + watchlist (expandida); para cada ativo da watchlist calcula Sharpe próprio, correlação com a carteira, delta Sharpe marginal (a 5% de peso) e peso no portfólio ótimo expandido; classifica como MELHORA / NEUTRO / PIORA; salva cache `optim_expansao_YYYY-MM-DD.json`
- `sbwaa.py /otimizar-expansao`: wrapper local para o script, com descrição no `/help`
- `/rebalancear`: lê cache de expansão quando disponível — seção "Candidatos da watchlist" com delta Sharpe e frescor de análise
- `/revisar-carteira`: lê cache de expansão quando disponível — seção "Oportunidades da Watchlist" no painel consolidado

### Changed
- Global → **v2.5.1** | investments → **v1.14.0**

---

## [2.5.0] — 2026-05-20 — FRONTEIRA EFICIENTE E OTIMIZAÇÃO DE PORTFÓLIO

### Added
- `calculators/optimization.py` (Quant/Data Engineer): motor de otimização — Monte Carlo (10k simulações), Max Sharpe exato (scipy.optimize SLSQP), Min Volatilidade exato, posição atual na fronteira, ajustes sugeridos por ativo (atual → ótimo)
- `run_quant.py`: seção `otimizacao` adicionada ao cache quant JSON — gerada automaticamente a cada execução do Quant
- `.claude/agents/quant-data-engineer/SKILL.md`: seção "Fronteira Eficiente" adicionada às métricas calculadas e ao formato de output (nova seção `## 🎯 Posição na Fronteira Eficiente`)
- `.claude/commands/risco_carteira.py`: bloco "FRONTEIRA EFICIENTE" no output — exibe Sharpe atual vs Max Sharpe possível, vol atual vs Min Vol possível, e top 5 ajustes sugeridos por ativo
- `.claude/commands/rebalancear.md`: passo de otimização adicionado — lê cache quant com dados de fronteira eficiente e os usa como referência quantitativa junto ao IPS
- `knowledge/raw/referencias-otimizacao-portfolio.md`: referências indexadas na base RAG — artigos fundacionais (Markowitz 1952, Sharpe 1964, Black-Litterman 1992, Fama-French 1992, Carhart 1997), livros essenciais, recursos sobre mercado brasileiro (NEFIN/USP), Python libs relevantes e glossário de conceitos

### Changed
- Global → **v2.5.0** | investments → **v1.13.0** | knowledge-base → **v1.2.0**

---

## [2.4.3] — 2026-05-20 — REORGANIZAÇÃO DE PASTAS

### Changed
- `docs/`: movidos GUIA-COMANDOS.md, SBWAA-LOGO.md, SBWAA-MASTER-BLUEPRINT.md, SBWAA-REFERENCIA.md (antes na raiz)
- `interface/`: movidos ui.py, splash.py (antes na raiz)
- `prompts/`: renomeado de `prompt/` (clareza de nomenclatura)
- `_standby/interface-streamlit/`: interface Streamlit legada movida para standby (era `interface/`)
- `sbwaa.py`: path de ui.py corrigido para `interface/ui.py`
- `iniciar.bat`, `iniciar.vbs`: paths de ui.py e splash.py atualizados
- `scripts/check_session_compliance.py`: paths de GUIA-COMANDOS.md e SBWAA-LOGO.md atualizados para `docs/`
- `CLAUDE.md`: seção "ESTRUTURA DE PASTAS — MAPA DE LOCALIZAÇÃO" adicionada; todos os paths de docs obrigatórios atualizados; checklist de sessão atualizado
- Global → **v2.4.3** | interface → **v2.2.0**

---

## [2.4.2] — 2026-05-20 — SBWAA-REFERENCIA.MD E REGRA DE ATUALIZAÇÃO NO CLAUDE.MD

### Added
- `SBWAA-REFERENCIA.md`: documento de referência completo — todos os comandos com descrição de campos, mockup de output representativo e notas de uso; separado do GUIA-COMANDOS.md (que cobre sintaxe/flags/rotinas)
- `CLAUDE.md`: `SBWAA-REFERENCIA.md` adicionado à tabela de docs obrigatórios e ao checklist de encerramento de sessão (etapa 7)

### Changed
- Global → **v2.4.2**

---

## [2.4.1] — 2026-05-20 — /WATCHLIST E /REVISAR-CARTEIRA

### Added
- `.claude/commands/watchlist.py`: comando local — lista todos os ativos analisados + carteira com último veredicto, data da análise e frescor (✅ atual / ⚠️ defasado >45d / 🔴 rever >90d); flag `--rever` filtra só os defasados; mostra se ativo está em carteira (●) ou só na watchlist (○)
- `.claude/commands/revisar-carteira.md`: comando de IA — PM revisa cada posição em carteira individualmente com veredicto MANTER/AUMENTAR/REDUZIR/SAIR, sizing alvo, prioridades imediatas, ativos para não mexer e alertas de IPS; salva em `vault/02-relatorios/revisoes/`
- `sbwaa.py`: `/watchlist` adicionado a `COMANDOS_LOCAIS`; `/revisar-carteira` adicionado a `COMANDOS_IA`; `/help` atualizado para v2.4.0
- `GUIA-COMANDOS.md`: seção `/revisar-carteira` adicionada

### Changed
- Global → **v2.4.1** | investments → **v1.12.0**

---

## [2.4.0] — 2026-05-20 — CONSENSO DE ANALISTAS NO VALUATION REVIEWER

### Added
- `scripts/data/fetch_consensus.py`: novo script — busca consenso de analistas via yfinance (primário) + scraping Investing.com (fallback); cache 24h em `consensus_{TICKER}_{DATA}.json`; exibe price target médio/alto/baixo, upside implícito, recomendação (normalizada PT-BR) e número de analistas; aviso explícito quando sem cobertura
- `.claude/agents/valuation-reviewer/SKILL.md`: novo Passo 5 "Precificação do mercado" — lê cache de consenso e cruza com DCF e múltiplos; novo bloco `## 📡 Precificação do Mercado` em ambas as versões de output (curta e longa), com tabela de consenso, inferência do que o mercado precifica e reação recente do preço
- `.claude/commands/analisar.md`: `fetch_consensus.py` adicionado à ETAPA 0; cache de consenso listado nos arquivos a ler

### Changed
- Global → **v2.4.0** | investments → **v1.11.0**

---

## [2.3.0] — 2026-05-19 — /VENDER, DIVIDENDOS REESCRITO E PROVENTOS NA CARTEIRA

### Added
- `.claude/commands/dividendos.py`: reescrito completo — usa Yahoo Finance (`yfinance`) em vez de Brapi (API exige token); exibe próximos dividendos (60 dias), dividendos declarados, histórico do ano por ativo e Yield on Cost; grava `.proventos-cache.json` em `vault/00-portfolio/` ao final
- `scripts/data/vender_ativo.py`: novo script de registro de venda — suporta venda parcial e total, calcula P&L realizado, atualiza `carteira.md` e `historico-trades.md`; flag `--data` para data customizada
- `.claude/commands/carteira.py`: exibe "Proventos Recebidos" e "Total c/ Proventos" na seção RESUMO quando `.proventos-cache.json` existe; se ausente, exibe prompt para executar `/dividendos`

### Changed
- `sbwaa.py`: `/vender` adicionado a `COMANDOS_LOCAIS`; banner `/help` atualizado para v2.3.0
- `ui.py`: label de versão atualizado para v2.3.0
- Global → **v2.3.0** | investments → **v1.10.0** | interface → **v2.1.0**

---

## [2.2.16] — 2026-05-18 — UI.PY LABEL SINCRONIZADO

### Fixed
- `ui.py`: label de versão corrigido de v2.2.13 para v2.2.16 (estava desatualizado desde a sessão anterior)

### Changed
- Global → **v2.2.16** | interface → **v2.0.6**

---

## [2.2.15] — 2026-05-18 — COMPLIANCE SCRIPT VERIFICA SBWAA-LOGO.MD

### Fixed
- `SBWAA-LOGO.md`: versão corrigida para v2.2.14 (desajuste detectado manualmente pois o script ainda não verificava o arquivo)

### Changed
- `scripts/check_session_compliance.py`: adicionada verificação de `SBWAA-LOGO.md` — agora o script detecta automaticamente quando a string de versão está desatualizada
- Global → **v2.2.15** | interface → **v2.0.5**

---

## [2.2.14] — 2026-05-18 — SBWAA-LOGO.MD VERSIONADO + REGRA NO CLAUDE.MD

### Fixed
- `SBWAA-LOGO.md`: versão corrigida de v2.2.9 para v2.2.13 (estava desatualizada desde a criação)

### Changed
- `CLAUDE.md`: adicionada `SBWAA-LOGO.md` à tabela de docs obrigatórios e ao checklist de encerramento de sessão (passo 7) — versão deve ser atualizada a cada bump
- Global → **v2.2.14** | interface → **v2.0.4**

---

## [2.2.13] — 2026-05-18 — REGRA DE MÓDULOS NO CLAUDE.MD

### Added
- `CLAUDE.md`: tabela de módulos com escopo explícito de cada um (investments / heartbeat / knowledge-base / interface) e regra obrigatória de bumpar o módulo afetado junto com a versão global a cada alteração

### Changed
- Global → **v2.2.13**

---

## [2.2.12] — 2026-05-18 — SINCRONIZAÇÃO DE VERSÕES DE MÓDULOS

### Fixed
- `VERSION.md`: versões de módulos corrigidas para refletir alterações reais das sessões anteriores
  - `investments` v1.7.3 → **v1.9.0** — RAG integrado nos agentes (v2.2.4) + injeção automática de tipo-tag nos runners (v2.2.6) — dois recursos MINOR que não foram contados
  - `interface` v2.0.1 → **v2.0.3** — `splash.py` (v2.2.9) e `SBWAA-LOGO.md` (v2.2.10) adicionados mas módulo não foi incrementado

### Changed
- Global → **v2.2.12**

---

## [2.2.11] — 2026-05-18 — GITIGNORE TEMP WINDOWS + COMPLIANCE INTELIGENTE

### Fixed
- `.gitignore`: adicionadas regras para arquivos temporários do Windows — GUIDs colados do clipboard (`{*}.*`), arquivos Office temporários (`~$*`) e `.tmp`
- `scripts/check_session_compliance.py`: detecta e separa arquivos temporários (GUIDs, `~$`, `.tmp`) dos arquivos reais no aviso de git status — exibe mensagem específica orientando apagar e ignorar

### Changed
- Global → **v2.2.11**

---

## [2.2.10] — 2026-05-18 — SBWAA-LOGO.MD + BLUEPRINT SINCRONIZADO

### Added
- `SBWAA-LOGO.md`: logo com ASCII block art para abrir como preview pinado no VS Code — visualmente presente enquanto trabalha no terminal integrado

### Fixed
- `SBWAA-MASTER-BLUEPRINT.md`: sincronizado com v2.2.10 — cabeçalho, bloco de Estado Atual e tabela de histórico cobrindo v2.2.2 → v2.2.10

### Changed
- Global → **v2.2.10**

---

## [2.2.9] — 2026-05-18 — SPLASH SCREEN + LOGO MD

### Added
- `SBWAA-LOGO.md`: logo com ASCII block art centralizado para abrir como preview no VS Code — fixar como aba pinada para ter o logo visível enquanto trabalha no terminal

### Added
- `splash.py`: tela de boas-vindas exibida no terminal a cada abertura pelo `iniciar.vbs` — mostra SBWAA em ASCII block art, versão lida dinamicamente do VERSION.md, data e hora atuais, lista de módulos iniciando, e fecha sozinho após 4 segundos com countdown
- `splash.py`: tela de boas-vindas exibida no terminal a cada abertura pelo `iniciar.vbs` — mostra SBWAA em ASCII block art, versão lida dinamicamente do VERSION.md, data e hora atuais, lista de módulos iniciando, e fecha sozinho após 4 segundos com countdown
- `iniciar.vbs`: chama `splash.py` como primeiro passo antes de abrir Obsidian, VS Code e painel (overlapping — splash fecha enquanto os apps carregam)

### Changed
- Global → **v2.2.9**

---

## [2.2.8] — 2026-05-18 — FIX INICIAR.VBS + BOTÃO IPS + REGRAS UI.PY

### Fixed
- `iniciar.vbs`: eliminado o CMD que ficava aberto ao iniciar o sistema — VBS agora chama cada processo diretamente via `WScript.Shell.Run` sem passar por `cmd /c iniciar.bat`
- `ui.py`: versão do painel atualizada de v2.1.3 para v2.2.8

### Added
- `ui.py`: botão **IPS** adicionado na aba Portfólio (único comando local que faltava no painel)
- `CLAUDE.md`: `ui.py` adicionado à tabela de "ATUALIZAÇÃO OBRIGATÓRIA DE DOCS" e como passo 6 explícito no checklist de encerramento de sessão

### Changed
- `interface` → v2.0.1
- Global → **v2.2.8**

---

## [2.2.7] — 2026-05-17 — PROTOCOLO DE SESSÃO + COMPLIANCE HOOK + CATCH-UP DE DOCS

### Added
- `CLAUDE.md`: seção **PROTOCOLO DE SESSÃO — CHECKLIST OBRIGATÓRIO** com passos explícitos para início e encerramento de sessão — garante que versionamento, git e releases nunca sejam esquecidos
- `.claude/settings.json`: Stop hook que executa `scripts/check_session_compliance.py` automaticamente ao final de cada sessão Claude Code
- `scripts/check_session_compliance.py`: script de auditoria que compara versões em VERSION.md, README.md e GUIA-COMANDOS.md, verifica presença do CHANGELOG para a versão atual e exibe git status de arquivos não commitados

### Fixed
- `README.md`: versão atualizada de v2.2.4 → v2.2.7 (estava 3 versões atrás)
- `GUIA-COMANDOS.md`: versão atualizada de v2.2.4 → v2.2.7 (estava 3 versões atrás)

### Changed
- Global → **v2.2.7**

---

## [2.2.6] — 2026-05-17 — COLORAÇÃO AUTOMÁTICA DO GRAPH VIEW OBSIDIAN

### Fixed
- `vault/.obsidian/graph.json`: colorGroups agora usa as tags que os agentes realmente escrevem (`macro`, `risk`, `earnings`, `equity-research`, `pm-decisao`, `relatorio`) — antes consultava só tags de tipo de ativo que nunca existiam nas notas, causando tudo verde (cor default)

### Added
- `run_earnings_reviewer.py`: injeta tag de tipo do ativo (ex: `acao-on`, `fii`) no frontmatter da nota ao salvar, lendo a carteira.md
- `run_valuation_reviewer.py`: mesma injeção automática de tipo
- `run_pm.py`: adiciona tag de tipo do ativo ao frontmatter da decisão do PM (lido do `carteira_completa` já disponível no script)
- Hierarquia de colorização no graph: tipos de nota têm prioridade (pm-decisao → risk → macro → earnings → valuation), tipos de ativo como fallback para notas raiz (tese.md já recebia o tag via `add_ativo.py`)

### Changed
- Global → **v2.2.6**

---

## [2.2.5] — 2026-05-17 — POLÍTICA DE GIT + GITHUB RELEASES

### Added
- `CLAUDE.md`: seção **GIT + GITHUB RELEASES — REGRA GLOBAL** — define quando commitar, quando criar release (MINOR/MAJOR obrigatório, PATCHes críticos), formato padrão de tag/título/notas e checklist de segurança para não expor dados privados
- `SBWAA-MASTER-BLUEPRINT.md`: mesma regra adicionada à seção de políticas globais; tabela de docs atualizável expandida com `GUIA-COMANDOS.md`

### Changed
- Global → **v2.2.5**

---

## [2.2.4] — 2026-05-17 — RAG INTEGRADO EM TODOS OS AGENTES

### Added
- RAG integrado em `run_valuation_reviewer.py`: busca benchmarks de valuation e metodologia do setor antes de gerar o equity research
- RAG integrado em `run_risk_engineer.py`: busca frameworks de gestão de risco (VaR, drawdown, concentração) antes de gerar o risk snapshot

### Fixed
- `knowledge/indexed/index_log.json`: corrigidos paths e tipos de 2 livros que estavam registrados com caminho antigo (raiz) e tipo "outro" em vez de "livro"
- `Active Portfolio Management.pdf` e `The Intelligent Investor` agora corretamente categorizados como `tipo: livro`

### Changed
- `knowledge-base` → v1.1.0 (RAG agora ativo em todos os 5 agentes que usam LLM: Market Researcher, Earnings Reviewer, Model Builder, Valuation Reviewer, Portfolio Manager, Risk Engineer)
- Global → **v2.2.4**

---

## [2.2.3] — 2026-05-16 — REPOSITÓRIO GITHUB + REESTRUTURAÇÃO DE DOCS

### Added
- `GUIA-COMANDOS.md`: referência completa de todos os comandos (conteúdo migrado do README.md anterior)
- `vault/00-portfolio/.gitkeep`: mantém o diretório no repositório sem versionas dados pessoais
- Repositório GitHub privado com push inicial do sistema

### Changed
- `README.md`: reescrito como guia de instalação para novos usuários (clone, install, configure, start). Não contém mais a referência de comandos — delegada ao GUIA-COMANDOS.md
- `.gitignore`: ampliado com exclusões de `settings.local.json`, `__pycache__`, `*.pyc`, `.venv/`, `vault/00-portfolio/decisoes.md`, `vault/01-ativos/`, `vault/.obsidian/workspace.json`
- `CLAUDE.md`: regra de atualização de docs atualizada para `GUIA-COMANDOS.md` (substituiu `GUIA-USO-MANUAL.md`)
- Global → **v2.2.3**

---

## [2.2.2] — 2026-05-16 — MASTER BLUEPRINT

### Added
- `SBWAA-MASTER-BLUEPRINT.md`: documento completo de reconstrução do sistema do zero. Cobre todas as 9 fases (F0-F8), arquitetura, código de todos os agentes, calculadoras, correções críticas aplicadas, rotina de testes e estado atual. Consolida os 11 prompts originais + todas as melhorias da sessão

### Changed
- Global → **v2.2.2**

---

## [2.2.1] — 2026-05-16 — README COMPLETO + /HELP REDESENHADO

### Added
- `README.md`: reescrito completamente — cobre instalação, todos os comandos com sintaxe exata, tipos de ativo, agentes, rotina de uso, estrutura de arquivos e segurança. Substitui o GUIA-USO-MANUAL.md como referência principal

### Changed
- `sbwaa.py` `/help`: redesenhado com seções separadas por tipo (Portfólio, Mercado, Knowledge, IA, Sistema), sintaxe completa `python sbwaa.py /comando` para cada entrada, exemplos reais e nota sobre PowerShell vs Git Bash
- Global → **v2.2.1**

### Removed
- `GUIA-USO-MANUAL.md`: descontinuado — conteúdo migrado e expandido no README.md

---

## [2.2.0] — 2026-05-16 — PAINEL CUSTOMTKINTER + CORREÇÕES CRÍTICAS

### Added
- `ui.py`: painel de controle visual em customtkinter — substitui a interface Streamlit como padrão do `/ui`. 5 abas: Portfólio, Análise (IA), Mercado, Stress Test, Relatórios, Knowledge. Output embutido com auto-clear a cada comando. Comandos locais rodam direto com output em tempo real; comandos de IA copiam para clipboard com instrução no painel
- `customtkinter` adicionado às dependências (pip install customtkinter)

### Fixed
- `scripts/data/fetch_brapi.py`: erros HTTP, conexão e timeout levantavam `SystemExit`, impedindo o fallback para Yahoo Finance em `update_carteira.py` — trocado para `ValueError` capturável
- `.claude/commands/carteira.py`: P&L% exibido no terminal mostrava o valor em R$ (P&L R$) em vez do percentual — índice de coluna corrigido de `cols[7]` para `cols[8]`
- `.claude/commands/carteira.py`: regex de "Última atualização" capturava `** 2026-...` (marcadores bold do markdown) — regex refatorado para capturar pelo padrão da data `\d{4}-\d{2}-\d{2}`

### Changed
- `sbwaa.py`: `/ui` agora aponta para `ui.py` (customtkinter) em vez de `interface/app.py` (Streamlit)
- `sbwaa.py`: descrição do `/ui` no `/help` atualizada para "Painel visual (customtkinter)"
- `interface` → v2.0.0
- `investments` → v1.7.3
- Global → **v2.2.0**

---

## [2.1.3] — 2026-05-16 — CORREÇÕES DE INTEGRIDADE + /SNAPSHOT

### Fixed
- `sbwaa.py`: Git Bash no Windows expandia `/carteira` para `C:/Program Files/Git/carteira`, tornando todos os comandos irreconhecíveis. Normalização automática: extrai o nome base e reprefixa com `/`
- `vault/00-portfolio/historico-trades.md`: linha em branco no corpo da tabela causaria inserção incorreta de posição pelo `/adicionar` — removida
- `.claude/agents/quant-data-engineer/run_quant.py`: função `safe()` morta removida (nunca era chamada; somente `safe_pct()` era usada)

### Added
- `sbwaa.py`: comando `/snapshot` exposto — mapeia para `scripts/data/market_snapshot.py` (snapshot diário macro + carteira)
- `GUIA-USO-MANUAL.md`: `/snapshot` documentado; sintaxe do `/adicionar` corrigida para flags corretas; nota sobre Git Bash adicionada

### Changed
- `investments` → v1.7.2
- Global → **v2.1.3**

---

## [2.1.2] — 2026-05-16 — CORREÇÃO CRÍTICA: CARTEIRA

### Fixed
- `scripts/data/update_carteira.py`: wikilink `[[path|display]]` no campo Ticker usava `|` que é o delimitador da tabela markdown — em execuções subsequentes o parser interpretava o caminho do arquivo como ticker (ex: `01-ATIVOS/PETR4/TESE`), zerando patrimônio e P&L. Corrigido: Ticker na tabela agora é sempre texto simples (ex: `PETR4`), sem wikilinks em células da tabela.

### Removed
- Dados de teste (PETR4) removidos de `carteira.md`, `historico-trades.md` e `vault/01-ativos/PETR4/`

---

## [2.1.1] — 2026-05-16 — TESTES COMPLETOS + CORREÇÕES

### Fixed
- `add_ativo.py`: `validar_ticker_brapi/yahoo` agora captura `BaseException` (antes `SystemExit` do fetch_brapi propagava sem ser capturado)
- `run_quant.py`: síntese via API encapsulada em try/except — degrada graciosamente sem API key, métricas preservadas no cache JSON
- `run_risk_engineer.py`: síntese via API encapsulada em try/except — mesmo fallback
- `run_risk_engineer.py`: serialização JSON com `_NpEncoder` para tratar `numpy.bool_` e outros tipos numpy não serializáveis
- `knowledge/retriever.py`: score de relevância corrigido de `1 - distance` (negativo para L2 > 1) para `1/(1+distance)` (sempre 0-100%)
- `scripts/heartbeat/heartbeat.py`: `logging.basicConfig` substituído por `FileHandler(encoding='utf-8')` para evitar garbling no log Windows

### Added
- `scripts/diagnostico.py`: auditoria 61/61 scripts
- `scripts/test_calculadoras.py`: teste unitário de 5 calculadoras quant+risk
- `scripts/check_estrutura.py`: verificação de estrutura run_analisar e SKILL.md PM
- `scripts/gerar_relatorio_testes.py`: relatório de métricas do sistema

### Test Results (12 blocos)
- Bloco 0 (Pré-requisitos):  ✅ 16 deps | ✅ 14 pastas | ✅ 9 arquivos | ⚠️ .env sem key (esperado)
- Bloco 1 (sbwaa.py):        ✅ sintaxe | ✅ /help | ✅ /status | ✅ 61/61 scripts
- Bloco 2 (Pipeline dados):  ✅ brapi | ✅ yahoo | ✅ snapshot | ✅ add_ativo | ✅ update_carteira
- Bloco 3 (Agentes):         ✅ 7/7 SKILL.md | ✅ 8/8 runners sintaxe | ⚠️ execução requer API key
- Bloco 4-5 (Quant+Risk):    ✅ 5/5 calculadoras | ✅ run_quant | ✅ run_risk (cache JSON OK)
- Bloco 7 (Comandos):        ✅ /carteira | ✅ /stress-test | ✅ /risco-carteira | ✅ /ips | ✅ /dividendos | ✅ /adicionar
- Bloco 8 (Heartbeat):       ✅ roda sem erro | ✅ log UTF-8 | ✅ detecta fim de semana
- Bloco 9 (Knowledge):       ✅ ChromaDB | ✅ modelo | ✅ indexação | ✅ busca | ✅ score corrigido
- Bloco 10 (Interface):      ✅ 13/13 sintaxe | ✅ CSS presente
- Bloco 11 (Integração):     ✅ PETR4 adicionado | ✅ carteira exibe P&L | ✅ risco com circuito correto

---

## [2.1.0] — 2026-05-16 — AUDITORIA E CORREÇÕES

### Fixed
- `sbwaa.py`: encoding UTF-8 forçado via `sys.stdout.reconfigure` + `PYTHONUTF8=1` propagado a todos os subprocessos — resolve UnicodeEncodeError no Windows cp1252
- `sbwaa.py`: `os.environ["PYTHONUTF8"]` definido antes de qualquer subprocess.run para garantir UTF-8 em todos os agentes filhos
- `chromadb` e `sentence-transformers` instalados no ambiente Python correto (store da Microsoft Store)

### Added
- `requirements.txt` completo com todas as dependências e versões mínimas
- `.env.template` — template para configuração da ANTHROPIC_API_KEY
- `scripts/diagnostico.py` — auditoria de presença e tamanho de todos os 61 scripts

### Verified
- 61/61 scripts presentes e com conteúdo (diagnóstico 100%)
- Todas as dependências importáveis: anthropic, yfinance, chromadb, streamlit, pandas, docx, openpyxl, sentence-transformers, PyPDF2, feedparser, plotly, dotenv, scipy
- `/carteira`, `/stress-test`, `/risco-carteira` funcionando sem erros
- Interface Streamlit: 13 arquivos sem erros de sintaxe
- Knowledge base: ChromaDB + modelo multilingual carregados com sucesso

---

## [2.0.0] — 2026-05-16 — BETA COMPLETO

### Added
- `interface/app.py` — dashboard principal Streamlit com cards HF, ações rápidas e equipe de agentes
- `interface/pages/01_carteira.py` — tabela de posições, P&L, gráfico de alocação, botão de atualização
- `interface/pages/02_analisar.py` — pipeline completo via UI com output em tempo real
- `interface/pages/03_morning_call.py` — exibe morning call do dia, botão de geração, calls anteriores
- `interface/pages/04_risco.py` — métricas HF, heatmap de correlação, stress tests, circuit breakers
- `interface/pages/05_relatorios.py` — listagem de relatórios diários, por ativo e macro; geração semanal/mensal
- `interface/pages/06_knowledge.py` — status RAG, busca semântica, indexação e coleta RSS
- `interface/pages/07_agentes.py` — grid completo dos 7 agentes com pixel art e status de execução
- `interface/components/pixel_art.py` — componente com fallback emoji quando PNG ausente
- `interface/components/metricas_hf.py` — bloco de 8 métricas + gráficos Plotly (correlação, alocação)
- `interface/components/alerts_bar.py` — alertas críticos/altos no topo de todas as páginas
- `interface/components/sidebar.py` — navegação lateral com links e versão do sistema
- `interface/style/sbwaa.css` — tema escuro (#0f0f0f), cards estilizados, botão dourado primário
- `vault/assets/agents-pixel/README.md` — especificações e sugestões visuais para os bonecos
- `_inserir_pixel_art_docx()` integrado em `run_valuation_reviewer.py` — pixel art no cabeçalho dos DOCX
- Comando `/ui` adicionado ao `sbwaa.py` — inicia Streamlit com caminho absoluto
- `sbwaa.py` `/help` atualizado com seção INTERFACE

### Changed
- `interface` → v1.0.0
- Global → **v2.0.0** — SBWAA Beta Completo

---

## [1.7.0] — 2026-05-16

### Added
- `knowledge/__init__.py` — pacote Python da base de conhecimento
- `knowledge/indexer.py` — indexador de documentos (PDF, DOCX, TXT, MD) no ChromaDB local com embeddings multilingual
- `knowledge/retriever.py` — interface de busca semântica; lazy-load de modelo e collection; retorna chunks rankeados por score cosine
- `knowledge/rss_collector.py` — coleta artigos RSS de fontes financeiras (Valor, InfoMoney, BCB, Bloomberg, Reuters) e indexa automaticamente
- `knowledge/knowledge_cmd.py` — comando `/knowledge` com subcomandos: `--status`, `--adicionar`, `--buscar`, `--listar`, `--coletar-rss`
- `knowledge/save_synthesis.py` — salva sínteses RAG no `vault/04-knowledge/` com wikilinks e metadados
- `knowledge/indexed/index_log.json` — log de documentos indexados com hash MD5 para deduplicação
- `knowledge/sources/sources.json` — configuração de feeds RSS ativos
- `vault/04-knowledge/` — diretório de sínteses geradas pelos agentes a partir do RAG
- Integração RAG em `run_market_researcher.py` — busca contexto macro antes de montar prompt
- Integração RAG em `run_earnings_reviewer.py` — busca contexto de setor e empresa
- Integração RAG em `run_model_builder.py` — busca premissas de valuation e WACC
- Integração RAG em `run_pm.py` — busca contexto amplo de risco/retorno/portfólio
- Seção `## BASE DE CONHECIMENTO (RAG)` adicionada a todos os SKILL.md (7 agentes)
- `scripts/heartbeat/heartbeat.py` atualizado — coleta RSS como passo 0 diário
- `sbwaa.py` atualizado — comando `/knowledge` registrado e exibido no `/help`
- `.gitignore` atualizado — `knowledge/.chromadb/` e `knowledge/raw/` excluídos

### Changed
- `investments` → v1.7.0
- `knowledge-base` → v1.0.0

---

## [1.6.0] — 2026-05-16

### Added
- `sbwaa.py` — ponto de entrada único para todos os comandos do sistema
- `.claude/commands/carteira.py` — snapshot completo com cotações atualizadas e alocação vs IPS
- `.claude/commands/ips.py` — exibir/editar IPS no terminal
- `.claude/commands/risco_carteira.py` — roda Quant + Risk e exibe métricas HF
- `.claude/commands/morning_call.py` — briefing pré-abertura com snapshot + Market Researcher + alertas
- `.claude/commands/mundo_economico.py` — panorama macro do dia via Sonnet
- `.claude/commands/investimento_do_dia.py` — sugestão de 1-2 ativos para /analisar baseada no IPS e macro
- `.claude/commands/tese.py` — pipeline rápido 6 etapas (sem Quant/Risk)
- `.claude/commands/comparar.py` — análise comparativa entre dois tickers
- `.claude/commands/rebalancear.py` — desvios vs IPS com sugestão de ajuste via Sonnet
- `.claude/commands/dividendos.py` — calendário e histórico de proventos via yfinance
- `.claude/commands/stress_test.py` — stress tests por cenário ou choque customizado
- `.claude/commands/relatorio_semanal.py` — P&L da semana com narrativa Sonnet + DOCX
- `.claude/commands/relatorio_mensal.py` — relatório completo do mês + comparação benchmarks + DOCX
- `scripts/alerts/check_alerts.py` — 8 tipos de alerta; log em logs/alerts.log; notas críticas no vault
- `scripts/heartbeat/heartbeat.py` — processo automático diário (snapshot + quant + risk + alertas + morning call)
- `scripts/heartbeat/schedule_heartbeat.py` — instruções de agendamento cron/Task Scheduler

---

## [1.5.0] — 2026-05-16

### Added
- `.claude/agents/portfolio-manager/SKILL.md` — identidade, processo de decisão e regras de comportamento do PM
- `.claude/agents/portfolio-manager/run_pm.py` — PM com streaming; veredicto COMPRAR/AGUARDAR/EVITAR; fluxo interativo S/N/D; cálculo local de sizing (dados privados nunca enviados à API); salvamento de decisão no vault e log em decisoes.md
- `.claude/agents/portfolio-manager/run_analisar.py` — orquestrador do pipeline completo 8 etapas com cache < 4h, barra de progresso, log de erros e listagem de arquivos gerados
- `vault/00-portfolio/decisoes.md` — log histórico de decisões do PM
- Patrimônio e valores absolutos isolados no script Python — API recebe apenas pesos percentuais

---

## [1.4.0] — 2026-05-15

### Added
- `.claude/agents/quant-data-engineer/SKILL.md` — metodologia de métricas quantitativas
- `calculators/returns.py` — retorno total, anualizado, volatilidade, Sharpe, drawdown, beta, períodos
- `calculators/portfolio_metrics.py` — volatilidade de carteira, correlação, contribuição de risco, HHI, beta ponderado
- `calculators/correlation.py` — pares de alta correlação, diversificação efetiva, correlação média
- `run_quant.py` — calcula métricas para todos os ativos e carteira; gera JSON de cache e nota no vault
- `.claude/agents/risk-engineer/SKILL.md` — VaR, CVaR, stress test, circuit breakers
- `calculators/var.py` — VaR histórico, VaR paramétrico, CVaR, retornos ponderados da carteira
- `calculators/stress_test.py` — 4 cenários históricos BR (2008, COVID-2020, Eleições-2022, Lula-2002)
- `run_risk_engineer.py` — calcula VaR/CVaR, roda stress tests, verifica IPS, gera JSON e nota de risco
- `scripts/run_research_pipeline.py` atualizado — pipeline completo 7 passos (Fases 1-4)
- Patrimônio normalizado R$ 100k em stress tests — dado privado nunca exposto à API

---

## [1.3.0] — 2026-05-15

### Added
- `.claude/agents/model-builder/SKILL.md` — metodologia DCF completa com output JSON estruturado
- `.claude/agents/model-builder/run_model_builder.py` — gera DCF via Claude Opus, exporta XLSX (4 abas: Premissas, Projeções, DCF, Sensibilidade) e JSON no cache
- `.claude/agents/valuation-reviewer/SKILL.md` — processo de revisão crítica com veredicto BARATO/JUSTO/CARO
- `.claude/agents/valuation-reviewer/run_valuation_reviewer.py` — gera equity research em markdown + DOCX (versões curta e longa)
- `scripts/run_research_pipeline.py` atualizado — pipeline completo Fases 1-3 (5 passos sequenciais)
- Flag `--tipo fii` no Model Builder: metodologia Gordon Growth direto no DY
- Flag `--tipo etf` no Model Builder: retorna aviso e pula DCF
- Flag `--versao longa` no Valuation Reviewer: relatório de 2 páginas com stress test e catalisadores

---

## [1.2.0] — 2026-05-15

### Added
- `.claude/agents/market-researcher/SKILL.md` — system prompt do agente Market Researcher
- `.claude/agents/market-researcher/run_market_researcher.py` — executa análise macro diária via Claude API
- `.claude/agents/earnings-reviewer/SKILL.md` — system prompt do agente Earnings Reviewer
- `.claude/agents/earnings-reviewer/run_earnings_reviewer.py` — analisa resultados trimestrais por ticker
- `scripts/run_research_pipeline.py` — pipeline integrado: snapshot → market researcher → earnings reviewer
- Outputs salvos em `vault/03-macro/` e `vault/01-ativos/{TICKER}/`
- Nota mensal acumulada em `vault/03-macro/macro-{MES-ANO}.md`
- Wikilinks automáticos em todos os outputs e links para tese.md do ativo

---

## [1.1.0] — 2026-05-15

### Added
- `fetch_brapi.py` — cotações e fundamentalistas de ativos BR via Brapi
- `fetch_yahoo.py` — dados macro, ETFs e histórico via Yahoo Finance
- `update_carteira.py` — atualiza cotações e P&L na carteira.md
- `add_ativo.py` — adiciona ativo à carteira e cria estrutura no vault
- `market_snapshot.py` — gera snapshot diário de mercado no vault
- Pasta `scripts/data/cache/` com TTL de 4h por arquivo
- `.gitignore` atualizado: `scripts/data/cache/` excluído

---

## [1.0.0] — 2026-05-15

### Added
- Estrutura de pastas completa do vault e do projeto
- CLAUDE.md com políticas de segurança, model routing, wikilinks,
  labels de ativos e regras de versionamento
- Arquivos base de portfólio: carteira.md, ips.md, historico-trades.md
- Sistema de versionamento: VERSION.md e CHANGELOG.md
- Graph view CSS: sbwaa-graph.css com coloração por tipo de ativo
- CSS snippet de coloração dos nós no Obsidian
