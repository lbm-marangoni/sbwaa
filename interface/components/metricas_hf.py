"""
Componente reutilizável: bloco de métricas HF da carteira.
Usado na página de risco, no dashboard e no output do PM.
"""
import streamlit as st
import plotly.graph_objects as go


def exibir_metricas_hf(risk_data: dict, quant_data: dict):
    carteira = quant_data.get("carteira", {})
    cb = risk_data.get("circuit_breakers", {})

    def status_icon(ok: bool) -> str:
        return "✅" if ok else "🚨"

    st.markdown("### 📊 Métricas HF da Carteira")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        v = carteira.get("sharpe")
        st.metric("Sharpe (12m)", f"{v:.2f}" if isinstance(v, float) else "—")
    with c2:
        v = carteira.get("volatilidade_pct")
        st.metric("Volatilidade Anual", f"{v:.1f}%" if isinstance(v, float) else "—")
    with c3:
        v = risk_data.get("var_historico_95_pct")
        icon = status_icon(cb.get("var_ok", True))
        st.metric(f"VaR 95% (1d) {icon}", f"{v:.1%}" if isinstance(v, float) else "—")
    with c4:
        v = risk_data.get("cvar_95_pct")
        st.metric("CVaR 95% (1d)", f"{v:.1%}" if isinstance(v, float) else "—")

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        v = risk_data.get("drawdown_atual_pct")
        icon = status_icon(cb.get("drawdown_ok", True))
        st.metric(f"Drawdown Atual {icon}", f"{v:.1%}" if isinstance(v, float) else "—")
    with c6:
        v = risk_data.get("drawdown_maximo_pct")
        st.metric("Max Drawdown Hist.", f"{v:.1%}" if isinstance(v, float) else "—")
    with c7:
        v = carteira.get("beta_ibov")
        st.metric("Beta vs IBOV", f"{v:.2f}" if isinstance(v, float) else "—")
    with c8:
        conc = risk_data.get("concentracao_maxima_pct")
        ticker_conc = risk_data.get("concentracao_maxima_ticker", "")
        icon = status_icon(cb.get("concentracao_ok", True))
        st.metric(
            f"Maior Conc. {icon}",
            f"{conc:.1f}% ({ticker_conc})" if isinstance(conc, float) else "—",
        )


def grafico_correlacao(matriz_corr: dict):
    if not matriz_corr:
        st.info("Matriz de correlação não disponível. Execute /risco-carteira primeiro.")
        return

    import pandas as pd

    df = pd.DataFrame(matriz_corr)
    fig = go.Figure(
        data=go.Heatmap(
            z=df.values,
            x=df.columns.tolist(),
            y=df.index.tolist(),
            colorscale="RdBu_r",
            zmid=0,
            zmin=-1,
            zmax=1,
            text=[[f"{v:.2f}" for v in row] for row in df.values],
            texttemplate="%{text}",
            showscale=True,
        )
    )
    fig.update_layout(
        title="Matriz de Correlação",
        height=400,
        margin=dict(l=40, r=40, t=40, b=40),
        paper_bgcolor="#1a1a1a",
        plot_bgcolor="#1a1a1a",
        font_color="#f5f5f5",
    )
    st.plotly_chart(fig, use_container_width=True)


def grafico_alocacao(ativos: dict):
    if not ativos:
        return
    labels = list(ativos.keys())
    values = [v.get("peso_carteira_pct", 0) for v in ativos.values()]
    fig = go.Figure(
        data=go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            textinfo="label+percent",
        )
    )
    fig.update_layout(
        title="Alocação da Carteira",
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="#1a1a1a",
        font_color="#f5f5f5",
    )
    st.plotly_chart(fig, use_container_width=True)
