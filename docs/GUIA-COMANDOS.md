# SBWAA — Guia de Comandos

> Referência completa de todos os comandos do sistema.
> Para instalação e configuração inicial: [`README.md`](README.md)

**Versão: v2.21.0**

---

## O que é o SBWAA

SBWAA é um sistema pessoal de gestão de portfólio e análise de ativos financeiros que combina:

- **8 agentes de IA especializados** que analisam ativos do zero ao veredicto final
- **Pipeline de dados automático** via Brapi (BR) e Yahoo Finance (macro/internacional)
- **Base de conhecimento RAG** com indexação semântica de PDFs, relatórios e notícias RSS
- **Painel visual** customtkinter com todos os comandos acessíveis por botão
- **Vault Obsidian** como repositório de notas, teses, decisões e relatórios

O sistema opera em dois modos:
- **Modo Claude Code** (padrão) — sem API key, comandos de IA rodam no chat do Claude Code
- **Modo API** — com `ANTHROPIC_API_KEY` no `.env`, agentes executam via subprocess

---

## Configuração inicial

### 1. Instalar dependências

```powershell
pip install -r requirements.txt
```

Pacotes principais: `anthropic`, `yfinance`, `pandas`, `numpy`, `chromadb`,
`sentence-transformers`, `PyPDF2`, `feedparser`, `customtkinter`, `plotly`,
`python-docx`, `openpyxl`, `beautifulsoup4`, `python-dotenv`, `requests`, `scipy`.

### 2. Configurar API key (opcional — só para modo API)

```powershell
Copy-Item ".env.template" ".env"
notepad ".env"    # substituir 'sua_chave_aqui' pela ANTHROPIC_API_KEY
```

Sem API key, todos os comandos locais funcionam normalmente.
Comandos de IA funcionam digitando os slash commands no chat do Claude Code.

### 3. Configurar UTF-8 no terminal (Windows — uma vez por sessão)

```powershell
$env:PYTHONUTF8 = "1"
```

> **Importante:** Use sempre **PowerShell** para rodar `python sbwaa.py /comando`.
> O Git Bash converte argumentos `/comando` em caminhos do sistema (`C:/Program Files/Git/comando`),
> o que quebra o roteamento. O sistema tenta corrigir isso automaticamente, mas PowerShell é mais seguro.

---

## Ponto de entrada

Todos os comandos passam pelo mesmo arquivo:

```powershell
python sbwaa.py /COMANDO [argumentos]
```

Para ver todos os comandos disponíveis com exemplos de uso:

```powershell
python sbwaa.py /help
python sbwaa.py /status    # versão atual e modo do sistema
```

---

## Comandos locais (sem IA / sem API key)

Estes comandos rodam scripts Python locais e retornam output no terminal imediatamente.

> **Dica — rodar comandos direto no chat do Claude Code:**
> Prefixe qualquer comando com `!` para executá-lo sem sair do chat.
> ```
> ! python sbwaa.py /carteira
> ! python sbwaa.py /risco-carteira
> ! python sbwaa.py /snapshot
> ```
> O output aparece diretamente na conversa. Útil para combinar um comando local
> com um slash command de IA na mesma sessão.

---

### `/carteira` — Snapshot da carteira

Atualiza cotações via Yahoo Finance e exibe posições, P&L, alocação vs IPS e proventos recebidos.

```powershell
python sbwaa.py /carteira
```

Output: tabela de posições com preço médio, preço atual, P&L%; seção RESUMO com patrimônio total,
total investido, P&L e — se `.proventos-cache.json` existir — proventos recebidos e total c/ proventos.
Para popular o cache de proventos, execute `/dividendos` antes.

---

### `/watchlist` — Ativos monitorados com veredicto e frescor

Lista todos os ativos analisados (`vault/01-ativos/`) e os da carteira com o último veredicto do PM, data da análise e indicador de frescor.

```powershell
python sbwaa.py /watchlist

# Exibe apenas ativos com análise defasada (> 45 dias) ou sem análise
python sbwaa.py /watchlist --rever
```

