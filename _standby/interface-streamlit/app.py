"""
SBWAA — Interface Visual
Versão Beta | Roda localmente em localhost:8501

Iniciar: python sbwaa.py /ui
       ou: streamlit run interface/app.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

# Garantir que interface/ está no path para imports de components
_INTERFACE_DIR = Path(__file__).parent
if str(_INTERFACE_DIR) not in sys.path:
    sys.path.insert(0, str(_INTERFACE_DIR))

st.set_page_config(
    page_title="SBWAA",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


def carregar_css():
    css_path = _INTERFACE_DIR / "style" / "sbwaa.css"
    if css_path.exists():
        with open(css_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


carregar_css()

BASE_DIR = _INTERFACE_DIR.parent
VAULT_DIR = BASE_DIR / "vault"
CACHE_DIR = BASE_DIR / "scripts" / "data" / "cache"

from components.alerts_bar import exibir_alertas
from components.pixel_art import exibir_equipe_resumo
from components.sidebar import exibir_sidebar

exibir_alertas()
exibir_sidebar()

st.title("🧠 SBWAA")
st.caption(
    f"Second Brain Wealth + Asset + Assessor Individual | "
    f"{datetime.now().strftime('%d/%m/%Y %H:%M')}"
)

st.divider()

# Cards de resumo rápido
hoje = datetime.now().strftime("%Y-%m-%d")
risk_cache = CACHE_DIR / f"risk_{hoje}.json"
quant_cache = CACHE_DIR / f"quant_{hoje}.json"

risk_data: dict = {}
quant_data: dict = {}

if risk_cache.exists():
    with open(risk_cache, encoding="utf-8") as f:
        risk_data = json.load(f)

if quant_cache.exists():
    with open(quant_cache, encoding="utf-8") as f:
        quant_data = json.load(f)

col1, col2, col3, col4 = st.columns(4)

with col1:
    v = quant_data.get("carteira", {}).get("sharpe")
    st.metric("Sharpe (12m)", f"{v:.2f}" if isinstance(v, float) else "—")

with col2:
    v = quant_data.get("carteira", {}).get("volatilidade_pct")
    st.metric("Volatilidade Anual", f"{v:.1f}%" if isinstance(v, float) else "—")

with col3:
    v = risk_data.get("var_historico_95_pct")
    st.metric("VaR 95% (1 dia)", f"{v:.1%}" if isinstance(v, float) else "—")

with col4:
    v = risk_data.get("drawdown_atual_pct")
    st.metric("Drawdown Atual", f"{v:.1%}" if isinstance(v, float) else "—",
              delta_color="inverse")

st.divider()

# Ações rápidas
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

# Equipe SBWAA
st.subheader("👥 Equipe SBWAA")
exibir_equipe_resumo()

st.divider()

# Status do sistema
with st.expander("⚙️ Status do sistema"):
    version_path = BASE_DIR / "VERSION.md"
    if version_path.exists():
        st.markdown(version_path.read_text(encoding="utf-8"))
    if not risk_cache.exists() and not quant_cache.exists():
        st.info(
            "Dados de hoje ainda não calculados. "
            "Execute `/morning-call` ou `/risco-carteira` no terminal."
        )
