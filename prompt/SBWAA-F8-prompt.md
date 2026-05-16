# SBWAA — FASE 8: INTERFACE VISUAL (STREAMLIT) + PIXEL ART
**Prompt para execução no Claude Code**
**Versão:** 2.0.0
**Fase:** 8 de 8 — VERSÃO BETA COMPLETA
**Pré-requisito:** Fases 0–7 concluídas (investments v1.7.0 | knowledge-base v1.0.0)

---

## CONTEXTO

A Fase 8 é a última fase do SBWAA. Ela constrói a **interface visual local**
em Streamlit — um dashboard que roda no browser, substituindo (opcionalmente)
o terminal como ponto de acesso ao sistema.

Esta é uma **versão beta/teste**. O objetivo é ter algo funcional e visual,
não perfeito. O terminal continua funcionando normalmente — a interface
é uma camada adicional, não uma substituição.

Aqui também são **inseridos os bonecos pixel art** nos relatórios e na
interface — um por agente, no estilo que o usuário criou.

Ao concluir esta fase, o SBWAA estará em **v2.0.0** — sistema completo
operacional.

---

## REGRAS GERAIS — LER ANTES DE EXECUTAR

1. Instalar dependências:
```bash
pip install streamlit plotly watchdog --break-system-packages
```
2. A interface roda 100% local — nunca em servidor externo
3. Porta padrão: `localhost:8501`
4. Os bonecos pixel art são inseridos via caminhos locais
   — o usuário já criou os arquivos PNG em `vault/assets/agents-pixel/`
5. Se algum arquivo de pixel art não existir, usar placeholder genérico
   sem quebrar a interface
6. Esta fase não cria novos agentes — apenas exibe o que já existe
7. Ao finalizar: versão global → **v2.0.0**, `interface` → v1.0.0

---

## PARTE 1 — ESTRUTURA DE ARQUIVOS

```
/sbwaa/interface/
├── app.py                  ← ponto de entrada Streamlit
├── pages/
│   ├── 01_carteira.py      ← página da carteira
│   ├── 02_analisar.py      ← página de análise de ativo
│   ├── 03_morning_call.py  ← página do morning call
│   ├── 04_risco.py         ← página de risco da carteira
│   ├── 05_relatorios.py    ← página de relatórios
│   ├── 06_knowledge.py     ← página da base de conhecimento
│   └── 07_agentes.py       ← página de status dos agentes
├── components/
│   ├── metricas_hf.py      ← componente de métricas HF reutilizável
│   ├── pixel_art.py        ← componente de exibição dos bonecos
│   ├── alerts_bar.py       ← barra de alertas no topo
│   └── sidebar.py          ← sidebar com navegação e status
└── style/
    └── sbwaa.css           ← estilos customizados
```

Adicionar ao `sbwaa.py` (Fase 6) o comando `/ui`:

```python
"/ui": None,  # tratado internamente
```

```python
if comando == "/ui":
    os.system("streamlit run interface/app.py")
    return
```

---

## PARTE 2 — ARQUIVO PRINCIPAL: `app.py`

Crie `/sbwaa/interface/app.py`:

