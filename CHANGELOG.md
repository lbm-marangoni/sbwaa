# SBWAA — CHANGELOG

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
