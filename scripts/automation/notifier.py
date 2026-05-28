"""
SBWAA Automation — Notificações Windows

Toast notification via PowerShell/Windows Forms — sem dependências externas.
Usa System.Windows.Forms.NotifyIcon (disponível em qualquer Windows com .NET).
"""

import logging
import subprocess

log = logging.getLogger("sbwaa.notifier")


def notify(title: str, body: str):
    """Exibe balloon tip na bandeja do sistema (tray). Não bloqueia."""
    title_safe = title.replace("'", "\\'").replace('"', '`"')
    body_safe = body.replace("'", "\\'").replace('"', '`"')

    # NotifyIcon via Windows Forms — disponível nativamente no Windows
    script = f"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$n = New-Object System.Windows.Forms.NotifyIcon
$n.Icon = [System.Drawing.SystemIcons]::Information
$n.Visible = $true
$n.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Info
$n.BalloonTipTitle = '{title_safe}'
$n.BalloonTipText = '{body_safe}'
$n.ShowBalloonTip(8000)
Start-Sleep -Milliseconds 9000
$n.Dispose()
"""
    try:
        subprocess.Popen(
            [
                "powershell",
                "-WindowStyle", "Hidden",
                "-NonInteractive",
                "-NoProfile",
                "-Command", script,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
    except Exception as e:
        log.warning(f"Notificação falhou: {e}")
