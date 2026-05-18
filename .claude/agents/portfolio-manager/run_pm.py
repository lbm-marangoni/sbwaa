"""
run_pm.py — Executa o agente Portfolio Manager do SBWAA.
Uso: python run_pm.py TICKER [--versao curta|longa]
"""

import re
import sys
import json
import math
import argparse
from datetime import datetime, timedelta
from pathlib import Path

AGENT_DIR = Path(__file__).parent
PROJECT_ROOT = AGENT_DIR.parent.parent.parent
VAULT_ROOT = PROJECT_ROOT / "vault"
SCRIPTS_DATA = PROJECT_ROOT / "scripts" / "data"
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"
SKILL_PATH = AGENT_DIR / "SKILL.md"
CACHE_DIR = SCRIPTS_DATA / "cache"
PORTFOLIO_DIR = VAULT_ROOT / "00-portfolio"
ATIVOS_DIR = VAULT_ROOT / "01-ativos"

CARTEIRA_PATH = PORTFOLIO_DIR / "carteira.md"
IPS_PATH = PORTFOLIO_DIR / "ips.md"
DECISOES_PATH = PORTFOLIO_DIR / "decisoes.md"
PATRIMONIO_NORMALIZADO = 100_000.0

_TIPO_TAG_MAP = {
    "AÇÃO ON": "acao-on", "ACAO ON": "acao-on",
    "AÇÃO PN": "acao-pn", "ACAO PN": "acao-pn",
    "FII": "fii", "ETF BR": "etf-br", "ETF INTL": "etf-intl",
    "RF": "renda-fixa", "TD": "tesouro", "DEB": "debenture", "CRI/CRA": "cri-cra",
}


def tipo_para_tag(tipo_raw: str) -> str:
    limpo = re.sub(r"[^\w\s/]", "", tipo_raw).strip().upper()
    return _TIPO_TAG_MAP.get(limpo, "")


IPS_DEFAULTS = {
    "var_maximo_pct": 0.03,
    "drawdown_maximo_pct": 0.15,
    "concentracao_maxima_pct": 0.20,
}


# ─── Loaders ──────────────────────────────────────────────────────────────────

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
    if not IPS_PATH.exists():
        return IPS_DEFAULTS.copy()
    conteudo = IPS_PATH.read_text(encoding="utf-8")
    return {
        "var_maximo_pct": parse_ips_limite(
            conteudo, r"VaR[^:]*:\s*([\d,\.]+)", IPS_DEFAULTS["var_maximo_pct"]),
        "drawdown_maximo_pct": parse_ips_limite(
            conteudo, r"[Dd]rawdown[^:]*:\s*([\d,\.]+)", IPS_DEFAULTS["drawdown_maximo_pct"]),
        "concentracao_maxima_pct": parse_ips_limite(
            conteudo, r"[Cc]oncentra[çc][aã]o[^:]*:\s*([\d,\.]+)",
            IPS_DEFAULTS["concentracao_maxima_pct"]),
    }


def carregar_carteira_completa() -> dict:
    """
    Lê carteira.md — retorna dados completos para uso LOCAL (sizing).
    Nunca enviado à API. Retorna {ticker: {qtd, preco_medio, preco_atual, tipo}}.
    """
    if not CARTEIRA_PATH.exists():
        return {}
    conteudo = CARTEIRA_PATH.read_text(encoding="utf-8")
    resultado = {}
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
            if len(cols) >= 6 and cols[0] and cols[0] not in ("", "Ticker"):
                try:
                    t = cols[0]
                    tipo = cols[1] if len(cols) > 1 else ""
                    qtd_s = cols[3].replace(".", "").replace(",", ".") if len(cols) > 3 else "0"
                    pm_s = re.sub(r"[^\d,.]", "", cols[4]).replace(",", ".") if len(cols) > 4 else "0"
                    pa_s = re.sub(r"[^\d,.]", "", cols[5]).replace(",", ".") if len(cols) > 5 else "0"
                    qtd = float(qtd_s) if qtd_s else 0.0
                    pm = float(pm_s) if pm_s else 0.0
                    pa = float(pa_s) if pa_s else pm
                    if t and qtd > 0:
                        resultado[t] = {"qtd": qtd, "preco_medio": pm, "preco_atual": pa, "tipo": tipo}
                except (ValueError, IndexError):
                    pass
        elif dentro and not stripped.startswith("|"):
            break
    return resultado


