"""
watchlist.py — Lista todos os ativos analisados + carteira com último veredicto e frescor da análise.
Uso: python sbwaa.py /watchlist
     python sbwaa.py /watchlist --rever      (mostra só os defasados)
"""

import sys
import re
from datetime import datetime, date
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
VAULT_ROOT = PROJECT_ROOT / "vault"
ATIVOS_DIR = VAULT_ROOT / "01-ativos"
CARTEIRA_PATH = VAULT_ROOT / "00-portfolio" / "carteira.md"

HOJE = date.today()

TIPO_LABEL = {
    "acao-on":    "🟦 AÇÃO ON",
    "acao-pn":    "🟦 AÇÃO PN",
    "fii":        "🟩 FII",
    "etf-br":     "🟨 ETF BR",
    "etf-intl":   "🟥 ETF INTL",
    "renda-fixa": "⬜ RF",
    "tesouro":    "🟪 TD",
    "debenture":  "🟫 DEB",
    "cri-cra":    "🟧 CRI/CRA",
}

VEREDICTO_COR = {
    "COMPRAR":      "✅",
    "COMPRA":       "✅",
    "AGUARDAR":     "⏳",
    "AGUARDA":      "⏳",
    "EVITAR":       "🚫",
    "BARATO":       "✅",
    "JUSTO":        "⚖️",
    "CARO":         "🔴",
}

STALE_DIAS = 45


def _frontmatter(texto: str) -> dict:
    """Extrai campos simples do bloco YAML frontmatter."""
    m = re.match(r"^---\s*\n(.*?)\n---", texto, re.DOTALL)
    if not m:
        return {}
    campos = {}
    for linha in m.group(1).splitlines():
        if ":" in linha:
            chave, _, valor = linha.partition(":")
            campos[chave.strip().lower()] = valor.strip().strip('"').strip("'")
    return campos


def _ultima_analise(ticker: str) -> tuple[str | None, date | None, str | None]:
    """Retorna (veredicto, data, preco_alvo) da análise mais recente do ativo."""
    pasta = ATIVOS_DIR / ticker
    if not pasta.exists():
        return None, None, None

    arquivos = sorted(pasta.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    for arq in arquivos:
        texto = arq.read_text(encoding="utf-8", errors="ignore")
        fm = _frontmatter(texto)

        veredicto = fm.get("veredicto") or fm.get("decisao")
        data_str = fm.get("data")
        preco_alvo = fm.get("preco_alvo") or fm.get("preco-alvo")

        # Fallback: buscar COMPRAR/AGUARDAR/EVITAR/BARATO/JUSTO/CARO no texto
        if not veredicto:
            for palavra in ("COMPRAR", "AGUARDAR", "EVITAR", "BARATO", "JUSTO", "CARO"):
                if f"**{palavra}**" in texto or f"VEREDICTO: {palavra}" in texto:
                    veredicto = palavra
                    break

        if not data_str:
            # Tentar extrair data do nome do arquivo (analise-TICKER-YYYY-MM-DD.md)
            m = re.search(r"(\d{4}-\d{2}-\d{2})", arq.name)
            if m:
                data_str = m.group(1)

        if veredicto or data_str:
            data_obj = None
            if data_str:
                try:
                    data_obj = date.fromisoformat(data_str)
                except ValueError:
                    pass
            return veredicto, data_obj, preco_alvo

    return None, None, None


def _status_frescor(data_analise: date | None) -> str:
    if data_analise is None:
        return "— sem análise"
    dias = (HOJE - data_analise).days
    if dias <= STALE_DIAS:
        return f"✅ {dias}d"
    if dias <= 90:
        return f"⚠️  {dias}d"
    return f"🔴 {dias}d"


def _carregar_carteira() -> dict[str, str]:
    """Retorna {ticker: tipo} dos ativos em carteira."""
    if not CARTEIRA_PATH.exists():
        return {}
    resultado = {}
    dentro = False
    for linha in CARTEIRA_PATH.read_text(encoding="utf-8").splitlines():
        stripped = linha.strip()
        if stripped.startswith("| Ticker"):
            dentro = True
            continue
        if dentro and stripped.startswith("|---"):
            continue
        if dentro and stripped.startswith("|"):
            cols = [c.strip() for c in stripped.split("|")[1:-1]]
            if cols and cols[0] and cols[0] not in ("", "Ticker"):
                ticker = cols[0].upper()
                tipo = cols[1].lower() if len(cols) > 1 else ""
                resultado[ticker] = tipo
        elif dentro and not stripped.startswith("|"):
            break
    return resultado


def _coletar_ativos_analisados() -> set[str]:
    if not ATIVOS_DIR.exists():
        return set()
    return {p.name.upper() for p in ATIVOS_DIR.iterdir() if p.is_dir()}


def main():
    args = sys.argv[1:]
    apenas_rever = "--rever" in args

    carteira = _carregar_carteira()
    analisados = _coletar_ativos_analisados()
    todos = sorted(analisados | set(carteira.keys()))

    linhas = []
    for ticker in todos:
        em_carteira = ticker in carteira
        tipo_raw = carteira.get(ticker, "")
        tipo_label = TIPO_LABEL.get(tipo_raw, tipo_raw or "—")
        veredicto, data_analise, preco_alvo = _ultima_analise(ticker)
        frescor = _status_frescor(data_analise)

        if apenas_rever:
            if data_analise is None or (HOJE - data_analise).days <= STALE_DIAS:
                continue

        icone_v = VEREDICTO_COR.get(veredicto.upper() if veredicto else "", "")
        veredicto_str = f"{icone_v} {veredicto}" if veredicto else "—"
        data_str = data_analise.strftime("%Y-%m-%d") if data_analise else "—"
        carteira_str = "●" if em_carteira else "○"
        preco_str = f"R$ {preco_alvo}" if preco_alvo else "—"

        linhas.append((ticker, carteira_str, tipo_label, veredicto_str, data_str, frescor, preco_str))

    print(f"\n{'═'*90}")
    titulo = "SBWAA — Watchlist" + (" (defasados)" if apenas_rever else f"  [{len(todos)} ativos]")
    print(f"  {titulo}  |  {HOJE}")
    print(f"{'═'*90}\n")

    if not linhas:
        if apenas_rever:
            print("  Nenhum ativo defasado. Todos com análise recente.\n")
        else:
            print("  Nenhum ativo encontrado em vault/01-ativos/ nem em carteira.\n")
        return

    cab = f"  {'Ticker':<10} {'C':<3} {'Tipo':<14} {'Veredicto':<22} {'Data':<12} {'Frescor':<12} {'Preço-Alvo'}"
    print(cab)
    print(f"  {'─'*84}")
    for linha in linhas:
        ticker, cart, tipo, verd, data, frescor, preco = linha
        print(f"  {ticker:<10} {cart:<3} {tipo:<14} {verd:<22} {data:<12} {frescor:<12} {preco}")

    print(f"\n  Legenda:  ● em carteira  ○ watchlist puro  ✅ análise recente  ⚠️ defasado (>{STALE_DIAS}d)  🔴 rever (>90d)")
    print(f"  Dica: /pm TICKER para reavaliar  |  /analisar TICKER para análise completa\n")


if __name__ == "__main__":
    main()
