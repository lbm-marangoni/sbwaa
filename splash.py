"""
splash.py — Tela de boas-vindas do SBWAA.
Exibida automaticamente pelo iniciar.vbs a cada abertura do sistema.
"""
import os
import re
import sys
import time
import ctypes
from datetime import datetime
from pathlib import Path

try:
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
except Exception:
    pass
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT  = Path(__file__).resolve().parent
DELAY = 4

BANNER = [
    "   ███████╗██████╗ ██╗    ██╗ █████╗  █████╗ ",
    "   ██╔════╝██╔══██╗██║    ██║██╔══██╗██╔══██╗",
    "   ███████╗██████╔╝██║ █╗ ██║███████║███████║",
    "   ╚════██║██╔══██╗██║███╗██║██╔══██║██╔══██║",
    "   ███████║██████╔╝╚███╔███╔╝██║  ██║██║  ██║",
    "   ╚══════╝╚═════╝  ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝",
]


def get_version():
    try:
        txt = (ROOT / "VERSION.md").read_text(encoding="utf-8")
        m = re.search(r"v\d+\.\d+\.\d+", txt)
        return m.group(0) if m else "v?.?.?"
    except Exception:
        return "v?.?.?"


def main():
    os.system("title SBWAA")
    os.system("mode con: cols=72 lines=23")

    version = get_version()
    now     = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

    W      = 70
    top    = "╔" + "═" * W + "╗"
    bottom = "╚" + "═" * W + "╝"
    empty  = "║" + " " * W + "║"

    def row(text="", align="center"):
        inner = text.center(W) if align == "center" else ("  " + text).ljust(W)
        return "║" + inner + "║"

    screen = [top, empty]
    for b in BANNER:
        screen.append(row(b))
    screen += [
        empty,
        row("Second Brain Wealth + Asset + Assessor Individual"),
        empty,
        row(f"{version:<30}{now:>36}"),
        empty,
        row("Iniciando...", "left"),
        row("  >> Obsidian", "left"),
        row("  >> VS Code  (Claude Code)", "left"),
        row("  >> Painel SBWAA", "left"),
        empty,
        bottom,
    ]

    print("\n".join(screen))
    print()

    for i in range(DELAY, 0, -1):
        sys.stdout.write(f"\r  Fechando em {i}s...   ")
        sys.stdout.flush()
        time.sleep(1)
    print()


if __name__ == "__main__":
    main()
