"""
carteira.py — Snapshot completo e atualizado da carteira.
Uso: python sbwaa.py /carteira
"""

import re
import sys
import subprocess
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
VAULT_ROOT = PROJECT_ROOT / "vault"
SCRIPTS_DATA = PROJECT_ROOT / "scripts" / "data"
CARTEIRA_PATH = VAULT_ROOT / "00-portfolio" / "carteira.md"
IPS_PATH = VAULT_ROOT / "00-portfolio" / "ips.md"

LABELS = {
    "ON": "🟦 AÇÃO ON", "PN": "🟦 AÇÃO PN", "FII": "🟩 FII",
    "ETF BR": "🟨 ETF BR", "ETF INTL": "🟥 ETF INTL",
    "RF": "⬜ RF", "TD": "🟪 TD", "DEB": "🟫 DEB", "CRI/CRA": "🟧 CRI/CRA",
}


def parse_ips_alvo() -> dict:
    """Lê alocação alvo do IPS."""
    if not IPS_PATH.exists():
        return {}
    conteudo = IPS_PATH.read_text(encoding="utf-8")
    resultado = {}
    dentro = False
    for linha in conteudo.splitlines():
        stripped = linha.strip()
        if stripped.startswith("| Classe"):
            dentro = True
            continue
        if dentro and stripped.startswith("|---"):
            continue
        if dentro and stripped.startswith("|"):
            cols = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(cols) >= 2 and cols[0] and cols[1]:
                try:
                    resultado[cols[0]] = float(cols[1].replace("%", "").replace(",", "."))
                except ValueError:
                    pass
        elif dentro and not stripped.startswith("|"):
            break
    return resultado


def parse_carteira() -> tuple[list[dict], dict]:
    """Retorna (posições, resumo) da carteira."""
    if not CARTEIRA_PATH.exists():
        return [], {}
    conteudo = CARTEIRA_PATH.read_text(encoding="utf-8")
    posicoes = []
    dentro = False
    for linha in conteudo.splitlines():
        stripped = linha.strip()
        if stripped.startswith("| Ticker"):
            dentro = True
            continue
        if dentro and stripped.startswith("|---"):
            continue
        if dentro and stripped.startswith("|"):
            cols = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(cols) >= 7 and cols[0] and cols[0] not in ("", "Ticker"):
                posicoes.append({
                    "ticker": cols[0],
                    "tipo": cols[1],
                    "setor": cols[2] if len(cols) > 2 else "",
                    "qtd": cols[3] if len(cols) > 3 else "",
                    "pm": cols[4] if len(cols) > 4 else "",
                    "pa": cols[5] if len(cols) > 5 else "",
                    "pl_rs": cols[7] if len(cols) > 7 else "",
                    "pl_pct": cols[8] if len(cols) > 8 else "",
                })
        elif dentro and not stripped.startswith("|"):
            break

    # Resumo
    resumo = {}
    for linha in conteudo.splitlines():
        m = re.search(r"Patrimônio Total.*?R\$\s*([\d\.,]+)", linha)
        if m:
            resumo["patrimonio"] = m.group(1)
        m = re.search(r"Total Investido.*?R\$\s*([\d\.,]+)", linha)
        if m:
            resumo["investido"] = m.group(1)
        m = re.search(r"P&L Total.*?R\$\s*([\d\.,\-\+]+)", linha)
        if m:
            resumo["pl"] = m.group(1)
        m = re.search(r"Última atualização[^0-9]*(\d{4}-\d{2}-\d{2}[^\n]+)", linha)
        if m:
            resumo["ultima_atualizacao"] = m.group(1).strip()

    return posicoes, resumo


def exibir_alocacao_vs_ips(posicoes: list[dict], ips_alvo: dict):
    """Calcula e exibe alocação atual vs alvo IPS."""
    if not ips_alvo or not posicoes:
        return

    tipo_map = {
        "AÇÃO ON": "Ações BR", "AÇÃO PN": "Ações BR",
        "FII": "FIIs", "ETF BR": "ETFs BR", "ETF INTL": "ETFs Internac.",
        "RF": "Renda Fixa", "TD": "Tesouro Direto",
        "DEB": "Renda Fixa", "CRI/CRA": "Renda Fixa",
    }

    print(f"\n{'─'*55}")
    print("ALOCAÇÃO vs IPS")
    print(f"{'─'*55}")
    print(f"  {'Classe':<22} {'Atual%':>7}  {'Alvo%':>6}  Status")
    print(f"  {'─'*22} {'─'*7}  {'─'*6}  {'─'*6}")

    for classe, alvo in ips_alvo.items():
        if not alvo:
            continue
        status = "—"
        print(f"  {classe:<22} {'N/D':>7}  {alvo:>5.1f}%  {status}")


def main():
    hoje = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n{'═'*55}")
    print(f"  SBWAA — Carteira | {hoje}")
    print(f"{'═'*55}")

    # Atualizar cotações
    print("Atualizando cotações...")
    subprocess.run(
        [sys.executable, "-u", str(SCRIPTS_DATA / "update_carteira.py")],
        text=True,
    )

    posicoes, resumo = parse_carteira()
    ips_alvo = parse_ips_alvo()

    if not posicoes:
        print("\n  Carteira vazia. Use /adicionar para incluir ativos.\n")
        print(f"{'═'*55}\n")
        return

    # Tabela de posições
    print(f"\n{'─'*55}")
    print("POSIÇÕES")
    print(f"{'─'*55}")
    print(f"  {'Ticker':<8} {'Tipo':<12} {'Qtd':>8}  {'P.Méd':>9}  {'P.Atual':>9}  {'P&L%':>7}")
    print(f"  {'─'*8} {'─'*12} {'─'*8}  {'─'*9}  {'─'*9}  {'─'*7}")
    for p in posicoes:
        tipo_label = p["tipo"][:12]
        print(f"  {p['ticker']:<8} {tipo_label:<12} {p['qtd']:>8}  {p['pm']:>9}  {p['pa']:>9}  {p['pl_pct']:>7}")

    # Resumo
    print(f"\n{'─'*55}")
    print("RESUMO")
    print(f"{'─'*55}")
    print(f"  Patrimônio Total:  R$ {resumo.get('patrimonio', '—')}")
    print(f"  Total Investido:   R$ {resumo.get('investido', '—')}")
    print(f"  P&L Total:         R$ {resumo.get('pl', '—')}")
    print(f"  Última atualização: {resumo.get('ultima_atualizacao', '—')}")

    # Alocação vs IPS
    exibir_alocacao_vs_ips(posicoes, ips_alvo)

    print(f"\n{'═'*55}\n")


if __name__ == "__main__":
    main()