def carregar_carteira_publica(carteira_completa: dict) -> dict:
    """Retorna apenas {ticker: peso_decimal} — seguro para enviar à API."""
    if not carteira_completa:
        return {}
    total = sum(d["qtd"] * d["preco_atual"] for d in carteira_completa.values())
    if total <= 0:
        return {t: 0.0 for t in carteira_completa}
    return {t: round(d["qtd"] * d["preco_atual"] / total, 4) for t, d in carteira_completa.items()}


def calcular_patrimonio(carteira: dict) -> float:
    return sum(d["qtd"] * d["preco_atual"] for d in carteira.values())


def carregar_json_cache(prefixo: str, hoje: str, dias_atras: int = 3) -> dict | None:
    for d in range(dias_atras + 1):
        dt = (datetime.strptime(hoje, "%Y-%m-%d") - timedelta(days=d)).strftime("%Y-%m-%d")
        path = CACHE_DIR / f"{prefixo}_{dt}.json"
        if path.exists():
            if d > 0:
                print(f"  [{prefixo}] usando cache de {dt}")
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def carregar_dcf(ticker: str, hoje: str) -> dict | None:
    for d in range(8):
        dt = (datetime.strptime(hoje, "%Y-%m-%d") - timedelta(days=d)).strftime("%Y-%m-%d")
        path = CACHE_DIR / f"dcf_{ticker}_{dt}.json"
        if path.exists():
            if d > 0:
                print(f"  [DCF] usando cache de {dt}")
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def carregar_market_researcher(hoje: str) -> str:
    for d in range(4):
        dt = (datetime.strptime(hoje, "%Y-%m-%d") - timedelta(days=d)).strftime("%Y-%m-%d")
        path = VAULT_ROOT / "03-macro" / f"market-researcher-{dt}.md"
        if path.exists():
            if d > 0:
                print(f"  [Market Researcher] usando {dt}")
            return path.read_text(encoding="utf-8")[:2000]
    return ""


def carregar_earnings(ticker: str) -> str:
    ativo_dir = ATIVOS_DIR / ticker
    if not ativo_dir.exists():
        return ""
    arquivos = sorted(ativo_dir.glob("earnings-*.md"), reverse=True)
    return arquivos[0].read_text(encoding="utf-8")[:2000] if arquivos else ""


def carregar_valuation(ticker: str, hoje: str, versao: str = "curta") -> str:
    ativo_dir = ATIVOS_DIR / ticker
    if not ativo_dir.exists():
        return ""
    for v in ([versao, "longa", "curta"] if versao != "longa" else ["longa", "curta"]):
        for d in range(8):
            dt = (datetime.strptime(hoje, "%Y-%m-%d") - timedelta(days=d)).strftime("%Y-%m-%d")
            path = ativo_dir / f"equity-research-{ticker}-{dt}-{v}.md"
            if path.exists():
                if d > 0:
                    print(f"  [Valuation] usando {dt}-{v}")
                return path.read_text(encoding="utf-8")[:3000]
    return ""


# ─── Cálculos de sizing (locais — nunca enviados à API) ───────────────────────

def calcular_novo_peso(valor_novo: float, patrimonio: float) -> float:
    total = patrimonio + valor_novo
    return valor_novo / total if total > 0 else 0.0


def estimar_novo_var(risk_data: dict, novo_peso_adicional: float) -> float | None:
    var = risk_data.get("var_historico_95_pct") or risk_data.get("var_parametrico_95_pct")
    if var is None:
        return None
    fator = 1 + novo_peso_adicional * 0.5
    return round(var * fator, 3)


def estimar_novo_sharpe(quant_data: dict, comprar: bool) -> float | None:
    sharpe = (quant_data.get("carteira") or {}).get("sharpe")
    if sharpe is None:
        return None
    delta = 0.03 if comprar else -0.03
    return round(sharpe + delta, 3)


