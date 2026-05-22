#!/usr/bin/env python3
"""
SBWAA — Painel de controle (customtkinter)
Uso: python ui.py  |  python sbwaa.py /ui
"""

import os
import sys
import threading
import subprocess
from datetime import datetime
from pathlib import Path

import customtkinter as ctk

os.environ["PYTHONUTF8"] = "1"
PROJECT_ROOT = Path(__file__).resolve().parent

# pythonw.exe (usado pelo iniciar.bat) não tem stdout — usar python.exe explicitamente
_exe = Path(sys.executable)
PYTHON_EXE = str(_exe.parent / "python.exe") if _exe.name.lower() == "pythonw.exe" else sys.executable

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

TIPOS_ATIVO = [
    "acao-on", "acao-pn", "fii", "etf-br", "etf-intl",
    "renda-fixa", "tesouro", "debenture", "cri-cra",
]


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SBWAA")
        self.geometry("980x700")
        self.minsize(820, 600)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=2)

        self._build_header()
        self._build_tabs()
        self._build_output()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_header(self):
        h = ctk.CTkFrame(self, height=46, corner_radius=0)
        h.grid(row=0, column=0, sticky="ew")
        h.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(h, text="SBWAA", font=ctk.CTkFont(size=17, weight="bold")).grid(
            row=0, column=0, padx=14, pady=10)
        ctk.CTkLabel(h, text="Second Brain Wealth + Asset + Assessor Individual",
                     text_color="gray60").grid(row=0, column=1, padx=4, sticky="w")
        ctk.CTkLabel(h, text="v2.7.0", text_color="gray50",
                     font=ctk.CTkFont(size=11)).grid(row=0, column=2, padx=14)

    def _build_tabs(self):
        wrap = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        wrap.grid(row=1, column=0, sticky="nsew", padx=8, pady=(6, 0))
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_rowconfigure(0, weight=1)

        self.tabs = ctk.CTkTabview(wrap)
        self.tabs.grid(row=0, column=0, sticky="nsew")

        self._tab_portfolio()
        self._tab_analise()
        self._tab_mercado()
        self._tab_relatorios()
        self._tab_knowledge()

    def _build_output(self):
        frame = ctk.CTkFrame(self, corner_radius=6)
        frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=8)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        bar = ctk.CTkFrame(frame, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(6, 0))
        ctk.CTkLabel(bar, text="Output", font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkButton(bar, text="Limpar", width=65, height=22,
                      command=self._clear_output).pack(side="right")

        self.output = ctk.CTkTextbox(
            frame, font=ctk.CTkFont(family="Consolas", size=12),
            wrap="none",
        )
        self.output.grid(row=1, column=0, sticky="nsew", padx=10, pady=(4, 8))
        self.output.configure(state="disabled")

    # ── Aba Portfólio ─────────────────────────────────────────────────────────

    def _tab_portfolio(self):
        tab = self.tabs.add("Portfólio")
        tab.grid_columnconfigure(0, weight=1)

        # Botões rápidos — linha 1
        row0 = ctk.CTkFrame(tab, fg_color="transparent")
        row0.grid(row=0, column=0, sticky="ew", padx=4, pady=(10, 2))
        for label, slug in [
            ("Carteira", "/carteira"),
            ("Watchlist", "/watchlist"),
            ("Risco Carteira", "/risco-carteira"),
            ("Otimizar Expansão", "/otimizar-expansao"),
        ]:
            ctk.CTkButton(row0, text=label, width=150,
                          command=lambda s=slug: self._local([s])
                          ).pack(side="left", padx=4)

        # Botões rápidos — linha 2
        row0b = ctk.CTkFrame(tab, fg_color="transparent")
        row0b.grid(row=1, column=0, sticky="ew", padx=4, pady=(2, 4))
        for label, slug in [
            ("Dividendos", "/dividendos"),
            ("Snapshot Mercado", "/snapshot"),
            ("IPS", "/ips"),
            ("Metas", "/metas"),
        ]:
            ctk.CTkButton(row0b, text=label, width=150,
                          command=lambda s=slug: self._local([s])
                          ).pack(side="left", padx=4)

        self._sep(tab, row=2)
        ctk.CTkLabel(tab, text="Adicionar ativo",
                     font=ctk.CTkFont(weight="bold")).grid(row=3, column=0, sticky="w", padx=10, pady=(4, 2))

        form = ctk.CTkFrame(tab, fg_color="transparent")
        form.grid(row=4, column=0, sticky="ew", padx=4, pady=4)

        self.f_ticker = self._labeled_entry(form, col=0, label="Ticker", placeholder="PETR4", width=88)
        self.f_tipo   = self._labeled_combo(form, col=2, label="Tipo",   values=TIPOS_ATIVO, default="acao-on", width=120)
        self.f_qtd    = self._labeled_entry(form, col=4, label="Qtd",    placeholder="100",   width=72)
        self.f_pm     = self._labeled_entry(form, col=6, label="P. Médio", placeholder="45.50", width=80)
        self.f_setor  = self._labeled_entry(form, col=8, label="Setor",  placeholder="energia", width=100)

        self.f_skip = ctk.CTkCheckBox(form, text="Skip validação", width=120)
        self.f_skip.grid(row=1, column=0, columnspan=2, padx=4, pady=(6, 0), sticky="w")

        ctk.CTkLabel(form, text="Data entrada").grid(row=1, column=2, padx=(8, 2), sticky="w")
        self.f_data = ctk.CTkEntry(form, placeholder_text=datetime.now().strftime("%Y-%m-%d"), width=104)
        self.f_data.grid(row=1, column=3, padx=(0, 6), pady=(6, 0))
        ctk.CTkLabel(form, text="(vazio = hoje)", text_color="gray55",
                     font=ctk.CTkFont(size=10)).grid(row=1, column=4, padx=(0, 4), sticky="w")

        ctk.CTkButton(form, text="Adicionar", width=100,
                      command=self._adicionar).grid(row=1, column=8, columnspan=2, padx=4, pady=(6, 0))

        ctk.CTkLabel(
            tab,
            text="Tipos: acao-on | acao-pn | fii | etf-br | etf-intl | renda-fixa | tesouro | debenture | cri-cra",
            text_color="gray55", font=ctk.CTkFont(size=11),
        ).grid(row=5, column=0, sticky="w", padx=10, pady=(4, 0))

        self._sep(tab, row=6)
        ctk.CTkLabel(tab, text="Registrar venda",
                     font=ctk.CTkFont(weight="bold")).grid(row=7, column=0, sticky="w", padx=10, pady=(4, 2))

        vform = ctk.CTkFrame(tab, fg_color="transparent")
        vform.grid(row=8, column=0, sticky="ew", padx=4, pady=4)

        self.v_ticker = self._labeled_entry(vform, col=0, label="Ticker",   placeholder="PETR4",  width=88)
        self.v_qtd    = self._labeled_entry(vform, col=2, label="Qtd",      placeholder="50",     width=72)
        self.v_preco  = self._labeled_entry(vform, col=4, label="Preço",    placeholder="45.00",  width=80)
        self.v_data   = self._labeled_entry(vform, col=6, label="Data",     placeholder=datetime.now().strftime("%Y-%m-%d"), width=104)
        ctk.CTkLabel(vform, text="(vazio = hoje)", text_color="gray55",
                     font=ctk.CTkFont(size=10)).grid(row=0, column=8, padx=(0, 4), sticky="w")

        ctk.CTkButton(vform, text="Vender", width=100, fg_color="#8B1A1A", hover_color="#6B1010",
                      command=self._vender).grid(row=1, column=0, columnspan=3, padx=4, pady=(6, 0), sticky="w")

    # ── Aba Análise (IA) ──────────────────────────────────────────────────────

    def _tab_analise(self):
        tab = self.tabs.add("Análise (IA)")
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="Ticker",
                     font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 2))

        row1 = ctk.CTkFrame(tab, fg_color="transparent")
        row1.grid(row=1, column=0, sticky="ew", padx=4)
        self.a_ticker = ctk.CTkEntry(row1, placeholder_text="PETR4", width=100)
        self.a_ticker.pack(side="left", padx=4)
        for label, slash in [
            ("Analisar (pipeline)", "analisar"),
            ("Tese rápida", "tese"),
            ("Earnings", "earnings"),
            ("PM — Decisão", "pm"),
        ]:
            ctk.CTkButton(row1, text=label, width=140,
                          command=lambda s=slash: self._ia_ticker(s, self.a_ticker)
                          ).pack(side="left", padx=4)

        self._sep(tab, row=2)
        ctk.CTkLabel(tab, text="Comparar dois ativos",
                     font=ctk.CTkFont(weight="bold")).grid(row=3, column=0, sticky="w", padx=10, pady=(0, 2))

        row2 = ctk.CTkFrame(tab, fg_color="transparent")
        row2.grid(row=4, column=0, sticky="ew", padx=4)
        self.c_t1 = ctk.CTkEntry(row2, placeholder_text="PETR4", width=100)
        self.c_t2 = ctk.CTkEntry(row2, placeholder_text="VALE3", width=100)
        self.c_t1.pack(side="left", padx=4)
        ctk.CTkLabel(row2, text="vs").pack(side="left", padx=2)
        self.c_t2.pack(side="left", padx=4)
        ctk.CTkButton(row2, text="Comparar", width=110,
                      command=self._comparar).pack(side="left", padx=8)

        self._ia_note(tab, row=5)

    # ── Aba Mercado ───────────────────────────────────────────────────────────

    def _tab_mercado(self):
        tab = self.tabs.add("Mercado")
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="Diário / Macro  (IA — copiado para clipboard)",
                     font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 4))

        row1 = ctk.CTkFrame(tab, fg_color="transparent")
        row1.grid(row=1, column=0, sticky="ew", padx=4)
        for label, slash in [
            ("Morning Call", "morning-call"),
            ("Mundo Econômico", "mundo-economico"),
            ("Investimento do Dia", "investimento-do-dia"),
        ]:
            ctk.CTkButton(row1, text=label, width=160,
                          command=lambda s=slash: self._ia_noarg(s)
                          ).pack(side="left", padx=4)

        self._sep(tab, row=2)
        ctk.CTkLabel(tab, text="Stress Test  (local — sem IA)",
                     font=ctk.CTkFont(weight="bold")).grid(row=3, column=0, sticky="w", padx=10, pady=(0, 4))

        row2 = ctk.CTkFrame(tab, fg_color="transparent")
        row2.grid(row=4, column=0, sticky="ew", padx=4)
        for label, arg in [
            ("Todos os cenários", None),
            ("Crise 2008", "crise-2008"),
            ("COVID-2020", "covid-2020"),
            ("Eleições 2022", "eleicoes-2022"),
            ("Lula 2002", "lula-2002"),
        ]:
            extra = [arg] if arg else []
            ctk.CTkButton(row2, text=label, width=130,
                          command=lambda e=extra: self._local(["/stress-test"] + e)
                          ).pack(side="left", padx=4)

        row3 = ctk.CTkFrame(tab, fg_color="transparent")
        row3.grid(row=5, column=0, sticky="ew", padx=4, pady=(10, 0))
        ctk.CTkLabel(row3, text="Choque custom:").pack(side="left", padx=4)
        self.stress_val = ctk.CTkEntry(row3, placeholder_text="-20", width=72)
        self.stress_val.pack(side="left", padx=4)
        ctk.CTkLabel(row3, text="%").pack(side="left")
        ctk.CTkButton(row3, text="Simular", width=90,
                      command=self._stress_custom).pack(side="left", padx=8)

    # ── Aba Relatórios (IA) ───────────────────────────────────────────────────

    def _tab_relatorios(self):
        tab = self.tabs.add("Relatórios (IA)")
        tab.grid_columnconfigure(0, weight=1)

        row = ctk.CTkFrame(tab, fg_color="transparent")
        row.grid(row=0, column=0, sticky="ew", padx=4, pady=(14, 4))
        for label, slash in [
            ("Relatório Semanal", "relatorio-semanal"),
            ("Relatório Mensal", "relatorio-mensal"),
            ("Rebalancear vs IPS", "rebalancear"),
            ("Revisar Carteira", "revisar-carteira"),
        ]:
            ctk.CTkButton(row, text=label, width=160,
                          command=lambda s=slash: self._ia_noarg(s)
                          ).pack(side="left", padx=4)

        self._ia_note(tab, row=1)

    # ── Aba Knowledge ─────────────────────────────────────────────────────────

    def _tab_knowledge(self):
        tab = self.tabs.add("Knowledge")
        tab.grid_columnconfigure(0, weight=1)

        row1 = ctk.CTkFrame(tab, fg_color="transparent")
        row1.grid(row=0, column=0, sticky="ew", padx=4, pady=(10, 4))
        for label, args in [
            ("Status",      ["/knowledge", "--status"]),
            ("Coletar RSS", ["/knowledge", "--coletar-rss"]),
            ("Listar",      ["/knowledge", "--listar"]),
        ]:
            ctk.CTkButton(row1, text=label, width=120,
                          command=lambda a=args: self._local(a)
                          ).pack(side="left", padx=4)

        self._sep(tab, row=1)

        row2 = ctk.CTkFrame(tab, fg_color="transparent")
        row2.grid(row=2, column=0, sticky="ew", padx=4, pady=4)
        ctk.CTkLabel(row2, text="Buscar:").pack(side="left", padx=4)
        self.k_busca = ctk.CTkEntry(row2, placeholder_text="valuation petróleo Brasil", width=300)
        self.k_busca.pack(side="left", padx=4)
        ctk.CTkButton(row2, text="Buscar", width=80,
                      command=self._kb_buscar).pack(side="left", padx=4)

        row3 = ctk.CTkFrame(tab, fg_color="transparent")
        row3.grid(row=3, column=0, sticky="ew", padx=4, pady=4)
        ctk.CTkLabel(row3, text="Indexar:").pack(side="left", padx=4)
        self.k_path = ctk.CTkEntry(row3, placeholder_text=r"C:\caminho\para\arquivo.pdf", width=300)
        self.k_path.pack(side="left", padx=4)
        ctk.CTkButton(row3, text="Adicionar", width=80,
                      command=self._kb_add).pack(side="left", padx=4)

    # ── Ações ──────────────────────────────────────────────────────────────────

    def _local(self, args: list):
        cmd = [PYTHON_EXE, str(PROJECT_ROOT / "sbwaa.py")] + args
        self._clear_output()
        self._append(f"> {' '.join(args)}\n")
        threading.Thread(target=self._run_proc, args=(cmd,), daemon=True).start()

    def _run_proc(self, cmd: list):
        env = {**os.environ, "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"}
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                cwd=str(PROJECT_ROOT), env=env,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            for line in proc.stdout:
                self.after(0, self._append, line)
            proc.wait()
            self.after(0, self._append, f"[concluído — código {proc.returncode}]\n")
        except Exception as e:
            self.after(0, self._append, f"Erro: {e}\n")

    def _ia_ticker(self, slash: str, entry: ctk.CTkEntry):
        ticker = entry.get().strip().upper()
        if not ticker:
            self._append("Informe o ticker.\n")
            return
        self._clipboard(f"/{slash} {ticker}")

    def _ia_noarg(self, slash: str):
        self._clipboard(f"/{slash}")

    def _comparar(self):
        t1 = self.c_t1.get().strip().upper()
        t2 = self.c_t2.get().strip().upper()
        if not t1 or not t2:
            self._append("Informe os dois tickers.\n")
            return
        self._clipboard(f"/comparar {t1} {t2}")

    def _adicionar(self):
        ticker = self.f_ticker.get().strip().upper()
        tipo   = self.f_tipo.get().strip()
        qtd    = self.f_qtd.get().strip()
        pm     = self.f_pm.get().strip()
        setor  = self.f_setor.get().strip()
        data   = self.f_data.get().strip()
        if not all([ticker, tipo, qtd, pm, setor]):
            self._append("Preencha todos os campos antes de adicionar.\n")
            return
        args = ["/adicionar", "--ticker", ticker, "--tipo", tipo,
                "--quantidade", qtd, "--preco-medio", pm, "--setor", setor]
        if data:
            args += ["--data", data]
        if self.f_skip.get():
            args.append("--skip-validacao")
        self._local(args)

    def _vender(self):
        ticker = self.v_ticker.get().strip().upper()
        qtd    = self.v_qtd.get().strip()
        preco  = self.v_preco.get().strip()
        data   = self.v_data.get().strip()
        if not all([ticker, qtd, preco]):
            self._append("Preencha Ticker, Qtd e Preço antes de vender.\n")
            return
        args = ["/vender", "--ticker", ticker, "--quantidade", qtd, "--preco", preco]
        if data:
            args += ["--data", data]
        self._local(args)

    def _stress_custom(self):
        val = self.stress_val.get().strip()
        if not val:
            self._append("Informe o valor do choque (ex: -20).\n")
            return
        try:
            float(val)
        except ValueError:
            self._append("Valor inválido. Use número (ex: -20 ou 15).\n")
            return
        self._local(["/stress-test", "custom", val])

    def _kb_buscar(self):
        q = self.k_busca.get().strip()
        if not q:
            self._append("Informe a query de busca.\n")
            return
        self._local(["/knowledge", "--buscar", q])

    def _kb_add(self):
        p = self.k_path.get().strip()
        if not p:
            self._append("Informe o caminho do arquivo ou pasta.\n")
            return
        self._local(["/knowledge", "--adicionar", p])

    def _clipboard(self, cmd: str):
        self._clear_output()
        try:
            self.clipboard_clear()
            self.clipboard_append(cmd)
            self.update()
            self._append(
                f"[IA] Comando copiado para o clipboard:\n"
                f"     {cmd}\n\n"
                f"     Cole no chat do Claude Code para executar.\n"
            )
        except Exception:
            self._append(f"[IA] Digite no Claude Code: {cmd}\n")

    def _append(self, text: str):
        self.output.configure(state="normal")
        self.output.insert("end", text)
        self.output.see("end")
        self.output.configure(state="disabled")

    def _clear_output(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    # ── Helpers de layout ──────────────────────────────────────────────────────

    def _sep(self, parent, row: int):
        ctk.CTkFrame(parent, height=1, fg_color="gray30").grid(
            row=row, column=0, sticky="ew", padx=4, pady=8)

    def _ia_note(self, parent, row: int):
        ctk.CTkLabel(
            parent,
            text="Comandos de IA: o botão copia o comando para o clipboard — cole no chat do Claude Code.",
            text_color="gray55", font=ctk.CTkFont(size=11),
        ).grid(row=row, column=0, sticky="w", padx=10, pady=(10, 0))

    def _labeled_entry(self, parent, col, label, placeholder, width) -> ctk.CTkEntry:
        ctk.CTkLabel(parent, text=label).grid(row=0, column=col, padx=(8, 2), sticky="w")
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, width=width)
        entry.grid(row=0, column=col + 1, padx=(0, 6))
        return entry

    def _labeled_combo(self, parent, col, label, values, default, width) -> ctk.CTkComboBox:
        ctk.CTkLabel(parent, text=label).grid(row=0, column=col, padx=(8, 2), sticky="w")
        combo = ctk.CTkComboBox(parent, values=values, width=width)
        combo.set(default)
        combo.grid(row=0, column=col + 1, padx=(0, 6))
        return combo


if __name__ == "__main__":
    App().mainloop()
