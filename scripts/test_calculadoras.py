#!/usr/bin/env python3
"""Testa calculadoras Quant e Risk sem depender da API."""
import sys, importlib
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).parent.parent

# === Quant calculadoras ===
print("=== Calculadoras Quant ===")
sys.path.insert(0, str(ROOT / ".claude/agents/quant-data-engineer"))

try:
    from calculators.returns import retorno_total, volatilidade_anualizada, sharpe
    prices = pd.Series([100.0, 102, 101, 105, 103, 108])
    rt = retorno_total(prices)
    vol = volatilidade_anualizada(prices)
    sh = sharpe(0.15, 0.20, 0.1275)
    print(f"  OK returns: retorno={rt:.2%}, vol={vol:.2%}, sharpe={sh:.2f}")
except Exception as e:
    print(f"  FALHOU returns: {e}")

try:
    from calculators.portfolio_metrics import drawdown_carteira_historico, matriz_correlacao, volatilidade_carteira
    rets = pd.Series(np.random.normal(0.001, 0.015, 252))
    dd = drawdown_carteira_historico(rets)
    print(f"  OK portfolio_metrics: max_dd={dd:.2%}")
except Exception as e:
    print(f"  FALHOU portfolio_metrics: {e}")

try:
    from calculators.correlation import correlacao_media, pares_alta_correlacao
    df = pd.DataFrame(np.random.randn(100, 3), columns=["A","B","C"])
    corr_matrix = df.corr()  # correlacao_media espera matriz de correlacao
    cm = correlacao_media(corr_matrix)
    pares = pares_alta_correlacao(corr_matrix)
    print(f"  OK correlation: correlacao_media={cm:.2f}, pares_alta={len(pares)}")
except Exception as e:
    print(f"  FALHOU correlation: {e}")

# === Risk calculadoras ===
# Precisam de path separado — usar importlib para evitar conflito de packages
print("\n=== Calculadoras Risk ===")

risk_path = str(ROOT / ".claude/agents/risk-engineer")
if risk_path not in sys.path:
    sys.path.insert(0, risk_path)

# Descarregar calculators para recarregar do path risk-engineer
for mod in list(sys.modules.keys()):
    if mod.startswith("calculators"):
        del sys.modules[mod]

try:
    from calculators.var import var_historico, var_parametrico, cvar
    retornos = pd.Series(np.random.normal(0.001, 0.02, 252))
    vh = var_historico(retornos)
    vp = var_parametrico(retornos.std())
    cv = cvar(retornos)
    assert cv >= vh, "CVaR deve ser >= VaR"
    print(f"  OK var: VaR_hist={vh:.2%}, VaR_param={vp:.2%}, CVaR={cv:.2%}")
except Exception as e:
    print(f"  FALHOU var: {e}")

try:
    from calculators.stress_test import impacto_cenario, rodar_todos_cenarios, CENARIOS
    # impacto_cenario(beta_carteira, cenario_dict)
    result = impacto_cenario(beta_carteira=0.9, cenario=CENARIOS["covid_2020"])
    todos = rodar_todos_cenarios(beta_carteira=0.9)
    print(f"  OK stress_test: covid={result['impacto_pct']}%, {len(todos)} cenarios")
except Exception as e:
    print(f"  FALHOU stress_test: {e}")

print("\nTeste calculadoras concluido.")