Output: tabela com ticker, se está em carteira (●) ou só na watchlist (○), tipo, veredicto, data, frescor (✅ < 45d / ⚠️ 45–90d / 🔴 > 90d) e preço-alvo.
Salva snapshot datado em `vault/02-relatorios/watchlist-YYYY-MM-DD.md` (mantém histórico, não sobrescreve).

> Use `--rever` no início da semana para montar o to-do de análises pendentes.

---

### `/adicionar` — Adicionar ativo à carteira

Valida o ticker nas APIs, insere na `carteira.md`, registra no `historico-trades.md`
e cria pasta `vault/01-ativos/TICKER/` com nota de tese inicial.
Se o ticker já existe na carteira, recalcula o preço médio ponderado e exibe P&L antes de atualizar.

```powershell
python sbwaa.py /adicionar --ticker PETR4 --tipo acao-on --quantidade 100 --preco-medio 38.50 --setor energia
python sbwaa.py /adicionar --ticker MXRF11 --tipo fii --quantidade 500 --preco-medio 9.80 --setor fundos-imobiliarios
python sbwaa.py /adicionar --ticker IVV --tipo etf-intl --quantidade 10 --preco-medio 520.00 --setor global

# Pular validação nas APIs (útil offline ou para ativos não suportados)
python sbwaa.py /adicionar --ticker XPTO3 --tipo acao-on --quantidade 50 --preco-medio 12.00 --setor tecnologia --skip-validacao

# Data de entrada personalizada (padrão: hoje)
python sbwaa.py /adicionar --ticker PETR4 --tipo acao-on --quantidade 50 --preco-medio 36.00 --setor energia --data 2024-03-15
```

**Tipos válidos para `--tipo`:**

| Flag          | Tipo                  | Label exibido   |
|---------------|-----------------------|-----------------|
| `acao-on`     | Ação Ordinária        | 🟦 AÇÃO ON      |
| `acao-pn`     | Ação Preferencial     | 🟦 AÇÃO PN      |
| `fii`         | Fundo Imobiliário     | 🟩 FII          |
| `etf-br`      | ETF Brasileiro        | 🟨 ETF BR       |
| `etf-intl`    | ETF Internacional     | 🟥 ETF INTL     |
| `renda-fixa`  | Renda Fixa            | ⬜ RF           |
| `tesouro`     | Tesouro Direto        | 🟪 TD           |
| `debenture`   | Debênture             | 🟫 DEB          |
| `cri-cra`     | CRI ou CRA            | 🟧 CRI/CRA      |

**Flags exclusivas para Renda Fixa (`renda-fixa` | `tesouro` | `debenture` | `cri-cra`):**

Para esses tipos, a validação via API é pulada automaticamente (sem ticker em bolsa).
O campo `--setor` passa a ser o **emissor** (XP, BTG, Nubank, Tesouro Nacional…).

```powershell
# CDB com todos os detalhes
python sbwaa.py /adicionar --ticker CDB001 --tipo renda-fixa --quantidade 1 --preco-medio 10000 \
  --setor "XP Investimentos" \
  --nome "CDB XP 110% CDI" \
  --indexador CDI --taxa "110%" --vencimento 2027-06-01

# Tesouro Direto
python sbwaa.py /adicionar --ticker TDREND30 --tipo tesouro --quantidade 1 --preco-medio 5000 \
  --setor "Tesouro Nacional" \
  --nome "Tesouro Renda+ 2030" \
  --indexador IPCA --taxa "+6%" --vencimento 2030-01-01

# Debênture com nome livre
python sbwaa.py /adicionar --ticker DEB001 --tipo debenture --quantidade 1 --preco-medio 20000 \
  --setor "BTG Pactual" \
  --nome "Debênture Incentivada BTG" \
  --indexador IPCA --taxa "+5.5%" --vencimento 2028-12-01
```

| Flag RF | Descrição |
|---------|-----------|
| `--nome "..."` | Nome legível do produto (ex: "CDB XP 110% CDI") |
| `--indexador X` | `CDI` \| `IPCA` \| `Selic` \| `PRE` \| `IGPM` |
| `--taxa "..."` | Taxa contratada (ex: `"110%"`, `"+6%"`, `"13.5% PRE"`) |
| `--vencimento YYYY-MM-DD` | Data de vencimento do título |