```python
"""
SBWAA — Interface Visual
Versão Beta | Roda localmente em localhost:8501

Iniciar: python sbwaa.py /ui
       ou: streamlit run interface/app.py
"""

import streamlit as st
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="SBWAA",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Carregar CSS customizado
def carregar_css():
    css_path = Path(__file__).parent / "style" / "sbwaa.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>",
                        unsafe_allow_html=True)

carregar_css()

# Caminhos base
BASE_DIR = Path(__file__).parent.parent
VAULT_DIR = BASE_DIR / "vault"
CACHE_DIR = BASE_DIR / "scripts" / "data" / "cache"
ASSETS_DIR = VAULT_DIR / "assets" / "agents-pixel"

# Barra de alertas no topo
from components.alerts_bar import exibir_alertas
exibir_alertas()

# Página principal — Dashboard
st.title("🧠 SBWAA")
st.caption(f"Second Brain Wealth + Asset + Assessor Individual | "
           f"{datetime.now().strftime('%d/%m/%Y %H:%M')}")

st.divider()

# Cards de resumo rápido (4 colunas)
col1, col2, col3, col4 = st.columns(4)

# Carregar dados do cache de risco (se existir)
hoje = datetime.now().strftime("%Y-%m-%d")
risk_cache = CACHE_DIR / f"risk_{hoje}.json"
quant_cache = CACHE_DIR / f"quant_{hoje}.json"

risk_data = {}
quant_data = {}

if risk_cache.exists():
    with open(risk_cache) as f:
        risk_data = json.load(f)

if quant_cache.exists():
    with open(quant_cache) as f:
        quant_data = json.load(f)

with col1:
    sharpe = quant_data.get("carteira", {}).get("sharpe", "—")
    st.metric(
        label="Sharpe (12m)",
        value=f"{sharpe:.2f}" if isinstance(sharpe, float) else sharpe
    )

with col2:
    vol = quant_data.get("carteira", {}).get("volatilidade_pct", "—")
    st.metric(
        label="Volatilidade Anual",
        value=f"{vol:.1f}%" if isinstance(vol, float) else vol
    )

with col3:
    var = risk_data.get("var_historico_95_pct", "—")
    st.metric(
        label="VaR 95% (1 dia)",
        value=f"{var:.1%}" if isinstance(var, float) else var
    )

with col4:
    dd = risk_data.get("drawdown_atual_pct", "—")
    st.metric(
        label="Drawdown Atual",
        value=f"{dd:.1%}" if isinstance(dd, float) else dd,
        delta_color="inverse"
    )

st.divider()

# Seção de ações rápidas
st.subheader("⚡ Ações Rápidas")

col_a, col_b, col_c, col_d = st.columns(4)

with col_a:
    if st.button("📊 Morning Call", use_container_width=True):
        st.switch_page("pages/03_morning_call.py")

with col_b:
    if st.button("💼 Carteira", use_container_width=True):
        st.switch_page("pages/01_carteira.py")

with col_c:
    if st.button("🛡️ Risco", use_container_width=True):
        st.switch_page("pages/04_risco.py")

with col_d:
    if st.button("🔍 Analisar Ativo", use_container_width=True):
        st.switch_page("pages/02_analisar.py")

st.divider()

# Status dos agentes
st.subheader("👥 Equipe SBWAA")
from components.pixel_art import exibir_equipe_resumo
exibir_equipe_resumo()
```

---

## PARTE 3 — COMPONENTES

### `components/pixel_art.py`

