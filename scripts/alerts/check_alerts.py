"""
check_alerts.py — Verifica condições de alerta na carteira e no mercado.
Inclui: variação de ativos, circuit breakers, dividendos, correlação e preços-alvo.
Chamado pelo heartbeat, pelo slot "alerta" e manualmente.
Uso: python scripts/alerts/check_alerts.py
"""

import re
import sys
import json
from datetime import datetime, timedelta, date
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
VAULT_ROOT = PROJECT_ROOT / "vault"
SCRIPTS_DATA = PROJECT_ROOT / "scripts" / "data"
CACHE_DIR = SCRIPTS_DATA / "cache"
LOGS_DIR = PROJECT_ROOT / "logs"
CARTEIRA_PATH = VAULT_ROOT / "00-portfolio" / "carteira.md"
IPS_PATH = VAULT_ROOT / "00-portfolio" / "ips.md"
RISK_ALERTS_DIR = VAULT_ROOT / "05-risk" / "snapshots"
ALERTAS_JSON = VAULT_ROOT / "00-portfolio" / "alertas.json"
HISTORICO_MD = VAULT_ROOT / "05-risk" / "alertas-historico.md"
HISTORICO_ANCORA = "<!-- ALERTAS DISPARADOS — não editar esta linha -->"

ALERTAS_CONFIG = {
    "queda_ativo":              {"threshold_pct": 5.0,  "severidade": "ALTO"},
    "alta_ativo":               {"threshold_pct": 7.0,  "severidade": "MÉDIO"},
    "circuit_breaker_var":      {"severidade": "CRÍTICO"},
    "circuit_breaker_drawdown": {"severidade": "CRÍTICO"},
    "circuit_breaker_concentracao": {"severidade": "ALTO"},
    "earnings_amanha":          {"severidade": "MÉDIO"},
    "dividendo_proximo":        {"severidade": "BAIXO"},
    "correlacao_subiu":         {"threshold_delta": 0.15, "severidade": "MÉDIO"},
}

SEVERIDADE_ICONE = {
    "CRÍTICO": "🚨",
    "ALTO": "⚠️ ",
    "MÉDIO": "ℹ️ ",
    "BAIXO": "💡",
}

SEVERIDADE_ACAO = {
    "circuit_breaker_var":          "python sbwaa.py /risco-carteira",
    "circuit_breaker_drawdown":     "python sbwaa.py /risco-carteira",
    "circuit_breaker_concentracao": "python sbwaa.py /rebalancear",
    "queda_ativo":                  "python sbwaa.py /analisar {ticker}",
    "alta_ativo":                   "python sbwaa.py /analisar {ticker}",
    "earnings_amanha":              "python sbwaa.py /earnings {ticker}",
    "dividendo_proximo":            "python sbwaa.py /dividendos",
    "correlacao_subiu":             "python sbwaa.py /risco-carteira",
}


def carregar_json_cache(prefixo: str) -> dict | None:
    hoje = datetime.now().strftime("%Y-%m-%d")
    for d in range(4):
        dt = (datetime.strptime(hoje, "%Y-%m-%d") - timedelta(days=d)).strftime("%Y-%m-%d")
        path = CACHE_DIR / f"{prefixo}_{dt}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def parse_ips_limite(conteudo: str, pattern: str, default: float) -> float:
    m = re.search(pattern, conteudo, re.IGNORECASE)
    if m:
        try:
            val = float(m.group(1).replace(",", ".").replace("%", "").strip())
            return val / 100 if val > 1 else val
        except ValueError:
            pass
    return default


def carregar_limites_ips() -> dict:
    defaults = {"var_maximo_pct": 0.03, "drawdown_maximo_pct": 0.15, "concentracao_maxima_pct": 0.20}
    if not IPS_PATH.exists():
        return defaults
    conteudo = IPS_PATH.read_text(encoding="utf-8")
    return {
        "var_maximo_pct": parse_ips_limite(conteudo, r"VaR[^:]*:\s*([\d,\.]+)", defaults["var_maximo_pct"]),
        "drawdown_maximo_pct": parse_ips_limite(conteudo, r"[Dd]rawdown[^:]*:\s*([\d,\.]+)", defaults["drawdown_maximo_pct"]),
        "concentracao_maxima_pct": parse_ips_limite(conteudo, r"[Cc]oncentra[çc][aã]o[^:]*:\s*([\d,\.]+)", defaults["concentracao_maxima_pct"]),
    }