A nota gerada em `vault/01-ativos/TICKER/` inclui tabela estruturada com indexador, taxa e vencimento.
Unidade exibida: **unidades** (não "ações") no output e no histórico de trades.

---

### `/vender` — Registrar venda de ativo

Registra venda parcial ou total. Calcula P&L realizado, atualiza `carteira.md` e `historico-trades.md`.
Remove o ativo da carteira automaticamente se a quantidade chegar a zero.

```powershell
python sbwaa.py /vender --ticker PETR4 --quantidade 50 --preco 45.00
python sbwaa.py /vender --ticker MXRF11 --quantidade 500 --preco 10.50    # venda total

# Data da venda personalizada (padrão: hoje)
python sbwaa.py /vender --ticker PETR4 --quantidade 30 --preco 46.00 --data 2024-06-10
```

---

### `/risco-carteira` — Métricas quantitativas de risco

Roda o Quant/Data Engineer e o Risk Engineer localmente (sem IA, só cálculo numérico)
e exibe VaR, CVaR, Sharpe, drawdown, beta e circuit breakers do IPS.

```powershell
python sbwaa.py /risco-carteira
```

Output: VaR 95% (1 dia), CVaR, Sharpe 12m, volatilidade anual, drawdown máximo,
beta vs IBOV, concentração máxima e status dos circuit breakers.

> Valores monetários normalizados em R$ 100k para preservar privacidade.

---

### `/otimizar-expansao` — Fronteira eficiente com candidatos da watchlist

Compara a fronteira eficiente da carteira atual com a fronteira expandida (carteira + ativos da watchlist). Identifica quais candidatos melhorariam, degradariam ou seriam neutros ao portfólio.

```powershell
python sbwaa.py /otimizar-expansao
```

Output por candidato: correlação com a carteira, ΔSharpe ao adicionar a 5% de peso, peso ótimo no portfólio Max Sharpe e classificação **MELHORA / NEUTRO / PIORA**.

> Requer dados históricos de preços dos ativos da watchlist. Salva cache para uso pelo `/rebalancear` e `/revisar-carteira`.

---

### `/dividendos` — Calendário e histórico de proventos

Busca dados de dividendos via Yahoo Finance para todos os ativos da carteira.
Ao final, grava `.proventos-cache.json` em `vault/00-portfolio/` para uso pelo `/carteira`.

```powershell
python sbwaa.py /dividendos
```

Output:
- Próximos dividendos nos 60 dias seguintes (data + valor estimado por ticker)
- Dividendos declarados (ex-date confirmada, ainda não pagos)
- Histórico do ano atual: total recebido por ativo e Yield on Cost
- Total consolidado de proventos recebidos no ano

---

### `/stress-test` — Simulação de choques na carteira

Aplica cenários históricos ou choque personalizado ao beta da carteira.

```powershell
# Todos os cenários históricos de uma vez
python sbwaa.py /stress-test

# Cenário específico (busca por nome parcial)
python sbwaa.py /stress-test crise-2008
python sbwaa.py /stress-test covid-2020
python sbwaa.py /stress-test eleicoes-2022
python sbwaa.py /stress-test lula-2002

# Choque personalizado (qualquer percentual)
python sbwaa.py /stress-test custom -20
python sbwaa.py /stress-test custom -35
python sbwaa.py /stress-test custom 15
```

Cenários disponíveis: Crise Financeira 2008 (-41%), COVID Março 2020 (-30%),
Incerteza Eleitoral 2022 (-15%), Crise de Confiança 2002 (-17%).

> Patrimônio normalizado em R$ 100k — privacidade preservada.

---

### `/simulacao` — Simulação Monte Carlo de patrimônio

Projeta a evolução do patrimônio ao longo do tempo via Monte Carlo (GBM),
usando parâmetros históricos da carteira (drift e volatilidade calculados pelo `/risco-carteira`).

```powershell
# Simulação padrão (1000 caminhos, 10 anos, aporte mensal do IPS)
python sbwaa.py /simulacao

# Horizonte e aporte personalizados
python sbwaa.py /simulacao --anos 20 --aporte 2000

# Salvar gráfico em vez de exibir
python sbwaa.py /simulacao --salvar
```

