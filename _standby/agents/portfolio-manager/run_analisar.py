"""
run_analisar.py — Orquestrador do pipeline completo SBWAA (/analisar).
Uso: python run_analisar.py TICKER [--versao curta|longa] [--tipo acao|fii|etf]

Pipeline sequencial:
1. market_snapshot.py          (Fase 1) — dados de mercado
2. run_market_researcher.py    (Fase 2) — contexto macro
3. run_earnings_reviewer.py    (Fase 2) — resultados da empresa
4. run_model_builder.py        (Fase 3) — DCF completo
5. run_valuation_reviewer.py   (Fase 3) — veredicto de valuation
6. run_quant.py                (Fase 4) — métricas quantitativas
7. run_risk_engineer.py        (Fase 4) — risco da carteira
8. run_pm.py                   (Fase 5) — decisão final + interação
"""

import sys
import time
import argparse
import subprocess
from datetime import datetime, date, timedelta
from pathlib import Path

AGENT_DIR = Path(__file__).parent
PROJECT_ROOT = AGENT_DIR.parent.parent.parent
SCRIPTS_DATA = PROJECT_ROOT / "scripts" / "data"
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"
VAULT_ROOT = PROJECT_ROOT / "vault"
CACHE_DIR = SCRIPTS_DATA / "cache"
LOGS_DIR = PROJECT_ROOT / "logs"

CACHE_TTL_HORAS = 4
TOTAL = 8


def get_trimestre(d=None) -> str:
    d = d or date.today()
    ano = str(d.year)[-2:]
    if d.month <= 3:
        return f"1T{ano}"
    elif d.month <= 6:
        return f"2T{ano}"
    elif d.month <= 9:
        return f"3T{ano}"
    else:
        return f"4T{ano}"


def cache_valido(path: Path | None) -> bool:
    if not path or not path.exists():
        return False
    age_horas = (time.time() - path.stat().st_mtime) / 3600
    return age_horas < CACHE_TTL_HORAS


