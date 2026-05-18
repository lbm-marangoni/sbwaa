"""
run_earnings_reviewer.py — Executa o agente Earnings Reviewer do SBWAA.
Uso: python run_earnings_reviewer.py PETR4
"""

import re
import sys
import json
import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
VAULT_ROOT = PROJECT_ROOT / "vault"
SCRIPTS_DATA = PROJECT_ROOT / "scripts" / "data"
SKILL_PATH = Path(__file__).parent / "SKILL.md"
CARTEIRA_PATH = VAULT_ROOT / "00-portfolio" / "carteira.md"

sys.path.insert(0, str(SCRIPTS_DATA))

_TIPO_TAG_MAP = {
    "AÇÃO ON": "acao-on", "ACAO ON": "acao-on",
    "AÇÃO PN": "acao-pn", "ACAO PN": "acao-pn",
    "FII": "fii", "ETF BR": "etf-br", "ETF INTL": "etf-intl",
    "RF": "renda-fixa", "TD": "tesouro", "DEB": "debenture", "CRI/CRA": "cri-cra",
}


def lookup_tipo_tag(ticker: str) -> str:
    if not CARTEIRA_PATH.exists():
        return ""
    dentro = False
    for linha in CARTEIRA_PATH.read_text(encoding="utf-8").splitlines():
        s = linha.strip()
        if s.startswith("| Ticker"):
            dentro = True
        elif dentro and s.startswith("|---"):
            pass
        elif dentro and s.startswith("|"):
            cols = [c.strip() for c in s.split("|")[1:-1]]
            if len(cols) >= 2 and cols[0] == ticker:
                limpo = re.sub(r"[^\w\s/]", "", cols[1]).strip().upper()
                return _TIPO_TAG_MAP.get(limpo, "")
        elif dentro:
            break
    return ""


def injetar_tipo_frontmatter(md: str, tipo_tag: str) -> str:
    if not tipo_tag or not md.startswith("---"):
        return md
    def _add(m):
        tags = m.group(1)
        return m.group(0) if tipo_tag in tags else f"tags: [{tags}, {tipo_tag}]"
    return re.sub(r"tags: \[([^\]]+)\]", _add, md, count=1)


def get_trimestre(data=None) -> str:
    if data is None:
        data = datetime.date.today()
    mes = data.month
    ano = str(data.year)[-2:]
    if mes <= 3:
        return f"1T{ano}"
    elif mes <= 6:
        return f"2T{ano}"
    elif mes <= 9:
        return f"3T{ano}"
    else:
        return f"4T{ano}"


def buscar_dados_ticker(ticker: str) -> dict:
    from fetch_brapi import buscar_ticker
    print(f"Buscando dados fundamentalistas de {ticker}...")
    return buscar_ticker(ticker)


def formatar_dados_para_prompt(ticker: str, dados: dict) -> str:
    def fmt(val, prefixo="", sufixo=""):
        if val is None:
            return "N/D"
        if isinstance(val, float):
            return f"{prefixo}{val:.2f}{sufixo}"
        return f"{prefixo}{val}{sufixo}"

    dividendos = dados.get("dividendos_recentes", [])
    div_str = ""
    if dividendos:
        div_str = "\n".join(
            f"  - {d['data']}: R$ {d['valor']}" for d in dividendos
        )
    else:
        div_str = "  Nenhum dividendo recente disponível."

    return f"""TICKER: {ticker}
NOME: {dados.get('nome', 'N/D')}
SETOR: {dados.get('setor', 'N/D')}
COTAÇÃO ATUAL: {fmt(dados.get('cotacao'), 'R$ ')}
VARIAÇÃO DIA: {fmt(dados.get('variacao_dia_pct'), sufixo='%')}

MÚLTIPLOS:
  P/L: {fmt(dados.get('pl'))}
  P/VP: {fmt(dados.get('pvp'))}
  EV/EBITDA: {fmt(dados.get('ev_ebitda'))}
  Dividend Yield: {fmt(dados.get('dy'), sufixo='%')}
  ROE: {fmt(dados.get('roe'), sufixo='%')}
  Dívida Líq./EBITDA: {fmt(dados.get('divida_liquida_ebitda'))}

DIVIDENDOS RECENTES:
{div_str}

FONTE: {dados.get('fonte', 'brapi')}
ATUALIZADO EM: {dados.get('atualizado_em', 'N/D')}

NOTA: Dados de DRE trimestral detalhado (receita, EBITDA, lucro por trimestre)
não estão disponíveis nesta versão da Brapi. Analise com base nos múltiplos
e dados disponíveis acima, sinalizando explicitamente o que está ausente.
"""