**Flags:**

| Flag | Padrão | Descrição |
|------|--------|-----------|
| `--anos N` | 10 | Horizonte de projeção em anos |
| `--aporte N` | IPS | Aporte mensal em R$ (sobrescreve o IPS) |
| `--salvar` | — | Salva gráfico em `vault/05-risk/simulacao-YYYY-MM-DD.png` |

**Output:** cabeçalho com parâmetros (drift, vol, nº de simulações) + tabela P10/P50/P90 por ano + resumo do patrimônio esperado no horizonte final. Com `--salvar`, gera também gráfico em `vault/05-risk/`.

<details>
<summary>Exemplo de output</summary>

```
══════════════════════════════════════════════════════
  SIMULAÇÃO MONTE CARLO — 10 anos | Aporte: R$ 2.000/mês
══════════════════════════════════════════════════════
  Parâmetros: drift 12,3% a.a. | vol 18,7% a.a. | 1.000 simulações

  Ano    P10         P50         P90
  1      R$ 25.200   R$ 28.400   R$ 34.100
  3      R$ 42.500   R$ 58.700   R$ 81.200
  5      R$ 68.300   R$ 103.900  R$ 162.400
  10     R$ 132.100  R$ 268.500  R$ 573.800

  Patrimônio atual: R$ 19.874 | Esperado P50 (10a): R$ 268.500
══════════════════════════════════════════════════════
```

</details>

> Requer `matplotlib` instalado. Parâmetros reutilizados do cache `logs/simulacao/params_cache.json`
> gerado pelo `/risco-carteira`.

---

### `/ips` — Exibir e editar o IPS

Exibe o Investment Policy Statement atual com perfil, alocação alvo e limites de risco.

```powershell
python sbwaa.py /ips
python sbwaa.py /ips --editar    # abre o arquivo para edição
```

---

### `/snapshot` — Snapshot diário de mercado

Busca dados macro globais (IBOV, S&P500, Nasdaq, DXY, BRL/USD, Petróleo WTI,
Ouro, Juros EUA 10Y) e cotações da carteira e salva nota no vault.

```powershell
python sbwaa.py /snapshot
```

Output salvo em: `vault/02-relatorios/diarios/snapshot-YYYY-MM-DD.md`

---

### `/knowledge` — Base de conhecimento RAG

Gerencia a base vetorial de documentos financeiros (ChromaDB + embeddings multilingual).

```powershell
# Ver status da base (total de documentos, tamanho, última indexação)
python sbwaa.py /knowledge --status

# Indexar arquivo único (PDF, DOCX, TXT, MD)
python sbwaa.py /knowledge --adicionar "C:\relatorios\resultado-petr4-3t24.pdf"

# Indexar pasta inteira recursivamente
python sbwaa.py /knowledge --adicionar "vault/01-ativos/PETR4/"

# Busca semântica (retorna chunks relevantes rankeados por score)
python sbwaa.py /knowledge --buscar "valuation petróleo Brasil"
python sbwaa.py /knowledge --buscar "resultado EBITDA 2024 siderurgia"

# Coletar e indexar notícias dos feeds RSS configurados
python sbwaa.py /knowledge --coletar-rss

# Listar todos os documentos indexados
python sbwaa.py /knowledge --listar
```

Fontes RSS padrão: Valor Econômico, InfoMoney, BCB, Bloomberg, Reuters.

---

### `/ui` — Painel visual

Abre o painel desktop em customtkinter com todos os comandos acessíveis por botão,
formulários para entrada de dados e output em tempo real na janela.

```powershell
python sbwaa.py /ui
# ou diretamente:
python ui.py
```

O painel tem 5 abas: **Portfólio**, **Análise (IA)**, **Mercado**, **Relatórios (IA)**, **Knowledge**.
Comandos locais executam direto. Comandos de IA copiam o comando para o clipboard.

---

## Comandos de IA (Claude Code — sem API key)

Estes comandos acionam agentes de IA. No modo padrão (sem API key),
o terminal exibe a instrução de uso e o botão `/ui` copia para o clipboard.
**Para executar: digite o comando diretamente no chat do Claude Code.**

