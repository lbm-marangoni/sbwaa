"""
Stress Test — SBWAA Risk Engineer
Cenários históricos e cambiais para impacto na carteira.
"""

CENARIOS = {
    "crise_2008": {
        "nome": "Crise Financeira 2008",
        "ibov_queda_pct": -41.0,
        "brl_usd_alta_pct": 40.0,
        "descricao": "IBOV -41% no ano, câmbio +40%"
    },
    "covid_2020": {
        "nome": "COVID — Março 2020",
        "ibov_queda_pct": -30.0,
        "brl_usd_alta_pct": 25.0,
        "descricao": "IBOV -30% em 30 dias"
    },
    "eleicoes_2022": {
        "nome": "Incerteza Eleitoral 2022",
        "ibov_queda_pct": -15.0,
        "brl_usd_alta_pct": 8.0,
        "descricao": "IBOV -15%, juros longos +200bps"
    },
    "lula1_2002": {
        "nome": "Crise de Confiança 2002",
        "ibov_queda_pct": -17.0,
        "brl_usd_alta_pct": 50.0,
        "descricao": "Spread soberano +800bps, câmbio +50%"
    },
    "brl_usd_mais_20": {
        "nome": "Desvalorização BRL +20% (câmbio isolado)",
        "ibov_queda_pct": 0.0,
        "brl_usd_alta_pct": 20.0,
        "descricao": "BRL enfraquece 20% vs USD — choque cambial isolado sem queda de bolsa"
    },
    "crise_fiscal_br": {
        "nome": "Crise Fiscal BR (câmbio +30%)",
        "ibov_queda_pct": -25.0,
        "brl_usd_alta_pct": 30.0,
        "descricao": "Crise doméstica: IBOV -25%, câmbio +30%, spread soberano sobe"
    },
}


def impacto_cenario(
    beta_carteira: float,
    cenario: dict,
    patrimonio_normalizado: float = 100_000.0,
    peso_intl_indireto: float = 0.0,
    peso_intl_direto: float = 0.0,
) -> dict:
    """
    Impacto estimado com duas componentes:
      - Mercado: Beta_carteira × Queda_IBOV
      - Câmbio:  exposição_USD × Alta_BRL/USD (positivo para ativos USD)

    peso_intl_indireto: fração da carteira em ETF INTL B3-BRL (ex: IVVB11)
    peso_intl_direto:   fração da carteira em ativos USD-listed (ex: SPY)
    Patrimônio normalizado: R$ 100.000 — dados privados nunca passados à API.
    """
    queda_ibov   = cenario["ibov_queda_pct"] / 100
    brl_usd_alta = cenario.get("brl_usd_alta_pct", 0) / 100

    # Componente de mercado: beta aplicado a toda a carteira
    impacto_mercado = beta_carteira * queda_ibov

    # Componente cambial: posições USD se beneficiam do BRL fraco
    # Direto (USD-listed): passthrough 100%
    # Indireto (B3 ETF INTL em BRL): passthrough ~92% (spread operacional do ETF)
    impacto_fx = (
        peso_intl_direto   * brl_usd_alta * 1.00 +
        peso_intl_indireto * brl_usd_alta * 0.92
    )

    impacto_total = impacto_mercado + impacto_fx

    return {
        "cenario":                    cenario["nome"],
        "impacto_pct":                round(impacto_total    * 100, 2),
        "impacto_mercado_pct":        round(impacto_mercado  * 100, 2),
        "impacto_fx_pct":             round(impacto_fx       * 100, 2),
        "impacto_reais_normalizado":  round(impacto_total    * patrimonio_normalizado, 2),
        "descricao":                  cenario["descricao"],
        "brl_usd_alta_pct":           cenario.get("brl_usd_alta_pct", 0),
    }


def rodar_todos_cenarios(
    beta_carteira: float,
    patrimonio_normalizado: float = 100_000.0,
    peso_intl_indireto: float = 0.0,
    peso_intl_direto: float = 0.0,
) -> dict:
    """Executa todos os cenários e retorna dict de resultados."""
    resultados = {}
    for key, cenario in CENARIOS.items():
        resultados[key] = impacto_cenario(
            beta_carteira, cenario, patrimonio_normalizado,
            peso_intl_indireto, peso_intl_direto,
        )
    return resultados
