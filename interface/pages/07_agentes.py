"""
Página: Agentes
Grid com todos os 7 agentes, pixel art, função e status da última execução.
"""
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

_INTERFACE_DIR = Path(__file__).parent.parent
if str(_INTERFACE_DIR) not in sys.path:
    sys.path.insert(0, str(_INTERFACE_DIR))

from components.alerts_bar import exibir_alertas
from components.sidebar import exibir_sidebar
from components.pixel_art import AGENTES, ASSETS_DIR

BASE_DIR = _INTERFACE_DIR.parent
VAULT_DIR = BASE_DIR / "vault"
LOGS_DIR = BASE_DIR / "logs"

exibir_alertas()
exibir_sidebar()

st.title("👥 Equipe SBWAA")
st.caption("7 agentes especializados em análise financeira")


def ultima_execucao(agente_id: str) -> str:
    """Tenta inferir a última execução do agente a partir do vault."""
    hoje = datetime.now().strftime("%Y-%m-%d")
    mapeamento = {
        "market-researcher": VAULT_DIR / "03-macro" / f"market-researcher-{hoje}.md",
        "earnings-reviewer": None,
        "model-builder": None,
        "valuation-reviewer": None,
        "quant-data-engineer": BASE_DIR / "scripts" / "data" / "cache" / f"quant_{hoje}.json",
        "risk-engineer": BASE_DIR / "scripts" / "data" / "cache" / f"risk_{hoje}.json",
        "portfolio-manager": VAULT_DIR / "00-portfolio" / "decisoes.md",
    }
    path = mapeamento.get(agente_id)
    if path and path.exists():
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        return f"Hoje {mtime.strftime('%H:%M')}"
    return "—"


st.divider()

agentes_ids = list(AGENTES.keys())
modelos = {
    "market-researcher":   "claude-sonnet-4-6",
    "earnings-reviewer":   "claude-sonnet-4-6",
    "model-builder":       "claude-opus-4-6",
    "valuation-reviewer":  "claude-sonnet-4-6",
    "quant-data-engineer": "claude-sonnet-4-6",
    "risk-engineer":       "claude-opus-4-6",
    "portfolio-manager":   "claude-opus-4-6",
}
comandos = {
    "market-researcher":   "run_market_researcher.py",
    "earnings-reviewer":   "/earnings TICKER",
    "model-builder":       "run_model_builder.py TICKER",
    "valuation-reviewer":  "run_valuation_reviewer.py TICKER",
    "quant-data-engineer": "/risco-carteira",
    "risk-engineer":       "/risco-carteira",
    "portfolio-manager":   "/pm TICKER",
}

for agente_id in agentes_ids:
    config = AGENTES[agente_id]
    img_path = ASSETS_DIR / config["arquivo"]
    ult_exec = ultima_execucao(agente_id)

    with st.container():
        c_img, c_nome, c_modelo, c_cmd, c_status = st.columns([1, 2, 2, 2, 1])

        with c_img:
            if img_path.exists():
                st.image(str(img_path), width=48)
            else:
                st.markdown(
                    f"<div style='font-size:36px;text-align:center'>"
                    f"{config['emoji']}</div>",
                    unsafe_allow_html=True,
                )

        with c_nome:
            st.markdown(
                f"<span style='color:{config['cor']};font-weight:600'>"
                f"{config['nome']}</span>",
                unsafe_allow_html=True,
            )
            st.caption(config["descricao"])

        with c_modelo:
            st.caption("Modelo")
            st.write(modelos.get(agente_id, "—"))

        with c_cmd:
            st.caption("Comando")
            st.code(comandos.get(agente_id, "—"), language="bash")

        with c_status:
            st.caption("Última exec.")
            cor = "#4ade80" if ult_exec != "—" else "#888"
            st.markdown(
                f"<span style='color:{cor};font-size:12px'>{ult_exec}</span>",
                unsafe_allow_html=True,
            )

        st.divider()

# Info sobre pixel art
st.subheader("🎨 Pixel Art")
pixel_readme = ASSETS_DIR / "README.md"
if pixel_readme.exists():
    with st.expander("Ver especificações dos bonecos"):
        st.markdown(pixel_readme.read_text(encoding="utf-8"))
else:
    st.info(
        "Adicione os bonecos PNG em `vault/assets/agents-pixel/` "
        "— o sistema detecta automaticamente. "
        "Formato: 64×64px PNG com fundo transparente."
    )
    faltando = [c["arquivo"] for c in AGENTES.values()
                if not (ASSETS_DIR / c["arquivo"]).exists()]
    if faltando:
        st.caption("Arquivos esperados: " + ", ".join(faltando))