```python
"""
Componente de exibição dos bonecos pixel art dos agentes.
Se o arquivo PNG não existir, exibe placeholder com emoji.
"""
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
ASSETS_DIR = BASE_DIR / "vault" / "assets" / "agents-pixel"

# Configuração de cada agente
AGENTES = {
    "market-researcher": {
        "nome": "Market Researcher",
        "descricao": "Macro & Notícias",
        "emoji": "📰",
        "arquivo": "market-researcher.png",
        "cor": "#78350F"  # marrom — macro
    },
    "earnings-reviewer": {
        "nome": "Earnings Reviewer",
        "descricao": "Resultados Trimestrais",
        "emoji": "📋",
        "arquivo": "earnings-reviewer.png",
        "cor": "#1E40AF"  # azul
    },
    "model-builder": {
        "nome": "Model Builder",
        "descricao": "DCF & Valuation",
        "emoji": "🏗️",
        "arquivo": "model-builder.png",
        "cor": "#065F46"  # verde escuro
    },
    "valuation-reviewer": {
        "nome": "Valuation Reviewer",
        "descricao": "Revisão & Comps",
        "emoji": "🔍",
        "arquivo": "valuation-reviewer.png",
        "cor": "#4338CA"  # índigo
    },
    "quant-data-engineer": {
        "nome": "Quant / Data Engineer",
        "descricao": "Sharpe, Beta, Correlação",
        "emoji": "📐",
        "arquivo": "quant-data-engineer.png",
        "cor": "#B45309"  # âmbar
    },
    "risk-engineer": {
        "nome": "Risk Engineer",
        "descricao": "VaR, CVaR, Stress Test",
        "emoji": "🛡️",
        "arquivo": "risk-engineer.png",
        "cor": "#991B1B"  # vermelho
    },
    "portfolio-manager": {
        "nome": "Portfolio Manager",
        "descricao": "Decisão Final",
        "emoji": "🎯",
        "arquivo": "portfolio-manager.png",
        "cor": "#B7791F"  # dourado
    }
}

def exibir_agente_card(agente_id: str, mostrar_descricao: bool = True):
    """Exibe card de um agente específico com pixel art ou emoji."""
    config = AGENTES.get(agente_id, {})
    if not config:
        return

    arquivo = ASSETS_DIR / config["arquivo"]
    col_img, col_info = st.columns([1, 3])

    with col_img:
        if arquivo.exists():
            st.image(str(arquivo), width=64)
        else:
            st.markdown(
                f"<div style='font-size:48px;text-align:center'>"
                f"{config['emoji']}</div>",
                unsafe_allow_html=True
            )

    with col_info:
        st.markdown(
            f"**{config['nome']}**",
            help=config['descricao']
        )
        if mostrar_descricao:
            st.caption(config['descricao'])


def exibir_equipe_resumo():
    """Exibe a equipe completa em grid 4+3."""
    agentes_ids = list(AGENTES.keys())
    # Linha 1: 4 agentes
    cols = st.columns(4)
    for i, col in enumerate(cols):
        if i < len(agentes_ids):
            with col:
                exibir_agente_mini(agentes_ids[i])
    # Linha 2: 3 agentes (centralizados)
    _, c1, c2, c3, _ = st.columns([0.5, 1, 1, 1, 0.5])
    for i, col in enumerate([c1, c2, c3]):
        idx = i + 4
        if idx < len(agentes_ids):
            with col:
                exibir_agente_mini(agentes_ids[idx])


def exibir_agente_mini(agente_id: str):
    """Card mínimo do agente — emoji + nome."""
    config = AGENTES.get(agente_id, {})
    arquivo = ASSETS_DIR / config.get("arquivo", "")
    st.markdown(
        f"<div style='text-align:center;padding:8px;"
        f"border-radius:8px;border:1px solid {config.get('cor','#333')}'>"
        f"<div style='font-size:32px'>{config.get('emoji','')}</div>"
        f"<div style='font-size:11px;margin-top:4px'>"
        f"{config.get('nome','')}</div></div>",
        unsafe_allow_html=True
    )
```

### `components/metricas_hf.py`

```python
"""
Componente reutilizável: bloco de métricas HF da carteira.
Usado na página de risco, no dashboard e no output do PM.
"""
import streamlit as st
import plotly.graph_objects as go

def exibir_metricas_hf(risk_data: dict, quant_data: dict):
    """
    Exibe o bloco completo de métricas HF em 2 linhas de cards.
    """
    carteira = quant_data.get("carteira", {})
    cb = risk_data.get("circuit_breakers", {})

    def status_icon(ok: bool) -> str:
        return "✅" if ok else "🚨"

    st.markdown("### 📊 Métricas HF da Carteira")

    # Linha 1
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Sharpe (12m)",
                  f"{carteira.get('sharpe', '—'):.2f}"
                  if isinstance(carteira.get('sharpe'), float) else "—")
    with c2:
        st.metric("Volatilidade Anual",
                  f"{carteira.get('volatilidade_pct', '—'):.1f}%"
                  if isinstance(carteira.get('volatilidade_pct'), float)
                  else "—")
    with c3:
        var = risk_data.get("var_historico_95_pct", None)
        icon = status_icon(cb.get("var_ok", True))
        st.metric(f"VaR 95% (1d) {icon}",
                  f"{var:.1%}" if isinstance(var, float) else "—")
    with c4:
        cvar = risk_data.get("cvar_95_pct", None)
        st.metric("CVaR 95% (1d)",
                  f"{cvar:.1%}" if isinstance(cvar, float) else "—")

    # Linha 2
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        dd = risk_data.get("drawdown_atual_pct", None)
        icon = status_icon(cb.get("drawdown_ok", True))
        st.metric(f"Drawdown Atual {icon}",
                  f"{dd:.1%}" if isinstance(dd, float) else "—")
    with c6:
        ddmax = risk_data.get("drawdown_maximo_pct", None)
        st.metric("Max Drawdown Hist.",
                  f"{ddmax:.1%}" if isinstance(ddmax, float) else "—")
    with c7:
        beta = carteira.get("beta_ibov", None)
        st.metric("Beta vs IBOV",
                  f"{beta:.2f}" if isinstance(beta, float) else "—")
    with c8:
        conc = risk_data.get("concentracao_maxima_pct", None)
        ticker_conc = risk_data.get("concentracao_maxima_ticker", "")
        icon = status_icon(cb.get("concentracao_ok", True))
        st.metric(f"Maior Conc. {icon}",
                  f"{conc:.1f}% ({ticker_conc})"
                  if isinstance(conc, float) else "—")


def grafico_correlacao(matriz_corr: dict):
    """Heatmap de correlação entre ativos da carteira."""
    if not matriz_corr:
        st.info("Matriz de correlação não disponível. "
                "Execute /risco-carteira primeiro.")
        return

    import pandas as pd
    df = pd.DataFrame(matriz_corr)
    fig = go.Figure(data=go.Heatmap(
        z=df.values,
        x=df.columns.tolist(),
        y=df.index.tolist(),
        colorscale="RdBu_r",
        zmid=0,
        zmin=-1, zmax=1,
        text=[[f"{v:.2f}" for v in row] for row in df.values],
        texttemplate="%{text}",
        showscale=True
    ))
    fig.update_layout(
        title="Matriz de Correlação",
        height=400,
        margin=dict(l=40, r=40, t=40, b=40)
    )
    st.plotly_chart(fig, use_container_width=True)


def grafico_alocacao(ativos: dict):
    """Gráfico de pizza com alocação atual."""
    if not ativos:
        return
    labels = list(ativos.keys())
    values = [v.get("peso_carteira_pct", 0) for v in ativos.values()]
    fig = go.Figure(data=go.Pie(
        labels=labels, values=values,
        hole=0.4,
        textinfo="label+percent"
    ))
    fig.update_layout(
        title="Alocação da Carteira",
        height=350,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)
```

