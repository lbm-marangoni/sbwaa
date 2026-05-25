#!/usr/bin/env python3
"""SBWAA — Diagnóstico de scripts."""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

scripts_necessarios = {
    "scripts/data/fetch_fundamentals.py": "Busca dados BR via Yahoo Finance",
    "scripts/data/fetch_yahoo.py": "Busca dados globais via Yahoo",
    "scripts/data/update_carteira.py": "Atualiza cotacoes na carteira",
    "scripts/data/add_ativo.py": "Adiciona ativo a carteira",
    "scripts/data/market_snapshot.py": "Snapshot diario de mercado",
    ".claude/agents/market-researcher/SKILL.md": "SKILL do Market Researcher",
    ".claude/agents/market-researcher/run_market_researcher.py": "Runner Market Researcher",
    ".claude/agents/earnings-reviewer/SKILL.md": "SKILL do Earnings Reviewer",
    ".claude/agents/earnings-reviewer/run_earnings_reviewer.py": "Runner Earnings Reviewer",
    ".claude/agents/model-builder/SKILL.md": "SKILL do Model Builder",
    ".claude/agents/model-builder/run_model_builder.py": "Runner Model Builder",
    ".claude/agents/valuation-reviewer/SKILL.md": "SKILL Valuation Reviewer",
    ".claude/agents/valuation-reviewer/run_valuation_reviewer.py": "Runner Valuation",
    ".claude/agents/quant-data-engineer/SKILL.md": "SKILL Quant",
    ".claude/agents/quant-data-engineer/run_quant.py": "Runner Quant",
    ".claude/agents/quant-data-engineer/calculators/returns.py": "Calculadora retornos",
    ".claude/agents/quant-data-engineer/calculators/portfolio_metrics.py": "Metricas portfolio",
    ".claude/agents/quant-data-engineer/calculators/correlation.py": "Correlacao",
    ".claude/agents/risk-engineer/SKILL.md": "SKILL Risk Engineer",
    ".claude/agents/risk-engineer/run_risk_engineer.py": "Runner Risk",
    ".claude/agents/risk-engineer/calculators/var.py": "Calculadora VaR/CVaR",
    ".claude/agents/risk-engineer/calculators/stress_test.py": "Stress test",
    ".claude/agents/portfolio-manager/SKILL.md": "SKILL Portfolio Manager",
    ".claude/agents/portfolio-manager/run_pm.py": "Runner PM",
    ".claude/agents/portfolio-manager/run_analisar.py": "Orquestrador /analisar",
    ".claude/commands/morning_call.py": "Comando /morning-call",
    ".claude/commands/mundo_economico.py": "Comando /mundo-economico",
    ".claude/commands/investimento_do_dia.py": "Comando /investimento-do-dia",
    ".claude/commands/carteira.py": "Comando /carteira",
    ".claude/commands/risco_carteira.py": "Comando /risco-carteira",
    ".claude/commands/relatorio_semanal.py": "Comando /relatorio-semanal",
    ".claude/commands/relatorio_mensal.py": "Comando /relatorio-mensal",
    ".claude/commands/stress_test.py": "Comando /stress-test",
    ".claude/commands/rebalancear.py": "Comando /rebalancear",
    ".claude/commands/dividendos.py": "Comando /dividendos",
    ".claude/commands/tese.py": "Comando /tese",
    ".claude/commands/ips.py": "Comando /ips",
    ".claude/commands/comparar.py": "Comando /comparar",
    "scripts/heartbeat/heartbeat.py": "Heartbeat automatico",
    "scripts/heartbeat/schedule_heartbeat.py": "Agendador heartbeat",
    "scripts/alerts/check_alerts.py": "Sistema de alertas",
    "scripts/run_research_pipeline.py": "Pipeline integrado",
    "knowledge/indexer.py": "Indexador RAG",
    "knowledge/retriever.py": "Retriever RAG",
    "knowledge/rss_collector.py": "Coletor RSS",
    "knowledge/knowledge_cmd.py": "Comando /knowledge",
    "knowledge/save_synthesis.py": "Salvador de sinteses",
    "knowledge/sources/sources.json": "Config fontes RSS",
    "interface/app.py": "Dashboard Streamlit",
    "interface/pages/01_carteira.py": "Pagina carteira",
    "interface/pages/02_analisar.py": "Pagina analise",
    "interface/pages/03_morning_call.py": "Pagina morning call",
    "interface/pages/04_risco.py": "Pagina risco",
    "interface/pages/05_relatorios.py": "Pagina relatorios",
    "interface/pages/06_knowledge.py": "Pagina knowledge",
    "interface/pages/07_agentes.py": "Pagina agentes",
    "interface/components/metricas_hf.py": "Componente metricas HF",
    "interface/components/pixel_art.py": "Componente pixel art",
    "interface/components/alerts_bar.py": "Barra alertas",
    "interface/components/sidebar.py": "Sidebar",
    "interface/style/sbwaa.css": "CSS customizado",
}

print(f"\n{'='*60}")
print("SBWAA — DIAGNOSTICO DE SCRIPTS")
print(f"{'='*60}")

faltando = []
existindo = []
for path_rel, descricao in scripts_necessarios.items():
    path_abs = ROOT / path_rel
    if path_abs.exists() and path_abs.stat().st_size > 10:
        existindo.append((path_rel, descricao))
    else:
        faltando.append((path_rel, descricao))

print(f"\n✅ EXISTEM ({len(existindo)} scripts):")
for p, d in existindo:
    print(f"   {p}")

print(f"\n❌ FALTANDO ({len(faltando)} scripts):")
for p, d in faltando:
    print(f"   {p} — {d}")

print(f"\n{'='*60}")
print(f"Total: {len(existindo)}/{len(scripts_necessarios)} presentes")
print(f"{'='*60}\n")