def parse_tickers_carteira() -> list[str]:
    if not CARTEIRA_PATH.exists():
        return []
    conteudo = CARTEIRA_PATH.read_text(encoding="utf-8")
    tickers = []
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
            if cols and cols[0] and cols[0] not in ("", "Ticker"):
                tickers.append(cols[0])
        elif dentro and not stripped.startswith("|"):
            break
    return tickers


def verificar_variacao_ativos(tickers: list[str]) -> list[dict]:
    """Verifica queda/alta significativa de ativos no dia."""
    alertas = []
    try:
        import yfinance as yf
        import re as _re

        def eh_br(t): return bool(_re.match(r"^[A-Z]{4}[0-9]{1,2}[FBP]?$", t))
        def ty(t): return f"{t}.SA" if eh_br(t) else t

        for ticker in tickers:
            try:
                info = yf.Ticker(ty(ticker)).info or {}
                var = info.get("regularMarketChangePercent") or 0
                if isinstance(var, (int, float)):
                    cfg_q = ALERTAS_CONFIG["queda_ativo"]
                    cfg_a = ALERTAS_CONFIG["alta_ativo"]
                    if var <= -cfg_q["threshold_pct"]:
                        alertas.append({
                            "tipo": "queda_ativo",
                            "severidade": cfg_q["severidade"],
                            "ticker": ticker,
                            "mensagem": f"{ticker} caiu {var:.1f}% hoje",
                        })
                    elif var >= cfg_a["threshold_pct"]:
                        alertas.append({
                            "tipo": "alta_ativo",
                            "severidade": cfg_a["severidade"],
                            "ticker": ticker,
                            "mensagem": f"{ticker} subiu {var:.1f}% hoje",
                        })
            except Exception:
                pass
    except ImportError:
        pass
    return alertas


def verificar_circuit_breakers(risk: dict, ips: dict) -> list[dict]:
    alertas = []
    cbs = risk.get("circuit_breakers", {})
    var_pct = risk.get("var_historico_95_pct")
    dd_pct = risk.get("drawdown_atual_pct", 0)
    conc_pct = risk.get("concentracao_maxima_pct", 0)
    conc_tk = risk.get("concentracao_maxima_ticker", "?")

    if var_pct and not cbs.get("var_ok", True):
        alertas.append({
            "tipo": "circuit_breaker_var",
            "severidade": "CRÍTICO",
            "ticker": None,
            "mensagem": f"VaR atual {var_pct:.2f}% > limite IPS {ips['var_maximo_pct']*100:.1f}%",
        })
    if not cbs.get("drawdown_ok", True):
        alertas.append({
            "tipo": "circuit_breaker_drawdown",
            "severidade": "CRÍTICO",
            "ticker": None,
            "mensagem": f"Drawdown {abs(dd_pct):.2f}% > limite IPS {ips['drawdown_maximo_pct']*100:.1f}%",
        })
    if not cbs.get("concentracao_ok", True):
        alertas.append({
            "tipo": "circuit_breaker_concentracao",
            "severidade": "ALTO",
            "ticker": conc_tk,
            "mensagem": f"{conc_tk} concentração {conc_pct:.1f}% > limite IPS {ips['concentracao_maxima_pct']*100:.1f}%",
        })
    return alertas


def verificar_correlacao(quant: dict) -> list[dict]:
    alertas = []
    pares = quant.get("pares_alta_correlacao", [])
    if len(pares) >= 3:
        alertas.append({
            "tipo": "correlacao_subiu",
            "severidade": "MÉDIO",
            "ticker": None,
            "mensagem": f"{len(pares)} pares com correlação alta na carteira",
        })
    return alertas


def verificar_dividendos_proximos(tickers: list[str]) -> list[dict]:
    alertas = []
    try:
        import yfinance as yf
        import re as _re
        hoje = date.today()
        prazo = hoje + timedelta(days=5)

        def eh_br(t): return bool(_re.match(r"^[A-Z]{4}[0-9]{1,2}[FBP]?$", t))
        def ty(t): return f"{t}.SA" if eh_br(t) else t

        for ticker in tickers:
            try:
                info = yf.Ticker(ty(ticker)).info or {}
                ex_ts = info.get("exDividendDate")
                if ex_ts:
                    ex_date = date.fromtimestamp(ex_ts)
                    if hoje <= ex_date <= prazo:
                        alertas.append({
                            "tipo": "dividendo_proximo",
                            "severidade": "BAIXO",
                            "ticker": ticker,
                            "mensagem": f"Data ex-dividendo de {ticker} em {ex_date.strftime('%d/%m')} ({(ex_date - hoje).days}d)",
                        })
            except Exception:
                pass
    except ImportError:
        pass
    return alertas


