"""
Página: Risco da Carteira
Métricas HF, correlações, stress tests e circuit breakers.
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

_INTERFACE_DIR = Path(__file__).parent.parent
if str(_INTERFACE_DIR) not in sys.path:
    sys.path.insert(0, str(_INTERFACE_DIR))

from components.alerts_bar import exibir_alertas
from components.sidebar import exibir_sidebar
from components.metricas_hf import exibir_metricas_hf, grafico_correlacao, grafico_alocacao
from components.pixel_art import exibir_agente_card

BASE_DIR = _INTERFACE_DIR.parent
CACHE_DIR = BASE_DIR / "scripts" / "data" / "cache"

exibir_alertas()
exibir_sidebar()

st.title("🛡️ Risco da Carteira")

with st.expander("Agente responsável", expanded=False):
    exibir_agente_card("risk-engineer")

hoje = datetime.now().strftime("%Y-%m-%d")
risk_cache = CACHE_DIR / f"risk_{hoje}.json"
quant_cache = CACHE_DIR / f"quant_{hoje}.json"

if not risk_cache.exists() or not quant_cache.exists():
    st.warning("⚠️ Dados de risco não encontrados para hoje.")
    if st.button("🔄 Calcular agora", type="primary"):
        with st.spinner("Calculando métricas de risco..."):
            subprocess.run(
                [sys.executable, str(BASE_DIR / "sbwaa.py"), "/risco-carteira"],
                capture_output=True, text=True,
            )
        st.rerun()
    st.stop()

with open(risk_cache, encoding="utf-8") as f:
    risk_data = json.load(f)
with open(quant_cache, encoding="utf-8") as f:
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
            st.metric("Impacto %", f"{dados.get('impacto_pct', 0):.1f}%")
        with col_rs:
            st.metric(
                "Impacto (R$100k norm.)",
                f"R$ {dados.get('impacto_reais_normalizado', 0):,.0f}",
            )
else:
    st.info("Stress tests não disponíveis. Execute /risco-carteira.")

st.divider()

# Flags do PM
flags = risk_data.get("flags_pm", [])
if flags:
    st.subheader("🚩 Flags para o Portfolio Manager")
    for flag in flags:
        st.warning(flag)

# Circuit Breakers
st.subheader("⚡ Circuit Breakers")
cb = risk_data.get("circuit_breakers", {})
if cb:
    col1, col2, col3 = st.columns(3)
    with col1:
        ok = cb.get("var_ok", True)
        st.metric("VaR", "✅ OK" if ok else "🚨 VIOLADO")
    with col2:
        ok = cb.get("drawdown_ok", True)
        st.metric("Drawdown", "✅ OK" if ok else "🚨 VIOLADO")
    with col3:
        ok = cb.get("concentracao_ok", True)
        st.metric("Concentração", "✅ OK" if ok else "🚨 VIOLADO")
