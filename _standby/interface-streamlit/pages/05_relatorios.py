"""
Página: Relatórios
Lista relatórios gerados no vault. Botões para gerar semanal/mensal.
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

BASE_DIR = _INTERFACE_DIR.parent
VAULT_DIR = BASE_DIR / "vault"
DIARIOS_DIR = VAULT_DIR / "02-relatorios" / "diarios"
ATIVOS_DIR = VAULT_DIR / "01-ativos"

exibir_alertas()
exibir_sidebar()

st.title("📋 Relatórios")

# Ações de geração
col1, col2, _ = st.columns([1, 1, 2])
with col1:
    if st.button("📅 Relatório Semanal", type="primary"):
        with st.spinner("Gerando relatório semanal..."):
            r = subprocess.run(
                [sys.executable, str(BASE_DIR / "sbwaa.py"), "/relatorio-semanal"],
                capture_output=True, text=True,
            )
        if r.returncode == 0:
            st.success("Relatório semanal gerado!")
            st.rerun()
        else:
            st.error(f"Erro: {r.stderr[:400]}")
with col2:
    if st.button("📆 Relatório Mensal"):
        with st.spinner("Gerando relatório mensal..."):
            r = subprocess.run(
                [sys.executable, str(BASE_DIR / "sbwaa.py"), "/relatorio-mensal"],
                capture_output=True, text=True,
            )
        if r.returncode == 0:
            st.success("Relatório mensal gerado!")
            st.rerun()
        else:
            st.error(f"Erro: {r.stderr[:400]}")

st.divider()

# Tabs por tipo
tab_diarios, tab_ativos, tab_macro = st.tabs(["📆 Diários", "🏢 Por Ativo", "🌍 Macro"])

with tab_diarios:
    arquivos = sorted(DIARIOS_DIR.glob("*.md"), reverse=True)[:30] if DIARIOS_DIR.exists() else []
    if not arquivos:
        st.info("Nenhum relatório diário encontrado.")
    else:
        for arq in arquivos:
            with st.expander(f"📄 {arq.stem}"):
                conteudo = arq.read_text(encoding="utf-8")
                st.markdown(conteudo[:3000] + ("..." if len(conteudo) > 3000 else ""))

with tab_ativos:
    if not ATIVOS_DIR.exists():
        st.info("Nenhum ativo analisado ainda.")
    else:
        ativos = sorted([d for d in ATIVOS_DIR.iterdir() if d.is_dir()])
        if not ativos:
            st.info("Nenhum ativo analisado ainda.")
        else:
            ticker_sel = st.selectbox("Selecionar ativo", [d.name for d in ativos])
            if ticker_sel:
                ativo_dir = ATIVOS_DIR / ticker_sel
                relatorios = sorted(ativo_dir.glob("*.md"), reverse=True)
                for rel in relatorios:
                    with st.expander(f"📄 {rel.stem}"):
                        conteudo = rel.read_text(encoding="utf-8")
                        st.markdown(conteudo[:3000] + ("..." if len(conteudo) > 3000 else ""))

with tab_macro:
    macro_dir = VAULT_DIR / "03-macro"
    arquivos_macro = sorted(macro_dir.glob("*.md"), reverse=True)[:20] if macro_dir.exists() else []
    if not arquivos_macro:
        st.info("Nenhum relatório macro encontrado.")
    else:
        for arq in arquivos_macro:
            with st.expander(f"📄 {arq.stem}"):
                conteudo = arq.read_text(encoding="utf-8")
                st.markdown(conteudo[:3000] + ("..." if len(conteudo) > 3000 else ""))