def calcular_sizing_ideal(ips: dict, patrimonio: float) -> float:
    ref = patrimonio if patrimonio > 0 else PATRIMONIO_NORMALIZADO
    conc_max = ips.get("concentracao_maxima_pct", IPS_DEFAULTS["concentracao_maxima_pct"])
    var_max = ips.get("var_maximo_pct", IPS_DEFAULTS["var_maximo_pct"])
    por_concentracao = ref * conc_max
    por_var = ref * var_max * 5
    return min(por_concentracao, por_var)


# ─── Formatação do prompt ─────────────────────────────────────────────────────

def montar_prompt_pm(
    ticker: str, hoje: str,
    macro: str, earnings: str,
    dcf: dict | None, valuation: str,
    quant: dict | None, risk: dict | None,
    pesos_publicos: dict, ips_conteudo: str,
) -> str:
    def pct(v):
        return f"{v:.2f}%" if v is not None else "N/D"

    # DCF
    dcf_txt = "Não disponível — executar run_model_builder.py"
    if dcf:
        cen = dcf.get("cenarios", {})
        base = cen.get("base", {})
        pess = cen.get("pessimista", {})
        otim = cen.get("otimista", {})
        dcf_txt = (
            f"Preço atual: R$ {dcf.get('preco_atual', 'N/D')}\n"
            f"Valor justo base: R$ {base.get('valor_justo', 'N/D')} | Upside: {base.get('upside_pct', 'N/D')}%\n"
            f"Valor justo pessimista: R$ {pess.get('valor_justo', 'N/D')} | Upside: {pess.get('upside_pct', 'N/D')}%\n"
            f"Valor justo otimista: R$ {otim.get('valor_justo', 'N/D')} | Upside: {otim.get('upside_pct', 'N/D')}%\n"
            f"WACC: {dcf.get('wacc_base', 'N/D')} | g perpetuidade: {dcf.get('g_perpetuidade', 'N/D')}"
        )

    # Quant
    quant_txt = "Não disponível — executar run_quant.py"
    if quant:
        cart = quant.get("carteira", {})
        quant_txt = (
            f"Sharpe: {cart.get('sharpe', 'N/D')} | Volatilidade: {pct(cart.get('volatilidade_pct'))} "
            f"| Beta IBOV: {cart.get('beta_ibov', 'N/D')}\n"
            f"Drawdown máximo: {pct(cart.get('drawdown_maximo_pct'))} | HHI: {cart.get('hhi', 'N/D')}\n"
            f"Correlação média: {cart.get('corr_media', 'N/D')}"
        )

    # Risk
    risk_txt = "Não disponível — executar run_risk_engineer.py"
    if risk:
        cbs = risk.get("circuit_breakers", {})
        flags = "\n".join(f"  {f}" for f in risk.get("flags_pm", []))
        risk_txt = (
            f"VaR 95% histórico: {pct(risk.get('var_historico_95_pct'))} | "
            f"CVaR: {pct(risk.get('cvar_95_pct'))}\n"
            f"Concentração máxima: {risk.get('concentracao_maxima_ticker', 'N/D')} = "
            f"{pct(risk.get('concentracao_maxima_pct'))}\n"
            f"Circuit breakers: VaR={'✅' if cbs.get('var_ok') else '🚨'} "
            f"DD={'✅' if cbs.get('drawdown_ok') else '🚨'} "
            f"Conc={'✅' if cbs.get('concentracao_ok') else '🚨'}\n"
            f"Flags:\n{flags}"
        )

    pesos_txt = json.dumps(pesos_publicos, ensure_ascii=False, indent=2) if pesos_publicos else "Carteira vazia."

    return f"""DATA: {hoje}
TICKER EM ANÁLISE: {ticker}

═══════════════════════════════════════════════
CONTEXTO MACRO (Market Researcher):
{macro if macro else "Não disponível — executar run_market_researcher.py"}

═══════════════════════════════════════════════
RESULTADOS TRIMESTRAIS (Earnings Reviewer):
{earnings if earnings else "Não disponível — executar run_earnings_reviewer.py"}

═══════════════════════════════════════════════
MODELO DCF (Model Builder):
{dcf_txt}

═══════════════════════════════════════════════
VEREDICTO DE VALUATION (Valuation Reviewer):
{valuation if valuation else "Não disponível — executar run_valuation_reviewer.py"}

═══════════════════════════════════════════════
MÉTRICAS QUANTITATIVAS (Quant/Data Engineer):
{quant_txt}

═══════════════════════════════════════════════
RISCO E CIRCUIT BREAKERS (Risk Engineer):
{risk_txt}

═══════════════════════════════════════════════
COMPOSIÇÃO DA CARTEIRA (pesos públicos — sem valores absolutos):
{pesos_txt}

IPS (RESUMO):
{ips_conteudo[:800] if ips_conteudo else "IPS não preenchido — usar defaults conservadores."}

═══════════════════════════════════════════════

Siga o processo do seu SKILL exatamente — Passos 1 a 4:
1. Leitura crítica de cada agente (contradições, nível de confiança)
2. Confronto com portfólio atual
3. Veredicto fundamentado: COMPRAR / AGUARDAR / EVITAR
4. Bloco de métricas HF (use os dados acima; valor em R$ 100k normalizado)

NÃO emita perguntas ao usuário — o fluxo interativo é conduzido pelo script.
"""


