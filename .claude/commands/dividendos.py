"""
dividendos.py — Calendário de dividendos e histórico de proventos.
Uso: python sbwaa.py /dividendos
"""

import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import yfinance as yf
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent.parent
VAULT_ROOT = PROJECT_ROOT / "vault"
CARTEIRA_PATH = VAULT_ROOT / "00-portfolio" / "carteira.md"


def eh_ticker_br(ticker: str) -> bool:
    return bool(re.match(r"^[A-Z]{4}[0-9]{1,2}[FBP]?$", ticker))


def ticker_yahoo(ticker: str) -> str:
    return f"{ticker}.SA" if eh_ticker_br(ticker) else ticker


def parse_carteira() -> list[dict]:
    if not CARTEIRA_PATH.exists():
        return []
    conteudo = CARTEIRA_PATH.read_text(encoding="utf-8")
    posicoes = []
    dentro = False
    for linha in conteudo.splitlines():
        stripped = linha.strip()
        if stripped.startswith("| Ticker"):
            dentro = True
            continue
        if dentro and stripped.startswith("|---"):
            continue
        if dentro and stripped.startswith("|"):
            cols = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(cols) >= 5 and cols[0] and cols[0] not in ("", "Ticker"):
                try:
                    qtd_s = cols[3].replace(".", "").replace(",", ".")
                    pm_s = re.sub(r"[^\d,.]", "", cols[4]).replace(",", ".")
                    qtd = float(qtd_s) if qtd_s else 0
                    pm = float(pm_s) if pm_s else 0
                    if cols[0] and qtd > 0:
                        posicoes.append({"ticker": cols[0], "tipo": cols[1], "qtd": qtd, "pm": pm})
                except (ValueError, IndexError):
                    pass
        elif dentro and not stripped.startswith("|"):
            break
    return posicoes


def main():
    hoje = datetime.now()
    prazo_60d = hoje + timedelta(days=60)
    ano_inicio = datetime(hoje.year, 1, 1)

    posicoes = parse_carteira()
    if not posicoes:
        print("\n  Carteira vazia. Use /adicionar para incluir ativos.\n")
        return

    print(f"\n{'═'*55}")
    print(f"  SBWAA — Dividendos | {hoje.strftime('%Y-%m-%d')}")
    print(f"{'═'*55}\n")

    proximos = []
    historico_ano = {}
    yoc_data = {}

    for pos in posicoes:
        tk = pos["ticker"]
        ty = ticker_yahoo(tk)
        try:
            t = yf.Ticker(ty)
            info = t.info or {}
            divs = t.dividends  # pd.Series

            # Próximos dividendos: usar ex_dividend_date e dividend_rate
            ex_date_ts = info.get("exDividendDate")
            div_rate = info.get("dividendRate") or info.get("trailingAnnualDividendRate") or 0
            div_yield = info.get("dividendYield") or info.get("trailingAnnualDividendYield") or 0
            preco_atual = info.get("regularMarketPrice") or info.get("previousClose") or pos["pm"]

            if ex_date_ts:
                ex_date = datetime.fromtimestamp(ex_date_ts)
                if ex_date >= hoje and ex_date <= prazo_60d:
                    proximos.append({
                        "ticker": tk,
                        "ex_date": ex_date.strftime("%Y-%m-%d"),
                        "valor_est": div_rate / 4 if div_rate else None,
                        "qtd": pos["qtd"],
                    })

            # Histórico no ano
            if divs is not None and not divs.empty:
                if hasattr(divs.index, "tz_localize"):
                    divs.index = divs.index.tz_localize(None) if divs.index.tzinfo else divs.index
                divs_ano = divs[divs.index >= pd.Timestamp(ano_inicio)]
                total_ano = float(divs_ano.sum()) * pos["qtd"] if not divs_ano.empty else 0.0
                historico_ano[tk] = total_ano

            # Yield on Cost
            if pos["pm"] > 0 and div_rate:
                yoc_data[tk] = round(div_rate / pos["pm"] * 100, 2)
            elif pos["pm"] > 0 and div_yield and preco_atual:
                yoc_data[tk] = round(div_yield * preco_atual / pos["pm"] * 100, 2)

        except Exception as e:
            print(f"  ⚠️  {tk}: {e}")

    # Exibir próximos dividendos
    print(f"  PRÓXIMOS DIVIDENDOS (60 dias)")
    print(f"  {'─'*50}")
    if proximos:
        for p in sorted(proximos, key=lambda x: x["ex_date"]):
            val = f"R$ {p['valor_est']:.4f}" if p["valor_est"] else "N/D"
            print(f"  {p['ticker']:<8} Ex-date: {p['ex_date']}  Valor/ação: {val}")
    else:
        print("  Nenhum dividendo de ativos da carteira nos próximos 60 dias.")

    # Histórico no ano
    total_ano = sum(historico_ano.values())
    print(f"\n  DIVIDENDOS RECEBIDOS EM {hoje.year}")
    print(f"  {'─'*50}")
    for tk, total in sorted(historico_ano.items(), key=lambda x: -x[1]):
        print(f"  {tk:<8} R$ {total:>10,.2f}")
    print(f"  {'─'*50}")
    print(f"  {'TOTAL':<8} R$ {total_ano:>10,.2f}")

    # Yield on Cost
    if yoc_data:
        print(f"\n  YIELD ON COST")
        print(f"  {'─'*50}")
        for tk, yoc in sorted(yoc_data.items(), key=lambda x: -x[1]):
            print(f"  {tk:<8} {yoc:>6.2f}% a.a.")

    print(f"\n{'═'*55}\n")


if __name__ == "__main__":
    main()