### `components/alerts_bar.py`

```python
"""
Barra de alertas exibida no topo de todas as páginas.
"""
import streamlit as st
from pathlib import Path
from datetime import datetime

def exibir_alertas():
    """Lê o log de alertas e exibe os ativos de hoje no topo."""
    log_path = Path(__file__).parent.parent.parent / "logs" / "alerts.log"
    if not log_path.exists():
        return

    hoje = datetime.now().strftime("%Y-%m-%d")
    alertas_hoje = []

    with open(log_path) as f:
        for linha in f.readlines()[-50:]:  # últimas 50 linhas
            if hoje in linha and (
                "CRÍTICO" in linha or "ALTO" in linha
            ):
                alertas_hoje.append(linha.strip())

    if not alertas_hoje:
        return

    with st.container():
        for alerta in alertas_hoje[:3]:  # máx 3 no topo
            if "CRÍTICO" in alerta:
                st.error(f"🚨 {alerta.split('|')[-1].strip()}")
            elif "ALTO" in alerta:
                st.warning(f"⚠️ {alerta.split('|')[-1].strip()}")
```

---

## PARTE 4 — PÁGINAS

### `pages/02_analisar.py` — Página principal de análise

```python
"""
Página: Analisar Ativo
Interface visual para o /analisar — dispara o pipeline completo.
"""
import streamlit as st
import subprocess
import sys
from pathlib import Path
from components.pixel_art import exibir_agente_card, AGENTES

st.title("🔍 Analisar Ativo")
st.caption("Pipeline completo: 8 agentes em sequência")

# Input do ticker
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    ticker = st.text_input("Ticker", placeholder="Ex: PETR4, VALE3, MXRF11",
                           max_chars=10).upper().strip()
with col2:
    versao = st.selectbox("Relatório", ["Curto (1 pág.)", "Longo (2 pág.)"])
with col3:
    st.write("")
    st.write("")
    rodar = st.button("▶ Iniciar Análise", type="primary",
                      use_container_width=True, disabled=not ticker)

if rodar and ticker:
    versao_flag = "curta" if "Curto" in versao else "longa"

    st.divider()
    st.subheader(f"Pipeline SBWAA — {ticker}")

    # Exibir progresso visual por agente
    agentes_pipeline = [
        ("market-researcher",    "Market Snapshot + Researcher"),
        ("earnings-reviewer",    "Earnings Reviewer"),
        ("model-builder",        "Model Builder (DCF)"),
        ("valuation-reviewer",   "Valuation Reviewer"),
        ("quant-data-engineer",  "Quant / Data Engineer"),
        ("risk-engineer",        "Risk Engineer"),
        ("portfolio-manager",    "Portfolio Manager"),
    ]

    status_containers = {}
    cols_agentes = st.columns(len(agentes_pipeline))

    for i, (agente_id, nome) in enumerate(agentes_pipeline):
        with cols_agentes[i]:
            config = AGENTES.get(agente_id, {})
            st.markdown(
                f"<div style='text-align:center'>"
                f"<div style='font-size:28px'>{config.get('emoji','')}</div>"
                f"<div style='font-size:10px'>{config.get('nome','')}</div>"
                f"<div id='status-{agente_id}'>⏳</div></div>",
                unsafe_allow_html=True
            )

    st.divider()

    # Output do pipeline em tempo real
    output_area = st.empty()
    output_text = ""

    sbwaa_path = Path(__file__).parent.parent.parent / "sbwaa.py"
    cmd = [sys.executable, str(sbwaa_path),
           "/analisar", ticker, "--versao", versao_flag]

    with st.spinner(f"Analisando {ticker}..."):
        processo = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for linha in processo.stdout:
            output_text += linha
            output_area.code(output_text, language="text")

        processo.wait()

    if processo.returncode == 0:
        st.success(f"✅ Análise de {ticker} concluída!")
        st.info("Abra o vault do Obsidian para ver os relatórios gerados "
                f"em vault/01-ativos/{ticker}/")
    else:
        st.error("❌ Erro durante a análise. Verifique o output acima.")
```

