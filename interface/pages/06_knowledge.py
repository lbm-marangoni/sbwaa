"""
Página: Knowledge Base
Status da base de conhecimento, busca semântica e indexação.
"""
import json
import subprocess
import sys
from pathlib import Path

import streamlit as st

_INTERFACE_DIR = Path(__file__).parent.parent
if str(_INTERFACE_DIR) not in sys.path:
    sys.path.insert(0, str(_INTERFACE_DIR))

BASE_DIR = _INTERFACE_DIR.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from components.alerts_bar import exibir_alertas
from components.sidebar import exibir_sidebar

INDEX_LOG_PATH = BASE_DIR / "knowledge" / "indexed" / "index_log.json"

exibir_alertas()
exibir_sidebar()

st.title("📚 Knowledge Base")
st.caption("Base de conhecimento RAG — ChromaDB local | embeddings multilingual")

# Status
st.subheader("📊 Status")

log: dict = {"documentos": []}
if INDEX_LOG_PATH.exists():
    with open(INDEX_LOG_PATH, encoding="utf-8") as f:
        log = json.load(f)

docs = log.get("documentos", [])
total_chunks = sum(d.get("chunks", 0) for d in docs)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total de documentos", len(docs))
with col2:
    st.metric("Total de chunks", f"{total_chunks:,}")
with col3:
    ultima = max((d.get("indexado_em", "") for d in docs), default="—")
    st.metric("Última atualização", ultima[:10] if ultima != "—" else "—")

# Por tipo
if docs:
    por_tipo: dict[str, int] = {}
    for d in docs:
        t = d.get("tipo", "outro")
        por_tipo[t] = por_tipo.get(t, 0) + 1
    labels = {"livro": "📚 Livros", "research": "📊 Research",
               "gestora": "📝 Gestoras", "macro": "🌍 Macro/RSS", "outro": "📁 Outros"}
    cols = st.columns(len(por_tipo))
    for i, (tipo, qtd) in enumerate(por_tipo.items()):
        with cols[i]:
            st.metric(labels.get(tipo, tipo), qtd)

st.divider()

# Ações
tab_buscar, tab_adicionar, tab_rss, tab_listar = st.tabs(
    ["🔍 Buscar", "➕ Adicionar", "📡 Coletar RSS", "📋 Listar"]
)

with tab_buscar:
    query = st.text_input("Busca semântica", placeholder='Ex: "valuation petróleo Brasil WACC"')
    n_resultados = st.slider("Número de resultados", 1, 10, 5)
    if st.button("🔍 Buscar", type="primary", disabled=not query):
        try:
            from knowledge.retriever import buscar, base_disponivel
            if not base_disponivel():
                st.warning("Base de conhecimento vazia. Indexe documentos primeiro.")
            else:
                with st.spinner("Buscando..."):
                    resultados = buscar(query, n_resultados=n_resultados)
                if not resultados:
                    st.info("Nenhum resultado encontrado.")
                else:
                    for i, r in enumerate(resultados, 1):
                        with st.expander(
                            f"[{i}] {r['fonte']} — {r['tipo']} (relevância: {r['score']:.0%})"
                        ):
                            st.write(r["texto"][:500])
        except ImportError:
            st.error("Instale: `pip install chromadb sentence-transformers`")

with tab_adicionar:
    st.info(
        "Coloque documentos em `knowledge/raw/` e use o caminho abaixo para indexar.\n\n"
        "Formatos suportados: PDF, DOCX, TXT, MD"
    )
    caminho = st.text_input(
        "Caminho do arquivo ou pasta",
        placeholder="knowledge/raw/books/security_analysis.pdf",
    )
    if st.button("📥 Indexar", type="primary", disabled=not caminho):
        with st.spinner("Indexando (pode demorar na primeira vez ~400MB download)..."):
            r = subprocess.run(
                [sys.executable, str(BASE_DIR / "sbwaa.py"),
                 "/knowledge", "--adicionar", caminho],
                capture_output=True, text=True, cwd=str(BASE_DIR),
            )
        if r.returncode == 0:
            st.success("Indexação concluída!")
            st.code(r.stdout[-2000:], language="text")
            st.rerun()
        else:
            st.error(f"Erro:\n{r.stderr[:400]}")

with tab_rss:
    st.info(
        "Coleta artigos dos feeds RSS configurados em `knowledge/sources/sources.json`.\n"
        "Fontes: Valor Econômico, InfoMoney, BCB, Bloomberg, Reuters"
    )
    if st.button("📡 Coletar agora", type="primary"):
        with st.spinner("Coletando RSS..."):
            r = subprocess.run(
                [sys.executable, str(BASE_DIR / "sbwaa.py"),
                 "/knowledge", "--coletar-rss"],
                capture_output=True, text=True, cwd=str(BASE_DIR),
            )
        if r.returncode == 0:
            st.success("Coleta concluída!")
            st.code(r.stdout[-1000:], language="text")
            st.rerun()
        else:
            st.error(f"Erro:\n{r.stderr[:400]}")

with tab_listar:
    if not docs:
        st.info("Nenhum documento indexado ainda.")
    else:
        import pandas as pd
        df = pd.DataFrame([
            {
                "Nome": d.get("nome", "—")[:40],
                "Tipo": d.get("tipo", "—"),
                "Chunks": d.get("chunks", 0),
                "Idioma": d.get("idioma", "—"),
                "Indexado em": d.get("indexado_em", "—"),
            }
            for d in docs
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
