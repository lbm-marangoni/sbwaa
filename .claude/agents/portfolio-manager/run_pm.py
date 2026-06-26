"""
run_pm.py — Executa o agente Portfolio Manager do SBWAA.
Uso: python run_pm.py TICKER [--versao curta|longa]
     python run_pm.py           → modo aporte interativo
     python run_pm.py 700       → modo aporte com valor pré-definido
"""

import re
import sys
import json
import math
import argparse
import subprocess
from datetime import datetime, timedelta, date
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


def carregar_econometria(ticker: str, hoje: str) -> dict | None:
    for d in range(8):
        dt = (datetime.strptime(hoje, "%Y-%m-%d") - timedelta(days=d)).strftime("%Y-%m-%d")
        path = CACHE_DIR / f"econometria_{ticker}_{dt}.json"
        if path.exists():
            if d > 0:
                print(f"  [Econometrician] usando cache de {dt}")
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
    posicao_atual: dict | None = None,
    econometria: dict | None = None,
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

    # Bloco de posição existente (Modo B)
    pos_txt = ""
    if posicao_atual:
        peso = posicao_atual.get("peso_pct", 0)
        pl = posicao_atual.get("pl_pct", 0)
        pos_txt = f"""
═══════════════════════════════════════════════
⚠️  MODO B — ATIVO JÁ ESTÁ NA CARTEIRA:
Peso atual: {peso:.1f}% do portfólio
P&L atual: {pl:+.1f}%
→ Usar AUMENTAR / MANTER / REDUZIR / SAIR (não COMPRAR/AGUARDAR/EVITAR)
→ Indicar peso atual → peso alvo no veredicto
═══════════════════════════════════════════════
"""

    # Bloco econométrico
    eco_txt = "Não disponível — executar /analisar para gerar cache econométrico."
    if econometria:
        garch = econometria.get("garch", {})
        beta = econometria.get("beta_dinamico", {})
        ff = econometria.get("fator_model", {})
        macro_sens = econometria.get("macro_sensibilidade", {})
        dd = econometria.get("drawdown_avancado", {})
        eco_txt = (
            f"GARCH: Vol {garch.get('vol_anualizada_atual_pct','N/D')}% | "
            f"Regime {garch.get('regime_volatilidade','N/D')} | "
            f"Persistência {garch.get('persistencia','N/D')} | "
            f"Half-life {garch.get('half_life_dias','N/D')}d\n"
            f"Beta: 60d={beta.get('beta_60d','N/D')} 126d={beta.get('beta_126d','N/D')} "
            f"252d={beta.get('beta_252d','N/D')} | Tendência: {beta.get('tendencia','N/D')}\n"
            f"Fama-French: Alpha {ff.get('alpha_anualizado_pct','N/D')}%a.a. "
            f"(p={ff.get('p_valor_alpha','N/D')}) | R²={ff.get('r2_ajustado','N/D')}\n"
            f"Macro driver: {macro_sens.get('principal_driver','N/D')} | R²={macro_sens.get('r2_ajustado','N/D')}\n"
            f"Drawdown: Calmar={dd.get('calmar_ratio','N/D')} | "
            f"Ulcer={dd.get('ulcer_index_pct','N/D')}% | "
            f"Tempo médio recuperação={dd.get('tempo_medio_recuperacao_dias','N/D')}d"
        )

    modo_instrucao = (
        "3. Veredicto fundamentado: AUMENTAR / MANTER / REDUZIR / SAIR (Modo B — posição existente)"
        if posicao_atual else
        "3. Veredicto fundamentado: COMPRAR / AGUARDAR / EVITAR (Modo A — nova posição)"
    )

    return f"""DATA: {hoje}
TICKER EM ANÁLISE: {ticker}
{pos_txt}
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
ECONOMETRICIAN:
{eco_txt}

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
{modo_instrucao}
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


def montar_prompt_sizing_reducao(
    ticker: str, valor_vender: float,
    peso_atual: float, novo_peso: float,
    novo_var: float | None, novo_sharpe: float | None,
    sair_total: bool,
) -> str:
    var_txt = f"{novo_var:.2f}%" if novo_var else "N/D"
    sharpe_txt = str(novo_sharpe) if novo_sharpe else "N/D"
    if sair_total:
        return f"""O usuário confirma saída total de {ticker}.

