"""
alerta_cmd.py — Interface CLI para alertas de preço.
Uso via: python sbwaa.py /alerta [flags]
"""

import sys
import json
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
ALERTAS_JSON = PROJECT_ROOT / "vault" / "00-portfolio" / "alertas.json"
HISTORICO_MD = PROJECT_ROOT / "vault" / "05-risk" / "alertas-historico.md"


def listar():
    if not ALERTAS_JSON.exists():
        print("\n  Nenhum alerta ativo.")
        print("  Execute /analisar, /tese ou /pm para gerar alertas automaticamente.\n")
        return
    try:
        dados = json.loads(ALERTAS_JSON.read_text(encoding="utf-8"))
    except Exception:
        print("  Erro ao ler alertas.json.")
        return
    alertas = dados.get("alertas", [])
    if not alertas:
        print("\n  ✅ Nenhum alerta ativo.\n")
        return

    print(f"\n{'═'*62}")
    print(f"  ALERTAS ATIVOS — {len(alertas)} configurado(s)")
    print(f"{'═'*62}")

    por_ticker: dict[str, list] = {}
    for a in alertas:
        por_ticker.setdefault(a["ticker"], []).append(a)

    for ticker, lista in sorted(por_ticker.items()):
        print(f"\n  {ticker}")
        for a in lista:
            sinal = "↑ acima de" if a["direcao"] == "acima" else "↓ abaixo de"
            print(f"    {sinal} R$ {a['preco']:.2f}  [{a['tipo']}]  {a['descricao']}")
            print(f"    Criado: {a['data_criacao']}  Ação: {a['acao_sugerida']}")

    print(f"\n{'═'*62}\n")


def historico():
    if not HISTORICO_MD.exists():
        print("\n  Nenhum histórico ainda. Os alertas disparados aparecerão aqui.\n")
        return
    texto = HISTORICO_MD.read_text(encoding="utf-8")
    linhas = texto.splitlines()

    nao_lidos = [l for l in linhas if l.strip().startswith("- [ ]")]
    lidos     = [l for l in linhas if l.strip().startswith("- [x]")]

    print(f"\n{'═'*62}")
    print(f"  HISTÓRICO — {len(nao_lidos)} não lido(s) / {len(lidos)} lido(s)")
    print(f"{'═'*62}")

    if nao_lidos:
        print(f"\n  ⚡ Não lidos:")
        for l in nao_lidos[:15]:
            print(f"  {l.strip()}")
        if len(nao_lidos) > 15:
            print(f"  ... e mais {len(nao_lidos) - 15}")

    if lidos:
        print(f"\n  ✅ Últimos lidos:")
        for l in lidos[:5]:
            print(f"  {l.strip()}")
        if len(lidos) > 5:
            print(f"  ... e mais {len(lidos) - 5}")

    print(f"\n  Marcar como lido: edite {HISTORICO_MD.name} no Obsidian (checkbox)")
    print(f"  Arquivo: {HISTORICO_MD}")
    print(f"{'═'*62}\n")


def remover(ticker: str):
    if not ALERTAS_JSON.exists():
        print(f"\n  Nenhum alerta para {ticker.upper()}.\n")
        return
    try:
        dados = json.loads(ALERTAS_JSON.read_text(encoding="utf-8"))
    except Exception:
        print("  Erro ao ler alertas.json.")
        return
    antes = len(dados.get("alertas", []))
    dados["alertas"] = [a for a in dados["alertas"] if a["ticker"].upper() != ticker.upper()]
    depois = len(dados["alertas"])
    ALERTAS_JSON.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    n = antes - depois
    if n:
        print(f"\n  ✅ {n} alerta(s) de {ticker.upper()} removido(s).\n")
    else:
        print(f"\n  Nenhum alerta encontrado para {ticker.upper()}.\n")


def verificar():
    sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.alerts.check_alerts import main as check_main
    check_main()


def main():
    parser = argparse.ArgumentParser(
        prog="python sbwaa.py /alerta",
        description="SBWAA — Monitor de alertas de preço",
    )
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--listar",    action="store_true",  help="Lista alertas ativos")
    grp.add_argument("--historico", action="store_true",  help="Histórico de alertas disparados")
    grp.add_argument("--verificar", action="store_true",  help="Roda verificação agora")
    grp.add_argument("--remover",   metavar="TICKER",     help="Remove alertas de um ticker")
    args = parser.parse_args()

    if args.listar:
        listar()
    elif args.historico:
        historico()
    elif args.verificar:
        verificar()
    elif args.remover:
        remover(args.remover)


if __name__ == "__main__":
    main()