---

### `/analisar TICKER [TICKER2 ...]` — Pipeline completo de análise (10 etapas, 8 agentes)

Executa todos os 8 agentes em sequência para um ou mais ativos.

```
/analisar PETR4
/analisar PETR4 VALE3 XPML11
```

Em batch (2+ tickers): pipeline completo e isolado para cada ticker em sequência,
output individual normal para cada um + tabela comparativa de veredictos ao final.

Etapas: dados de mercado (Brapi + Yahoo + BCB) → Market Researcher → Earnings Reviewer →
Model Builder (DCF) → Valuation Reviewer (incl. preço teto/chão) → Quant → **Econometrician**
(GARCH, beta dinâmico, Fama-French 3F, macro BCB, correlações rolling, drawdown avançado) →
Risk Engineer → Portfolio Manager → Salvar nota.

Output gerado em `vault/01-ativos/TICKER/`.

---

### `/tese TICKER` — Tese rápida (Research + DCF + PM)

Versão acelerada do pipeline — pula Earnings detalhado e Quant/Risk standalone.
Ideal para primeira avaliação de um ativo.

```
/tese PETR4
/tese VALE3 --completo
```

---

### `/earnings TICKER` — Revisão de resultados trimestrais

Analisa os resultados mais recentes do ativo: receita, EBITDA, lucro líquido,
dívida e guidance. Compara com trimestres anteriores.

```
/earnings PETR4
/earnings WEGE3
```

---

### `/comparar TICKER1 TICKER2` — Análise comparativa

Coloca dois ativos lado a lado em valuation, qualidade, risco e retorno.
Gera recomendação de alocação relativa.

```
/comparar PETR4 VALE3
/comparar MXRF11 HGLG11
```

---

### `/pm TICKER` — Decisão do Portfolio Manager

Executa apenas o Portfolio Manager com base nos dados já cacheados do ativo.
Retorna veredicto COMPRAR / AGUARDAR / EVITAR com sizing sugerido.

```
/pm PETR4
/pm VALE3
```

> O sizing é calculado localmente (sem enviar patrimônio à API).

Após emitir o veredicto, salva automaticamente:
- **Uma linha** na tabela de `vault/00-portfolio/decisoes.md` (histórico permanente de decisões do PM)
- **`vault/01-ativos/TICKER/pm-decisao-TICKER-YYYY-MM-DD.md`** com frontmatter estruturado (`veredicto`, `ticker`, `data`, `sizing`)

---

### `/pm` · `/pm 700` — Modo Aporte (PM conversacional)

PM distribui um valor entre múltiplos ativos da watchlist e carteira, priorizando pelo desvio de IPS e qualidade da análise.

```
/pm            → perguntas interativas completas
/pm 700        → atalho: valor pré-definido, demais perguntas normais
/pm 1500       → atalho com valor maior
```

**Fluxo interativo:**

```
PM: Qual valor você tem disponível para aporte? (R$)     ← pulada no atalho /pm 700
PM: Preferência de classe de ativo?
    [1] Automático pelo IPS  [2] FII  [3] Ação  [4] ETF  [5] Renda Fixa / Tesouro
PM: Em quantos ativos diferentes quer distribuir? (ex: 3, 5)
PM: Alguma restrição ou observação? (Enter para pular)
    Ex: 'sem XPML11', 'prefiro FIIs logística', 'nada de petróleo'
```

**Requisito de candidatos:**
- Ativos precisam ter análise prévia em `vault/01-ativos/TICKER/`
- Mínimo: `/pm TICKER` (pm-decisao presente)
- Ideal: `/analisar TICKER` (equity-research + quant + risk presentes)
- Se faltar análise: PM lista os pendentes, oferece rodar `/analisar` e **retoma automaticamente** ao concluir

**Lógica de seleção e distribuição:**
- Filtra por veredicto COMPRAR (fora da carteira) ou AUMENTAR (já em carteira)
- Prioriza: AUMENTAR > COMPRAR, gap IPS da classe, frescor da análise (<45d), presença de /analisar
- Distribuição: 60% igual entre os N ativos + 40% ponderado pelo gap de IPS
- Arredonda para cotas inteiras usando preço atual (cache ou carteira)