Impacto calculado localmente:
- Posição atual: {peso_atual:.1f}% do portfólio → 0% após saída
- VaR estimado após saída: {var_txt}
- Sharpe estimado após saída: {sharpe_txt}

Emita o parecer de saída conforme Passo 5 do seu SKILL: confirme a operação,
aponte o impacto no portfólio e oriente sobre o destino do capital liberado.
"""
    return f"""O usuário planeja vender R$ {valor_vender:,.0f} de {ticker}.

Impacto calculado localmente:
- Peso atual de {ticker}: {peso_atual:.1f}% → {novo_peso:.1f}% após redução
- Novo VaR estimado 95% (1 dia): {var_txt}
- Novo Sharpe estimado: {sharpe_txt}

Emita o parecer de redução conforme Passo 5 do seu SKILL: confirme se o novo
peso alvo é adequado, aponte o impacto no portfólio e oriente sobre o capital liberado.
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
    for v in ["AUMENTAR", "MANTER", "REDUZIR", "SAIR", "COMPRAR", "AGUARDAR", "EVITAR"]:
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


# ─── MODO APORTE — constantes e helpers ──────────────────────────────────────

STALE_APORTE_DIAS = 45

TIPO_CLASSE_IPS: dict[str, str] = {
    "acao-on":    "Ações BR",
    "acao-pn":    "Ações BR",
    "fii":        "FIIs",
    "renda-fixa": "Renda Fixa",
    "tesouro":    "Tesouro Direto",
    "etf-br":     "ETFs BR",
    "etf-intl":   "ETFs Internac.",
}

CLASSE_ALVO_IPS: dict[str, float] = {
    "Ações BR":       0.25,
    "FIIs":           0.35,
    "Renda Fixa":     0.20,
    "Tesouro Direto": 0.12,
    "ETFs Internac.": 0.08,
}

CLASSE_TIPOS: dict[str, list[str]] = {
    "fii":  ["fii"],
    "acao": ["acao-on", "acao-pn"],
    "etf":  ["etf-br", "etf-intl"],
    "rf":   ["renda-fixa", "tesouro"],
}


def _frontmatter_simples(texto: str) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---", texto, re.DOTALL)
    if not m:
        return {}
    campos: dict = {}
    for linha in m.group(1).splitlines():
        if ":" in linha:
            k, _, v = linha.partition(":")
            campos[k.strip().lower()] = v.strip().strip('"').strip("'")
    return campos