def montar_prompt_sizing(
    ticker: str, valor_novo: float,
    novo_peso: float, novo_var: float | None, novo_sharpe: float | None,
    sizing_ideal: float, ips: dict, viola_ips: bool,
) -> str:
    var_txt = f"{novo_var:.2f}%" if novo_var else "N/D"
    sharpe_txt = str(novo_sharpe) if novo_sharpe else "N/D"
    conc_max_pct = ips.get("concentracao_maxima_pct", IPS_DEFAULTS["concentracao_maxima_pct"]) * 100
    return f"""O usuário planeja alocar R$ {valor_novo:,.0f} em {ticker}.

Impacto calculado localmente:
- Nova concentração de {ticker}: {novo_peso*100:.1f}%
- Novo VaR estimado 95% (1 dia): {var_txt}
- Novo Sharpe estimado: {sharpe_txt}
- Viola limite de concentração IPS ({conc_max_pct:.0f}%): {'SIM 🚨' if viola_ips else 'Não ✅'}

Sizing ideal calculado pelo sistema: R$ {sizing_ideal:,.0f} ({sizing_ideal / (sizing_ideal + 1) * 100:.1f}% do portfólio)

Com base nesses dados, emita o parecer de sizing conforme Passo 5 do seu SKILL.
Se o valor está acima do ideal, diga explicitamente e por quanto.
"""


def montar_prompt_duvida(ticker: str, ponto: str) -> str:
    pontos = {"1": "Valuation", "2": "Risco", "3": "Timing", "4": "Outro"}
    label = pontos.get(ponto, "Outro")
    return (
        f"O usuário está em dúvida sobre {label} de {ticker}. "
        f"Com base em toda a análise que você já realizou, responda especificamente a esse ponto "
        f"com dados concretos. Seja direto. Não repita o veredicto completo."
    )


# ─── Persistência ─────────────────────────────────────────────────────────────

def extrair_veredicto(texto: str) -> str:
    for v in ["COMPRAR", "AGUARDAR", "EVITAR"]:
        if v in texto.upper():
            return v
    return "—"


def salvar_decisao(ticker: str, hoje: str, conteudo: str) -> Path:
    ativo_dir = ATIVOS_DIR / ticker
    ativo_dir.mkdir(parents=True, exist_ok=True)
    path = ativo_dir / f"pm-decisao-{hoje}.md"
    path.write_text(conteudo, encoding="utf-8")
    return path


