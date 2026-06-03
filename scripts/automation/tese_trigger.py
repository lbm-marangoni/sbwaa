"""
SBWAA Automation — Tese Trigger

Rodado pelo slot "tese" (seg-sex 08:30), 45 min após o morning automático.
Fluxo:
  1. Verifica flag logs/morning_auto_{hoje}.flag — aborta se não existir
  2. Lê morning-call-{hoje}.md e extrai tickers do "Ponto de Atenção"
  3. Para cada ticker: classifica (carteira/watchlist/novo) e roda /tese
  4. Lê veredicto do vault, calcula comando sugerido
  5. Salva logs/tese_queue_{hoje}.json
  6. Dispara tray notification com resumo

Só roda quando disparado pelo Task Scheduler (flag obrigatória).
O /morning-call manual NÃO cria o flag — nunca aciona este script.
"""

import json
import logging
import re
import sys
from datetime import date, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
VAULT = PROJECT_ROOT / "vault"
RELATORIOS_DIR = VAULT / "02-relatorios" / "diarios"
ATIVOS_DIR = VAULT / "01-ativos"
CARTEIRA_PATH = VAULT / "00-portfolio" / "carteira.md"

LOGS_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    handlers=[
        logging.FileHandler(str(LOGS_DIR / "automation.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("sbwaa.tese_trigger")

sys.path.insert(0, str(PROJECT_ROOT))
from scripts.automation.runner import run_claude
from scripts.automation.notifier import notify

TIPO_LABEL = {
    "fii":       "🟩 FII",
    "acao-on":   "🟦 AÇÃO ON",
    "acao-pn":   "🟦 AÇÃO PN",
    "etf-br":    "🟨 ETF BR",
    "etf-intl":  "🟥 ETF INTL",
    "renda-fixa": "⬜ RF",
    "tesouro":   "🟪 TD",
}


# ── Verificações de pré-condição ──────────────────────────────────────────────

def flag_existe(hoje: str) -> bool:
    return (LOGS_DIR / f"morning_auto_{hoje}.flag").exists()


# ── Extração de tickers ───────────────────────────────────────────────────────

def extrair_tickers(morning_call_path: Path) -> list[str]:
    """Extrai tickers do 'Ponto de Atenção do Dia' — seção mais curada."""
    try:
        content = morning_call_path.read_text(encoding="utf-8")
    except Exception as e:
        log.error(f"Erro ao ler morning call: {e}")
        return []

    # Localizar seção Ponto de Atenção
    secao = []
    in_section = False
    for line in content.splitlines():
        if re.match(r"#{1,3}\s+.*[Pp]onto.*[Aa]ten", line):
            in_section = True
            continue
        if in_section:
            if re.match(r"#{1,3}\s+", line):
                break
            secao.append(line)

    if not secao:
        log.warning("Seção 'Ponto de Atenção' não encontrada — verificar formato do morning call.")
        return []

    texto = "\n".join(secao)

    # Tickers: 3-6 letras maiúsculas + 1-2 dígitos (ex: XPML11, PETR4, VALE3)
    raw = re.findall(r'\b([A-Z]{3,6}[0-9]{1,2})\b', texto)

    # Deduplicar mantendo ordem
    seen: set[str] = set()
    result: list[str] = []
    for t in raw:
        if t not in seen:
            seen.add(t)
            result.append(t)

    log.info(f"Tickers extraídos do Ponto de Atenção: {result}")
    return result


# ── Classificação do ativo ────────────────────────────────────────────────────

def classificar(ticker: str) -> str:
    """Retorna 'carteira', 'watchlist' ou 'novo'."""
    try:
        content = CARTEIRA_PATH.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("|") and f"| {ticker} |" in line:
                return "carteira"
    except Exception:
        pass

    ativo_dir = ATIVOS_DIR / ticker
    if ativo_dir.exists() and any(ativo_dir.glob("*.md")):
        return "watchlist"

    return "novo"


# ── Tipo/label do ativo ───────────────────────────────────────────────────────

def detectar_label(ticker: str) -> str:
    ativo_dir = ATIVOS_DIR / ticker
    if ativo_dir.exists():
        for md in ativo_dir.glob("*.md"):
            try:
                text = md.read_text(encoding="utf-8")
                m = re.search(r'^tipo:\s*["\']?([^"\'\n]+)["\']?', text, re.MULTILINE)
                if m:
                    return TIPO_LABEL.get(m.group(1).strip().lower(), "—")
            except Exception:
                continue

    # Fallback por padrão de ticker
    if ticker.endswith("11"):
        return "🟩 FII"
    if re.match(r'^[A-Z]{4}[0-9]$', ticker):
        return "🟦 AÇÃO ON"
    return "—"


# ── Leitura do veredicto ──────────────────────────────────────────────────────

def encontrar_tese(ticker: str) -> Path | None:
    ativo_dir = ATIVOS_DIR / ticker
    if not ativo_dir.exists():
        return None
    candidatos = sorted(
        ativo_dir.glob("tese*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if candidatos:
        return candidatos[0]
    # Fallback: qualquer .md mais recente
    todos = sorted(ativo_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    return todos[0] if todos else None


def extrair_veredicto(path: Path) -> str | None:
    try:
        content = path.read_text(encoding="utf-8")
        # Buscar na metade final onde fica a seção do PM
        trecho = content[len(content) // 2:]
        patterns = [
            r'\*\*[Vv]eredicto[:\s]*\*\*\s*(COMPRAR|AGUARDAR|EVITAR)',
            r'[Vv]eredicto[:\s]+\*\*(COMPRAR|AGUARDAR|EVITAR)\*\*',
            r'(?i)(?:veredicto|decisão)[:\s]+(COMPRAR|AGUARDAR|EVITAR)',
            r'\b(COMPRAR|AGUARDAR|EVITAR)\b',
        ]
        for p in patterns:
            m = re.search(p, trecho)
            if m:
                return m.group(1).upper()
    except Exception:
        pass
    return None


# ── Cálculo do comando sugerido ───────────────────────────────────────────────

def calcular_comando(ticker: str, status: str, tese_data: str) -> str:
    try:
        dias = (date.today() - datetime.strptime(tese_data, "%Y-%m-%d").date()).days
    except Exception:
        dias = 999

    if dias >= 60 or status == "novo":
        return f"/analisar {ticker}"
    return f"/pm {ticker}"


# ── Pipeline principal ────────────────────────────────────────────────────────

def main():
    hoje = date.today().strftime("%Y-%m-%d")
    log.info(f"{'═'*60}")
    log.info(f"TESE TRIGGER | {hoje}")
    log.info(f"{'═'*60}")

    # Pré-condição: morning automático rodou hoje
    if not flag_existe(hoje):
        log.info("Flag de morning automático não encontrada — slot tese ignorado.")
        return

    # Localizar morning call de hoje
    mc_path = RELATORIOS_DIR / f"morning-call-{hoje}.md"
    if not mc_path.exists():
        log.error(f"Morning call não encontrado: {mc_path}")
        return

    tickers = extrair_tickers(mc_path)
    if not tickers:
        log.info("Nenhum ticker extraído — encerrando.")
        return

    log.info(f"Processando {len(tickers)} ticker(s): {', '.join(tickers)}")

    resultados = []

    for ticker in tickers:
        log.info(f"── /tese {ticker}")
        status = classificar(ticker)
        label = detectar_label(ticker)

        ok, _ = run_claude(f"/tese {ticker}", timeout=600, name=f"tese_{ticker}")

        if not ok:
            log.warning(f"  /tese {ticker} falhou — pulando.")
            continue

        tese_path = encontrar_tese(ticker)
        if not tese_path:
            log.warning(f"  Arquivo de tese não encontrado para {ticker}.")
            continue

        veredicto = extrair_veredicto(tese_path)
        if not veredicto:
            log.warning(f"  Veredicto não identificado em {tese_path.name}.")
            veredicto = "N/D"

        tese_data = hoje
        try:
            # Preferir data do frontmatter se disponível
            content = tese_path.read_text(encoding="utf-8")
            m = re.search(r'^data:\s*(\d{4}-\d{2}-\d{2})', content, re.MULTILINE)
            if m:
                tese_data = m.group(1)
        except Exception:
            pass

        cmd = calcular_comando(ticker, status, tese_data)

        resultados.append({
            "ticker": ticker,
            "label": label,
            "status": status,
            "veredicto": veredicto,
            "tese_data": tese_data,
            "comando_sugerido": cmd,
        })
        log.info(f"  {ticker} → veredicto={veredicto} | status={status} | cmd={cmd}")

    # Salvar fila
    queue = {
        "data": hoje,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "ativos": resultados,
    }
    queue_path = LOGS_DIR / f"tese_queue_{hoje}.json"
    queue_path.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"Fila salva: {queue_path.name}")

    # Notificação
    comprar = [r for r in resultados if r["veredicto"] == "COMPRAR"]
    total = len(resultados)
    if comprar:
        tickers_str = " · ".join(
            f"{a['ticker']} ({a['status']})" for a in comprar
        )
        notify(
            f"SBWAA — {len(comprar)}/{total} tese(s) com COMPRAR",
            f"{tickers_str}\nAbra o painel para ver os comandos",
        )
    else:
        notify(
            f"SBWAA — {total} tese(s) concluída(s)",
            "Nenhum sinal COMPRAR hoje. Ver vault para detalhes.",
        )

    log.info(f"Tese trigger concluído: {len(comprar)}/{total} COMPRAR")


if __name__ == "__main__":
    main()
