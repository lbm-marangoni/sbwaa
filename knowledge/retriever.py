"""
SBWAA — Knowledge Retriever
Interface de busca semântica na base de conhecimento.
Chamado pelos agentes para enriquecer análises com contexto.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CHROMA_PATH = PROJECT_ROOT / "knowledge" / ".chromadb"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

_collection = None
_modelo = None


def _get_collection():
    global _collection
    if _collection is None:
        import chromadb
        client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        _collection = client.get_or_create_collection(
            name="sbwaa_knowledge",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _get_modelo():
    global _modelo
    if _modelo is None:
        from sentence_transformers import SentenceTransformer
        _modelo = SentenceTransformer(EMBEDDING_MODEL)
    return _modelo


def base_disponivel() -> bool:
    """Retorna True se a base de conhecimento existe e tem documentos."""
    try:
        col = _get_collection()
        return col.count() > 0
    except Exception:
        return False


def buscar(query: str, n_resultados: int = 5,
           filtro_tipo: str = None) -> list[dict]:
    """
    Busca semântica na base de conhecimento.

    Args:
        query: pergunta ou contexto para buscar
        n_resultados: número de chunks a retornar
        filtro_tipo: filtrar por tipo (livro, research, gestora, macro)

    Returns:
        Lista de dicts com: texto, fonte, tipo, score de relevância
    """
    try:
        collection = _get_collection()
        if collection.count() == 0:
            return []

        modelo = _get_modelo()
        query_embedding = modelo.encode([query]).tolist()

        where = {"tipo": filtro_tipo} if filtro_tipo else None

        resultados = collection.query(
            query_embeddings=query_embedding,
            n_results=min(n_resultados, collection.count()),
            where=where,
        )

        chunks = []
        for i, doc in enumerate(resultados["documents"][0]):
            chunks.append({
                "texto": doc,
                "fonte": resultados["metadatas"][0][i]["fonte"],
                "tipo": resultados["metadatas"][0][i]["tipo"],
                "score": 1 / (1 + resultados["distances"][0][i]),
            })

        return sorted(chunks, key=lambda x: x["score"], reverse=True)

    except Exception:
        return []


def formatar_contexto_para_agente(chunks: list[dict],
                                   max_tokens: int = 2000) -> str:
    """
    Formata os chunks recuperados em texto estruturado
    para inserir no prompt do agente.
    """
    if not chunks:
        return ""

    linhas = ["## Contexto da Base de Conhecimento\n"]
    tokens_usados = 0

    for chunk in chunks:
        bloco = (
            f"**Fonte:** {chunk['fonte']} "
            f"(relevância: {chunk['score']:.0%})\n"
            f"{chunk['texto']}\n"
            f"---\n"
        )
        tokens_estimados = len(bloco.split()) * 1.3
        if tokens_usados + tokens_estimados > max_tokens:
            break
        linhas.append(bloco)
        tokens_usados += tokens_estimados

    return "\n".join(linhas)
