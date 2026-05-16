"""
tese.py — Pipeline rápido de análise: Research + DCF + Valuation + PM.
Pula Quant e Risk (usa cache existente).
Uso:
    python sbwaa.py /tese PETR4
    python sbwaa.py /tese PETR4 --completo
"""

import sys
import time
import argparse
import subprocess
from datetime import datetime, date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DATA = PROJECT_ROOT / "scripts" / "data"
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"
VAULT_ROOT = PROJECT_ROOT / "vault"
CACHE_DIR = SCRIPTS_DATA / "cache"

CACHE_TTL = 4  # horas


def get_trimestre(d=None) -> str:
    d = d or date.today()
    ano = str(d.year)[-2:]
    if d.month <= 3: return f"1T{ano}"
    elif d.month <= 6: return f"2T{ano}"
    elif d.month <= 9: return f"3T{ano}"
    else: return f"4T{ano}"


def cache_valido(path: Path | None) -> bool:
    if not path or not path.exists():
        return False
    return (time.time() - path.stat().st_mtime) / 3600 < CACHE_TTL


def rodar(num: int, total: int, desc: str, cmd: list[str], cache: Path | None = None) -> bool:
    if cache_valido(cache):
        print(f"  [{num}/{total}] {desc:<40} ⏭️  (cache)")
        return True
    print(f"  [{num}/{total}] {desc:<40} ⏳")
    r = subprocess.run(cmd, text=True)
    ok = r.returncode == 0
    print(f"  [{num}/{total}] {desc:<40} {'✅' if ok else '⚠️'}")
    return ok


def main():
    parser = argparse.ArgumentParser(description="/tese — SBWAA")
    parser.add_argument("ticker")
    parser.add_argument("--completo", action="store_true", help="Versão longa do valuation")
    parser.add_argument("--tipo", choices=["acao", "fii", "etf"], default="acao")
    args = parser.parse_args()

    ticker = args.ticker.upper()
    versao = "longa" if args.completo else "curta"
    hoje = datetime.now().strftime("%Y-%m-%d")
    trimestre = get_trimestre()
    ativo_dir = VAULT_ROOT / "01-ativos" / ticker
    TOTAL = 6

    print(f"\n{'═'*55}")
    print(f"  SBWAA — /tese {ticker} (pipeline rápido)")
    print(f"  {hoje} | versao={versao} | tipo={args.tipo}")
    print(f"{'─'*55}\n")

    # 1. Snapshot
    snap_path = VAULT_ROOT / "02-relatorios" / "diarios" / f"snapshot-{hoje}.md"
    rodar(1, TOTAL, "Market Snapshot",
          [sys.executable, str(SCRIPTS_DATA / "market_snapshot.py")], snap_path)

    # 2. Market Researcher
    mr_path = VAULT_ROOT / "03-macro" / f"market-researcher-{hoje}.md"
    rodar(2, TOTAL, "Market Researcher",
          [sys.executable, str(AGENTS_DIR / "market-researcher" / "run_market_researcher.py")],
          mr_path)

    # 3. Earnings
    er_cache = None
    if ativo_dir.exists():
        lista = sorted(ativo_dir.glob(f"earnings-{trimestre}-*.md"), reverse=True)
        er_cache = lista[0] if lista else None
    rodar(3, TOTAL, f"Earnings Reviewer ({ticker})",
          [sys.executable, str(AGENTS_DIR / "earnings-reviewer" / "run_earnings_reviewer.py"), ticker],
          er_cache)

    # 4. DCF
    dcf_cache = CACHE_DIR / f"dcf_{ticker}_{hoje}.json"
    if args.tipo == "etf":
        print(f"  [4/{TOTAL}] Model Builder DCF                        ⏭️  (ETF)")
    else:
        rodar(4, TOTAL, f"Model Builder DCF ({ticker})",
              [sys.executable, str(AGENTS_DIR / "model-builder" / "run_model_builder.py"),
               ticker, "--tipo", args.tipo], dcf_cache)

    # 5. Valuation
    val_cache = None
    if ativo_dir.exists():
        p = ativo_dir / f"equity-research-{ticker}-{hoje}-{versao}.md"
        val_cache = p if p.exists() else None
    if args.tipo == "etf":
        print(f"  [5/{TOTAL}] Valuation Reviewer                       ⏭️  (ETF)")
    else:
        rodar(5, TOTAL, f"Valuation Reviewer ({ticker})",
              [sys.executable, str(AGENTS_DIR / "valuation-reviewer" / "run_valuation_reviewer.py"),
               ticker, "--versao", versao], val_cache)

    # 6. PM (interativo)
    print(f"\n  [6/{TOTAL}] Portfolio Manager — decisão final")
    print(f"{'─'*55}")
    subprocess.run(
        [sys.executable,
         str(AGENTS_DIR / "portfolio-manager" / "run_pm.py"),
         ticker, "--versao", versao],
        text=True,
    )

    print(f"\n{'═'*55}")
    print(f"  /tese {ticker} concluída | {hoje}")
    print(f"{'═'*55}\n")


if __name__ == "__main__":
    main()