def atualizar_decisoes_log(hoje: str, ticker: str, veredicto: str,
                           valor: float | None, sizing_ok: bool | None):
    if not DECISOES_PATH.exists():
        return
    valor_txt = f"R$ {valor:,.0f}" if valor else "—"
    sizing_txt = "✅" if sizing_ok is True else ("⚠️" if sizing_ok is False else "—")
    nova_linha = f"| {hoje} | {ticker} | — | {veredicto} | {valor_txt} | {sizing_txt} | [[pm-decisao-{hoje}]] |"
    conteudo = DECISOES_PATH.read_text(encoding="utf-8")
    placeholder = "|      |        |      |           |            |           |       |"
    if placeholder in conteudo:
        conteudo = conteudo.replace(placeholder, nova_linha, 1)
    else:
        conteudo = conteudo.rstrip() + f"\n{nova_linha}\n"
    DECISOES_PATH.write_text(conteudo, encoding="utf-8")


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Portfolio Manager — SBWAA")
    parser.add_argument("ticker")
    parser.add_argument("--versao", choices=["curta", "longa"], default="curta")
    args = parser.parse_args()

    ticker = args.ticker.upper()
    hoje = datetime.now().strftime("%Y-%m-%d")

    print(f"\n{'═'*55}")
    print(f"  PORTFOLIO MANAGER — {ticker} | {hoje}")
    print(f"{'═'*55}\n")

    # ── Carregar todos os inputs ──────────────────────────────────────────────
    print("Carregando inputs dos agentes...")
    macro = carregar_market_researcher(hoje)
    earnings = carregar_earnings(ticker)
    dcf = carregar_dcf(ticker, hoje)
    valuation = carregar_valuation(ticker, hoje, args.versao)
    quant = carregar_json_cache("quant", hoje)
    risk = carregar_json_cache("risk", hoje)

    # Dados privados — ficam locais para cálculo de sizing
    carteira_completa = carregar_carteira_completa()
    patrimonio = calcular_patrimonio(carteira_completa)
    pesos_publicos = carregar_carteira_publica(carteira_completa)
    ips_conteudo = IPS_PATH.read_text(encoding="utf-8") if IPS_PATH.exists() else ""
    ips_limites = carregar_limites_ips()

    # Alertas sobre dados faltantes
    faltando = [
        nome for nome, dado in [
            ("Market Researcher", macro),
            ("Earnings Reviewer", earnings),
            ("Model Builder (DCF)", dcf),
            ("Valuation Reviewer", valuation),
            ("Quant/Data Engineer", quant),
            ("Risk Engineer", risk),
        ] if not dado
    ]
    if faltando:
        print(f"\n⚠️  Dados ausentes: {', '.join(faltando)}")
        print("   PM emitirá veredicto com confiança reduzida.\n")

    # ── RAG: buscar contexto amplo: macro + setor + tese ─────────────────────
    import sys as _sys
    _sys.path.insert(0, str(PROJECT_ROOT))
    contexto_rag = ""
    try:
        from knowledge.retriever import buscar, formatar_contexto_para_agente, base_disponivel
        if base_disponivel():
            setor_pm = ""
            if dcf:
                setor_pm = dcf.get("setor", "")
            query_pm = f"investimento {ticker} {setor_pm} risco retorno portfólio"
            chunks = buscar(query_pm, n_resultados=5)
            contexto_rag = formatar_contexto_para_agente(chunks, max_tokens=2000)
    except Exception:
        pass

    # ── Enviar ao PM (streaming) ──────────────────────────────────────────────
    import anthropic
    client = anthropic.Anthropic()
    skill = SKILL_PATH.read_text(encoding="utf-8")
    prompt = montar_prompt_pm(
        ticker, hoje, macro, earnings,
        dcf, valuation, quant, risk,
        pesos_publicos, ips_conteudo,
    )
    if contexto_rag:
        prompt = prompt + f"\n\n{contexto_rag}"

    print(f"Enviando ao Portfolio Manager (claude-opus-4-6)...\n")
    print("─" * 55)
    output_pm = ""
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=3000,
        system=skill,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            output_pm += text
    print(f"\n{'─'*55}\n")

    veredicto = extrair_veredicto(output_pm)
    sizing_output = ""
    valor_alocado = None
    sizing_ok = None

    # ── Fluxo interativo ──────────────────────────────────────────────────────
    print(f"{'─'*40}")
    print(f"PM: Você pretende investir em {ticker}?")
    print(f"    [S] Sim  [N] Não  [D] Ainda em dúvida")
    print(f"{'─'*40}")

    try:
        resposta = input("> ").strip().upper()
    except (EOFError, KeyboardInterrupt):
        resposta = "N"

    if resposta == "S":
        print(f"\nPM: Qual valor você planeja alocar? (R$)")
        try:
            valor_str = input("R$ ").strip().replace(".", "").replace(",", ".")
            valor_alocado = float(valor_str)
        except (ValueError, EOFError):
            print("Valor inválido. Pulando cálculo de sizing.")
            valor_alocado = None

        if valor_alocado and valor_alocado > 0:
            novo_peso = calcular_novo_peso(valor_alocado, patrimonio)
            novo_var = estimar_novo_var(risk or {}, novo_peso)
            novo_sharpe = estimar_novo_sharpe(quant or {}, comprar=(veredicto == "COMPRAR"))
            sizing_ideal = calcular_sizing_ideal(ips_limites, patrimonio)
            conc_max = ips_limites.get("concentracao_maxima_pct", IPS_DEFAULTS["concentracao_maxima_pct"])
            viola_ips = novo_peso > conc_max
            sizing_ok = not viola_ips and valor_alocado <= sizing_ideal * 1.05

            p_sizing = montar_prompt_sizing(
                ticker, valor_alocado, novo_peso,
                novo_var, novo_sharpe, sizing_ideal, ips_limites, viola_ips,
            )
            print(f"\n{'─'*55}")
            with client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=600,
                system=skill,
                messages=[
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": output_pm},
                    {"role": "user", "content": p_sizing},
                ],
            ) as stream:
                for text in stream.text_stream:
                    print(text, end="", flush=True)
                    sizing_output += text
            print(f"\n{'─'*55}\n")

    elif resposta == "N":
        print(f"\nPM: Registrado. A análise de {ticker} fica salva no vault.")
        print(f"    Execute /analisar {ticker} novamente quando quiser revisitar.\n")

    elif resposta == "D":
        print(f"\nPM: Entendido. O que está pesando na sua decisão?")
        print(f"    [1] Valuation  [2] Risco  [3] Timing  [4] Outro")
        try:
            ponto = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            ponto = "4"
        p_duvida = montar_prompt_duvida(ticker, ponto)
        print(f"\n{'─'*55}")
        with client.messages.stream(
            model="claude-opus-4-6",
            max_tokens=600,
            system=skill,
            messages=[
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": output_pm},
                {"role": "user", "content": p_duvida},
            ],
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
        print(f"\n{'─'*55}\n")

    # ── Salvar decisão no vault ───────────────────────────────────────────────
    tipo_raw = carteira_completa.get(ticker, {}).get("tipo", "")
    tipo_tag = tipo_para_tag(tipo_raw)
    tags_list = f"relatorio, pm-decisao, {ticker.lower()}" + (f", {tipo_tag}" if tipo_tag else "")
    conteudo_md = f"""---
tags: [{tags_list}]
cssclasses: [node-pm-decisao]
data: {hoje}
ticker: {ticker}
veredicto: {veredicto}
agente: portfolio-manager
---

{output_pm}
"""
    if sizing_output:
        conteudo_md += f"\n## 🎯 Sizing\n\n{sizing_output}\n"

    conteudo_md += f"""
## Links

- [[carteira]] | [[ips]] | [[decisoes]]
- [[market-researcher-{hoje}]]
- [[equity-research-{ticker.lower()}-{hoje}-{args.versao}]]
- [[risk-{hoje}]]
"""

    path_salvo = salvar_decisao(ticker, hoje, conteudo_md)
    atualizar_decisoes_log(hoje, ticker, veredicto, valor_alocado, sizing_ok)

    print(f"\n{'═'*55}")
    print(f"  PM — Decisão salva: {path_salvo.relative_to(PROJECT_ROOT)}")
    print(f"  Veredicto: {veredicto}")
    print(f"{'═'*55}\n")


if __name__ == "__main__":
    main()
