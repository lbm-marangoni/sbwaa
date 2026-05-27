"""
fetch_investidor10.py — Dados complementares do Investidor10 (scraping).
Foco: campos que o Yahoo Finance não cobre bem para o mercado BR.
  - FIIs: P/VP, DY 12m, vacância, DPA mensal, cotas, VPA, patrimônio, liquidez
  - Ações: P/L, P/VP, LPA, VPA, DY, ROE, EV/EBITDA, liquidez

Uso: python fetch_investidor10.py XPML11 PETR4
Saída: investidor10_{TICKER}_{DATA}.json
Merge: enriquece fundamentals_{TICKER}_{DATA}.json com campos _i10_*
"""

import sys
import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)
CACHE_TTL_HORAS = 4

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://investidor10.com.br/",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


# ── helpers ───────────────────────────────────────────────────────────────────

def cache_valido(caminho: Path) -> bool:
    if not caminho.exists():
        return False
    modificado = datetime.fromtimestamp(caminho.stat().st_mtime)
    return datetime.now() - modificado < timedelta(hours=CACHE_TTL_HORAS)


def _num(texto: str) -> float | None:
    """Converte '1.234,56', 'R$ 6,47 Bilhões', '10,30%', '704.712' para float.
    Regras:
    - Se tem vírgula E ponto → BR decimal: 1.234,56 → 1234.56
    - Se tem só vírgula → BR decimal: 10,30 → 10.30
    - Se tem só ponto e parte decimal tem 3 dígitos → milhar: 704.712 → 704712
    - Bilhões/Milhões multiplicam o resultado
    """
    if not texto:
        return None
    s = texto.strip()
    mult = 1
    sl = s.lower()
    if "bilh" in sl:
        mult = 1_000_000_000
    elif "milh" in sl:
        mult = 1_000_000
    # Remove R$, %, letras e espaços — mantém dígitos, vírgula, ponto, hífen
    s = re.sub(r"[^\d,.\-]", "", s)
    if not s:
        return None
    if "," in s and "." in s:
        # Formato BR: 1.234,56
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        # Só vírgula: 10,30 ou 110,46
        s = s.replace(",", ".")
    elif "." in s:
        # Só ponto: pode ser milhar (704.712) ou decimal (0.97)
        # Se a parte após o último ponto tem exatamente 3 dígitos → milhar
        after_dot = s.rsplit(".", 1)[-1]
        if len(after_dot) == 3:
            s = s.replace(".", "")
    try:
        return float(s) * mult if s else None
    except ValueError:
        return None


def _detectar_tipo(ticker: str) -> str:
    return "fii" if ticker.upper().endswith("11") else "acao"


# ── FII ───────────────────────────────────────────────────────────────────────

