"""
Stress Test — SBWAA Risk Engineer
Cenários históricos brasileiros para impacto na carteira.
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
    }
}


def impacto_cenario(beta_carteira: float,
                    cenario: dict,
                    patrimonio_normalizado: float = 100_000.0) -> dict:
    """
    Impacto estimado = Beta_carteira × Queda_IBOV × Patrimônio
    Simplificação: usa beta como sensibilidade ao mercado.
    Patrimônio normalizado: R$ 100.000 (dados privados nunca passados à API).
    """
    queda_ibov = cenario["ibov_queda_pct"] / 100
    impacto_pct = beta_carteira * queda_ibov
    impacto_reais = impacto_pct * patrimonio_normalizado

    return {
        "cenario": cenario["nome"],
        "impacto_pct": round(impacto_pct * 100, 2),
        "impacto_reais_normalizado": round(impacto_reais, 2),
        "descricao": cenario["descricao"]
    }


def rodar_todos_cenarios(beta_carteira: float,
                         patrimonio_normalizado: float = 100_000.0) -> dict:
    """Executa todos os cenários históricos e retorna dict de resultados."""
    resultados = {}
    for key, cenario in CENARIOS.items():
        resultados[key] = impacto_cenario(beta_carteira, cenario,
                                          patrimonio_normalizado)
    return resultados