def registrar_log(alertas: list[dict]):
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOGS_DIR / "alerts.log"
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as f:
        for a in alertas:
            f.write(f"[{agora}] {a['severidade']:<8} | {a['tipo']:<30} | {a['mensagem']}\n")


def salvar_alerta_vault(alertas: list[dict]):
    criticos_altos = [a for a in alertas if a["severidade"] in ("CRÍTICO", "ALTO")]
    if not criticos_altos:
        return
    agora = datetime.now()
    RISK_ALERTS_DIR.mkdir(parents=True, exist_ok=True)
    nome = f"alerta-{agora.strftime('%Y-%m-%d-%H%M')}.md"
    path = RISK_ALERTS_DIR / nome
    conteudo = f"""---
tags: [alerta, risco]
cssclasses: [node-alerta]
data: {agora.strftime('%Y-%m-%d')}
hora: {agora.strftime('%H:%M')}
---

# Alertas — {agora.strftime('%Y-%m-%d %H:%M')}

"""
    for a in criticos_altos:
        icone = SEVERIDADE_ICONE.get(a["severidade"], "")
        acao = SEVERIDADE_ACAO.get(a["tipo"], "")
        if a.get("ticker"):
            acao = acao.replace("{ticker}", a["ticker"])
        conteudo += f"## {icone} {a['severidade']} — {a['mensagem']}\n"
        if acao:
            conteudo += f"→ `{acao}`\n"
        conteudo += "\n"
    conteudo += "## Links\n[[carteira]] | [[ips]]\n"
    path.write_text(conteudo, encoding="utf-8")


def exibir_alertas(alertas: list[dict]):
    if not alertas:
        print("  ✅ Nenhum alerta ativo.\n")
        return

    agora = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n{'═'*55}")
    print(f"  ⚡ ALERTAS SBWAA — {agora}")
    print(f"{'═'*55}")

    ordem = ["CRÍTICO", "ALTO", "MÉDIO", "BAIXO"]
    for sev in ordem:
        for a in alertas:
            if a["severidade"] == sev:
                icone = SEVERIDADE_ICONE.get(sev, "")
                acao = SEVERIDADE_ACAO.get(a["tipo"], "")
                if a.get("ticker"):
                    acao = acao.replace("{ticker}", a["ticker"])
                print(f"\n  {icone} {sev:<8}  {a['mensagem']}")
                if acao:
                    print(f"             → {acao}")

    print(f"\n{'═'*55}\n")


def verificar_precos_alvo() -> list[dict]:
    """Verifica alertas de preço-alvo configurados em alertas.json (gerados pelos agentes)."""
    alertas: list[dict] = []
    if not ALERTAS_JSON.exists():
        return alertas
    try:
        dados = json.loads(ALERTAS_JSON.read_text(encoding="utf-8"))
    except Exception:
        return alertas

    ativos = dados.get("alertas", [])
    if not ativos:
        return alertas

    try:
        import yfinance as yf
        import re as _re
        def eh_br(t): return bool(_re.match(r"^[A-Z]{4}[0-9]{1,2}[FBP]?$", t))
        def ty(t): return f"{t}.SA" if eh_br(t) else t
    except ImportError:
        return alertas

    disparados: list[str] = []

    for alerta in ativos:
        ticker = alerta["ticker"]
        preco_alvo = float(alerta["preco"])
        direcao = alerta["direcao"]
        try:
            info = yf.Ticker(ty(ticker)).info or {}
            cotacao = info.get("regularMarketPrice") or info.get("currentPrice")
            if not cotacao:
                continue
            cotacao = float(cotacao)
            disparou = (
                (direcao == "acima"  and cotacao >= preco_alvo) or
                (direcao == "abaixo" and cotacao <= preco_alvo)
            )
            if disparou:
                sinal = "↑" if direcao == "acima" else "↓"
                sev = "ALTO" if alerta["tipo"] == "stop" else "MÉDIO"
                alertas.append({
                    "tipo":          f"preco_alvo_{alerta['tipo']}",
                    "severidade":    sev,
                    "ticker":        ticker,
                    "mensagem":      f"{ticker} {sinal} R${cotacao:.2f} [{alerta['tipo']}] alvo R${preco_alvo:.2f} — {alerta['descricao']}",
                    "acao_sugerida": alerta.get("acao_sugerida", f"/pm {ticker}"),
                    "_alerta_id":    alerta["id"],
                    "_cotacao":      cotacao,
                    "_preco_alvo":   preco_alvo,
                })
                disparados.append(alerta["id"])
        except Exception:
            continue

    # Remove alertas one-shot disparados
    if disparados:
        dados["alertas"] = [a for a in dados["alertas"] if a["id"] not in disparados]
        ALERTAS_JSON.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

    return alertas


