"""
rf_oportunidade.py — Gerencia o saldo da RF Oportunidade (Caixinha Nubank).
Uso:
    python rf_oportunidade.py --saldo
    python rf_oportunidade.py --depositar 500.00 --data 2026-05-29
    python rf_oportunidade.py --retirar 300.00 --destino MXRF11
    python rf_oportunidade.py --atualizar-saldo 1847.32 --data-deposito 2026-05-01
"""

import argparse
import re
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from calculos_tributarios import calcular_rdb_nubank, bloco_rf_oportunidade

VAULT_ROOT  = Path(__file__).parent.parent.parent / "vault"
ARQ_OPORT   = VAULT_ROOT / "00-portfolio" / "rf-oportunidade.md"


# ── Leitura / escrita ──────────────────────────────────────────────────────────

def _ler_yaml_bloco(conteudo: str) -> dict:
    """Extrai saldo_bruto e data_deposito do bloco ```yaml``` no arquivo."""
    # Aceita tanto "data" (aspas normais) quanto \"data\" (aspas escapadas)
    m = re.search(
        r"```yaml\s*\nsaldo_bruto:\s*([\d.,]+)\ndata_deposito:\s*\\?\"([^\"\\]+)\\?\"",
        conteudo,
    )
    if not m:
        return {"saldo_bruto": 0.0, "data_deposito": "—"}
    saldo = float(m.group(1).replace(",", ""))
    return {"saldo_bruto": saldo, "data_deposito": m.group(2)}


def _escrever_yaml_bloco(conteudo: str, saldo: float, data_dep: str) -> str:
    nova_linha = f'saldo_bruto: {saldo:.2f}\ndata_deposito: "{data_dep}"'
    return re.sub(
        r"(```yaml\s*\n)saldo_bruto:.*\ndata_deposito:.*",
        lambda m: m.group(1) + nova_linha,
        conteudo,
    )


def _atualizar_atualizado(conteudo: str) -> str:
    hoje = date.today().strftime("%Y-%m-%d")
    return re.sub(r"atualizado: .*", f"atualizado: {hoje}", conteudo)


def _adicionar_movimentacao(conteudo: str, tipo: str, valor: float, dest: str, saldo_apos: float) -> str:
    hoje = date.today().strftime("%Y-%m-%d")
    nova = f"| {hoje} | {tipo} | {valor:,.2f} | {dest} | {saldo_apos:,.2f} |"
    # Insere após a linha separadora da tabela de movimentações
    return re.sub(
        r"(\| Data \| Tipo \| Valor[^\n]+\n\|[-| ]+\|)\n\| — \|.*",
        rf"\1\n{nova}",
        conteudo,
        count=1,
    )


def _atualizar_tabela_estimativa(conteudo: str, dados: dict) -> str:
    """Atualiza a tabela de estimativa tributária no arquivo."""
    linhas_novas = (
        f"| Saldo bruto | R$ {dados['total_bruto']:,.2f} |\n"
        f"| Rendimento est. | R$ {dados['rendimento_bruto']:,.2f} |\n"
        f"| IOF est. | R$ {dados['iof_valor']:,.2f} |\n"
        f"| IR est. | R$ {dados['ir_valor']:,.2f} |\n"
        f"| **Líquido disponível** | **R$ {dados['liquido']:,.2f}** |"
    )
    return re.sub(
        r"\| Saldo bruto \|.*?\| \*\*Líquido disponível\*\* \|.*?\|",
        linhas_novas,
        conteudo,
        flags=re.DOTALL,
    )


def ler_estado() -> tuple[float, str]:
    """Retorna (saldo_bruto, data_deposito) do arquivo."""
    if not ARQ_OPORT.exists():
        return 0.0, "—"
    dados = _ler_yaml_bloco(ARQ_OPORT.read_text(encoding="utf-8"))
    return dados["saldo_bruto"], dados["data_deposito"]


def salvar_estado(saldo: float, data_dep: str, tipo_mov: str, valor_mov: float, destino: str):
    conteudo = ARQ_OPORT.read_text(encoding="utf-8")
    conteudo = _escrever_yaml_bloco(conteudo, saldo, data_dep)
    conteudo = _atualizar_atualizado(conteudo)
    if valor_mov != 0:
        conteudo = _adicionar_movimentacao(conteudo, tipo_mov, abs(valor_mov), destino, saldo)
    # Atualizar estimativa tributária
    try:
        trib = calcular_rdb_nubank(saldo, data_dep)
        conteudo = _atualizar_tabela_estimativa(conteudo, {
            "total_bruto": trib.total_bruto,
            "rendimento_bruto": trib.rendimento_bruto,
            "iof_valor": trib.iof_valor,
            "ir_valor": trib.ir_valor,
            "liquido": trib.liquido,
        })
    except Exception:
        pass
    ARQ_OPORT.write_text(conteudo, encoding="utf-8")


