"""Sidebar com navegação, status e versão."""
import streamlit as st
from pathlib import Path


def exibir_sidebar():
    with st.sidebar:
        st.markdown("### 🧠 SBWAA")
        st.caption("Second Brain Financeiro")
        st.divider()

        version_file = Path(__file__).parent.parent.parent / "VERSION.md"
        if version_file.exists():
            with open(version_file, encoding="utf-8") as f:
                for linha in f.readlines():
                    if "Global" in linha or "v2." in linha or "v1." in linha:
                        st.caption(linha.strip().replace("**", "").replace("#", "").strip())
                        break

        st.divider()

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
