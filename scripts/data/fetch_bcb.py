"""
fetch_bcb.py — Coleta dados macro do Banco Central do Brasil (SGS API)
Uso: python scripts/data/fetch_bcb.py

Séries coletadas:
  11    — Selic Over diária (% a.d.)
  433   — IPCA mensal (% a.m.)
  1     — BRL/USD (taxa de câmbio, venda)
  24363 — IBC-Br mensal (proxy PIB, variação %)
  4392  — IPCA-15 mensal
  4189  — Taxa de juros — Selic acumulada no mês
  7326  — Spread bancário — operações de crédito (p.p.)
"""

import json
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CACHE_DIR = PROJECT_ROOT / "scripts" / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Endpoint por intervalo de datas (sem limite artificial de observações)
BCB_BASE = (
    "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"
    "?formato=json&dataInicial={inicio}&dataFinal={fim}"
)

SERIES = {
    "selic_diaria":      {"code": 11,    "anos": 3, "freq": "D", "desc": "Selic Over diária (% a.d.)"},
    "ipca_mensal":       {"code": 433,   "anos": 5, "freq": "M", "desc": "IPCA mensal (% a.m.)"},
    "brl_usd":           {"code": 1,     "anos": 3, "freq": "D", "desc": "BRL/USD taxa de câmbio (venda)"},
    "ibc_br":            {"code": 24363, "anos": 3, "freq": "M", "desc": "IBC-Br variação mensal (proxy PIB)"},
    "ipca15_mensal":     {"code": 4392,  "anos": 5, "freq": "M", "desc": "IPCA-15 mensal (% a.m.)"},
    "selic_acum_mes":    {"code": 4189,  "anos": 5, "freq": "M", "desc": "Selic acumulada no mês (% a.m.)"},
    "spread_credito":    {"code": 7326,  "anos": 5, "freq": "M", "desc": "Spread bancário crédito (p.p.)"},
}


def fetch_serie(nome: str, config: dict, hoje: date) -> list[dict]:
    inicio = (hoje - timedelta(days=config["anos"] * 365)).strftime("%d/%m/%Y")
    fim = hoje.strftime("%d/%m/%Y")
    url = BCB_BASE.format(code=config["code"], inicio=inicio, fim=fim)
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        dados = r.json()
        resultado = []
        for d in dados:
            val = d.get("valor")
            if val not in (None, "", "null"):
                try:
                    resultado.append({"data": d["data"], "valor": float(str(val).replace(",", "."))})
                except (ValueError, TypeError):
                    pass
        return resultado
    except Exception as e:
        print(f"  ⚠️  {nome}: {e}", file=sys.stderr)
        return []


def calcular_resumo(dados: list[dict], freq: str) -> dict:
    if not dados:
        return {}
    valores = [d["valor"] for d in dados]
    ultimo = dados[-1]
    anterior = dados[-2] if len(dados) >= 2 else dados[-1]
    resumo = {
        "ultimo_valor": ultimo["valor"],
        "ultima_data": ultimo["data"],
        "anterior_valor": anterior["valor"],
        "variacao_pp": round(ultimo["valor"] - anterior["valor"], 4),
    }
    if freq == "M":
        resumo["anualizado_pct"] = round(((1 + ultimo["valor"] / 100) ** 12 - 1) * 100, 2)
        ultimos_12 = valores[-12:]
        acum = 1.0
        for v in ultimos_12:
            acum *= (1 + v / 100)
        resumo["acumulado_12m_pct"] = round((acum - 1) * 100, 2)
    return resumo


def main():
    hoje = date.today()
    hoje_str = hoje.isoformat()
    saida = {
        "data_coleta": hoje_str,
        "fonte": "Banco Central do Brasil — SGS (api.bcb.gov.br)",
        "series": {}
    }

    print("Coletando dados macro — Banco Central do Brasil (SGS)")
    for nome, cfg in SERIES.items():
        print(f"  → {nome} (série {cfg['code']})...")
        dados = fetch_serie(nome, cfg, hoje)
        saida["series"][nome] = {
            "descricao": cfg["desc"],
            "frequencia": cfg["freq"],
            "n_observacoes": len(dados),
            "historico": dados,
            "resumo": calcular_resumo(dados, cfg["freq"]),
        }

    # Selic anual atual (converte % a.d. para % a.a.)
    selic_dados = saida["series"]["selic_diaria"]["historico"]
    if selic_dados:
        selic_dia = selic_dados[-1]["valor"] / 100
        saida["selic_anual_pct"] = round(((1 + selic_dia) ** 252 - 1) * 100, 2)
        saida["selic_data"] = selic_dados[-1]["data"]
    else:
        saida["selic_anual_pct"] = None

    # BRL/USD atual
    brl_dados = saida["series"]["brl_usd"]["historico"]
    if brl_dados:
        saida["brl_usd_atual"] = brl_dados[-1]["valor"]
        saida["brl_usd_data"] = brl_dados[-1]["data"]

    # IPCA acumulado 12m
    ipca_res = saida["series"]["ipca_mensal"].get("resumo", {})
    if "acumulado_12m_pct" in ipca_res:
        saida["ipca_12m_pct"] = ipca_res["acumulado_12m_pct"]

    path = CACHE_DIR / f"bcb_{hoje_str}.json"
    path.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ Salvo: {path}")

    print(f"\n  Selic anual:  {saida.get('selic_anual_pct', 'N/D')}% a.a.")
    print(f"  IPCA 12m:     {saida.get('ipca_12m_pct', 'N/D')}%")
    print(f"  BRL/USD:      {saida.get('brl_usd_atual', 'N/D')}")

    return saida


if __name__ == "__main__":
    main()
