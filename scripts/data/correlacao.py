"""
correlacao.py — Heatmap de correlações da carteira.

- Lê quant_YYYY-MM-DD.json (cache do agente Quant)
- Se cache vazio/ausente: roda run_quant.py inline e recarrega
- Saídas:
    1. Terminal: tabela ASCII com ANSI colors
    2. PNG: vault/02-relatorios/correlacao-YYYY-MM-DD.png
    3. Obsidian: vault/02-relatorios/correlacao-YYYY-MM-DD.md
- Destaca pares com correlação > THRESHOLD (default 0.70)
- Coluna extra: correlação de cada ativo com IBOV

Uso: python scripts/data/correlacao.py [--threshold 0.6]
"""

import argparse
import json
import math
import subprocess
import sys
import warnings
from datetime import date, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

PROJECT_ROOT  = Path(__file__).parent.parent.parent
VAULT_ROOT    = PROJECT_ROOT / "vault"
SCRIPTS_DIR   = Path(__file__).parent
CACHE_DIR     = SCRIPTS_DIR / "cache"
RELATORIOS_DIR = VAULT_ROOT / "02-relatorios"
QUANT_SCRIPT  = PROJECT_ROOT / ".claude" / "agents" / "quant-data-engineer" / "run_quant.py"

THRESHOLD_DEFAULT = 0.70

# ANSI
RED    = "\033[91m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

# Cores matplotlib (tema dark — mesmo de simulacao_carteira.py)
COR_FUNDO  = "#0f1117"
COR_PAINEL = "#161b27"
COR_GRADE  = "#2a2a3a"
COR_TEXTO  = "#e0e0e0"


# ── Cache ──────────────────────────────────────────────────────────────────────

def carregar_cache() -> dict | None:
    """Carrega quant cache mais recente (até 7 dias)."""
    hoje = date.today()
    for d in range(8):
        dt = (hoje - timedelta(days=d)).isoformat()
        p = CACHE_DIR / f"quant_{dt}.json"
        if p.exists():
            try:
                dados = json.loads(p.read_text(encoding="utf-8"))
                if dados.get("matriz_correlacao"):
                    return dados
            except Exception:
                pass
    return None


