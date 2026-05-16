"""
run_research_pipeline.py — Pipeline de research completo — Fases 1, 2, 3 e 4.
Uso: python run_research_pipeline.py [TICKER] [--versao curta|longa] [--tipo fii|etf]

Ordem de execução:
  1. market_snapshot.py          — dados de mercado
  2. run_market_researcher.py    — contexto macro
  3. run_earnings_reviewer.py    — resultados da empresa (se ticker)
  4. run_model_builder.py        — DCF completo (se ticker, não ETF)
  5. run_valuation_reviewer.py   — veredicto de valuation (se ticker, não ETF)
  6. run_quant.py                — métricas quantitativas da carteira (sempre)
  7. run_risk_engineer.py        — risk snapshot da carteira (sempre)
"""

import sys
import argparse
import subprocess
from datetime import datetime, date
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DATA = PROJECT_ROOT / "scripts" / "data"
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"
VAULT_ROOT = PROJECT_ROOT / "vault"


def rodar(descricao: str, args: list[str]) -> int:
    print(f"\n{'='*60}")
    print(f"  {descricao}")
    print(f"{'='*60}")
    resultado = subprocess.run(args, text=True)
    return resultado.returncode


def get_trimestre(d=None) -> str:
    d = d or date.today()
    ano = str(d.year)[-2:]
    if d.month <= 3: return f"1T{ano}"
    elif d.month <= 6: return f"2T{ano}"
    elif d.month <= 9: return f"3T{ano}"
    else: return f"4T{ano}"


def main():
    parser = argparse.ArgumentParser(description="Pipeline SBWAA — Fases 1-4")
    parser.add_argument("ticker", nargs="?", default=None)
    parser.add_argument("--versao", choices=["curta", "longa"], default="curta")
    parser.add_argument("--tipo", choices=["acao", "fii", "etf"], default="acao")
    args = parser.parse_args()

    ticker = args.ticker.upper() if args.ticker else None
    hoje = datetime.now().strftime("%Y-%m-%d")
    mes_ano = datetime.now().strftime("%m-%Y")
    trimestre = get_trimestre()

    arquivos_gerados = []

    # ── 1. Snapshot macro ─────────────────────────────────────────────────────
    rodar("1/7 — Snapshot macro", [sys.executable, str(SCRIPTS_DATA / "market_snapshot.py")])
    snap = VAULT_ROOT / "02-relatorios" / "diarios" / f"snapshot-{hoje}.md"
    if snap.exists(): arquivos_gerados.append(snap)

    # ── 2. Market Researcher ──────────────────────────────────────────────────
    rodar("2/7 — Market Researcher",
          [sys.executable, str(AGENTS_DIR / "market-researcher" / "run_market_researcher.py")])
    mr = VAULT_ROOT / "03-macro" / f"market-researcher-{hoje}.md"
    if mr.exists(): arquivos_gerados.append(mr)
    mensal = VAULT_ROOT / "03-macro" / f"macro-{mes_ano}.md"
    if mensal.exists(): arquivos_gerados.append(mensal)

    if ticker:
        # ── 3. Earnings Reviewer ──────────────────────────────────────────────
        rodar(f"3/7 — Earnings Reviewer ({ticker})",
              [sys.executable,
               str(AGENTS_DIR / "earnings-reviewer" / "run_earnings_reviewer.py"), ticker])
        er = VAULT_ROOT / "01-ativos" / ticker / f"earnings-{trimestre}-{hoje}.md"
        if er.exists(): arquivos_gerados.append(er)

        if args.tipo != "etf":
            # ── 4. Model Builder ──────────────────────────────────────────────
            rodar(f"4/7 — Model Builder DCF ({ticker})",
                  [sys.executable,
                   str(AGENTS_DIR / "model-builder" / "run_model_builder.py"),
                   ticker, "--tipo", args.tipo])
            ativo_dir = VAULT_ROOT / "01-ativos" / ticker
            xlsxs = sorted(ativo_dir.glob(f"dcf-{ticker}-v*.xlsx"), reverse=True)
            if xlsxs: arquivos_gerados.append(xlsxs[0])

            # ── 5. Valuation Reviewer ─────────────────────────────────────────
            rodar(f"5/7 — Valuation Reviewer ({ticker} | {args.versao})",
                  [sys.executable,
                   str(AGENTS_DIR / "valuation-reviewer" / "run_valuation_reviewer.py"),
                   ticker, "--versao", args.versao])
            for ext in [".md", ".docx"]:
                p = ativo_dir / f"equity-research-{ticker}-{hoje}-{args.versao}{ext}"
                if p.exists(): arquivos_gerados.append(p)
        else:
            print(f"\n{'='*60}")
            print(f"  3-5/7 — DCF e Valuation ignorados ({ticker} é ETF)")
            print(f"{'='*60}")
    else:
        print(f"\n{'='*60}")
        print("  3-5/7 — Nenhum ticker passado; passos de ativo ignorados")
        print(f"{'='*60}")

    # ── 6. Quant/Data Engineer ────────────────────────────────────────────────
    rodar("6/7 — Quant/Data Engineer (carteira completa)",
          [sys.executable, str(AGENTS_DIR / "quant-data-engineer" / "run_quant.py")])
    quant_nota = VAULT_ROOT / "05-risk" / "snapshots" / f"quant-{hoje}.md"
    if quant_nota.exists(): arquivos_gerados.append(quant_nota)

    # ── 7. Risk Engineer ──────────────────────────────────────────────────────
    rodar("7/7 — Risk Engineer (carteira completa)",
          [sys.executable, str(AGENTS_DIR / "risk-engineer" / "run_risk_engineer.py")])
    risk_nota = VAULT_ROOT / "05-risk" / "snapshots" / f"risk-{hoje}.md"
    if risk_nota.exists(): arquivos_gerados.append(risk_nota)

    print(f"\n{'='*60}")
    print("  PIPELINE CONCLUÍDO")
    print(f"{'='*60}")
    print(f"\nArquivos gerados ({len(arquivos_gerados)}):")
    for path in arquivos_gerados:
        try:
            rel = path.relative_to(PROJECT_ROOT)
        except ValueError:
            rel = path
        print(f"  ✓ {rel}")

    print(f"\nLinks do vault:")
    for path in arquivos_gerados:
        if path.suffix == ".md":
            print(f"  [[{path.stem}]]")


if __name__ == "__main__":
    main()