### `pages/04_risco.py` — Página de risco

```python
"""
Página: Risco da Carteira
Métricas HF, correlações, stress tests e circuit breakers.
"""
import streamlit as st
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from components.metricas_hf import (exibir_metricas_hf,
                                     grafico_correlacao,
                                     grafico_alocacao)
from components.pixel_art import exibir_agente_card

st.title("🛡️ Risco da Carteira")

# Exibir agente responsável
with st.expander("Agente responsável", expanded=False):
    exibir_agente_card("risk-engineer")

BASE_DIR = Path(__file__).parent.parent.parent
CACHE_DIR = BASE_DIR / "scripts" / "data" / "cache"
hoje = datetime.now().strftime("%Y-%m-%d")

# Carregar dados ou oferecer para rodar
risk_cache = CACHE_DIR / f"risk_{hoje}.json"
quant_cache = CACHE_DIR / f"quant_{hoje}.json"

if not risk_cache.exists() or not quant_cache.exists():
    st.warning("⚠️ Dados de risco não encontrados para hoje.")
    if st.button("🔄 Calcular agora", type="primary"):
        sbwaa = BASE_DIR / "sbwaa.py"
        subprocess.run([sys.executable, str(sbwaa), "/risco-carteira"])
        st.rerun()
    st.stop()

with open(risk_cache) as f:
    risk_data = json.load(f)
with open(quant_cache) as f:
    quant_data = json.load(f)

# Métricas HF
exibir_metricas_hf(risk_data, quant_data)

st.divider()

# Gráficos lado a lado
col_corr, col_aloc = st.columns(2)
with col_corr:
    grafico_correlacao(quant_data.get("matriz_correlacao", {}))
with col_aloc:
    grafico_alocacao(quant_data.get("ativos", {}))

st.divider()

# Stress Tests
st.subheader("🔥 Stress Tests")
stress = risk_data.get("stress_tests", {})
if stress:
    for cenario, dados in stress.items():
        col_nome, col_pct, col_rs = st.columns([3, 1, 1])
        with col_nome:
            st.write(dados.get("cenario", cenario))
        with col_pct:
            st.metric("Impacto %",
                      f"{dados.get('impacto_pct', 0):.1f}%")
        with col_rs:
            st.metric("Impacto (R$100k norm.)",
                      f"R$ {dados.get('impacto_reais_normalizado', 0):,.0f}")
else:
    st.info("Stress tests não disponíveis. Execute /risco-carteira.")
```

### Páginas adicionais — estrutura mínima

Para cada página restante, criar estrutura básica funcional:

**`pages/01_carteira.py`** — Tabela da carteira com cotações atualizadas,
gráfico de alocação, P&L por ativo, botão "Atualizar cotações" que roda
`update_carteira.py`.

