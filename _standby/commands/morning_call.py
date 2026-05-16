"""
morning_call.py — Briefing completo pré-abertura.
Uso: python sbwaa.py /morning-call
"""

import sys
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
VAULT_ROOT = PROJECT_ROOT / "vault"
SCRIPTS_DATA = PROJECT_ROOT / "scripts" / "data"
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"
CACHE_DIR = SCRIPTS_DATA / "cache"
ALERTS_SCRIPT = PROJECT_ROOT / "scripts" / "alerts" / "check_alerts.py"


def carregar_json_cache(prefixo: str, hoje: str, dias: int = 1) -> dict | None:
    for d in range(dias + 1):
        dt = (datetime.strptime(hoje, "%Y-%m-%d") - timedelta(days=d)).strftime("%Y-%m-%d")
        path = CACHE_DIR / f"{prefixo}_{dt}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def ler_market_researcher(hoje: str) -> str:
    path = VAULT_ROOT / "03-macro" / f"market-researcher-{hoje}.md"
    if path.exists():
        conteudo = path.read_text(encoding="utf-8")
        # Pegar apenas as primeiras linhas relevantes (sem frontmatter)
        linhas = [l for l in conteudo.splitlines() if not l.startswith("---") and l.strip()]
        return "\n".join(linhas[:30])
    return "Dados do Market Researcher não disponíveis."


def ler_snapshot(hoje: str) -> dict:
    path = VAULT_ROOT / "02-relatorios" / "diarios" / f"snapshot-{hoje}.md"
    if not path.exists():
        return {}
    conteudo = path.read_text(encoding="utf-8")
    dados = {}
    for linha in conteudo.splitlines():
        # Extrai pares chave: valor do snapshot
        m_ibov = __import__("re").search(r"IBOV[^|]*\|\s*([\d,\.]+)[^|]*\|\s*([+-][\d,\.]+%?)", linha)
        if m_ibov:
            dados["ibov"] = {"valor": m_ibov.group(1), "var": m_ibov.group(2)}
    return dados


def ler_alertas(hoje: str) -> list[str]:
    log_path = PROJECT_ROOT / "logs" / "alerts.log"
    if not log_path.exists():
        return []
    alertas = []
    for linha in log_path.read_text(encoding="utf-8").splitlines():
        if hoje in linha:
            alertas.append(linha.strip())
    return alertas[-5:]  # Últimos 5 alertas do dia


def main():
    hoje = datetime.now().strftime("%Y-%m-%d")
    hora = datetime.now().strftime("%H:%M")

    print(f"\n{'═'*55}")
    print(f"  SBWAA — Morning Call | {hoje} | {hora}")
    print(f"{'═'*55}\n")

    # ── 1. Snapshot de mercado ────────────────────────────────────────────────
    print("[1/3] Atualizando dados de mercado...")
    subprocess.run(
        [sys.executable, str(SCRIPTS_DATA / "market_snapshot.py")],
        text=True,
    )

    # ── 2. Market Researcher ──────────────────────────────────────────────────
    mr_path = VAULT_ROOT / "03-macro" / f"market-researcher-{hoje}.md"
    if not mr_path.exists():
        print("[2/3] Market Researcher...")
        subprocess.run(
            [sys.executable, str(AGENTS_DIR / "market-researcher" / "run_market_researcher.py")],
            text=True,
        )
    else:
        print("[2/3] Market Researcher (cache)...")

    # ── 3. Alertas ────────────────────────────────────────────────────────────
    if ALERTS_SCRIPT.exists():
        print("[3/3] Verificando alertas...")
        subprocess.run([sys.executable, str(ALERTS_SCRIPT)], text=True)
    else:
        print("[3/3] Verificando alertas (skipped — check_alerts.py não encontrado)")

    # ── Montar output ─────────────────────────────────────────────────────────
    snap_json = carregar_json_cache("yahoo_INDICE_BVSP", hoje, dias=0)
    risk = carregar_json_cache("risk", hoje, dias=3)
    quant = carregar_json_cache("quant", hoje, dias=3)
    mr_texto = ler_market_researcher(hoje)
    alertas = ler_alertas(hoje)

    output = f"""# Morning Call — {hoje}

## 🌍 MACRO GLOBAL

"""
    # Indices do cache Yahoo
    for symbol, label in [
        ("INDICE_GSPC", "S&P 500"),
        ("INDICE_IXIC", "NASDAQ"),
        ("INDICE_BVSP", "IBOV"),
        ("INDICE_TNX", "Juros 10Y"),
        ("DX_Y.NYB", "DXY"),
        ("BRL_X", "BRL/USD"),
        ("CL_F", "Petróleo"),
        ("GC_F", "Ouro"),
    ]:
        cache_path = CACHE_DIR / f"yahoo_{symbol}_{hoje}.json"
        if cache_path.exists():
            try:
                d = json.loads(cache_path.read_text(encoding="utf-8"))
                preco = d.get("regularMarketPrice") or d.get("price") or "—"
                var = d.get("regularMarketChangePercent") or d.get("changePercent") or 0
                var_str = f"{var:+.2f}%" if isinstance(var, (int, float)) else str(var)
                output += f"  {label:<14} {preco}  ({var_str})\n"
            except Exception:
                output += f"  {label:<14} N/D\n"

    output += f"""
## 💡 FOCO DO DIA (Market Researcher)

{mr_texto}

## 📊 CARTEIRA — MÉTRICAS HF

"""
    if risk and quant:
        cart = quant.get("carteira", {})
        output += f"  Sharpe (12m):    {cart.get('sharpe', 'N/D')}\n"
        output += f"  VaR 95%:         {risk.get('var_historico_95_pct', 'N/D')}%\n"
        output += f"  Circuit breakers: {'✅ OK' if all(risk.get('circuit_breakers', {}).values()) else '⚠️ VERIFICAR'}\n"
    else:
        output += "  Execute /risco-carteira para métricas atualizadas.\n"

    if alertas:
        output += "\n## ⚡ ALERTAS ATIVOS\n\n"
        for a in alertas:
            output += f"  {a}\n"

    output += f"\n---\n*Gerado em {hora} | SBWAA v1.6.0*\n"

    # Salvar no vault
    mc_dir = VAULT_ROOT / "02-relatorios" / "diarios"
    mc_dir.mkdir(parents=True, exist_ok=True)
    mc_path = mc_dir / f"morning-call-{hoje}.md"
    mc_path.write_text(output, encoding="utf-8")

    # Exibir resumo no terminal
    print(f"\n{'═'*55}")
    print(f"  MORNING CALL — {hoje} | {hora}")
    print(f"{'─'*55}")
    print(mr_texto[:400] if mr_texto else "  Sem dados macro disponíveis.")
    if alertas:
        print(f"\n  ⚡ {len(alertas)} alerta(s) ativo(s) — ver logs/alerts.log")
    print(f"\n  Relatório completo: {mc_path.relative_to(PROJECT_ROOT)}")
    print(f"{'═'*55}\n")


if __name__ == "__main__":
    main()