**Output do PM:**
- Valida e ajusta a distribuição
- Justificativa por ativo (veredicto, risco principal)
- Alerta de violação de IPS (concentração máx)
- Tabela final: Ticker | Valor (R$) | Cotas | Prioridade | Observação
- Loop de ajuste: campo livre para refinar a sugestão

**Salva automaticamente:**
- `vault/00-portfolio/pm-aporte-YYYY-MM-DD.md` com frontmatter e análise completa
- Linha no log `vault/00-portfolio/decisoes.md`

---

### `/morning-call` — Briefing pré-abertura

Compila snapshot macro + Market Researcher + alertas ativos em um briefing diário.

```
/morning-call
```

---

### `/mundo-economico` — Macro do dia

Panorama do cenário econômico global e impactos no Brasil.

```
/mundo-economico
```

---

### `/investimento-do-dia` — Oportunidade do dia

Sugere 1-2 ativos para explorar análise com base no IPS e no cenário macro atual.

```
/investimento-do-dia
```

---

### `/relatorio-semanal` — Relatório semanal

P&L da semana, métricas de performance e outlook. Gera `.md` e `.docx`.

```
/relatorio-semanal
```

Output em: `vault/02-relatorios/semanais/semana-YYYY-WNN.md`

Gera também **risk snapshot semanal** em `vault/05-risk/snapshots/risk-YYYY-MM-DD.md` — tabela de métricas (VaR, CVaR, drawdown, concentração) vs limites do IPS, com status de circuit breakers.

---

### `/relatorio-mensal` — Relatório mensal

Relatório completo do mês: performance, análise de risco, revisão de teses,
comparação com benchmarks. Gera `.md` e `.docx`.

```
/relatorio-mensal
```

Output em: `vault/02-relatorios/mensais/`

---

### `/metas` — Dashboard de metas financeiras

Exibe o progresso de todas as metas definidas em `vault/00-portfolio/metas.md` com projeções de quando serão atingidas.

```
/metas
```

Output: barras de progresso para renda passiva mensal, patrimônio total, reserva de emergência e metas livres (viagem, imóvel, etc.). Cada meta exibe % atingido, valor atual vs alvo, projeção com e sem aportes e status OK / ATENÇÃO vs prazo.

Configure as metas em `vault/00-portfolio/metas.md` ou pelo IPS (`/ips --editar`).

---

### `/rebalancear` — Sugestão de rebalanceamento

Compara alocação atual com os alvos do IPS, identifica desvios acima de ±5%
e sugere ajustes com valores estimados de compra/venda.

```
/rebalancear
```

---

### `/revisar-carteira` — Revisão completa de posições

PM avalia cada ativo em carteira individualmente e emite:
**MANTER / AUMENTAR / REDUZIR / SAIR** com sizing alvo e justificativa.
Inclui painel consolidado, prioridades imediatas e alertas de IPS.

```
/revisar-carteira
```

Output em: `vault/02-relatorios/revisoes/`

---

## Automação — Task Scheduler (v2.12.0)

O módulo `scripts/automation/` controla o agendamento automático via Windows Task Scheduler.
Três slots rodam sem interação: morning (07:45), EOD (17:00) e weekend (08:00).

```powershell
# Instalar as 3 tarefas no Task Scheduler (ativa WakeToRun + StartWhenAvailable)
python scripts/automation/setup_scheduler.py --instalar

# Ver status e próximas execuções
python scripts/automation/setup_scheduler.py --status

# Remover todas as tarefas
python scripts/automation/setup_scheduler.py --remover

# Disparar um slot agora (teste)
python scripts/automation/setup_scheduler.py --testar morning
python scripts/automation/setup_scheduler.py --testar eod
python scripts/automation/setup_scheduler.py --testar weekend
```

**Slots disponíveis:**

| Slot | Horário | Dias | O que executa |
|------|---------|------|---------------|
| `morning` | 07:45 | seg–sex | RSS → snapshot → quant → risk → alertas → `/morning-call` |
| `eod` | 17:00 | seg–sex | snapshot EOD → alertas → `/snapshot` |
| `weekend` | 08:00 | sáb–dom | `/relatorio-semanal` (dom) + `/relatorio-mensal` (1° fds) |