**`pages/03_morning_call.py`** — Exibe o último morning-call do vault,
botão "Gerar agora" que roda `/morning-call`, tabela macro formatada.

**`pages/05_relatorios.py`** — Lista todos os relatórios gerados no vault
(diários, semanais, mensais) com links para abrir o markdown. Botões
para gerar `/relatorio-semanal` e `/relatorio-mensal`.

**`pages/06_knowledge.py`** — Status da base de conhecimento (total de
docs, chunks por tipo), campo de busca semântica manual, botão para
indexar novo documento, botão para coletar RSS.

**`pages/07_agentes.py`** — Grid com todos os 7 agentes, seus bonecos
pixel art, descrição de função e status da última execução (lê logs).

---

## PARTE 5 — CSS CUSTOMIZADO

Crie `/sbwaa/interface/style/sbwaa.css`:

```css
/* SBWAA — Interface Visual */

/* Fundo escuro sutil */
[data-testid="stAppViewContainer"] {
    background-color: #0f0f0f;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #1a1a1a;
    border-right: 1px solid #2a2a2a;
}

/* Cards de métricas */
[data-testid="metric-container"] {
    background-color: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 12px;
}

/* Títulos */
h1, h2, h3 {
    color: #f5f5f5;
}

/* Botão primário */
[data-testid="stButton"] button[kind="primary"] {
    background-color: #B7791F;
    border: none;
    color: white;
    font-weight: 600;
}

[data-testid="stButton"] button[kind="primary"]:hover {
    background-color: #92400E;
}

/* Divider */
hr {
    border-color: #2a2a2a;
}

/* Code blocks */
[data-testid="stCode"] {
    background-color: #111;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    font-size: 12px;
}

/* Caption/subtextos */
[data-testid="stCaptionContainer"] {
    color: #888;
}

/* Alertas */
[data-testid="stAlert"] {
    border-radius: 6px;
}
```

---

## PARTE 6 — SIDEBAR

Crie `components/sidebar.py` e chame em todas as páginas:

```python
"""Sidebar com navegação, status e versão."""
import streamlit as st
from pathlib import Path

def exibir_sidebar():
    with st.sidebar:
        st.markdown("### 🧠 SBWAA")
        st.caption("Second Brain Financeiro")
        st.divider()

        # Versão global
        version_file = Path(__file__).parent.parent.parent / "VERSION.md"
        if version_file.exists():
            with open(version_file) as f:
                linhas = f.readlines()
                for linha in linhas:
                    if "Global" in linha or "v2." in linha:
                        st.caption(linha.strip())
                        break

        st.divider()

        # Navegação
        st.markdown("**Navegação**")
        st.page_link("app.py", label="🏠 Dashboard")
        st.page_link("pages/01_carteira.py", label="💼 Carteira")
        st.page_link("pages/02_analisar.py", label="🔍 Analisar")
        st.page_link("pages/03_morning_call.py", label="☀️ Morning Call")
        st.page_link("pages/04_risco.py", label="🛡️ Risco")
        st.page_link("pages/05_relatorios.py", label="📋 Relatórios")
        st.page_link("pages/06_knowledge.py", label="📚 Knowledge Base")
        st.page_link("pages/07_agentes.py", label="👥 Agentes")

        st.divider()
        st.caption("Dados: 100% locais\nPrivacidade preservada")
```

---

## PARTE 7 — INSERÇÃO DE PIXEL ART NOS DOCX

Atualizar o `run_valuation_reviewer.py` (Fase 3) para inserir a
imagem do agente nos relatórios DOCX gerados:

```python
from docx import Document
from docx.shared import Inches, Pt
from pathlib import Path

def inserir_pixel_art_docx(doc: Document, agente_id: str):
    """
    Insere o boneco pixel art do agente no cabeçalho do DOCX.
    Se o arquivo não existir, pula silenciosamente.
    """
    assets_dir = Path(__file__).parent.parent.parent.parent / \
                 "vault" / "assets" / "agents-pixel"
    img_path = assets_dir / f"{agente_id}.png"

    if not img_path.exists():
        return  # sem pixel art disponível ainda — não quebra

    # Inserir no cabeçalho
    section = doc.sections[0]
    header = section.header
    para = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    run = para.add_run()
    run.add_picture(str(img_path), width=Inches(0.5))
```

