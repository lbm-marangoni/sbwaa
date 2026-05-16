"""
run_market_researcher.py — Executa o agente Market Researcher do SBWAA.
Uso: python run_market_researcher.py
"""

import re
import sys
import subprocess
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
VAULT_ROOT = PROJECT_ROOT / "vault"
SCRIPTS_DATA = PROJECT_ROOT / "scripts" / "data"
SKILL_PATH = Path(__file__).parent / "SKILL.md"

SNAPSHOTS_DIR = VAULT_ROOT / "02-relatorios" / "diarios"
MACRO_DIR = VAULT_ROOT / "03-macro"
CARTEIRA_PATH = VAULT_ROOT / "00-portfolio" / "carteira.md"


def get_snapshot_do_dia(hoje: str) -> str:
    snapshot_path = SNAPSHOTS_DIR / f"snapshot-{hoje}.md"
    if not snapshot_path.exists():
        print("Snapshot do dia não encontrado. Gerando agora...")
        resultado = subprocess.run(
            [sys.executable, str(SCRIPTS_DATA / "market_snapshot.py")],
            capture_output=True,
            text=True,
        )
        print(resultado.stdout)
        if resultado.returncode != 0:
            print(f"AVISO: market_snapshot.py retornou erro:\n{resultado.stderr}")
    if snapshot_path.exists():
        return snapshot_path.read_text(encoding="utf-8")
    return "Snapshot não disponível."


def extrair_tickers_e_setores(carteira_path: Path) -> tuple[list[str], list[str]]:
    tickers = []
    setores = []
    if not carteira_path.exists():
        return tickers, setores
    conteudo = carteira_path.read_text(encoding="utf-8")
    dentro = False
    for linha in conteudo.splitlines():
        stripped = linha.strip()
        if stripped.startswith("| Ticker"):
            dentro = True
            continue
        if dentro and stripped.startswith("|---"):
            continue
        if dentro and stripped.startswith("|"):
            celulas = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(celulas) >= 3:
                ticker_raw = celulas[0].replace("[[", "").replace("]]", "").split("|")[0].strip()
                ticker_raw = re.sub(r"01-ativos/([^/]+)/tese", r"\1", ticker_raw)
                setor_raw = celulas[2].strip()
                if ticker_raw:
                    tickers.append(ticker_raw.upper())
                if setor_raw and setor_raw not in setores and setor_raw != "—":
                    setores.append(setor_raw)
        elif dentro:
            break
    return tickers, setores


def atualizar_nota_mensal(hoje: str, caminho_relatorio: Path) -> None:
    mes_ano = datetime.now().strftime("%m-%Y")
    nota_mensal = MACRO_DIR / f"macro-{mes_ano}.md"
    nome_mes = datetime.now().strftime("%B %Y").capitalize()
    link = f"- [[market-researcher-{hoje}]]"
    if nota_mensal.exists():
        conteudo = nota_mensal.read_text(encoding="utf-8")
        if link not in conteudo:
            conteudo += f"\n{link}"
            nota_mensal.write_text(conteudo, encoding="utf-8")
    else:
        conteudo = f"""---
tags: [macro, mensal]
cssclasses: [node-macro]
mes: {mes_ano}
---

# Macro — {nome_mes}

## Relatórios do Mês

{link}
"""
        nota_mensal.write_text(conteudo, encoding="utf-8")
    print(f"Nota mensal atualizada: {nota_mensal}")


def main():
    import sys as _sys
    _sys.path.insert(0, str(PROJECT_ROOT))
    import anthropic

    hoje = datetime.now().strftime("%Y-%m-%d")
    mes_ano = datetime.now().strftime("%m-%Y")

    print(f"Market Researcher — {hoje}")
    print("=" * 50)

    skill_content = SKILL_PATH.read_text(encoding="utf-8")
    conteudo_snapshot = get_snapshot_do_dia(hoje)
    tickers, setores = extrair_tickers_e_setores(CARTEIRA_PATH)

    lista_tickers = ", ".join(tickers) if tickers else "Nenhum ativo na carteira ainda."
    lista_setores = ", ".join(setores) if setores else "Nenhum setor identificado ainda."
    setor_principal = setores[0] if setores else "mercado"

    # RAG: buscar contexto macro relevante
    contexto_rag = ""
    try:
        from knowledge.retriever import buscar, formatar_contexto_para_agente, base_disponivel
        if base_disponivel():
            query_macro = f"cenário macroeconômico Brasil {setor_principal} {datetime.now().year}"
            chunks_macro = buscar(query_macro, n_resultados=4, filtro_tipo="macro")
            contexto_rag = formatar_contexto_para_agente(chunks_macro, max_tokens=1500)
    except Exception:
        pass

    contexto_do_dia = f"""DATA: {hoje}

SNAPSHOT MACRO:
{conteudo_snapshot}

SETORES PRESENTES NA CARTEIRA (apenas setores, sem valores):
{lista_setores}

TICKERS MONITORADOS:
{lista_tickers}
{chr(10) + contexto_rag if contexto_rag else ""}"""

    print("Enviando contexto ao agente Market Researcher...")
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=skill_content,
        messages=[
            {"role": "user", "content": contexto_do_dia}
        ],
    )

    output = response.content[0].text

    MACRO_DIR.mkdir(parents=True, exist_ok=True)
    saida = MACRO_DIR / f"market-researcher-{hoje}.md"
    saida.write_text(output, encoding="utf-8")

    atualizar_nota_mensal(hoje, saida)

    print("\n" + "=" * 50)
    print(output)
    print("=" * 50)
    print(f"\nRelatório salvo em: {saida}")


if __name__ == "__main__":
    main()