**Execução manual por slot (com `--dry-run` para simular sem executar):**

```powershell
python scripts/automation/main.py --slot morning
python scripts/automation/main.py --slot morning --dry-run
```

> **PC em sleep:** `WakeToRun` acorda o computador automaticamente.
> **PC desligado:** `StartWhenAvailable` executa no próximo boot.
> Log em: `logs/automation.log`

---

## Manutenção do sistema

### `/att-info-system` — Sincronização completa de sessão

```
/att-info-system
```

Executa o protocolo completo de fechamento de sessão de forma autônoma:

1. Lê `VERSION.md`, `git log`, `git diff` e `git status`
2. Detecta automaticamente o que mudou (módulo, tipo: MAJOR/MINOR/PATCH)
3. Cria ou complementa a entrada do `CHANGELOG.md`
4. Atualiza strings de versão em todos os docs (README, GUIA-COMANDOS, REFERENCIA, WORKFLOW, APRESENTACAO, MASTER-BLUEPRINT, LOGO, sbwaa.py)
5. Atualiza conteúdo onde necessário: novos comandos em sbwaa.py /help, botões em ui.py, seções em GUIA-COMANDOS, REFERENCIA, WORKFLOW, APRESENTACAO, MASTER-BLUEPRINT
6. Verifica segurança git (bloqueia vault/00-portfolio/, .env, caches)
7. Faz commit + push + gh release (obrigatório para MINOR/MAJOR)
8. Exibe relatório final compacto do que foi feito

> Usar este comando ao encerrar **qualquer sessão** que tenha alterado o sistema.

---

## Comandos de sistema

```powershell
python sbwaa.py /help      # lista todos os comandos com sintaxe
python sbwaa.py /status    # versão atual, modo e data
```

---

## Os 8 agentes

| Agente             | Modelo            | Função                                                       |
|--------------------|-------------------|--------------------------------------------------------------|
| Market Researcher  | claude-sonnet-4-6 | Análise macro, setorial e posicionamento                     |
| Earnings Reviewer  | claude-sonnet-4-6 | Revisão de resultados trimestrais                            |
| Model Builder      | claude-opus-4-6   | Construção de DCF e modelos de valuation                     |
| Valuation Reviewer | claude-sonnet-4-6 | Revisão crítica do modelo, equity research                   |
| Quant/Data Eng.    | claude-sonnet-4-6 | Métricas quantitativas: Sharpe, VaR, correlação              |
| Econometrician     | claude-sonnet-4-6 | GARCH, beta dinâmico rolling, Fama-French 3F, macro BCB      |
| Risk Engineer      | claude-opus-4-6   | VaR, CVaR, stress tests, circuit breakers, Fronteira Markowitz |
| Portfolio Manager  | claude-opus-4-6   | Decisão final: COMPRAR / AGUARDAR / EVITAR / MANTER / SAIR  |

Cada agente tem um `SKILL.md` com seu sistema de instruções e um `run_*.py`
que pode ser chamado diretamente ou via pipeline `/analisar`.

---

## Rotinas de uso

> Workflow completo por cadência e por fluxo oportunístico, com árvores de decisão e encadeamento de comandos:
>
> → **[`docs/SBWAA-WORKFLOW.md`](SBWAA-WORKFLOW.md)**

Resumo rápido das cadências:

| Cadência | Tempo | Foco |
|----------|-------|------|
| Diária (pré-abertura) | 5–10 min | `/morning-call` + `/snapshot` |
| Semanal | 20–30 min | `/risco-carteira` + `/relatorio-semanal` + `/rebalancear` |
| Mensal | 60–90 min | `/risco-carteira` + `/stress-test` + `/simulacao` + `/otimizar-expansao` + `/revisar-carteira` + `/rebalancear` |
| Trimestral (resultados) | 2–3h | `/earnings` por ativo + recalibração completa |
| Anual | meio período | Revisão do IPS + reposicionamento |

---

## Estrutura de arquivos

