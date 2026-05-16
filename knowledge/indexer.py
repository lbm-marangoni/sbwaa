"""
SBWAA — Knowledge Base Indexer
Indexa documentos locais no ChromaDB para RAG.

Uso:
  python knowledge/indexer.py --file caminho/para/documento.pdf
  python knowledge/indexer.py --pasta knowledge/raw/gestoras/
  python knowledge/indexer.py --status
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
CHROMA_PATH = KNOWLEDGE_DIR / ".chromadb"
INDEX_LOG_PATH = KNOWLEDGE_DIR / "indexed" / "index_log.json"

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

EXTENSOES_SUPORTADAS = {".pdf", ".docx", ".txt", ".md"}


# ─── ChromaDB / Embeddings ────────────────────────────────────────────────────

def get_collection():
    import chromadb
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return client.get_or_create_collection(
        name="sbwaa_knowledge",
        metadata={"hnsw:space": "cosine"},
    )


def get_modelo():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBEDDING_MODEL)


# ─── Log de índice ────────────────────────────────────────────────────────────

def carregar_log() -> dict:
    if INDEX_LOG_PATH.exists():
        return json.loads(INDEX_LOG_PATH.read_text(encoding="utf-8"))
    return {"documentos": []}


def salvar_log(log: dict):
    INDEX_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_LOG_PATH.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")


def md5_arquivo(caminho: Path) -> str:
    h = hashlib.md5()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(8192), b""):
            h.update(bloco)
    return h.hexdigest()


def ja_indexado(log: dict, md5: str) -> bool:
    return any(d["md5"] == md5 for d in log["documentos"])


# ─── Extração de texto ────────────────────────────────────────────────────────

def extrair_texto(caminho: Path) -> str:
    ext = caminho.suffix.lower()

    if ext == ".pdf":
        try:
            import PyPDF2
            texto = []
            with open(caminho, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for pagina in reader.pages:
                    t = pagina.extract_text()
                    if t:
                        texto.append(t)
            resultado = "\n".join(texto)
            if not resultado.strip():
                print(f"  ⚠️  PDF protegido — extraia o texto manualmente e salve como .txt")
                return ""
            return resultado
        except Exception as e:
            print(f"  ⚠️  Erro ao ler PDF: {e}")
            return ""

    if ext == ".docx":
        try:
            from docx import Document
            doc = Document(str(caminho))
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception as e:
            print(f"  ⚠️  Erro ao ler DOCX: {e}")
            return ""

    # TXT / MD
    try:
        return caminho.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"  ⚠️  Erro ao ler arquivo: {e}")
        return ""


# ─── Chunking ─────────────────────────────────────────────────────────────────

def chunk_texto(texto: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    palavras = texto.split()
    chunks = []
    i = 0
    while i < len(palavras):
        chunk = palavras[i:i + chunk_size]
        chunks.append(" ".join(chunk))
        i += chunk_size - overlap
    return [c for c in chunks if c.strip()]


# ─── Inferência de metadados ──────────────────────────────────────────────────

def inferir_tipo(caminho: Path) -> str:
    partes = [p.lower() for p in caminho.parts]
    if "books" in partes or "livros" in partes:
        return "livro"
    if "research" in partes:
        return "research"
    if "gestoras" in partes:
        return "gestora"
    if "macro" in partes:
        return "macro"
    return "outro"


def inferir_idioma(caminho: Path) -> str:
    nome = caminho.name.lower()
    # Heurística simples por nome de arquivo
    termos_en = ["annual", "report", "minutes", "outlook", "bloomberg", "reuters"]
    if any(t in nome for t in termos_en):
        return "en"
    return "pt"


# ─── Indexação ────────────────────────────────────────────────────────────────

def indexar_arquivo(caminho: Path, collection, modelo, log: dict) -> bool:
    """Indexa um único arquivo. Retorna True se indexado com sucesso."""
    if caminho.suffix.lower() not in EXTENSOES_SUPORTADAS:
        print(f"  ⏭  Extensão não suportada: {caminho.name}")
        return False

    md5 = md5_arquivo(caminho)
    if ja_indexado(log, md5):
        print(f"  ✓  Já indexado: {caminho.name}")
        return False

    print(f"  📄 Extraindo texto: {caminho.name}")
    texto = extrair_texto(caminho)
    if not texto.strip():
        print(f"  ⏭  Texto vazio — pulando: {caminho.name}")
        return False

    chunks = chunk_texto(texto)
    total = len(chunks)
    tipo = inferir_tipo(caminho)
    idioma = inferir_idioma(caminho)
    nome_base = caminho.stem

    print(f"  🔢 Gerando embeddings para {total} chunks...")
    embeddings = modelo.encode(chunks, show_progress_bar=False).tolist()

    ids = [f"{nome_base}__chunk_{i}" for i in range(total)]
    metadatas = [
        {
            "fonte": caminho.name,
            "tipo": tipo,
            "autor": "desconhecido",
            "ano": "desconhecido",
            "idioma": idioma,
            "chunk_id": i,
            "total_chunks": total,
        }
        for i in range(total)
    ]

    # ChromaDB aceita no máximo 5461 itens por batch
    BATCH = 500
    for inicio in range(0, total, BATCH):
        fim = min(inicio + BATCH, total)
        print(f"  [{fim}/{total} chunks] Indexando: {caminho.name}...")
        collection.add(
            documents=chunks[inicio:fim],
            embeddings=embeddings[inicio:fim],
            metadatas=metadatas[inicio:fim],
            ids=ids[inicio:fim],
        )

    log["documentos"].append({
        "arquivo": str(caminho),
        "nome": caminho.name,
        "tipo": tipo,
        "md5": md5,
        "chunks": total,
        "idioma": idioma,
        "indexado_em": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    salvar_log(log)
    print(f"  ✅ Indexado: {caminho.name} ({total} chunks)")
    return True


def indexar_pasta(pasta: Path, collection, modelo, log: dict) -> int:
    arquivos = [f for f in pasta.rglob("*") if f.is_file() and f.suffix.lower() in EXTENSOES_SUPORTADAS]
    if not arquivos:
        print(f"Nenhum arquivo suportado em: {pasta}")
        return 0
    indexados = 0
    for arq in sorted(arquivos):
        if indexar_arquivo(arq, collection, modelo, log):
            indexados += 1
    return indexados


# ─── Comandos ─────────────────────────────────────────────────────────────────

def cmd_status():
    log = carregar_log()
    docs = log.get("documentos", [])
    total_chunks = sum(d.get("chunks", 0) for d in docs)
    por_tipo: dict[str, dict] = {}
    for d in docs:
        t = d.get("tipo", "outro")
        if t not in por_tipo:
            por_tipo[t] = {"docs": 0, "chunks": 0}
        por_tipo[t]["docs"] += 1
        por_tipo[t]["chunks"] += d.get("chunks", 0)

    ultima = max((d.get("indexado_em", "") for d in docs), default="—")

    print("═" * 47)
    print(f"SBWAA — Knowledge Base | {datetime.now().strftime('%Y-%m-%d')}")
    print("═" * 47)
    print(f"Total de documentos:  {len(docs)}")
    print(f"Total de chunks:      {total_chunks:,}")
    print("─" * 47)
    print("Por tipo:")
    LABELS = {
        "livro": "📚 Livros",
        "research": "📊 Research",
        "gestora": "📝 Gestoras",
        "macro": "🌍 Macro/RSS",
        "outro": "📁 Outros",
    }
    for tipo, label in LABELS.items():
        info = por_tipo.get(tipo, {"docs": 0, "chunks": 0})
        print(f"  {label:<18} {info['docs']} docs | {info['chunks']:,} chunks")
    print("─" * 47)
    print(f"Modelo de embedding:  {EMBEDDING_MODEL}")
    print(f"Banco de vetores:     ChromaDB local")
    print(f"Última atualização:   {ultima}")
    print("═" * 47)


def main():
    parser = argparse.ArgumentParser(description="SBWAA Knowledge Base Indexer")
    parser.add_argument("--file", help="Arquivo a indexar")
    parser.add_argument("--pasta", help="Pasta a indexar recursivamente")
    parser.add_argument("--status", action="store_true", help="Exibir status da base")
    args = parser.parse_args()

    if args.status:
        cmd_status()
        return

    if not args.file and not args.pasta:
        parser.print_help()
        return

    print(f"Carregando modelo de embeddings ({EMBEDDING_MODEL})...")
    print("(Download ~400MB na primeira execução — aguarde se necessário)")
    collection = get_collection()
    modelo = get_modelo()
    log = carregar_log()

    if args.file:
        caminho = Path(args.file)
        if not caminho.exists():
            print(f"Arquivo não encontrado: {caminho}")
            sys.exit(1)
        indexar_arquivo(caminho, collection, modelo, log)

    elif args.pasta:
        pasta = Path(args.pasta)
        if not pasta.exists():
            print(f"Pasta não encontrada: {pasta}")
            sys.exit(1)
        total = indexar_pasta(pasta, collection, modelo, log)
        print(f"\nTotal indexado: {total} documento(s)")


if __name__ == "__main__":
    main()