def _scrape_fii(ticker: str, soup: BeautifulSoup) -> dict:
    dados: dict = {}

    # 1. Cards de destaque (div._card com class secundária específica)
    for card in soup.select("div._card"):
        classes = card.get("class", [])
        texto = card.get_text(separator="|", strip=True)
        partes = [p.strip() for p in texto.split("|") if p.strip()]
        # Pega o último token não-vazio como valor
        valor_raw = partes[-1] if partes else ""

        if "cotacao" in classes:
            dados["cotacao"] = _num(valor_raw)
        elif "dy" in classes and "DY" in texto.upper() and "VARIAÇÃO" not in texto.upper():
            dados["dy_12m_pct"] = _num(valor_raw)
        elif "vp" in classes:
            dados["pvp"] = _num(valor_raw)
        elif "val" in classes:
            dados["liquidez_diaria_str"] = valor_raw
            dados["liquidez_diaria"] = _num(valor_raw)

    # 2. Seção INFORMAÇÕES (div.cell dentro da section.box correspondente)
    for section in soup.select("section.box"):
        if "INFORMAÇÕES" not in section.get_text():
            continue
        for cell in section.select("div.cell"):
            parts = [p.strip() for p in cell.get_text(separator="|", strip=True).split("|") if p.strip()]
            if len(parts) < 2:
                continue
            label = parts[0].upper()
            valor = parts[-1]
            if "VACÂNCIA" in label or "VACANCIA" in label:
                dados["vacancia_pct"] = _num(valor)
            elif "COTAS EMITIDAS" in label:
                dados["num_cotas"] = _num(valor)
            elif "VAL. PATRIMONIAL P/ COTA" in label or "VP/COTA" in label:
                dados["vpa"] = _num(valor)
            elif "VALOR PATRIMONIAL" in label and "P/" not in label:
                dados["patrimonio_liq"] = _num(valor)
            elif "ÚLTIMO RENDIMENTO" in label or "ULTIMO RENDIMENTO" in label:
                dados["dpa_ultimo"] = _num(valor)
            elif "TAXA DE ADMINISTRAÇÃO" in label or "TAXA ADM" in label:
                dados["taxa_adm"] = valor
            elif "SEGMENTO" in label:
                dados["segmento"] = valor
            elif "TIPO DE FUNDO" in label:
                dados["tipo_fundo"] = valor
            elif "NÚMERO DE COTISTAS" in label or "NUMERO DE COTISTAS" in label:
                dados["num_cotistas"] = _num(valor)
        break  # só processa a primeira seção INFORMAÇÕES

    # 3. Tabela de dividendos: colunas [tipo | data com | pagamento | valor]
    # A página tem múltiplas tabelas — buscar a que tem as 4 colunas esperadas
    dividendos = []
    for tbl in soup.select("table"):
        ths = [th.get_text(strip=True).lower() for th in tbl.select("th")]
        # Requer exatamente as colunas da tabela de rendimentos
        if "data com" in ths and "valor" in ths and "pagamento" in ths:
            for tr in tbl.select("tbody tr")[:24]:
                cols = [td.get_text(strip=True) for td in tr.select("td")]
                if len(cols) >= 4:
                    data_com = cols[1]
                    valor = _num(cols[3])
                    if valor and valor > 0:
                        dividendos.append({"data_com": data_com, "data_pagamento": cols[2], "valor": round(valor, 6)})
            break
    if dividendos:
        dados["dividendos_mensais"] = dividendos
        dpa_12m = sum(d["valor"] for d in dividendos[:12])
        dados["dpa_anualizado"] = round(dpa_12m, 4)

    return dados


# ── AÇÃO ──────────────────────────────────────────────────────────────────────

def _scrape_acao(ticker: str, soup: BeautifulSoup) -> dict:
    dados: dict = {}

    # 1. Cards de destaque (classe secundária diferente de FIIs)
    # cotacao → cotação | pl → variação 12m | val → P/L | vp → P/VP | dy → DY
    for card in soup.select("div._card"):
        classes = card.get("class", [])
        partes = [p.strip() for p in card.get_text(separator="|", strip=True).split("|") if p.strip()]
        # Cada card tem [Label, Valor] ou só [Valor]
        if len(partes) < 2:
            continue
        label_c = partes[0].upper()
        valor_c = partes[-1]

        if "cotacao" in classes:
            dados["cotacao"] = _num(valor_c)
        elif "val" in classes and "P/L" in label_c:
            dados["pl"] = _num(valor_c)
        elif "vp" in classes and "P/VP" in label_c:
            dados["pvp"] = _num(valor_c)
        elif "dy" in classes and "DY" in label_c and "VARIAÇÃO" not in label_c:
            dados["dy_pct"] = _num(valor_c)

    # 2. Tabela de indicadores fundamentalistas (div.cell com estrutura:
    #    "Label | Valor Ativo | Setor: | Valor Setor | Subsetor: | ...")
    # O valor do ativo é sempre parts[1] (segundo elemento).
    for cell in soup.select("div.cell"):
        parts = [p.strip() for p in cell.get_text(separator="|", strip=True).split("|") if p.strip()]
        if len(parts) < 2:
            continue
        label = parts[0].upper()
        valor = parts[1]  # sempre o valor do ativo, não do setor

        if label in ("P/L",):
            dados["pl"] = dados.get("pl") or _num(valor)
        elif label in ("P/VP",):
            dados["pvp"] = dados.get("pvp") or _num(valor)
        elif label == "LPA":
            dados["lpa"] = _num(valor)
        elif label == "VPA":
            dados["vpa"] = _num(valor)
        elif label == "ROE":
            dados["roe_pct"] = _num(valor)
        elif label in ("EV/EBITDA", "EV/EBIT"):
            if "EBITDA" in label:
                dados["ev_ebitda"] = _num(valor)
        elif "MARGEM EBTIDA" in label or "MARGEM EBITDA" in label:
            dados["margem_ebitda_pct"] = _num(valor)
        elif "MARGEM LÍQUIDA" in label or "MARGEM LIQUIDA" in label:
            dados["margem_liq_pct"] = _num(valor)
        elif "MARGEM BRUTA" in label:
            dados["margem_bruta_pct"] = _num(valor)
        elif label == "PAYOUT":
            dados["payout_pct"] = _num(valor)
        elif label == "DIVIDEND YIELD":
            dados["dy_pct"] = dados.get("dy_pct") or _num(valor)
        elif "DÍVIDA LÍQUIDA/EBITDA" in label or "DIV. LÍQUIDA/EBITDA" in label:
            dados["divida_liq_ebitda"] = _num(valor)

    # 3. Liquidez diária: extrair apenas o valor numérico (ex: "R$ 2,35 B")
    for el in soup.select("span, div"):
        texto = el.get_text(strip=True)
        if "Liquidez" in texto and ("M" in texto or "B" in texto or "K" in texto):
            v = _num(texto)
            if v:
                dados.setdefault("liquidez_diaria", v)
                # Extrair só o valor (ex: "R$ 2,35 B"), descartando o label
                m = re.search(r"R\$\s*[\d.,]+\s*[KMBkmbilhõe]+", texto)
                dados.setdefault("liquidez_diaria_str", m.group(0) if m else texto[-20:].strip())
                break

    return dados


