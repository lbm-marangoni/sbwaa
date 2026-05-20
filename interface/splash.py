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


def _resize_center_topmost(cols=72, lines=23):
    try:
        HWND_TOPMOST   = -1
        SWP_SHOWWINDOW = 0x0040
        SM_CXSCREEN    = 0
        SM_CYSCREEN    = 1
        STD_OUTPUT     = -11

        user32   = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        hwnd = kernel32.GetConsoleWindow()
        hout = kernel32.GetStdHandle(STD_OUTPUT)
        if not hwnd or not hout:
            return

        class COORD(ctypes.Structure):
            _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

        class SMALL_RECT(ctypes.Structure):
            _fields_ = [("Left",  ctypes.c_short), ("Top",    ctypes.c_short),
                        ("Right", ctypes.c_short), ("Bottom", ctypes.c_short)]

        class RECT(ctypes.Structure):
            _fields_ = [("left",  ctypes.c_long), ("top",    ctypes.c_long),
                        ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

        # Encolhe primeiro para evitar conflito buffer vs janela
        kernel32.SetConsoleWindowInfo(hout, True,
            ctypes.byref(SMALL_RECT(0, 0, 1, 1)))
        kernel32.SetConsoleScreenBufferSize(hout, COORD(cols, lines))
        kernel32.SetConsoleWindowInfo(hout, True,
            ctypes.byref(SMALL_RECT(0, 0, cols - 1, lines - 1)))

        time.sleep(0.05)  # garante que o Win32 aplica o resize antes de medir

        rect = RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        win_w = rect.right  - rect.left
        win_h = rect.bottom - rect.top

        screen_w = user32.GetSystemMetrics(SM_CXSCREEN)
        screen_h = user32.GetSystemMetrics(SM_CYSCREEN)

        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2

        user32.SetWindowPos(hwnd, HWND_TOPMOST, x, y, 0, 0, SWP_SHOWWINDOW)
    except Exception:
        pass


def main():
    os.system("title SBWAA")
    _resize_center_topmost()

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
