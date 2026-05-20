"""
Barra de alertas exibida no topo de todas as páginas.
"""
import streamlit as st
from pathlib import Path
from datetime import datetime


def exibir_alertas():
    log_path = Path(__file__).parent.parent.parent / "logs" / "alerts.log"
    if not log_path.exists():
        return

    hoje = datetime.now().strftime("%Y-%m-%d")
    alertas_hoje = []

    with open(log_path, encoding="utf-8", errors="ignore") as f:
        for linha in f.readlines()[-50:]:
            if hoje in linha and ("CRÍTICO" in linha or "ALTO" in linha):
                alertas_hoje.append(linha.strip())

    if not alertas_hoje:
        return

    with st.container():
        for alerta in alertas_hoje[:3]:
            msg = alerta.split("|")[-1].strip() if "|" in alerta else alerta
            if "CRÍTICO" in alerta:
                st.error(f"🚨 {msg}")
            elif "ALTO" in alerta:
                st.warning(f"⚠️ {msg}")