# ── interface pública ─────────────────────────────────────────────────────────

def buscar_ticker(ticker: str) -> dict:
    ticker = ticker.upper().strip()
    hoje = datetime.now().strftime("%Y-%m-%d")
    cache_path = CACHE_DIR / f"investidor10_{ticker}_{hoje}.json"

    if cache_valido(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            print(f"  [{ticker}] Usando cache ({cache_path.name})")
            return json.load(f)

    tipo = _detectar_tipo(ticker)
    url = (
        f"https://investidor10.com.br/fiis/{ticker.lower()}/"
        if tipo == "fii"
        else f"https://investidor10.com.br/acoes/{ticker.lower()}/"
    )
    print(f"  [{ticker}] Investidor10 → {url}")

    try:
        resp = SESSION.get(url, timeout=15)
        resp.raise_for_status()
    except requests.HTTPError as e:
        raise ValueError(f"HTTP {e.response.status_code} para {ticker} no Investidor10")
    except requests.RequestException as e:
        raise ValueError(f"Erro de rede no Investidor10 para {ticker}: {e}")

    soup = BeautifulSoup(resp.text, "html.parser")

    if tipo == "fii":
        campos = _scrape_fii(ticker, soup)
    else:
        campos = _scrape_acao(ticker, soup)

    dados = {
        "ticker": ticker,
        "tipo_ativo": tipo.upper(),
        "fonte": "investidor10",
        "url": url,
        "atualizado_em": datetime.now().isoformat(timespec="seconds"),
        **campos,
    }

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"  [{ticker}] OK — salvo em {cache_path.name}")
    return dados


