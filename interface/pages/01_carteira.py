"""
Página: Carteira
Tabela com cotações atualizadas, P&L por ativo e gráfico de alocação.
"""
import json
import subprocess
import sys
from pathlib import Path

import streamlit as st

_INTERFACE_DIR = Path(__file__).parent.parent
if str(_INTERFACE_DIR) not in sys.path:
    sys.path.insert(0, str(_INTERFACE_DIR))

from components.alerts_bar import exibir_alertas
from components.sidebar import exibir_sidebar
from components.metricas_hf import grafico_alocacao

BASE_DIR = _INTERFACE_DIR.parent
VAULT_DIR = BASE_DIR / "vault"
CARTEIRA_PATH = VAULT_DIR / "00-portfolio" / "carteira.md"
SCRIPTS_DATA = BASE_DIR / "scripts" / "data"
CACHE_DIR = SCRIPTS_DATA / "cache"

exibir_alertas()
exibir_sidebar()

st.title("💼 Carteira")

# Botão de atualizar cotações
col_btn, col_info = st.columns([1, 3])
with col_btn:
    if st.button("🔄 Atualizar cotações", type="primary"):
        with st.spinner("Atualizando..."):
            r = subprocess.run(
                [sys.executable, str(SCRIPTS_DATA / "update_carteira.py")],
                capture_output=True, text=True,
            )
        if r.returncode == 0:
            st.success("Cotações atualizadas!")
            st.rerun()
        else:
            st.error(f"Erro: {r.stderr[:300]}")

if not CARTEIRA_PATH.exists():
    st.warning("carteira.md não encontrado. Adicione ativos com `/adicionar`.")
    st.stop()

conteudo = CARTEIRA_PATH.read_text(encoding="utf-8")

# Extrair tabela de ativos
linhas = conteudo.splitlines()
dentro = False
cabecalho = []
linhas_dados = []

for linha in linhas:
    s = linha.strip()
    if s.startswith("| Ticker"):
        dentro = True
        cabecalho = [c.strip() for c in s.split("|")[1:-1]]
        continue
    if dentro and s.startswith("|---"):
        continue
    if dentro and s.startswith("|"):
        celulas = [c.strip() for c in s.split("|")[1:-1]]
        linhas_dados.append(celulas)
    elif dentro:
        break

if linhas_dados and cabecalho:
    import pandas as pd
    # Normalizar colunas — preencher se diferirem
    max_cols = max(len(cabecalho), max(len(r) for r in linhas_dados))
    while len(cabecalho) < max_cols:
        cabecalho.append(f"Col{len(cabecalho)}")
    linhas_norm = [r + [""] * (max_cols - len(r)) for r in linhas_dados]
    df = pd.DataFrame(linhas_norm, columns=cabecalho)

    st.subheader("📋 Posições")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Tentar gráfico de alocação a partir do cache quant
    from datetime import datetime
    hoje = datetime.now().strftime("%Y-%m-%d")
    quant_path = CACHE_DIR / f"quant_{hoje}.json"
    if quant_path.exists():
        with open(quant_path, encoding="utf-8") as f:
            quant_data = json.load(f)
        st.divider()
        grafico_alocacao(quant_data.get("ativos", {}))
    else:
        st.info("Execute `/risco-carteira` para ver o gráfico de alocação.")
else:
    st.info("Carteira vazia ou sem tabela reconhecível.")

st.divider()

# Exibir conteúdo bruto em expander
with st.expander("📄 Ver carteira.md completo"):
    st.markdown(conteudo)
