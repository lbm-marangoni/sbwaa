"""
SBWAA Automation — Registro de tarefas por slot

Cada Task define: nome, descrição, tipo (python|claude), comando, timeout e se está ativa.
Slots:
  morning  — seg-sex 07:45 — pré-mercado
  eod      — seg-sex 17:00 — fechamento
  weekend  — sáb-dom 08:00 — relatórios
"""

import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DATA = PROJECT_ROOT / "scripts" / "data"
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"
ALERTS_SCRIPT        = PROJECT_ROOT / "scripts" / "alerts" / "check_alerts.py"
FLUXO_CAIXA_SCRIPT      = PROJECT_ROOT / "scripts" / "data" / "fluxo_caixa.py"
EARNINGS_CAL_SCRIPT     = PROJECT_ROOT / "scripts" / "data" / "earnings_calendar.py"
PERFORMANCE_SCRIPT   = PROJECT_ROOT / "scripts" / "data"   / "performance.py"
UPDATE_CARTEIRA_SCRIPT = PROJECT_ROOT / "scripts" / "data" / "update_carteira.py"
KNOWLEDGE_DIR        = PROJECT_ROOT / "knowledge"

PYTHON = sys.executable


@dataclass
class Task:
    name: str
    description: str
    task_type: str        # "python" | "claude"
    command: object       # list[str] para python, str para claude prompt
    timeout: int          # segundos
    enabled: bool = True


# ── SLOT MORNING ─────────────────────────────────────────────────────────────
# Roda seg-sex ~07:45 — antes da abertura de mercado

MORNING_TASKS: list[Task] = [
    Task(
        name="rss_collector",
        description="Coletar feeds RSS para a base de conhecimento",
        task_type="python",
        command=[PYTHON, str(KNOWLEDGE_DIR / "rss_collector.py")],
        timeout=300,
    ),
    Task(
        name="market_snapshot",
        description="Snapshot de mercado — preços e variações",
        task_type="python",
        command=[PYTHON, str(SCRIPTS_DATA / "market_snapshot.py")],
        timeout=180,
    ),
    Task(
        name="quant_metrics",
        description="Métricas quantitativas da carteira (Sharpe, Vol, Beta...)",
        task_type="python",
        command=[PYTHON, str(AGENTS_DIR / "quant-data-engineer" / "run_quant.py")],
        timeout=300,
    ),
    Task(
        name="risk_engineer",
        description="Risk snapshot — VaR, drawdown, circuit breakers",
        task_type="python",
        command=[PYTHON, str(AGENTS_DIR / "risk-engineer" / "run_risk_engineer.py")],
        timeout=300,
    ),
    Task(
        name="check_alerts_morning",
        description="Alertas matinais — circuit breakers, variações, dividendos",
        task_type="python",
        command=[PYTHON, str(ALERTS_SCRIPT)],
        timeout=180,
    ),
    Task(
        name="morning_call",
        description="Morning call completo via Claude Code",
        task_type="claude",
        command="/morning-call",
        timeout=900,
    ),
]


# ── SLOT EOD ──────────────────────────────────────────────────────────────────
# Roda seg-sex ~17:00 — após fechamento de mercado

EOD_TASKS: list[Task] = [
    Task(
        name="market_snapshot_eod",
        description="Snapshot EOD — preços de fechamento",
        task_type="python",
        command=[PYTHON, str(SCRIPTS_DATA / "market_snapshot.py")],
        timeout=180,
    ),
    Task(
        name="update_carteira_eod",
        description="Atualiza carteira e salva snapshot JSON diário de P&L",
        task_type="python",
        command=[PYTHON, str(UPDATE_CARTEIRA_SCRIPT)],
        timeout=240,
    ),
    Task(
        name="check_alerts_eod",
        description="Alertas EOD — variações no fechamento",
        task_type="python",
        command=[PYTHON, str(ALERTS_SCRIPT)],
        timeout=180,
    ),
    Task(
        name="performance_build",
        description="Performance vs benchmarks — atualiza série histórica",
        task_type="python",
        command=[PYTHON, str(PERFORMANCE_SCRIPT)],
        timeout=300,
    ),
    Task(
        name="risk_snapshot_eod",
        description="Risk snapshot EOD via Claude Code",
        task_type="claude",
        command="/snapshot",
        timeout=600,
    ),
]


# ── SLOT WEEKEND ──────────────────────────────────────────────────────────────
# Roda domingo 08:00 — relatório semanal
# Lógica de quando aplicar cada task está no main.py (domingo = semanal, 1° fds = mensal)

WEEKEND_TASKS: list[Task] = [
    Task(
        name="fluxo_caixa_build",
        description="Atualiza projeção de fluxo de caixa — renda passiva 12 meses",
        task_type="python",
        command=[PYTHON, str(FLUXO_CAIXA_SCRIPT)],
        timeout=300,
    ),
    Task(
        name="relatorio_semanal",
        description="Relatório semanal de performance e risco",
        task_type="claude",
        command="/relatorio-semanal",
        timeout=1200,
    ),
]

MONTHLY_TASKS: list[Task] = [
    Task(
        name="earnings_calendar",
        description="Atualiza calendário de resultados trimestrais (ações + FIIs)",
        task_type="python",
        command=[PYTHON, str(EARNINGS_CAL_SCRIPT)],
        timeout=300,
    ),
    Task(
        name="relatorio_mensal",
        description="Relatório mensal completo — performance, risco, revisão de teses",
        task_type="claude",
        command="/relatorio-mensal",
        timeout=1800,
    ),
]


# ── SLOT ALERTA ────────────────────────────────────────────────────────────────
# Roda seg-sex a cada 60 min (10:00–17:00) — monitor intraday de preços-alvo
# Controle de horário feito em main.py — fora do pregão o slot retorna lista vazia

ALERTA_TASKS: list[Task] = [
    Task(
        name="check_precos_alvo",
        description="Monitor intraday — preços-alvo, circuit breakers e dividendos",
        task_type="python",
        command=[PYTHON, str(ALERTS_SCRIPT)],
        timeout=120,
    ),
]
