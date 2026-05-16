"""
SBWAA — Comando /knowledge
Gerencia a base de conhecimento RAG local.

Uso:
  python sbwaa.py /knowledge --status
  python sbwaa.py /knowledge --adicionar caminho/arquivo.pdf
  python sbwaa.py /knowledge --buscar "valuation petróleo Brasil"
  python sbwaa.py /knowledge --listar
  python sbwaa.py /knowledge --coletar-rss
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

INDEX_LOG_PATH = PROJECT_ROOT / "knowledge" / "indexed" / "index_log.json"


def cmd_status():
    from knowledge.indexer import cmd_status as _status
    _status()


def cmd_adicionar(caminho_str: str):
    from knowledge.indexer import (
        get_collection, get_modelo, carregar_log,
        indexar_arquivo, indexar_pasta,
    )
    caminho = Path(caminho_str)
    if not caminho.exists():
        print(f"❌ Caminho não encontrado: {caminho}")
        sys.exit(1)

    print(f"Carregando modelo de embeddings...")
    collection = get_collection()
    modelo = get_modelo()
    log = carregar_log()

    if caminho.is_file():
        indexar_arquivo(caminho, collection, modelo, log)
    elif caminho.is_dir():
        total = indexar_pasta(caminho, collection, modelo, log)
        print(f"\nTotal indexado: {total} documento(s)")
    else:
        print(f"❌ Caminho inválido: {caminho}")


def cmd_buscar(query: str):
    from knowledge.retriever import buscar, base_disponivel

    if not base_disponivel():
        print("Base de conhecimento vazia. Use --adicionar para indexar documentos.")
        return

    print(f"\nBuscando: \"{query}\"")
    print("=" * 55)

    resultados = buscar(query, n_resultados=5)

    if not resultados:
        print("Nenhum resultado encontrado.")
        return

    for i, r in enumerate(resultados, 1):
        print(f"\n[{i}] {r['fonte']} — {r['tipo']} (relevância: {r['score']:.0%})")
        print("─" * 55)
        trecho = r["texto"][:400]
        if len(r["texto"]) > 400:
            trecho += "..."
        print(trecho)

    print(f"\n{len(resultados)} resultado(s) encontrado(s).")


def cmd_listar():
    if not INDEX_LOG_PATH.exists():
        print("Log de índice não encontrado.")
        return

    log = json.loads(INDEX_LOG_PATH.read_text(encoding="utf-8"))
    docs = log.get("documentos", [])

    if not docs:
        print("Nenhum documento indexado ainda.")
        return

    print(f"\n{'═'*65}")
    print(f"{'SBWAA — Documentos Indexados':^65}")
    print(f"{'═'*65}")
    print(f"{'#':<4} {'Nome':<35} {'Tipo':<10} {'Chunks':<8} {'Data'}")
    print(f"{'─'*65}")

    for i, d in enumerate(docs, 1):
        nome = d.get("nome", "—")[:34]
        tipo = d.get("tipo", "—")[:9]
        chunks = d.get("chunks", 0)
        data = d.get("indexado_em", "—")[:10]
        print(f"{i:<4} {nome:<35} {tipo:<10} {chunks:<8} {data}")

    print(f"{'─'*65}")
    total_chunks = sum(d.get("chunks", 0) for d in docs)
    print(f"{'Total:':<4} {len(docs)} documentos | {total_chunks:,} chunks")
    print(f"{'═'*65}\n")


def cmd_coletar_rss():
    from knowledge.rss_collector import coletar_todos_feeds
    print("Iniciando coleta RSS...")
    total = coletar_todos_feeds()
    if total == 0:
        print("Nenhum artigo novo coletado.")
    else:
        print(f"✅ {total} artigo(s) novo(s) indexado(s).")


def main():
    parser = argparse.ArgumentParser(description="SBWAA Knowledge Base")
    parser.add_argument("--status", action="store_true", help="Exibir métricas da base")
    parser.add_argument("--adicionar", metavar="CAMINHO", help="Indexar arquivo ou pasta")
    parser.add_argument("--buscar", metavar="QUERY", help="Busca semântica manual")
    parser.add_argument("--listar", action="store_true", help="Listar documentos indexados")
    parser.add_argument("--coletar-rss", action="store_true", dest="coletar_rss",
                        help="Forçar coleta RSS imediata")
    args = parser.parse_args()

    if args.status:
        cmd_status()
    elif args.adicionar:
        cmd_adicionar(args.adicionar)
    elif args.buscar:
        cmd_buscar(args.buscar)
    elif args.listar:
        cmd_listar()
    elif args.coletar_rss:
        cmd_coletar_rss()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
