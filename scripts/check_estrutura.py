#!/usr/bin/env python3
"""Verifica estrutura de run_analisar e SKILL.md do PM."""
from pathlib import Path
ROOT = Path(__file__).parent.parent

print("=== run_analisar: 8 etapas ===")
code = (ROOT / ".claude/agents/portfolio-manager/run_analisar.py").read_text(encoding="utf-8")
etapas = ["market_snapshot","market_researcher","earnings_reviewer","model_builder",
          "valuation_reviewer","quant","risk","run_pm"]
for e in etapas:
    ok = e in code or e.replace("_","-") in code
    print(f"  {'OK' if ok else 'FALTA'} {e}")

print("\n=== PM SKILL.md: secoes criticas ===")
skill = (ROOT / ".claude/agents/portfolio-manager/SKILL.md").read_text(encoding="utf-8")
checks = [
    ("COMPRAR/AGUARDAR/EVITAR", "COMPRAR" in skill and "AGUARDAR" in skill),
    ("Sharpe+VaR", "Sharpe" in skill and "VaR" in skill),
    ("Sizing", "sizing" in skill.lower() or "Sizing" in skill),
    ("Portfolio Manager", "Portfolio Manager" in skill),
]
for nome, ok in checks:
    print(f"  {'OK' if ok else 'FALTA'} {nome}")
