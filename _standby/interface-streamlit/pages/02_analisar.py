"""
Página: Analisar Ativo
Interface visual para o /analisar — dispara o pipeline completo.
"""
import subprocess
import sys
from pathlib import Path

import streamlit as st

_INTERFACE_DIR = Path(__file__).parent.parent
if str(_INTERFACE_DIR) not in sys.path:
    sys.path.insert(0, str(_INTERFACE_DIR))

from components.alerts_bar import exibir_alertas
from components.sidebar import exibir_sidebar
from components.pixel_art import AGENTES, exibir_agente_card

BASE_DIR = _INTERFACE_DIR.parent

exibir_alertas()
exibir_sidebar()

st.title("🔍 Analisar Ativo")
st.caption("Pipeline completo: 8 agentes em sequência")

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    ticker = st.text_input(
        "Ticker", placeholder="Ex: PETR4, VALE3, MXRF11", max_chars=10
    ).upper().strip()
with col2:
    versao = st.selectbox("Relatório", ["Curto (1 pág.)", "Longo (2 pág.)"])
with col3:
    st.write("")
    st.write("")
    rodar = st.button(
        "▶ Iniciar Análise",
        type="primary",
        use_container_width=True,
        disabled=not ticker,
    )

if rodar and ticker:
    versao_flag = "curta" if "Curto" in versao else "longa"

    st.divider()
    st.subheader(f"Pipeline SBWAA — {ticker}")

    agentes_pipeline = [
        ("market-researcher",   "Market Snapshot + Researcher"),
        ("earnings-reviewer",   "Earnings Reviewer"),
        ("model-builder",       "Model Builder (DCF)"),
        ("valuation-reviewer",  "Valuation Reviewer"),
        ("quant-data-engineer", "Quant / Data Engineer"),
        ("risk-engineer",       "Risk Engineer"),
        ("portfolio-manager",   "Portfolio Manager"),
    ]

    cols_agentes = st.columns(len(agentes_pipeline))
    for i, (agente_id, _) in enumerate(agentes_pipeline):
        with cols_agentes[i]:
            config = AGENTES.get(agente_id, {})
            st.markdown(
                f"<div style='text-align:center'>"
                f"<div style='font-size:28px'>{config.get('emoji','')}</div>"
                f"<div style='font-size:10px'>{config.get('nome','')}</div>"
                f"<div>⏳</div></div>",
                unsafe_allow_html=True,
            )

    st.divider()

    output_area = st.empty()
    output_text = ""

    sbwaa_path = BASE_DIR / "sbwaa.py"
    cmd = [sys.executable, str(sbwaa_path), "/analisar", ticker, "--versao", versao_flag]

    with st.spinner(f"Analisando {ticker}..."):
        processo = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        for linha in processo.stdout:
            output_text += linha
            output_area.code(output_text, language="text")

        processo.wait()

    if processo.returncode == 0:
        st.success(f"✅ Análise de {ticker} concluída!")
        st.info(
            f"Abra o vault do Obsidian para ver os relatórios gerados "
            f"em vault/01-ativos/{ticker}/"
        )
    else:
        st.error("❌ Erro durante a análise. Verifique o output acima.")

elif not rodar:
    st.divider()
    st.subheader("👥 Agentes do Pipeline")
    agentes_pipeline = [
        ("market-researcher",   "1. Snapshot + análise macro do dia"),
        ("earnings-reviewer",   "2. Revisão de resultados trimestrais"),
        ("model-builder",       "3. Modelo DCF com projeções 5 anos"),
        ("valuation-reviewer",  "4. Equity research e comps"),
        ("quant-data-engineer", "5. Métricas quantitativas da carteira"),
        ("risk-engineer",       "6. VaR, CVaR, circuit breakers"),
        ("portfolio-manager",   "7. Veredicto: COMPRAR / AGUARDAR / EVITAR"),
    ]
    for agente_id, descricao in agentes_pipeline:
        with st.container():
            c1, c2 = st.columns([1, 5])
            with c1:
                exibir_agente_card(agente_id, mostrar_descricao=False)
            with c2:
                st.write(descricao)