def _ultima_analise_ativo(ticker: str) -> tuple[str | None, date | None, str | None, bool]:
    """Retorna (veredicto, data, tipo, tem_analise_completa)."""
    pasta = ATIVOS_DIR / ticker
    if not pasta.exists():
        return None, None, None, False

    tem_completa = (
        any(pasta.glob("equity-research-*.md"))
        or any(pasta.glob("analise-*.md"))
    )
    arquivos = sorted(pasta.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    veredicto: str | None = None
    data_obj: date | None = None
    tipo: str | None = None

    for arq in arquivos:
        texto = arq.read_text(encoding="utf-8", errors="ignore")
        fm = _frontmatter_simples(texto)
        v = fm.get("veredicto") or fm.get("decisao")
        d = fm.get("data")
        t = fm.get("tipo")
        if not v:
            for palavra in ("AUMENTAR", "COMPRAR", "MANTER", "AGUARDAR", "EVITAR", "SAIR", "REDUZIR"):
                if f"**{palavra}**" in texto or f"VEREDICTO: {palavra}" in texto:
                    v = palavra
                    break
        veredicto = veredicto or v
        tipo = tipo or t
        if d and not data_obj:
            try:
                data_obj = date.fromisoformat(d)
            except ValueError:
                pass
        if not data_obj:
            m2 = re.search(r"(\d{4}-\d{2}-\d{2})", arq.name)
            if m2:
                try:
                    data_obj = date.fromisoformat(m2.group(1))
                except ValueError:
                    pass
        if veredicto and data_obj:
            break

    return veredicto, data_obj, tipo, tem_completa


def _calcular_gaps_ips(carteira: dict, patrimonio: float) -> dict[str, float]:
    """Retorna {classe: gap_decimal} — positivo = classe subpesada."""
    alocacao: dict[str, float] = {k: 0.0 for k in CLASSE_ALVO_IPS}
    total = patrimonio if patrimonio > 0 else 1.0
    for dados in carteira.values():
        classe = TIPO_CLASSE_IPS.get(dados.get("tipo", ""), "")
        if classe in alocacao:
            alocacao[classe] += dados["qtd"] * dados["preco_atual"] / total
    return {classe: CLASSE_ALVO_IPS[classe] - alocacao[classe] for classe in CLASSE_ALVO_IPS}


def _preco_ativo(ticker: str, carteira: dict, hoje: str) -> float | None:
    if ticker in carteira:
        return carteira[ticker].get("preco_atual")
    dcf = carregar_dcf(ticker, hoje)
    if dcf:
        return dcf.get("preco_atual") or dcf.get("cotacao_atual")
    return None


def _filtrar_classe(tipo: str | None, filtro: str) -> bool:
    if filtro == "auto":
        return True
    return (tipo or "").lower() in CLASSE_TIPOS.get(filtro, [])


# ─── MODO APORTE — fluxo principal ───────────────────────────────────────────

def modo_aporte(
    versao: str, hoje: str, macro: str,
    carteira_completa: dict, patrimonio: float,
    pesos_publicos: dict, ips_conteudo: str, ips_limites: dict,
    client, skill: str,
    _params: dict | None = None,
) -> None:
    """Distribui capital entre múltiplos ativos da watchlist/carteira."""
    hoje_date = date.fromisoformat(hoje)

    print(f"\n{'═'*55}")
    print(f"  PORTFOLIO MANAGER — MODO APORTE | {hoje}")
    print(f"{'═'*55}\n")

    if _params and all(v is not None for v in _params.values()):
        valor_total   = _params["valor"]
        filtro_classe = _params["classe"]
        n_ativos      = _params["n_ativos"]
        restricoes    = _params["restricoes"]
        print(f"  ↩ Retomando: R$ {valor_total:,.0f} | classe={filtro_classe} | "
              f"n={n_ativos} ativos\n")
    else:
        pre = _params or {}

        # Valor
        if pre.get("valor") is not None:
            valor_total = pre["valor"]
            print(f"PM: Valor pré-definido: R$ {valor_total:,.0f}")
        else:
            print("PM: Qual valor você tem disponível para aporte? (R$)")
            try:
                valor_total = float(input("R$ ").strip().replace(".", "").replace(",", "."))
            except (ValueError, EOFError):
                print("Valor inválido. Encerrando.")
                return

        # Classe
        print("\nPM: Preferência de classe de ativo?")
        print("  [1] Automático pelo IPS  [2] FII  [3] Ação  [4] ETF  [5] Renda Fixa / Tesouro")
        try:
            escolha = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            escolha = "1"
        filtro_classe = {"1": "auto", "2": "fii", "3": "acao",
                         "4": "etf", "5": "rf"}.get(escolha, "auto")

        # Quantidade de ativos
        print("\nPM: Em quantos ativos diferentes quer distribuir? (ex: 3, 5)")
        try:
            n_ativos = max(1, int(input("> ").strip()))
        except (ValueError, EOFError):
            n_ativos = 3

        # Campo livre
        print("\nPM: Alguma restrição ou observação? (Enter para pular)")
        print("  Ex: 'sem XPML11', 'prefiro FIIs logística', 'nada de petróleo'")
        try:
            restricoes = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            restricoes = ""

    params_atuais = {
        "valor": valor_total, "classe": filtro_classe,
        "n_ativos": n_ativos, "restricoes": restricoes,
    }

    print(f"\n{'─'*55}")
    print("  Escaneando watchlist e carteira...")
    print(f"{'─'*55}")

    # ── Coletar todos os tickers conhecidos ──────────────────────────────────
    tickers_todos: set[str] = set(carteira_completa.keys())
    if ATIVOS_DIR.exists():
        tickers_todos |= {p.name.upper() for p in ATIVOS_DIR.iterdir() if p.is_dir()}

    candidatos_ok:       list[dict] = []
    candidatos_basic:    list[dict] = []
    sem_analise:         list[str]  = []
    ignorados:           set[str]   = set()
    veredicto_inelegivel: set[str]  = set()   # analisado mas EVITAR/AGUARDAR/MANTER

    gaps_ips = _calcular_gaps_ips(carteira_completa, patrimonio)
    em_carteira_set = set(carteira_completa.keys())

    for ticker in sorted(tickers_todos):
        # Restrições textuais (ex: "sem XPML11")
        if restricoes and ticker.upper() in restricoes.upper():
            ignorados.add(ticker)
            continue

        veredicto, data_analise, tipo, tem_completa = _ultima_analise_ativo(ticker)

        # Filtro de classe
        if not _filtrar_classe(tipo, filtro_classe):
            ignorados.add(ticker)
            continue

        # Veredictos elegíveis
        em_carteira = ticker in em_carteira_set
        veredictos_ok = {"AUMENTAR"} if em_carteira else {"COMPRAR", "AUMENTAR"}
        if not veredicto or veredicto.upper() not in veredictos_ok:
            if not veredicto:
                sem_analise.append(ticker)
            else:
                veredicto_inelegivel.add(ticker)  # tem análise, veredicto desfavorável
            continue

        dias = (hoje_date - data_analise).days if data_analise else 999
        info = {
            "ticker":      ticker,
            "veredicto":   veredicto.upper(),
            "tipo":        tipo or "",
            "em_carteira": em_carteira,
            "dias":        dias,
            "fresco":      dias <= STALE_APORTE_DIAS,
            "tem_completa": tem_completa,
            "gap_ips":     gaps_ips.get(TIPO_CLASSE_IPS.get(tipo or "", ""), 0.0),
        }
        if tem_completa:
            candidatos_ok.append(info)
        else:
            candidatos_basic.append(info)

    # ── Ranquear ──────────────────────────────────────────────────────────────
    def _score(c: dict) -> float:
        s = 3.0 if c["veredicto"] == "AUMENTAR" else 2.0
        s += max(0.0, c["gap_ips"]) * 5.0
        s += 1.0 if c["fresco"] else 0.0
        s += 1.5 if c["tem_completa"] else 0.0
        return s

    todos_candidatos = sorted(candidatos_ok + candidatos_basic, key=_score, reverse=True)
    selecionados     = todos_candidatos[:n_ativos]

    # ── Candidatos insuficientes → oferecer /analisar ─────────────────────────
    if len(selecionados) < n_ativos:
        faltam = n_ativos - len(selecionados)
        print(f"\n⚠️  Apenas {len(selecionados)} candidato(s) com análise suficiente "
              f"(solicitado: {n_ativos}).")

        # Ativos conhecidos mas sem análise completa suficiente
        # Pendentes = sem análise ou análise incompleta (exclui os que têm veredicto desfavorável)
        com_analise = {c["ticker"] for c in todos_candidatos} | ignorados | veredicto_inelegivel
        pendentes = [t for t in sorted(tickers_todos) if t not in com_analise][:faltam + 4]

        if veredicto_inelegivel:
            print(f"\n   Analisados mas veredicto desfavorável (EVITAR/AGUARDAR): "
                  f"{', '.join(sorted(veredicto_inelegivel))}")
        if pendentes:
            print(f"\n   Ativos sem análise suficiente — rode /analisar:")
            for t in pendentes:
                print(f"     - {t}  →  /analisar {t}")

        if len(selecionados) == 0:
            if veredicto_inelegivel and not pendentes:
                print("\nPM: Os ativos conhecidos foram analisados mas têm veredicto "
                      "desfavorável (EVITAR/AGUARDAR).")
                print("    Adicione novos ativos à watchlist com /analisar TICKER.\n")
            else:
                print("\nPM: Nenhum candidato disponível. Rode /analisar nos ativos de interesse "
                      "e volte com /pm.\n")
            return

        if not pendentes:
            # Faltam candidatos mas não há nada a analisar (todos inelegíveis por veredicto)
            print(f"\nPM: Continuando com os {len(selecionados)} candidatos disponíveis.")
        else:
            print(f"\nPM: Deseja rodar /analisar nesses ativos agora e retomar automaticamente?")
            print(f"    [S] Sim, analisar e retomar  "
                  f"[N] Continuar com os {len(selecionados)} disponível(is)")
        resp = "N"
        if pendentes:
            try:
                resp = input("> ").strip().upper()
            except (EOFError, KeyboardInterrupt):
                resp = "N"

        if resp == "S" and pendentes:
            analisar_script = AGENT_DIR / "run_analisar.py"
            for t in pendentes[:faltam]:
                print(f"\n{'─'*55}")
                print(f"  Iniciando /analisar {t}...")
                print(f"{'─'*55}")
                result = subprocess.run(
                    [sys.executable, str(analisar_script), t, "--versao", versao],
                    cwd=str(PROJECT_ROOT),
                )
                if result.returncode != 0:
                    print(f"\n⚠️  /analisar {t} terminou com erro — continuando.")
            print(f"\n{'─'*55}")
            print("  ✅ Análises concluídas. Retomando modo aporte...")
            print(f"{'─'*55}")
            modo_aporte(
                versao, hoje, macro, carteira_completa, patrimonio,
                pesos_publicos, ips_conteudo, ips_limites,
                client, skill, _params=params_atuais,
            )
            return

    # ── Distribuição de capital ───────────────────────────────────────────────
    n = len(selecionados)
    total_gap = sum(max(0.0, c["gap_ips"]) for c in selecionados) or 1.0

    distribuicao: list[dict] = []
    for c in selecionados:
        peso_gap   = max(0.0, c["gap_ips"]) / total_gap
        peso_final = 0.60 / n + 0.40 * peso_gap
        valor_bruto = valor_total * peso_final
        preco = _preco_ativo(c["ticker"], carteira_completa, hoje)
        if preco and preco > 0:
            cotas       = max(1, int(valor_bruto / preco))
            valor_real  = round(cotas * preco, 2)
        else:
            cotas      = None
            valor_real = round(valor_bruto, 2)
        distribuicao.append({**c, "valor": valor_real, "cotas": cotas, "preco": preco})

    # ── Prompt ao PM ──────────────────────────────────────────────────────────
    linhas_dist = "\n".join(
        f"- {d['ticker']} ({d['tipo']}): R$ {d['valor']:,.0f}"
        + (f" (~{d['cotas']} cotas @ R$ {d['preco']:.2f})" if d['cotas'] else "")
        + f" — {d['veredicto']} — gap IPS {d['gap_ips']*100:+.1f}%"
        for d in distribuicao
    )
    gaps_txt = "\n".join(
        f"  {k}: alvo {CLASSE_ALVO_IPS.get(k, 0)*100:.0f}% — gap {v*100:+.1f}%"
        for k, v in gaps_ips.items()
    )
    restricoes_txt = f"\nRestrições do usuário: {restricoes}" if restricoes else ""
    conc_max_pct   = ips_limites.get("concentracao_maxima_pct", 0.20) * 100

    prompt_aporte = f"""O usuário deseja aportar R$ {valor_total:,.0f} distribuídos entre {n} ativos.

DISTRIBUIÇÃO PROPOSTA (calculada pelo sistema):
{linhas_dist}

GAPS IPS ATUAIS (positivo = classe subpesada):
{gaps_txt}

PATRIMÔNIO ATUAL: R$ {patrimonio:,.0f}{restricoes_txt}

Sua tarefa como Portfolio Manager:
1. Valide a distribuição proposta — ajuste pesos se necessário com justificativa
2. Para cada ativo: cite o veredicto, por que faz sentido agora e o risco principal
3. Alerte se alguma alocação ultrapassar concentração máxima do IPS ({conc_max_pct:.0f}%)
4. Feche com tabela: Ticker | Valor (R$) | Cotas | Prioridade | Observação

Contexto macro:
{macro[:500] if macro else "(sem dados de mercado disponíveis)"}

IPS do investidor:
{ips_conteudo[:800]}
"""

    print(f"\n{'─'*55}")
    print("  Enviando ao Portfolio Manager (claude-opus-4-8)...")
    print(f"{'─'*55}\n")

    output_pm = ""
    with client.messages.stream(
        model="claude-opus-4-8",
        max_tokens=2000,
        system=skill,
        messages=[{"role": "user", "content": prompt_aporte}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            output_pm += text
    print(f"\n{'─'*55}\n")

    # ── Salvar decisão de aporte ──────────────────────────────────────────────
    linhas_md = "\n".join(
        f"| {d['ticker']} | {d['tipo']} | R$ {d['valor']:,.0f} | "
        + (str(d["cotas"]) if d["cotas"] else "—") + f" | {d['veredicto']} |"
        for d in distribuicao
    )
    links_ativos = "\n".join(f"- [[{d['ticker'].lower()}]]" for d in distribuicao)
    conteudo_md = f"""---
tags: [portfolio, pm-aporte, aporte]
cssclasses: [node-pm-decisao]
data: {hoje}
valor_total: {valor_total}
n_ativos: {n}
classe: {filtro_classe}
agente: portfolio-manager
---

# PM — Sugestão de Aporte | {hoje}

**Valor total:** R$ {valor_total:,.0f}
**Ativos:** {n}
**Classe:** {filtro_classe}
{"**Restrições:** " + restricoes if restricoes else ""}

## Distribuição

| Ticker | Tipo | Valor | Cotas | Veredicto |
|--------|------|-------|-------|-----------|
{linhas_md}

## Análise do PM

{output_pm}

## Links

- [[carteira]] | [[ips]] | [[decisoes]]
{links_ativos}
"""
    path_decisao = VAULT_ROOT / "00-portfolio" / f"pm-aporte-{hoje}.md"
    path_decisao.write_text(conteudo_md, encoding="utf-8")

    tickers_log = ", ".join(d["ticker"] for d in distribuicao)
    atualizar_decisoes_log(hoje, f"APORTE({tickers_log})", "APORTE", valor_total, True)

    print(f"\n{'═'*55}")
    print(f"  PM — Decisão salva: {path_decisao.relative_to(PROJECT_ROOT)}")
    print(f"  Ativos: {tickers_log}")
    print(f"{'═'*55}\n")

    # ── Loop de ajuste ────────────────────────────────────────────────────────
    print("PM: Quer ajustar a sugestão? Descreva o ajuste ou [N] para encerrar:")
    try:
        ajuste = input("> ").strip()
    except (EOFError, KeyboardInterrupt):
        ajuste = "N"

    if ajuste.upper() != "N" and ajuste:
        p_ajuste = (
            f"O usuário quer ajustar a sugestão de aporte. Pedido: '{ajuste}'. "
            f"Recalcule a distribuição de R$ {valor_total:,.0f} entre os ativos "
            f"considerando o pedido e o IPS. Apresente nova tabela com valores e cotas."
        )
        print(f"\n{'─'*55}")
        with client.messages.stream(
            model="claude-opus-4-8",
            max_tokens=1000,
            system=skill,
            messages=[
                {"role": "user",      "content": prompt_aporte},
                {"role": "assistant", "content": output_pm},
                {"role": "user",      "content": p_ajuste},
            ],
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
        print(f"\n{'─'*55}\n")


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Portfolio Manager — SBWAA")
    parser.add_argument("ticker", nargs="?", default=None)
    parser.add_argument("--versao", choices=["curta", "longa"], default="curta")
    args = parser.parse_args()

    hoje = datetime.now().strftime("%Y-%m-%d")

    # ── Detectar modo aporte (sem ticker ou ticker é um valor monetário) ──────
    ticker_arg = args.ticker
    valor_pre: float | None = None
    if ticker_arg is None:
        modo = "aporte"
    else:
        try:
            valor_pre = float(ticker_arg.replace(",", ".").replace("R$", "").strip())
            modo = "aporte"
        except ValueError:
            modo = "ticker"

    if modo == "aporte":
        macro = carregar_market_researcher(hoje)
        carteira_completa = carregar_carteira_completa()
        patrimonio = calcular_patrimonio(carteira_completa)
        pesos_publicos = carregar_carteira_publica(carteira_completa)
        ips_conteudo = IPS_PATH.read_text(encoding="utf-8") if IPS_PATH.exists() else ""
        ips_limites = carregar_limites_ips()

        import anthropic
        client = anthropic.Anthropic()
        skill = SKILL_PATH.read_text(encoding="utf-8")

        params_pre = {"valor": valor_pre, "classe": None, "n_ativos": None, "restricoes": None} \
            if valor_pre is not None else None

        modo_aporte(
            args.versao, hoje, macro, carteira_completa, patrimonio,
            pesos_publicos, ips_conteudo, ips_limites,
            client, skill, _params=params_pre,
        )
        return

    ticker = ticker_arg.upper()
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
    econometria = carregar_econometria(ticker, hoje)

    # Dados privados — ficam locais para cálculo de sizing
    carteira_completa = carregar_carteira_completa()
    patrimonio = calcular_patrimonio(carteira_completa)
    pesos_publicos = carregar_carteira_publica(carteira_completa)
    ips_conteudo = IPS_PATH.read_text(encoding="utf-8") if IPS_PATH.exists() else ""
    ips_limites = carregar_limites_ips()

    # Detectar Modo A vs Modo B
    em_carteira = ticker in carteira_completa
    posicao_atual = None
    if em_carteira:
        pos = carteira_completa[ticker]
        valor_pos = pos["qtd"] * pos["preco_atual"]
        pl_pct = (pos["preco_atual"] / pos["preco_medio"] - 1) * 100 if pos["preco_medio"] > 0 else 0.0
        peso_pct = (valor_pos / patrimonio * 100) if patrimonio > 0 else 0.0
        posicao_atual = {"peso_pct": peso_pct, "pl_pct": pl_pct, "valor": valor_pos}
        print(f"  [Modo B] {ticker} já está na carteira — {peso_pct:.1f}% | P&L {pl_pct:+.1f}%")
    else:
        print(f"  [Modo A] {ticker} não está na carteira — nova posição")

    if econometria:
        print(f"  [Econometrician] cache disponível ({econometria.get('data','?')})")
    else:
        print(f"  [Econometrician] sem cache — rodar /analisar {ticker} para gerar")

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
        posicao_atual=posicao_atual,
        econometria=econometria,
    )
    if contexto_rag:
        prompt = prompt + f"\n\n{contexto_rag}"

    print(f"Enviando ao Portfolio Manager (claude-opus-4-8)...\n")
    print("─" * 55)
    output_pm = ""
    with client.messages.stream(
        model="claude-opus-4-8",
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

    # ── Fluxo interativo (Modo A ou Modo B) ──────────────────────────────────
    print(f"{'─'*40}")
    if veredicto in ("REDUZIR", "SAIR"):
        print(f"PM: Você pretende executar a redução em {ticker}?")
        print(f"    [S] Sim  [N] Não  [D] Ainda em dúvida")
    elif veredicto == "MANTER":
        print(f"PM: Registrar decisão de MANTER {ticker}?")
        print(f"    [S] Sim  [N] Não  [D] Ainda em dúvida")
    else:
        print(f"PM: Você pretende investir em {ticker}?")
        print(f"    [S] Sim  [N] Não  [D] Ainda em dúvida")
    print(f"{'─'*40}")

    try:
        resposta = input("> ").strip().upper()
    except (EOFError, KeyboardInterrupt):
        resposta = "N"

    if resposta == "S":
        if veredicto == "SAIR":
            # Saída total
            peso_atual_pct = posicao_atual["peso_pct"] if posicao_atual else 0.0
            novo_var = estimar_novo_var(risk or {}, -peso_atual_pct / 100)
            novo_sharpe = estimar_novo_sharpe(quant or {}, comprar=False)
            p_sizing = montar_prompt_sizing_reducao(
                ticker, 0, peso_atual_pct, 0.0, novo_var, novo_sharpe, sair_total=True,
            )
            sizing_ok = True
            valor_alocado = -(posicao_atual["valor"] if posicao_atual else 0)

        elif veredicto == "REDUZIR":
            print(f"\nPM: Quanto você planeja vender? (R$)")
            try:
                valor_str = input("R$ ").strip().replace(".", "").replace(",", ".")
                valor_alocado = -float(valor_str)
            except (ValueError, EOFError):
                print("Valor inválido. Pulando cálculo de sizing.")
                valor_alocado = None

            if valor_alocado and abs(valor_alocado) > 0:
                peso_atual_pct = posicao_atual["peso_pct"] if posicao_atual else 0.0
                novo_peso_pct = max(0.0, peso_atual_pct - (abs(valor_alocado) / patrimonio * 100)) if patrimonio > 0 else 0.0
                novo_var = estimar_novo_var(risk or {}, -abs(valor_alocado) / patrimonio if patrimonio > 0 else 0)
                novo_sharpe = estimar_novo_sharpe(quant or {}, comprar=False)
                conc_max = ips_limites.get("concentracao_maxima_pct", IPS_DEFAULTS["concentracao_maxima_pct"])
                viola_ips = False
                sizing_ok = True
                p_sizing = montar_prompt_sizing_reducao(
                    ticker, abs(valor_alocado), peso_atual_pct, novo_peso_pct,
                    novo_var, novo_sharpe, sair_total=False,
                )
            else:
                p_sizing = None

        elif veredicto == "MANTER":
            print(f"\nPM: Decisão de MANTER {ticker} registrada.")
            sizing_ok = True
            p_sizing = None

        else:
            # COMPRAR ou AUMENTAR
            print(f"\nPM: Qual valor você planeja alocar? (R$)")
            try:
                valor_str = input("R$ ").strip().replace(".", "").replace(",", ".")
                valor_alocado = float(valor_str)
            except (ValueError, EOFError):
                print("Valor inválido. Pulando cálculo de sizing.")
                valor_alocado = None

            p_sizing = None
            if valor_alocado and valor_alocado > 0:
                novo_peso = calcular_novo_peso(valor_alocado, patrimonio)
                novo_var = estimar_novo_var(risk or {}, novo_peso)
                novo_sharpe = estimar_novo_sharpe(quant or {}, comprar=True)
                sizing_ideal = calcular_sizing_ideal(ips_limites, patrimonio)
                conc_max = ips_limites.get("concentracao_maxima_pct", IPS_DEFAULTS["concentracao_maxima_pct"])
                viola_ips = novo_peso > conc_max
                sizing_ok = not viola_ips and valor_alocado <= sizing_ideal * 1.05
                p_sizing = montar_prompt_sizing(
                    ticker, valor_alocado, novo_peso,
                    novo_var, novo_sharpe, sizing_ideal, ips_limites, viola_ips,
                )

        if p_sizing:
            print(f"\n{'─'*55}")
            with client.messages.stream(
                model="claude-opus-4-8",
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
            model="claude-opus-4-8",
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