def adicionar_ao_historico(alertas: list[dict]):
    """Appenda alertas de preço-alvo em alertas-historico.md (formato Obsidian checkbox)."""
    preco_alertas = [a for a in alertas if a.get("tipo", "").startswith("preco_alvo_")]
    if not preco_alertas:
        return

    HISTORICO_MD.parent.mkdir(parents=True, exist_ok=True)

    if not HISTORICO_MD.exists():
        HISTORICO_MD.write_text(
            "---\ntags: [alertas, historico]\ncssclasses: [node-alertas]\n---\n\n"
            "# Alertas — Histórico\n\n"
            "> Clique no checkbox para marcar como lido. Atualizado automaticamente pelo monitor.\n\n"
            "---\n\n"
            f"{HISTORICO_ANCORA}\n",
            encoding="utf-8",
        )

    texto = HISTORICO_MD.read_text(encoding="utf-8")
    agora = datetime.now().strftime("%Y-%m-%d %H:%M")

    novas: list[str] = []
    for a in preco_alertas:
        icone = "⚠️" if a["severidade"] == "ALTO" else "ℹ️"
        tipo_label = a["tipo"].replace("preco_alvo_", "").upper()
        novas.append(f"- [ ] {agora} | {icone} {tipo_label} | {a['mensagem']} | {a['acao_sugerida']}")

    insercao = "\n".join(novas) + "\n"
    if HISTORICO_ANCORA in texto:
        texto = texto.replace(HISTORICO_ANCORA, HISTORICO_ANCORA + "\n" + insercao, 1)
    else:
        texto += "\n" + HISTORICO_ANCORA + "\n" + insercao

    HISTORICO_MD.write_text(texto, encoding="utf-8")


def _notificar(alertas: list[dict]):
    """Dispara notificação Windows para alertas CRÍTICO e ALTO."""
    urgentes = [a for a in alertas if a.get("severidade") in ("CRÍTICO", "ALTO")]
    if not urgentes:
        return
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from scripts.automation.notifier import notify  # type: ignore
        titulo = f"SBWAA — {len(urgentes)} alerta(s)"
        linhas = [
            f"{SEVERIDADE_ICONE.get(a['severidade'], '')} {a['mensagem']}"
            for a in urgentes[:3]
        ]
        if len(urgentes) > 3:
            linhas.append(f"... e mais {len(urgentes) - 3}")
        notify(titulo, "\n".join(linhas))
    except Exception:
        pass


def verificar_alertas() -> list[dict]:
    """Ponto de entrada principal — retorna lista de alertas ativos."""
    alertas = []
    tickers = parse_tickers_carteira()
    risk = carregar_json_cache("risk")
    quant = carregar_json_cache("quant")
    ips = carregar_limites_ips()

    # Circuit breakers (do risk JSON)
    if risk:
        alertas += verificar_circuit_breakers(risk, ips)

    # Variação dos ativos no dia
    if tickers:
        alertas += verificar_variacao_ativos(tickers)
        alertas += verificar_dividendos_proximos(tickers)

    # Correlação
    if quant:
        alertas += verificar_correlacao(quant)

    # Preços-alvo configurados pelos agentes
    alertas += verificar_precos_alvo()

    return alertas


def main():
    alertas = verificar_alertas()

    if alertas:
        registrar_log(alertas)
        salvar_alerta_vault(alertas)
        adicionar_ao_historico(alertas)
        _notificar(alertas)

    exibir_alertas(alertas)
    return alertas


if __name__ == "__main__":
    main()
