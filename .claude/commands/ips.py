"""
ips.py — Exibir ou abrir o IPS do usuário.
Uso:
    python sbwaa.py /ips
    python sbwaa.py /ips --editar
"""

import sys
import os
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
IPS_PATH = PROJECT_ROOT / "vault" / "00-portfolio" / "ips.md"


def exibir_ips():
    if not IPS_PATH.exists():
        print("\n❌ IPS não encontrado em vault/00-portfolio/ips.md")
        print("   Crie o arquivo com seu perfil de risco e limites.\n")
        return

    conteudo = IPS_PATH.read_text(encoding="utf-8")
    print(f"\n{'═'*55}")
    print("  SBWAA — IPS | Investment Policy Statement")
    print(f"{'═'*55}\n")
    # Exibir sem frontmatter
    linhas = conteudo.splitlines()
    em_frontmatter = False
    for i, linha in enumerate(linhas):
        if i == 0 and linha.strip() == "---":
            em_frontmatter = True
            continue
        if em_frontmatter and linha.strip() == "---":
            em_frontmatter = False
            continue
        if not em_frontmatter:
            print(f"  {linha}")
    print(f"\n{'═'*55}\n")
    print(f"  Arquivo: {IPS_PATH.relative_to(PROJECT_ROOT)}")
    print(f"  Editar:  python sbwaa.py /ips --editar\n")


def main():
    parser = argparse.ArgumentParser(description="IPS — SBWAA")
    parser.add_argument("--editar", action="store_true")
    args = parser.parse_args()

    if args.editar:
        editor = os.environ.get("EDITOR", "notepad" if sys.platform == "win32" else "nano")
        os.system(f'{editor} "{IPS_PATH}"')
    else:
        exibir_ips()


if __name__ == "__main__":
    main()