Chamar `inserir_pixel_art_docx(doc, "valuation-reviewer")` antes de
salvar qualquer DOCX gerado pelo sistema.

---

## PARTE 8 — ARQUIVO DE BONECOS PIXEL ART

Criar guia de especificações para os bonecos:

**Criar `/sbwaa/vault/assets/agents-pixel/README.md`:**

```markdown
# SBWAA — Pixel Art dos Agentes

Especificações para os bonecos de cada agente:

## Dimensões e formato
- Tamanho: 64×64 pixels (padrão) ou 32×32 (mini)
- Formato: PNG com fundo transparente
- Estilo: pixel art, 16 cores ou menos

## Arquivos esperados (um por agente)
- market-researcher.png
- earnings-reviewer.png
- model-builder.png
- valuation-reviewer.png
- quant-data-engineer.png
- risk-engineer.png
- portfolio-manager.png

## Sugestões visuais por agente

| Agente | Sugestão visual |
|--------|----------------|
| Market Researcher | Jornalista com jornal/tablet, cor marrom |
| Earnings Reviewer | Contador com documentos, cor azul |
| Model Builder | Engenheiro com calculadora/planta, cor verde |
| Valuation Reviewer | Detetive com lupa, cor índigo |
| Quant / Data Engineer | Cientista com gráficos, cor âmbar |
| Risk Engineer | Soldado/guarda com escudo, cor vermelha |
| Portfolio Manager | Executivo sênior com pasta, cor dourada |

## Como adicionar
Salvar o PNG do boneco com o nome exato acima nesta pasta.
O sistema detecta automaticamente ao iniciar a interface.
```

---

## PARTE 9 — VALIDAÇÃO FINAL

- [ ] `interface/app.py` criado — dashboard principal funcional
- [ ] Todas as 7 páginas criadas (mínimo funcional)
- [ ] `components/pixel_art.py` criado — exibe emoji se PNG ausente
- [ ] `components/metricas_hf.py` criado — métricas + gráficos Plotly
- [ ] `components/alerts_bar.py` criado — alertas no topo
- [ ] `components/sidebar.py` criado — navegação lateral
- [ ] `style/sbwaa.css` criado — tema escuro aplicado
- [ ] Comando `/ui` adicionado ao `sbwaa.py`
- [ ] Interface inicia com `python sbwaa.py /ui` sem erros
- [ ] Dashboard exibe cards de Sharpe, VaR, volatilidade, drawdown
- [ ] Página `/analisar` dispara o pipeline e exibe output em tempo real
- [ ] Página `/risco` exibe métricas HF + heatmap + stress tests
- [ ] `inserir_pixel_art_docx()` integrado nos DOCXs da Fase 3
- [ ] `README.md` de pixel art criado em `assets/agents-pixel/`
- [ ] `VERSION.md` atualizado: global → **v2.0.0**, `interface` → v1.0.0
- [ ] `CHANGELOG.md` com entrada da Fase 8 e marco v2.0.0
- [ ] `README.md` principal atualizado: todas as fases ✅ Completo

Ao finalizar, confirme: **"SBWAA v2.0.0 — Sistema completo operacional"**

---

## OBSERVAÇÕES IMPORTANTES

1. Esta é uma versão **beta** — funcionalidade sobre estética.
   Se algo visual não ficar perfeito, priorizar que funcione.

2. O Streamlit atualiza automaticamente ao salvar arquivos Python
   — desenvolvimento iterativo é fácil.

3. Pixel art: se o usuário ainda não criou os bonecos, o sistema
   funciona normalmente com os emojis como fallback. Os PNGs podem
   ser adicionados a qualquer momento em `vault/assets/agents-pixel/`
   e a interface detecta automaticamente.

4. O `subprocess.Popen` na página `/analisar` roda o pipeline real
   e captura o output em tempo real. Em alguns sistemas, o buffer
   pode atrasar a exibição — se isso ocorrer, adicionar `flush=True`
   nos prints do pipeline.

5. Streamlit não é thread-safe por padrão — não rodar múltiplas
   análises simultâneas. Um `/analisar` por vez.

6. O sistema completo está em **v2.0.0**. A partir daqui, qualquer
   melhoria segue o versionamento semântico normalmente:
   - Nova feature → v2.1.0
   - Bug fix → v2.0.1
   - Refatoração grande → v3.0.0
```