def enriquecer_fundamentals(ticker: str) -> dict | None:
    """
    Complementa o cache fundamentals_{TICKER} com campos _i10_* do Investidor10.
    Yahoo Finance tem prioridade; apenas campos ausentes ou específicos do I10
    são adicionados com prefixo _i10_ para rastreabilidade.
    """
    ticker = ticker.upper().strip()
    hoje = datetime.now().strftime("%Y-%m-%d")
    fund_path = CACHE_DIR / f"fundamentals_{ticker}_{hoje}.json"

    if not fund_path.exists():
        print(f"  [{ticker}] Cache fundamentals não encontrado — rode fetch_fundamentals.py primeiro.")
        return None

    with open(fund_path, "r", encoding="utf-8") as f:
        fund = json.load(f)

    try:
        i10 = buscar_ticker(ticker)
    except ValueError as e:
        print(f"  [{ticker}] Investidor10 falhou: {e} — fundamentals inalterado.")
        return fund

    # Campos exclusivos do Investidor10 (não existem no Yahoo Finance)
    campos_exclusivos = [
        "vacancia_pct", "dpa_ultimo", "dpa_anualizado", "dividendos_mensais",
        "num_cotas", "num_cotistas", "taxa_adm", "segmento", "tipo_fundo",
        "liquidez_diaria", "liquidez_diaria_str",
        "lpa", "vpa", "margem_ebitda_pct", "margem_liq_pct",
        "subsetor",
    ]
    for campo in campos_exclusivos:
        if campo in i10 and i10[campo] is not None:
            fund[f"_i10_{campo}"] = i10[campo]

    # Patrimônio líquido: Yahoo Finance não tem para FIIs
    if i10.get("patrimonio_liq"):
        fund["_i10_patrimonio_liq"] = i10["patrimonio_liq"]

    # VPA por cota (importante para P/VP real de FIIs)
    if i10.get("vpa"):
        fund["_i10_vpa"] = i10["vpa"]

    # P/VP: usar Yahoo Finance se disponível; I10 como fallback
    if not fund.get("pvp") and i10.get("pvp"):
        fund["pvp"] = i10["pvp"]
        fund["pvp_fonte"] = "investidor10"

    # DY: usar Yahoo Finance se disponível; I10 12m como fallback
    if (not fund.get("dy") or fund.get("dy", 0) == 0) and i10.get("dy_12m_pct"):
        fund["dy"] = i10["dy_12m_pct"]
        fund["dy_fonte"] = "investidor10"

    fund["fontes"] = sorted({fund.get("fonte", "yahoo_finance"), "investidor10"})
    fund["atualizado_em"] = datetime.now().isoformat(timespec="seconds")

    with open(fund_path, "w", encoding="utf-8") as f:
        json.dump(fund, f, ensure_ascii=False, indent=2)
    print(f"  [{ticker}] fundamentals enriquecido com dados Investidor10.")
    return fund


# ── exibição ──────────────────────────────────────────────────────────────────

def exibir_resumo(dados: dict) -> None:
    t = dados
    sep = "=" * 54
    print(f"\n{sep}")
    print(f"  Investidor10 | {t['ticker']} ({t.get('tipo_ativo','?')})")
    if t.get("cotacao"):
        print(f"  Cotação      : R$ {t['cotacao']:.2f}")

    if t.get("tipo_ativo") == "FII":
        print(f"  P/VP         : {t.get('pvp') or '—'}")
        print(f"  DY 12m       : {t.get('dy_12m_pct') or '—'}%")
        print(f"  Vacância     : {t.get('vacancia_pct') or '—'}%")
        print(f"  VPA (p/cota) : R$ {t.get('vpa') or '—'}")
        print(f"  DPA último   : R$ {t.get('dpa_ultimo') or '—'}")
        print(f"  DPA anual.   : R$ {t.get('dpa_anualizado') or '—'}")
        print(f"  Liquidez/dia : {t.get('liquidez_diaria_str') or '—'}")
        print(f"  Segmento     : {t.get('segmento') or '—'}")
        if t.get("dividendos_mensais"):
            print("  Últimos rendimentos:")
            for d in t["dividendos_mensais"][:4]:
                print(f"    {d['data_com']}  R$ {d['valor']}")
    else:
        print(f"  P/L          : {t.get('pl') or '—'}")
        print(f"  P/VP         : {t.get('pvp') or '—'}")
        print(f"  LPA          : R$ {t.get('lpa') or '—'}")
        print(f"  VPA          : R$ {t.get('vpa') or '—'}")
        print(f"  DY           : {t.get('dy_pct') or '—'}%")
        print(f"  ROE          : {t.get('roe_pct') or '—'}%")
        print(f"  EV/EBITDA    : {t.get('ev_ebitda') or '—'}")
        print(f"  Liquidez/dia : {t.get('liquidez_diaria_str') or '—'}")
    print(sep)


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    tickers = [t.upper() for t in sys.argv[1:] if t]
    if not tickers:
        print("Uso: python fetch_investidor10.py TICKER1 TICKER2 ...")
        sys.exit(1)

    for ticker in tickers:
        print(f"\nBuscando {ticker} no Investidor10...")
        try:
            dados = buscar_ticker(ticker)
            exibir_resumo(dados)
            fund = enriquecer_fundamentals(ticker)
            if fund:
                n = sum(1 for k in fund if k.startswith("_i10_"))
                print(f"  → {n} campo(s) _i10_* adicionado(s) ao fundamentals.")
        except ValueError as e:
            print(f"  AVISO: {e}")
        time.sleep(0.5)


if __name__ == "__main__":
    main()