def rodar_quant() -> dict | None:
    """Executa run_quant.py e recarrega o cache."""
    print("  Cache vazio — rodando Quant/Data Engineer...")
    try:
        result = subprocess.run(
            [sys.executable, str(QUANT_SCRIPT)],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode != 0:
            print(f"  Quant retornou erro:\n{result.stderr[-500:]}")
        return carregar_cache()
    except subprocess.TimeoutExpired:
        print("  Timeout ao rodar o Quant (>5 min).")
        return None
    except Exception as e:
        print(f"  Erro ao rodar Quant: {e}")
        return None


# ── Helpers ────────────────────────────────────────────────────────────────────

def _cor_ansi(v: float, threshold: float) -> str:
    av = abs(v)
    if av >= threshold:
        return RED + BOLD
    if av >= 0.40:
        return YELLOW
    return GREEN


def _cor_hex(v: float) -> str:
    """Retorna cor hex para matplotlib: RdBu_r (red=+1, blue=-1, white=0)."""
    cmap = plt.cm.RdBu_r
    return cmap((v + 1) / 2)


# ── Terminal ───────────────────────────────────────────────────────────────────

def exibir_terminal(
    tickers: list[str],
    matrix: np.ndarray,
    corr_ibov: dict[str, float | None],
    pares: list[dict],
    metricas: dict,
    threshold: float,
):
    n = len(tickers)
    col_w = 8
    lbl_w = 8

    print(f"\n{BOLD}{'═'*70}{RESET}")
    print(f"{BOLD}  CORRELAÇÃO DA CARTEIRA — {date.today().isoformat()}{RESET}")
    print(f"{'═'*70}")
    print(f"  Threshold de alerta: {threshold:.2f} | Período: 252 dias úteis\n")

    # Cabeçalho
    header = f"  {'':>{lbl_w}}"
    for tk in tickers:
        header += f"  {tk[:col_w]:>{col_w}}"
    header += f"  {'IBOV':>{col_w}}"
    print(header)
    print(f"  {'─'*(lbl_w + (col_w + 2) * (n + 1) + 2)}")

    # Linhas
    for i, ti in enumerate(tickers):
        linha = f"  {ti[:lbl_w]:>{lbl_w}}"
        for j in range(n):
            v = matrix[i, j]
            if i == j:
                linha += f"  {DIM}{'1.00':>{col_w}}{RESET}"
            else:
                cor = _cor_ansi(v, threshold)
                linha += f"  {cor}{v:>{col_w}.2f}{RESET}"
        # Coluna IBOV
        vi = corr_ibov.get(ti)
        if vi is not None:
            cor = _cor_ansi(vi, threshold)
            linha += f"  {cor}{vi:>{col_w}.2f}{RESET}"
        else:
            linha += f"  {'N/D':>{col_w}}"
        print(linha)

    print(f"\n  {GREEN}■{RESET} < 0.40   {YELLOW}■{RESET} 0.40–{threshold:.2f}   {RED}■{RESET} ≥ {threshold:.2f}")

    # Pares problemáticos
    if pares:
        print(f"\n{BOLD}  ⚠️  PARES COM CORRELAÇÃO ≥ {threshold:.2f}{RESET}")
        print(f"  {'─'*50}")
        for p in pares:
            sinal = "↑" if p["tipo"] == "positiva" else "↓"
            print(f"  {RED}{BOLD}{p['ativo_a']:<8} × {p['ativo_b']:<8}{RESET}  "
                  f"{sinal} {p['correlacao']:+.3f}  — diversificação reduzida")
    else:
        print(f"\n  {GREEN}✅ Nenhum par com correlação ≥ {threshold:.2f}{RESET}")

    # Métricas
    cm  = metricas.get("corr_media")
    de  = metricas.get("diversificacao_efetiva")
    hhi = metricas.get("hhi")
    print(f"\n  Correlação média          : {cm:.3f}" if cm else "")
    print(f"  Diversificação efetiva    : {de:.1f} ativos independentes" if de else "")
    print(f"  HHI (concentração)        : {hhi:.4f}" if hhi else "")
    print(f"\n{'═'*70}\n")


# ── Heatmap PNG ────────────────────────────────────────────────────────────────

def gerar_heatmap(
    tickers: list[str],
    matrix: np.ndarray,
    corr_ibov: dict[str, float | None],
    pares: list[dict],
    output_path: Path,
    threshold: float,
):
    n = len(tickers)
    ibov_col = np.array([corr_ibov.get(t, np.nan) for t in tickers])

    # Layout: n×n + 1 coluna IBOV + 1 coluna colorbar
    fig = plt.figure(figsize=(max(8, n * 1.1 + 3), max(6, n * 1.0 + 2)),
                     facecolor=COR_FUNDO)

    # GridSpec: heatmap principal | coluna IBOV | colorbar
    gs = fig.add_gridspec(1, 3, width_ratios=[n, 1, 0.4], wspace=0.05)
    ax_main = fig.add_subplot(gs[0, 0])
    ax_ibov = fig.add_subplot(gs[0, 1])
    ax_cb   = fig.add_subplot(gs[0, 2])

    cmap = plt.cm.RdBu_r
    vmin, vmax = -1.0, 1.0

    # ── Heatmap principal ─────────────────────────────────────────────────────
    im = ax_main.imshow(matrix, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    ax_main.set_xticks(range(n))
    ax_main.set_yticks(range(n))
    ax_main.set_xticklabels(tickers, rotation=45, ha="right",
                             color=COR_TEXTO, fontsize=9)
    ax_main.set_yticklabels(tickers, color=COR_TEXTO, fontsize=9)
    ax_main.tick_params(colors=COR_TEXTO, length=0)
    for sp in ax_main.spines.values():
        sp.set_color(COR_GRADE)

    # Anotações + highlight
    for i in range(n):
        for j in range(n):
            v = matrix[i, j]
            txt_color = "white" if abs(v) > 0.65 else "black"
            weight = "bold" if abs(v) >= threshold and i != j else "normal"
            ax_main.text(j, i, f"{v:.2f}", ha="center", va="center",
                         color=txt_color, fontsize=8, fontweight=weight)
            # Borda vermelha nos pares problemáticos
            if abs(v) >= threshold and i != j:
                ax_main.add_patch(mpatches.Rectangle(
                    (j - 0.5, i - 0.5), 1, 1,
                    fill=False, edgecolor="#FF4444", linewidth=2, zorder=5
                ))

    ax_main.set_title("Correlação da Carteira", color=COR_TEXTO,
                      fontsize=12, fontweight="bold", pad=12)

    # ── Coluna IBOV ───────────────────────────────────────────────────────────
    ibov_2d = ibov_col.reshape(-1, 1)
    ax_ibov.imshow(ibov_2d, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    ax_ibov.set_xticks([0])
    ax_ibov.set_xticklabels(["IBOV"], rotation=45, ha="right",
                              color=COR_TEXTO, fontsize=9)
    ax_ibov.set_yticks([])
    ax_ibov.tick_params(colors=COR_TEXTO, length=0)
    for sp in ax_ibov.spines.values():
        sp.set_color(COR_GRADE)
    ax_ibov.set_facecolor(COR_PAINEL)

    for i, v in enumerate(ibov_col):
        if not math.isnan(v):
            txt_color = "white" if abs(v) > 0.65 else "black"
            weight = "bold" if abs(v) >= threshold else "normal"
            ax_ibov.text(0, i, f"{v:.2f}", ha="center", va="center",
                         color=txt_color, fontsize=8, fontweight=weight)
        else:
            ax_ibov.text(0, i, "N/D", ha="center", va="center",
                         color=COR_GRADE, fontsize=7)

    ax_ibov.set_title("IBOV", color=COR_TEXTO, fontsize=10,
                       fontweight="bold", pad=12)

    # ── Colorbar ──────────────────────────────────────────────────────────────
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
    sm.set_array([])
    cb = fig.colorbar(sm, cax=ax_cb)
    cb.ax.tick_params(colors=COR_TEXTO, labelsize=8)
    cb.outline.set_edgecolor(COR_GRADE)
    ax_cb.yaxis.set_tick_params(color=COR_TEXTO)
    plt.setp(ax_cb.yaxis.get_ticklabels(), color=COR_TEXTO)

    # ── Legenda pares problemáticos ───────────────────────────────────────────
    if pares:
        txt = f"⚠ Pares ≥ {threshold:.2f}: " + ", ".join(
            f"{p['ativo_a']}×{p['ativo_b']} ({p['correlacao']:+.2f})" for p in pares
        )
        fig.text(0.01, 0.01, txt, color="#FF8888", fontsize=7.5,
                 ha="left", va="bottom", style="italic")

    fig.text(0.5, 0.97,
             f"SBWAA — Correlação  |  {date.today().isoformat()}  |  252 dias úteis",
             ha="center", va="top", color=COR_TEXTO, fontsize=8, alpha=0.7)

    RELATORIOS_DIR.mkdir(parents=True, exist_ok=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=COR_FUNDO)
    plt.close(fig)
    print(f"  PNG salvo: {output_path}")


# ── Nota Obsidian ──────────────────────────────────────────────────────────────

def gerar_nota_obsidian(
    hoje_str: str,
    tickers: list[str],
    matrix: np.ndarray,
    corr_ibov: dict[str, float | None],
    pares: list[dict],
    metricas: dict,
    png_path: Path,
    threshold: float,
):
    n = len(tickers)
    cm  = metricas.get("corr_media")
    de  = metricas.get("diversificacao_efetiva")
    hhi = metricas.get("hhi")

    linhas = [
        "---",
        "tags: [relatorio, correlacao, quant, risco]",
        "cssclasses: [node-relatorio]",
        f"data: {hoje_str}",
        f"pares_alta_correlacao: {len(pares)}",
        f"corr_media: {cm:.3f}" if cm else "corr_media: null",
        f"threshold: {threshold}",
        "---",
        "",
        f"# Correlação da Carteira — {hoje_str}",
        "",
        f"> Gerado em {hoje_str} — base: últimos 252 dias úteis (ativos equity).",
        "",
    ]

    # Alerta
    if pares:
        linhas += [
            f"> [!warning] ⚠️ {len(pares)} par(es) com correlação ≥ {threshold:.2f} "
            f"— diversificação comprometida",
            "",
        ]
    else:
        linhas += [
            f"> [!tip] ✅ Nenhum par com correlação ≥ {threshold:.2f}",
            "",
        ]

    # Imagem
    png_nome = png_path.name
    linhas += [
        f"![[{png_nome}]]",
        "",
    ]

    # Pares problemáticos
    if pares:
        linhas += [
            "---",
            "",
            f"## ⚠️ Pares com Alta Correlação (≥ {threshold:.2f})",
            "",
            "| Ativo A | Ativo B | Correlação | Direção | Risco |",
            "|---------|---------|-----------|---------|-------|",
        ]
        for p in pares:
            risco = "ALTO" if abs(p["correlacao"]) >= 0.85 else "MÉDIO"
            sinal = "↑ positiva" if p["tipo"] == "positiva" else "↓ negativa"
            linhas.append(
                f"| [[{p['ativo_a']}]] | [[{p['ativo_b']}]] "
                f"| **{p['correlacao']:+.3f}** | {sinal} | {risco} |"
            )
        linhas.append("")

    # Correlação com IBOV
    linhas += [
        "---",
        "",
        "## 📊 Correlação com IBOV",
        "",
        "| Ativo | Corr. IBOV | Exposição Sistemática |",
        "|-------|-----------|----------------------|",
    ]
    for tk in tickers:
        vi = corr_ibov.get(tk)
        if vi is not None:
            if abs(vi) >= 0.70:
                exp = "🔴 Alta"
            elif abs(vi) >= 0.40:
                exp = "🟡 Moderada"
            else:
                exp = "🟢 Baixa"
            linhas.append(f"| [[{tk}]] | {vi:+.3f} | {exp} |")
        else:
            linhas.append(f"| [[{tk}]] | N/D | — |")
    linhas.append("")

    # Matriz completa (markdown)
    linhas += [
        "---",
        "",
        "## 🔢 Matriz Completa",
        "",
    ]
    header = "| " + " | ".join([""] + tickers) + " |"
    sep = "|" + "|".join(["---"] * (n + 1)) + "|"
    linhas += [header, sep]
    for i, ti in enumerate(tickers):
        celulas = [f"[[{ti}]]"]
        for j in range(n):
            v = matrix[i, j]
            if i == j:
                celulas.append("**1.00**")
            elif abs(v) >= threshold:
                celulas.append(f"**{v:+.2f}** ⚠️")
            else:
                celulas.append(f"{v:+.2f}")
        linhas.append("| " + " | ".join(celulas) + " |")
    linhas.append("")

    # Métricas
    linhas += [
        "---",
        "",
        "## 📈 Métricas de Diversificação",
        "",
        "| Métrica | Valor | Interpretação |",
        "|---------|-------|--------------|",
    ]
    if cm is not None:
        nivel_cm = "alta (baixa diversificação)" if cm > 0.6 else ("moderada" if cm > 0.35 else "baixa (boa diversificação)")
        linhas.append(f"| Correlação média | {cm:.3f} | {nivel_cm} |")
    if de is not None:
        linhas.append(f"| Diversificação efetiva | {de:.1f} ativos independentes | Quanto maior melhor |")
    if hhi is not None:
        nivel_hhi = "alta concentração" if hhi > 0.25 else ("moderada" if hhi > 0.10 else "bem diversificado")
        linhas.append(f"| HHI (concentração) | {hhi:.4f} | {nivel_hhi} |")
    linhas += [
        "",
        "---",
        "",
        "## Links",
        "",
        "[[carteira]] | [[ips]] | [[risco-carteira]]",
        "",
    ]

    nota_path = RELATORIOS_DIR / f"correlacao-{hoje_str}.md"
    RELATORIOS_DIR.mkdir(parents=True, exist_ok=True)
    nota_path.write_text("\n".join(linhas), encoding="utf-8")
    print(f"  Nota Obsidian: {nota_path}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SBWAA — Heatmap de correlações")
    parser.add_argument("--threshold", type=float, default=THRESHOLD_DEFAULT,
                        help=f"Threshold de alerta (default: {THRESHOLD_DEFAULT})")
    args = parser.parse_args()
    threshold = args.threshold

    hoje_str = date.today().isoformat()
    print(f"\nSBWAA Correlação — {hoje_str}")
    print("=" * 60)

    # Carrega ou roda quant
    dados = carregar_cache()
    if dados is None:
        dados = rodar_quant()
    if dados is None or not dados.get("matriz_correlacao"):
        print("  ❌ Não foi possível obter a matriz de correlação.")
        print("     Verifique se a carteira tem ativos equity (ações/FIIs/ETFs).")
        return

    corr_dict = dados["matriz_correlacao"]
    metricas_ativos = dados.get("ativos", {})

    tickers = list(corr_dict.keys())
    if not tickers:
        print("  Matriz vazia — nenhum ativo equity na carteira.")
        return

    n = len(tickers)
    matrix = np.array([
        [corr_dict[ti].get(tj, float("nan")) if isinstance(corr_dict[ti], dict)
         else float("nan")
         for tj in tickers]
        for ti in tickers
    ], dtype=float)

    # IBOV correlation per asset (from quant cache)
    corr_ibov = {
        tk: metricas_ativos.get(tk, {}).get("correlacao_ibov")
        for tk in tickers
    }

    # Pares alta correlação
    pares = dados.get("pares_alta_correlacao", [])
    # Re-filter by user threshold (cache uses 0.7 default)
    if threshold != 0.70:
        pares = [p for p in pares if abs(p["correlacao"]) >= threshold]

    # Métricas carteira
    cart = dados.get("carteira", {})
    metricas = {
        "corr_media":             cart.get("corr_media"),
        "diversificacao_efetiva": cart.get("diversificacao_efetiva"),
        "hhi":                    cart.get("hhi"),
    }

    print(f"  Ativos: {tickers}")
    print(f"  Threshold: {threshold} | Pares alertas: {len(pares)}")

    # 1. Terminal
    exibir_terminal(tickers, matrix, corr_ibov, pares, metricas, threshold)

    # 2. PNG
    png_path = RELATORIOS_DIR / f"correlacao-{hoje_str}.png"
    gerar_heatmap(tickers, matrix, corr_ibov, pares, png_path, threshold)

    # 3. Obsidian
    gerar_nota_obsidian(
        hoje_str, tickers, matrix, corr_ibov, pares, metricas, png_path, threshold
    )

    print(f"\n  Concluído. Abra vault/02-relatorios/ no Obsidian para ver o heatmap.\n")


if __name__ == "__main__":
    main()