def rodar_etapa(num: int, descricao: str, cmd: list[str],
                cache_path: Path | None, erros: list, pular: bool = False) -> bool:
    """
    Executa uma etapa do pipeline. Usa cache se válido.
    Retorna True se bem-sucedida ou pulada intencionalmente.
    """
    if pular:
        print(f"  [{num}/{TOTAL}] {descricao:<38} ⏭️  (ignorado)")
        return True

    if cache_valido(cache_path):
        print(f"  [{num}/{TOTAL}] {descricao:<38} ⏭️  (cache < {CACHE_TTL_HORAS}h)")
        return True

    print(f"  [{num}/{TOTAL}] {descricao:<38} ⏳", flush=True)
    try:
        resultado = subprocess.run(cmd, text=True)
        if resultado.returncode != 0:
            erros.append(f"Etapa {num} ({descricao}): código {resultado.returncode}")
            print(f"  [{num}/{TOTAL}] {descricao:<38} ⚠️  ERRO (dados parciais)")
            return False
        print(f"  [{num}/{TOTAL}] {descricao:<38} ✅")
        return True
    except Exception as e:
        erros.append(f"Etapa {num} ({descricao}): {e}")
        print(f"  [{num}/{TOTAL}] {descricao:<38} ⚠️  EXCEÇÃO: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="/analisar — Pipeline completo SBWAA")
    parser.add_argument("ticker")
    parser.add_argument("--versao", choices=["curta", "longa"], default="curta")
    parser.add_argument("--tipo", choices=["acao", "fii", "etf"], default="acao")
    args = parser.parse_args()

    ticker = args.ticker.upper()
    hoje = datetime.now().strftime("%Y-%m-%d")
    trimestre = get_trimestre()
    erros: list[str] = []
    arquivos_gerados: list[Path] = []
    ativo_dir = VAULT_ROOT / "01-ativos" / ticker

    print(f"\n{'═'*55}")
    print(f"  SBWAA — /analisar {ticker}")
    print(f"  {hoje} | versao={args.versao} | tipo={args.tipo}")
    print(f"{'─'*55}\n")

    # ── 1. Market Snapshot ────────────────────────────────────────────────────
    snap_path = VAULT_ROOT / "02-relatorios" / "diarios" / f"snapshot-{hoje}.md"
    rodar_etapa(
        1, "Market Snapshot",
        [sys.executable, str(SCRIPTS_DATA / "market_snapshot.py")],
        snap_path, erros,
    )
    if snap_path.exists():
        arquivos_gerados.append(snap_path)

    # ── 2. Market Researcher ──────────────────────────────────────────────────
    mr_path = VAULT_ROOT / "03-macro" / f"market-researcher-{hoje}.md"
    rodar_etapa(
        2, "Market Researcher",
        [sys.executable, str(AGENTS_DIR / "market-researcher" / "run_market_researcher.py")],
        mr_path, erros,
    )
    if mr_path.exists():
        arquivos_gerados.append(mr_path)

    # ── 3. Earnings Reviewer ──────────────────────────────────────────────────
    er_existente = None
    if ativo_dir.exists():
        lista = sorted(ativo_dir.glob(f"earnings-{trimestre}-*.md"), reverse=True)
        er_existente = lista[0] if lista else None

    rodar_etapa(
        3, f"Earnings Reviewer ({ticker})",
        [sys.executable,
         str(AGENTS_DIR / "earnings-reviewer" / "run_earnings_reviewer.py"), ticker],
        er_existente, erros,
        pular=(args.tipo == "etf"),
    )
    if ativo_dir.exists():
        lista = sorted(ativo_dir.glob(f"earnings-{trimestre}-*.md"), reverse=True)
        if lista:
            arquivos_gerados.append(lista[0])

    # ── 4. Model Builder (DCF) ────────────────────────────────────────────────
    dcf_cache = CACHE_DIR / f"dcf_{ticker}_{hoje}.json"
    rodar_etapa(
        4, f"Model Builder DCF ({ticker})",
        [sys.executable,
         str(AGENTS_DIR / "model-builder" / "run_model_builder.py"),
         ticker, "--tipo", args.tipo],
        dcf_cache, erros,
        pular=(args.tipo == "etf"),
    )
    if ativo_dir.exists():
        xlsxs = sorted(ativo_dir.glob(f"dcf-{ticker}-v*.xlsx"), reverse=True)
        if xlsxs:
            arquivos_gerados.append(xlsxs[0])

    # ── 5. Valuation Reviewer ─────────────────────────────────────────────────
    val_existente = None
    if ativo_dir.exists():
        for v in [args.versao, "longa", "curta"]:
            p = ativo_dir / f"equity-research-{ticker}-{hoje}-{v}.md"
            if p.exists():
                val_existente = p
                break

    rodar_etapa(
        5, f"Valuation Reviewer ({ticker})",
        [sys.executable,
         str(AGENTS_DIR / "valuation-reviewer" / "run_valuation_reviewer.py"),
         ticker, "--versao", args.versao],
        val_existente, erros,
        pular=(args.tipo == "etf"),
    )
    if ativo_dir.exists():
        for ext in [".md", ".docx"]:
            p = ativo_dir / f"equity-research-{ticker}-{hoje}-{args.versao}{ext}"
            if p.exists():
                arquivos_gerados.append(p)

    # ── 6. Quant / Data Engineer ──────────────────────────────────────────────
    quant_cache = CACHE_DIR / f"quant_{hoje}.json"
    rodar_etapa(
        6, "Quant / Data Engineer",
        [sys.executable, str(AGENTS_DIR / "quant-data-engineer" / "run_quant.py")],
        quant_cache, erros,
    )
    quant_nota = VAULT_ROOT / "05-risk" / "snapshots" / f"quant-{hoje}.md"
    if quant_nota.exists():
        arquivos_gerados.append(quant_nota)

    # ── 7. Risk Engineer ──────────────────────────────────────────────────────
    risk_cache = CACHE_DIR / f"risk_{hoje}.json"
    rodar_etapa(
        7, "Risk Engineer",
        [sys.executable, str(AGENTS_DIR / "risk-engineer" / "run_risk_engineer.py")],
        risk_cache, erros,
    )
    risk_nota = VAULT_ROOT / "05-risk" / "snapshots" / f"risk-{hoje}.md"
    if risk_nota.exists():
        arquivos_gerados.append(risk_nota)

    # ── 8. Portfolio Manager (interativo) ─────────────────────────────────────
    print(f"\n  [8/{TOTAL}] Portfolio Manager — decisão final")
    print(f"{'─'*55}")
    pm_result = subprocess.run(
        [sys.executable,
         str(AGENT_DIR / "run_pm.py"),
         ticker, "--versao", args.versao],
        text=True,
    )
    if pm_result.returncode != 0:
        erros.append(f"Etapa 8 (Portfolio Manager): código {pm_result.returncode}")

    pm_path = ativo_dir / f"pm-decisao-{hoje}.md"
    if pm_path.exists():
        arquivos_gerados.append(pm_path)

    # ── Resumo final ──────────────────────────────────────────────────────────
    print(f"\n{'═'*55}")
    print(f"  Análise concluída — {ticker} | {hoje}")
    print(f"{'─'*55}")
    for path in arquivos_gerados:
        try:
            rel = path.relative_to(PROJECT_ROOT)
        except ValueError:
            rel = path
        print(f"  ✓ {rel}")

    if erros:
        print(f"\n  ⚠️  Erros ({len(erros)}):")
        for e in erros:
            print(f"     • {e}")
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_path = LOGS_DIR / f"analisar-erros-{hoje}.log"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now().isoformat()}] /analisar {ticker}\n")
            for e in erros:
                f.write(f"  {e}\n")

    print(f"{'═'*55}\n")


if __name__ == "__main__":
    main()
