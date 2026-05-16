"""
Página: Morning Call
Exibe o último morning call do vault e permite gerar novo.
"""
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

BASE_DIR = _INTERFACE_DIR.parent
VAULT_DIR = BASE_DIR / "vault"
DIARIOS_DIR = VAULT_DIR / "02-relatorios" / "diarios"

exibir_alertas()
exibir_sidebar()

st.title("☀️ Morning Call")

hoje = datetime.now().strftime("%Y-%m-%d")
mc_path = DIARIOS_DIR / f"morning-call-{hoje}.md"
mr_path = DIARIOS_DIR / f"market-researcher-{hoje}.md"

col_btn1, col_btn2, _ = st.columns([1, 1, 2])
with col_btn1:
    if st.button("🔄 Gerar Morning Call", type="primary"):
        with st.spinner("Gerando morning call (pode demorar ~1 min)..."):
            r = subprocess.run(
                [sys.executable, str(BASE_DIR / "sbwaa.py"), "/morning-call"],
                capture_output=True, text=True,
            )
        if r.returncode == 0:
            st.success("Morning call gerado!")
            st.rerun()
        else:
            st.error(f"Erro: {r.stderr[:400]}")

with col_btn2:
    if st.button("📰 Só Market Researcher"):
        with st.spinner("Rodando Market Researcher..."):
            r = subprocess.run(
                [sys.executable, str(BASE_DIR / "sbwaa.py"), "/mundo-economico"],
                capture_output=True, text=True,
            )
        if r.returncode == 0:
            st.success("Concluído!")
            st.rerun()

st.divider()

# Exibir morning call do dia
if mc_path.exists():
    st.subheader(f"Morning Call — {hoje}")
    conteudo = mc_path.read_text(encoding="utf-8")
    # Remover frontmatter
    linhas = conteudo.splitlines()
    inicio = 0
    if linhas and linhas[0].strip() == "---":
        for i, l in enumerate(linhas[1:], 1):
            if l.strip() == "---":
                inicio = i + 1
                break
    st.markdown("\n".join(linhas[inicio:]))
else:
    st.info(f"Nenhum morning call gerado para hoje ({hoje}). Clique em 'Gerar Morning Call'.")

# Exibir market researcher se existir
if mr_path.exists():
    st.divider()
    with st.expander("📰 Market Researcher — análise macro completa"):
        conteudo_mr = mr_path.read_text(encoding="utf-8")
        st.markdown(conteudo_mr)

# Listar calls anteriores
st.divider()
with st.expander("📅 Calls anteriores"):
    calls = sorted(DIARIOS_DIR.glob("morning-call-*.md"), reverse=True)[:10]
    if calls:
        for c in calls:
            data = c.stem.replace("morning-call-", "")
            if st.button(f"📄 {data}", key=f"mc_{data}"):
                st.text(c.read_text(encoding="utf-8"))
    else:
        st.info("Nenhum morning call anterior encontrado.")