```
SBWAA/
├── sbwaa.py                    ← ponto de entrada único de todos os comandos
├── ui.py                       ← painel visual (customtkinter)
├── requirements.txt
├── .env                        ← API key (não versionado)
├── .env.template
├── CLAUDE.md                   ← políticas globais, roteamento de modelos
├── VERSION.md
├── CHANGELOG.md
│
├── .claude/
│   ├── agents/
│   │   ├── market-researcher/      ← SKILL.md + run_market_researcher.py
│   │   ├── earnings-reviewer/      ← SKILL.md + run_earnings_reviewer.py
│   │   ├── model-builder/          ← SKILL.md + run_model_builder.py
│   │   ├── valuation-reviewer/     ← SKILL.md + run_valuation_reviewer.py
│   │   ├── quant-data-engineer/    ← SKILL.md + run_quant.py + calculators/
│   │   ├── risk-engineer/          ← SKILL.md + run_risk_engineer.py + calculators/
│   │   └── portfolio-manager/      ← SKILL.md + run_pm.py + run_analisar.py
│   └── commands/                   ← script de cada slash command local
│       ├── carteira.py
│       ├── risco_carteira.py
│       ├── dividendos.py
│       ├── stress_test.py
│       ├── ips.py
│       └── ...
│
├── scripts/
│   ├── data/
│   │   ├── fetch_brapi.py          ← cotações e fundamentalistas BR (Brapi)
│   │   ├── fetch_yahoo.py          ← macro, ETFs e histórico (Yahoo Finance)
│   │   ├── update_carteira.py      ← atualiza preços e P&L na carteira.md
│   │   ├── add_ativo.py            ← adiciona ativo à carteira
│   │   ├── vender_ativo.py         ← registra venda e P&L realizado
│   │   ├── market_snapshot.py      ← snapshot diário de mercado
│   │   └── cache/                  ← cache JSON com TTL de 4h
│   ├── alerts/
│   │   └── check_alerts.py         ← 8 tipos de alerta automático
│   ├── heartbeat/
│   │   ├── heartbeat.py            ← processo diário automatizado
│   │   └── schedule_heartbeat.py   ← instruções de agendamento
│   └── diagnostico.py              ← auditoria de integridade do sistema
│
├── knowledge/
│   ├── indexer.py                  ← indexação de documentos no ChromaDB
│   ├── retriever.py                ← busca semântica
│   ├── rss_collector.py            ← coleta de feeds RSS
│   ├── knowledge_cmd.py            ← handler do comando /knowledge
│   ├── save_synthesis.py           ← salva sínteses RAG no vault
│   ├── raw/                        ← documentos brutos (.gitignore)
│   ├── indexed/                    ← log de indexação (hash MD5)
│   └── sources/                    ← configuração de feeds RSS
│
└── vault/                          ← notas Obsidian
    ├── 00-portfolio/
    │   ├── carteira.md             ← posições ativas (gerenciado automaticamente)
    │   ├── ips.md                  ← Investment Policy Statement
    │   ├── historico-trades.md     ← log de operações
    │   └── decisoes.md             ← log de decisões do PM
    ├── 01-ativos/                  ← uma pasta por ticker (tese, DCF, earnings...)
    ├── 02-relatorios/              ← diários, semanais, mensais
    ├── 03-macro/                   ← notas do Market Researcher
    ├── 04-knowledge/               ← sínteses RAG
    └── 05-risk/                    ← snapshots de risco quantitativo
```

---

## Segurança

- Dados de portfólio (posições, preço médio, patrimônio) **nunca saem do vault local**
- APIs externas recebem apenas tickers públicos, datas e parâmetros de mercado
- Sizing do Portfolio Manager é calculado localmente — a API recebe apenas pesos percentuais
- Stress tests normalizam o patrimônio em R$ 100k para exibição
- Cache em `scripts/data/cache/` fica exclusivamente local

Regras completas: `CLAUDE.md` — seção Security Policy.

---

## Dependências e compatibilidade

- **Python:** 3.10+
- **SO:** Windows 10/11 (testado), macOS e Linux (compatível)
- **Terminal:** PowerShell recomendado no Windows
- **Obsidian:** opcional — vault funciona sem o app aberto

```powershell
pip install -r requirements.txt
```
