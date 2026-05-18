"""
check_session_compliance.py — Auditoria de conformidade ao encerrar sessão SBWAA.
Roda automaticamente via Claude Code Stop hook (.claude/settings.json).
"""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent


def _ler(path: Path, linhas: int = 20) -> str:
    if not path.exists():
        return ""
    return "\n".join(path.read_text(encoding="utf-8").splitlines()[:linhas])


def _extrair_versao(texto: str) -> str:
    m = re.search(r"v(\d+\.\d+\.\d+)", texto)
    return m.group(0) if m else "?"


def main():
    print("\n" + "=" * 55)
    print("  SBWAA -- Compliance Check de Sessao")
    print("=" * 55)

    # 1. Versão canônica
    version_txt = _ler(ROOT / "VERSION.md")
    versao_atual = _extrair_versao(version_txt)
    print(f"\n  Versao canonica (VERSION.md): {versao_atual}")

    # 2. README.md
    readme_txt = _ler(ROOT / "README.md", 10)
    versao_readme = _extrair_versao(readme_txt)
    status_readme = "[OK]" if versao_readme == versao_atual else f"[FAIL] desatualizado ({versao_readme})"
    print(f"  README.md:         {status_readme}")

    # 3. GUIA-COMANDOS.md
    guia_txt = _ler(ROOT / "GUIA-COMANDOS.md", 10)
    versao_guia = _extrair_versao(guia_txt)
    status_guia = "[OK]" if versao_guia == versao_atual else f"[FAIL] desatualizado ({versao_guia})"
    print(f"  GUIA-COMANDOS.md:  {status_guia}")

    # 4. CHANGELOG.md tem entrada para versão atual?
    changelog_txt = _ler(ROOT / "CHANGELOG.md", 5)
    tem_changelog = versao_atual.lstrip("v") in changelog_txt
    status_cl = "[OK]" if tem_changelog else f"[FAIL] faltando entrada para {versao_atual}"
    print(f"  CHANGELOG.md:      {status_cl}")

    # 5. Git status
    print()
    try:
        r = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, cwd=ROOT, timeout=10
        )
        import re as _re
        linhas_git = [l for l in r.stdout.strip().splitlines() if l.strip()]
        # Separar arquivos temporarios (GUIDs, ~$, .tmp) dos arquivos reais
        _guid = _re.compile(r"\{[0-9A-Fa-f\-]{30,}\}")
        temporarios = [l for l in linhas_git if _guid.search(l) or "~$" in l or l.strip().endswith(".tmp")]
        reais = [l for l in linhas_git if l not in temporarios]

        if temporarios:
            print(f"  [WARN] Arquivos temporarios do Windows detectados ({len(temporarios)}) -- apagar e ignorar via .gitignore:")
            for l in temporarios:
                print(f"     {l.strip()}")
        if reais:
            print(f"  [WARN] Git -- {len(reais)} arquivo(s) com mudancas nao commitadas:")
            for l in reais[:10]:
                print(f"     {l}")
            if len(reais) > 10:
                print(f"     ... e mais {len(reais) - 10}")
        if not reais and not temporarios:
            print("  [OK] Git -- working tree limpo")
    except Exception as e:
        print(f"  ⚠️  Git check falhou: {e}")

    # 6. Resumo
    ok = all([
        versao_readme == versao_atual,
        versao_guia == versao_atual,
        tem_changelog,
    ])
    print()
    if ok:
        print("  [OK] Docs em conformidade com VERSION.md")
    else:
        print("  [FAIL] ACAO NECESSARIA: atualize os arquivos marcados acima")
        print("     antes de encerrar a sessao (ver CLAUDE.md -- PROTOCOLO DE SESSAO)")

    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()
