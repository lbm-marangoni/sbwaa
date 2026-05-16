"""
Componente de exibição dos bonecos pixel art dos agentes.
Se o arquivo PNG não existir, exibe placeholder com emoji.
"""
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
ASSETS_DIR = BASE_DIR / "vault" / "assets" / "agents-pixel"

AGENTES = {
    "market-researcher": {
        "nome": "Market Researcher",
        "descricao": "Macro & Notícias",
        "emoji": "📰",
        "arquivo": "market-researcher.png",
        "cor": "#78350F",
    },
    "earnings-reviewer": {
        "nome": "Earnings Reviewer",
        "descricao": "Resultados Trimestrais",
        "emoji": "📋",
        "arquivo": "earnings-reviewer.png",
        "cor": "#1E40AF",
    },
    "model-builder": {
        "nome": "Model Builder",
        "descricao": "DCF & Valuation",
        "emoji": "🏗️",
        "arquivo": "model-builder.png",
        "cor": "#065F46",
    },
    "valuation-reviewer": {
        "nome": "Valuation Reviewer",
        "descricao": "Revisão & Comps",
        "emoji": "🔍",
        "arquivo": "valuation-reviewer.png",
        "cor": "#4338CA",
    },
    "quant-data-engineer": {
        "nome": "Quant / Data Engineer",
        "descricao": "Sharpe, Beta, Correlação",
        "emoji": "📐",
        "arquivo": "quant-data-engineer.png",
        "cor": "#B45309",
    },
    "risk-engineer": {
        "nome": "Risk Engineer",
        "descricao": "VaR, CVaR, Stress Test",
        "emoji": "🛡️",
        "arquivo": "risk-engineer.png",
        "cor": "#991B1B",
    },
    "portfolio-manager": {
        "nome": "Portfolio Manager",
        "descricao": "Decisão Final",
        "emoji": "🎯",
        "arquivo": "portfolio-manager.png",
        "cor": "#B7791F",
    },
}


def exibir_agente_card(agente_id: str, mostrar_descricao: bool = True):
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
                unsafe_allow_html=True,
            )

    with col_info:
        st.markdown(f"**{config['nome']}**", help=config["descricao"])
        if mostrar_descricao:
            st.caption(config["descricao"])


def exibir_equipe_resumo():
    agentes_ids = list(AGENTES.keys())
    cols = st.columns(4)
    for i, col in enumerate(cols):
        if i < len(agentes_ids):
            with col:
                exibir_agente_mini(agentes_ids[i])
    _, c1, c2, c3, _ = st.columns([0.5, 1, 1, 1, 0.5])
    for i, col in enumerate([c1, c2, c3]):
        idx = i + 4
        if idx < len(agentes_ids):
            with col:
                exibir_agente_mini(agentes_ids[idx])


def exibir_agente_mini(agente_id: str):
    config = AGENTES.get(agente_id, {})
    st.markdown(
        f"<div style='text-align:center;padding:8px;"
        f"border-radius:8px;border:1px solid {config.get('cor','#333')}'>"
        f"<div style='font-size:32px'>{config.get('emoji','')}</div>"
        f"<div style='font-size:11px;margin-top:4px'>"
        f"{config.get('nome','')}</div></div>",
        unsafe_allow_html=True,
    )