def atualizar_tese_com_link(ticker: str, nome_earnings: str) -> None:
    tese_path = VAULT_ROOT / "01-ativos" / ticker / "tese.md"
    if not tese_path.exists():
        return
    conteudo = tese_path.read_text(encoding="utf-8")
    link = f"- [[{ticker}/{nome_earnings}]]"
    if link not in conteudo:
        if "## Earnings" in conteudo:
            conteudo = conteudo.replace(
                "## Earnings",
                f"## Earnings\n{link}",
                1,
            )
        else:
            conteudo += f"\n\n## Earnings\n{link}\n"
        tese_path.write_text(conteudo, encoding="utf-8")
        print(f"Wikilink adicionado à tese: {tese_path}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python run_earnings_reviewer.py TICKER")
        print("Exemplo: python run_earnings_reviewer.py PETR4")
        sys.exit(1)

    import anthropic

    ticker = sys.argv[1].upper().strip()
    hoje = datetime.date.today().strftime("%Y-%m-%d")
    trimestre = get_trimestre()

    print(f"Earnings Reviewer — {ticker} | {trimestre}")
    print("=" * 50)

    skill_content = SKILL_PATH.read_text(encoding="utf-8")

    try:
        dados = buscar_dados_ticker(ticker)
    except Exception as e:
        print(f"ERRO ao buscar dados de {ticker}: {e}")
        sys.exit(1)

    dados_prompt = formatar_dados_para_prompt(ticker, dados)

    # RAG: buscar contexto específico do setor e empresa
    contexto_rag = ""
    try:
        import sys as _sys
        _sys.path.insert(0, str(PROJECT_ROOT))
        from knowledge.retriever import buscar, formatar_contexto_para_agente, base_disponivel
        if base_disponivel():
            setor = dados.get("setor", "")
            query_earnings = f"análise resultados {ticker} {setor} margem EBITDA receita"
            chunks = buscar(query_earnings, n_resultados=3)
            contexto_rag = formatar_contexto_para_agente(chunks, max_tokens=1000)
    except Exception:
        pass

    contexto = f"""TICKER PARA ANÁLISE: {ticker}
TRIMESTRE: {trimestre}
DATA: {hoje}

DADOS DISPONÍVEIS VIA BRAPI:
{dados_prompt}
{chr(10) + contexto_rag if contexto_rag else ""}
Gere a análise de earnings conforme o formato definido no seu SKILL.
"""

    print("Enviando dados ao agente Earnings Reviewer...")
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=skill_content,
        messages=[
            {"role": "user", "content": contexto}
        ],
    )

    output = response.content[0].text
    output = injetar_tipo_frontmatter(output, lookup_tipo_tag(ticker))

    ativo_dir = VAULT_ROOT / "01-ativos" / ticker
    ativo_dir.mkdir(parents=True, exist_ok=True)

    nome_earnings = f"earnings-{trimestre}-{hoje}"
    saida = ativo_dir / f"{nome_earnings}.md"
    saida.write_text(output, encoding="utf-8")

    atualizar_tese_com_link(ticker, nome_earnings)

    print("\n" + "=" * 50)
    print(output)
    print("=" * 50)
    print(f"\nRelatório salvo em: {saida}")


if __name__ == "__main__":
    main()