# ── Comandos ───────────────────────────────────────────────────────────────────

def cmd_saldo():
    saldo, data_dep = ler_estado()
    if saldo == 0.0 or data_dep == "—":
        print("\n[RF Oportunidade] Nenhum saldo registrado.")
        print("Use: python rf_oportunidade.py --atualizar-saldo X.XX --data-deposito YYYY-MM-DD")
        return

    trib = calcular_rdb_nubank(saldo, data_dep)
    print(f"\n{'━'*52}")
    print("💰 RF OPORTUNIDADE — CAIXINHA NUBANK")
    print(f"{'─'*52}")
    print(f"  Saldo bruto:          R$ {saldo:>10,.2f}")
    print(f"  Data depósito base:   {data_dep}  ({trib.dias} dias corridos)")
    print(f"  Rendimento est.*:     R$ {trib.rendimento_bruto:>10,.2f}")
    print(f"  IOF ({trib.iof_aliquota_pct:.0f}%):            R$ {trib.iof_valor:>10,.2f}  {'✅ zerado' if trib.iof_valor == 0 else '⚠️'}")
    print(f"  IR  ({trib.ir_aliquota_pct:.1f}%):           R$ {trib.ir_valor:>10,.2f}  (só no resgate)")
    print(f"  {'─'*50}")
    print(f"  Líquido disponível:   R$ {trib.liquido:>10,.2f}")
    print(f"{'━'*52}")
    print("  * CDI 14,75% a.a. — estimativa; IR realizado no resgate.")


def cmd_depositar(valor: float, data: str | None):
    saldo_ant, _ = ler_estado()
    novo_saldo = round(saldo_ant + valor, 2)
    data_dep = data or date.today().strftime("%Y-%m-%d")
    salvar_estado(novo_saldo, data_dep, "DEPÓSITO", valor, "Nubank Caixinha")
    print(f"\n[OK] Depósito de R$ {valor:,.2f} registrado.")
    print(f"     Saldo anterior: R$ {saldo_ant:,.2f}")
    print(f"     Saldo atual:    R$ {novo_saldo:,.2f}")
    print(f"     Data depósito:  {data_dep}")


def cmd_retirar(valor: float, destino: str):
    saldo_ant, data_dep = ler_estado()
    if saldo_ant < valor:
        print(f"\n[ERRO] Saldo insuficiente. Disponível: R$ {saldo_ant:,.2f}")
        sys.exit(1)
    novo_saldo = round(saldo_ant - valor, 2)
    salvar_estado(novo_saldo, data_dep, "RETIRADA", -valor, destino)
    print(f"\n[OK] Retirada de R$ {valor:,.2f} → {destino} registrada.")
    print(f"     Saldo anterior: R$ {saldo_ant:,.2f}")
    print(f"     Saldo atual:    R$ {novo_saldo:,.2f}")


def cmd_atualizar(saldo: float, data_dep: str):
    _, data_ant = ler_estado()
    salvar_estado(saldo, data_dep, "ATUALIZAÇÃO", 0, "—")
    print(f"\n[OK] Saldo atualizado: R$ {saldo:,.2f}  |  Data depósito: {data_dep}")
    cmd_saldo()


def cmd_checar_aporte(valor: float):
    """Exibe bloco de validação de aporte a partir da Oportunidade."""
    saldo, data_dep = ler_estado()
    if saldo == 0.0 or data_dep == "—":
        print("\n[RF Oportunidade] Saldo não configurado. Use --atualizar-saldo.")
        return
    print(bloco_rf_oportunidade(saldo, data_dep, valor))


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Gerencia RF Oportunidade (Caixinha Nubank)")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--saldo",          action="store_true")
    g.add_argument("--depositar",      type=float, metavar="VALOR")
    g.add_argument("--retirar",        type=float, metavar="VALOR")
    g.add_argument("--atualizar-saldo",type=float, metavar="VALOR", dest="atualizar")
    g.add_argument("--checar-aporte",  type=float, metavar="VALOR", dest="checar")
    p.add_argument("--destino",        default="—")
    p.add_argument("--data",           default=None, help="Data YYYY-MM-DD (depósito)")
    p.add_argument("--data-deposito",  default=None, dest="data_deposito",
                   help="Data base de depósito YYYY-MM-DD (para --atualizar-saldo)")
    args = p.parse_args()

    if args.saldo:
        cmd_saldo()
    elif args.depositar is not None:
        cmd_depositar(args.depositar, args.data)
    elif args.retirar is not None:
        cmd_retirar(args.retirar, args.destino)
    elif args.atualizar is not None:
        if not args.data_deposito:
            print("Erro: --atualizar-saldo requer --data-deposito YYYY-MM-DD")
            sys.exit(1)
        cmd_atualizar(args.atualizar, args.data_deposito)
    elif args.checar is not None:
        cmd_checar_aporte(args.checar)


if __name__ == "__main__":
    main()
