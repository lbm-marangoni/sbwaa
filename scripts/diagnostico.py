#!/usr/bin/env python3
"""SBWAA — Diagnóstico de scripts."""
from pathlib import Path

ROOT = Path(__file__).parent.parent

scripts_necessarios = {
    # --- Coleta de dados ---
    "scripts/data/fetch_fundamentals.py": "Busca dados BR via Yahoo Finance",
    "scripts/data/fetch_investidor10.py": "Dados complementares via scraping Investidor10",
    "scripts/data/fetch_yahoo.py": "Busca dados globais via Yahoo Finance",
    "scripts/data/fetch_bcb.py": "Busca macro BR via BCB (Selic, IPCA, BRL/USD)",
    "scripts/data/fetch_consensus.py": "Consenso de analistas",
    "scripts/data/update_carteira.py": "Atualiza cotações na carteira",
    "scripts/data/add_ativo.py": "Adiciona ativo à carteira",
    "scripts/data/market_snapshot.py": "Snapshot diário de mercado",

    # --- Agentes — SKILLs (arquitetura atual: .md) ---
    ".claude/agents/market-researcher/SKILL.md": "SKILL do Market Researcher",
    ".claude/agents/earnings-reviewer/SKILL.md": "SKILL do Earnings Reviewer",
    ".claude/agents/model-builder/SKILL.md": "SKILL do Model Builder",
    ".claude/agents/valuation-reviewer/SKILL.md": "SKILL do Valuation Reviewer",
    ".claude/agents/quant-data-engineer/SKILL.md": "SKILL do Quant/Data Engineer",
    ".claude/agents/risk-engineer/SKILL.md": "SKILL do Risk Engineer",
    ".claude/agents/portfolio-manager/SKILL.md": "SKILL do Portfolio Manager",
    ".claude/agents/econometrician/SKILL.md": "SKILL do Econometrician",

    # --- Agentes — runners Python (apenas os que ainda existem) ---
    ".claude/agents/quant-data-engineer/run_quant.py": "Runner Quant",
    ".claude/agents/quant-data-engineer/calculators/returns.py": "Calculadora retornos",
    ".claude/agents/quant-data-engineer/calculators/portfolio_metrics.py": "Métricas portfólio",
    ".claude/agents/quant-data-engineer/calculators/correlation.py": "Correlação",
    ".claude/agents/risk-engineer/run_risk_engineer.py": "Runner Risk Engineer",
    ".claude/agents/risk-engineer/calculators/var.py": "Calculadora VaR/CVaR",
    ".claude/agents/risk-engineer/calculators/stress_test.py": "Stress test",
    ".claude/agents/econometrician/run_econometrician.py": "Runner Econometrician",

    # --- Comandos — skills (arquitetura atual: .md) ---
    ".claude/commands/analisar.md": "Skill /analisar",
    ".claude/commands/tese.md": "Skill /tese",
    ".claude/commands/pm.md": "Skill /pm",
    ".claude/commands/morning-call.md": "Skill /morning-call",
    ".claude/commands/investimento-do-dia.md": "Skill /investimento-do-dia",
    ".claude/commands/mundo-economico.md": "Skill /mundo-economico",
    ".claude/commands/relatorio-semanal.md": "Skill /relatorio-semanal",
    ".claude/commands/relatorio-mensal.md": "Skill /relatorio-mensal",
    ".claude/commands/rebalancear.md": "Skill /rebalancear",
    ".claude/commands/comparar.md": "Skill /comparar",
    ".claude/commands/revisar-carteira.md": "Skill /revisar-carteira",
    ".claude/commands/earnings.md": "Skill /earnings",
    ".claude/commands/metas.md": "Skill /metas",

    # --- Interface desktop ---
    "interface/ui.py": "Painel customtkinter (interface atual)",
    "interface/splash.py": "Splash screen",

    # --- Alertas e heartbeat ---
    "scripts/heartbeat/heartbeat.py": "Heartbeat automático",
    "scripts/heartbeat/schedule_heartbeat.py": "Agendador heartbeat",
    "scripts/alerts/check_alerts.py": "Sistema de alertas",

    # --- Knowledge base ---
    "knowledge/indexer.py": "Indexador RAG",
    "knowledge/retriever.py": "Retriever RAG",
    "knowledge/rss_collector.py": "Coletor RSS",
    "knowledge/knowledge_cmd.py": "Comando /knowledge",
    "knowledge/save_synthesis.py": "Salvador de sínteses",
    "knowledge/sources/sources.json": "Config fontes RSS",

    # --- Documentação obrigatória ---
    "docs/GUIA-COMANDOS.md": "Guia de comandos",
    "docs/SBWAA-WORKFLOW.md": "Workflow e cadências",
    "docs/SBWAA-REFERENCIA.md": "Referência técnica",
    "docs/SBWAA-GLOSSARIO.md": "Glossário de termos e siglas",
    "docs/SBWAA-MASTER-BLUEPRINT.md": "Blueprint de arquitetura",
    "VERSION.md": "Controle de versão",
    "CHANGELOG.md": "Histórico de mudanças",
}

print(f"\n{'='*60}")
print("SBWAA — DIAGNÓSTICO DE SCRIPTS")
print(f"{'='*60}")

faltando = []
existindo = []
for path_rel, descricao in scripts_necessarios.items():
    path_abs = ROOT / path_rel
    if path_abs.exists() and path_abs.stat().st_size > 10:
        existindo.append((path_rel, descricao))
    else:
        faltando.append((path_rel, descricao))

print(f"\n✅ EXISTEM ({len(existindo)} arquivos):")
for p, d in existindo:
    print(f"   {p}")

if faltando:
    print(f"\n❌ FALTANDO ({len(faltando)} arquivos):")
    for p, d in faltando:
        print(f"   {p} — {d}")
else:
    print(f"\n✅ Nenhum arquivo faltando.")

print(f"\n{'='*60}")
print(f"Total: {len(existindo)}/{len(scripts_necessarios)} presentes")
print(f"{'='*60}\n")
