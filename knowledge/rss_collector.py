"""
SBWAA — RSS Collector
Coleta artigos de fontes confiáveis via RSS e indexa no ChromaDB.
Chamado pelo heartbeat diariamente.
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
SOURCES_PATH = KNOWLEDGE_DIR / "sources" / "sources.json"
INDEX_LOG_PATH = KNOWLEDGE_DIR / "indexed" / "index_log.json"

sys.path.insert(0, str(PROJECT_ROOT))


def carregar_log() -> dict:
    if INDEX_LOG_PATH.exists():
        return json.loads(INDEX_LOG_PATH.read_text(encoding="utf-8"))
    return {"documentos": []}


def url_ja_indexada(log: dict, url: str) -> bool:
    return any(d.get("url") == url for d in log.get("documentos", []))


def extrair_texto_artigo(url: str) -> str:
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {"User-Agent": "Mozilla/5.0 SBWAA/1.0 RSS Collector"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return ""
        soup = BeautifulSoup(resp.text, "html.parser")
        # Remove scripts, styles e navegação
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()
        paragrafos = soup.find_all("p")
        texto = "\n".join(p.get_text(strip=True) for p in paragrafos if p.get_text(strip=True))
        return texto[:8000]  # limite de 8k chars por artigo
    except Exception:
        return ""


def indexar_texto_rss(titulo: str, texto: str, url: str, fonte: str,
                       tipo: str, idioma: str, collection, modelo, log: dict):
    """Indexa um artigo RSS diretamente sem passar pelo indexer de arquivo."""
    from knowledge.indexer import chunk_texto, salvar_log

    if not texto.strip():
        return

    chunks = chunk_texto(f"{titulo}\n\n{texto}")
    if not chunks:
        return

    embeddings = modelo.encode(chunks, show_progress_bar=False).tolist()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    nome_base = url.split("/")[-1][:50] or "rss_artigo"
    ids = [f"rss__{nome_base}__chunk_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "fonte": fonte,
            "tipo": tipo,
            "autor": "desconhecido",
            "ano": str(datetime.now().year),
            "idioma": idioma,
            "chunk_id": i,
            "total_chunks": len(chunks),
            "url": url,
        }
        for i in range(len(chunks))
    ]

    try:
        collection.add(
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )
    except Exception as e:
        # IDs duplicados são ignorados silenciosamente
        if "already exists" not in str(e).lower():
            print(f"  ⚠️  Erro ao indexar chunks RSS: {e}")
        return

    log["documentos"].append({
        "arquivo": url,
        "nome": titulo[:80],
        "tipo": tipo,
        "md5": "",
        "url": url,
        "chunks": len(chunks),
        "idioma": idioma,
        "indexado_em": now,
    })
    salvar_log(log)


def coletar_feed(feed_config: dict, max_artigos: int, max_idade_dias: int,
                  collection, modelo, log: dict) -> int:
    import feedparser

    nome = feed_config["nome"]
    url_feed = feed_config["url"]
    tipo = feed_config.get("tipo", "macro")
    idioma = feed_config.get("idioma", "pt")

    print(f"  📡 Coletando: {nome}")
    try:
        feed = feedparser.parse(url_feed)
    except Exception as e:
        print(f"  ⚠️  Erro ao parsear feed {nome}: {e}")
        return 0

    limite_data = datetime.now(tz=timezone.utc) - timedelta(days=max_idade_dias)
    coletados = 0

    for entry in feed.entries[:max_artigos]:
        url = entry.get("link", "")
        titulo = entry.get("title", "Sem título")

        if not url:
            continue

        if url_ja_indexada(log, url):
            continue

        # Verificar data do artigo
        published = entry.get("published_parsed") or entry.get("updated_parsed")
        if published:
            import time
            pub_dt = datetime.fromtimestamp(time.mktime(published), tz=timezone.utc)
            if pub_dt < limite_data:
                continue

        texto = extrair_texto_artigo(url)
        if not texto:
            # Usar resumo do feed se disponível
            texto = entry.get("summary", "") or entry.get("description", "")

        if texto.strip():
            indexar_texto_rss(titulo, texto, url, nome, tipo, idioma,
                               collection, modelo, log)
            print(f"    ✅ {titulo[:60]}...")
            coletados += 1

    return coletados


def coletar_todos_feeds() -> int:
    """Coleta todos os feeds ativos. Retorna total de artigos indexados."""
    if not SOURCES_PATH.exists():
        print("sources.json não encontrado.")
        return 0

    config = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    feeds = [f for f in config.get("rss_feeds", []) if f.get("ativo", True)]
    max_artigos = config.get("coleta_max_artigos_por_feed", 5)
    max_idade = config.get("coleta_max_idade_dias", 3)

    if not feeds:
        print("Nenhum feed ativo configurado.")
        return 0

    print(f"Carregando modelo de embeddings...")
    from knowledge.indexer import get_collection, get_modelo
    collection = get_collection()
    modelo = get_modelo()
    log = carregar_log()

    total = 0
    for feed in feeds:
        total += coletar_feed(feed, max_artigos, max_idade, collection, modelo, log)

    print(f"\nRSS: {total} novos artigos indexados.")
    return total


if __name__ == "__main__":
    coletar_todos_feeds()
