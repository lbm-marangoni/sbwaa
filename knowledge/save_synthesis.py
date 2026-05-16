"""
SBWAA — Knowledge Synthesis Saver
Salva sínteses geradas a partir do RAG no vault/04-knowledge/.
"""

from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
VAULT_KNOWLEDGE_DIR = PROJECT_ROOT / "vault" / "04-knowledge"


def salvar_sintese(titulo: str, conteudo: str,
                   ticker: str = None, tipo: str = "geral",
                   fontes: list[dict] = None) -> Path:
    """
    Salva síntese gerada a partir do RAG no vault/04-knowledge/.
    Cria wikilinks automáticos para o ativo se ticker fornecido.

    Args:
        titulo: título da síntese
        conteudo: conteúdo gerado pelo agente
        ticker: ticker do ativo (opcional)
        tipo: tipo de síntese (geral, valuation, macro, risco, etc.)
        fontes: lista de dicts com 'fonte' e 'score' dos chunks usados

    Returns:
        Path do arquivo salvo
    """
    VAULT_KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

    hoje = datetime.now().strftime("%Y-%m-%d")
    hora = datetime.now().strftime("%H:%M")
    slug = titulo.lower().replace(" ", "-")[:40]
    nome_arquivo = f"sintese-{slug}-{hoje}.md"
    caminho = VAULT_KNOWLEDGE_DIR / nome_arquivo

    fontes_lista = ""
    if fontes:
        fontes_lista = "\n".join(
            f"- {f['fonte']} (relevância: {f['score']:.0%})"
            for f in fontes
        )
    else:
        fontes_lista = "- Base de conhecimento local"

    links_extras = ""
    if ticker:
        links_extras = f"- [[{ticker}/tese]]\n- [[01-ativos/{ticker}]]"

    conteudo_nota = f"""---
tags: [knowledge, sintese, {tipo}]
cssclasses: [node-knowledge]
data: {hoje}
hora: {hora}
ticker: {ticker or "null"}
tipo: {tipo}
---

# Síntese: {titulo}

{conteudo}

## Fontes Consultadas

{fontes_lista}

## Links

{links_extras}
- [[market-researcher-{hoje}]]
"""

    caminho.write_text(conteudo_nota, encoding="utf-8")
    return caminho
