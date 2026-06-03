#!/usr/bin/env python3
"""
SBWAA — Painel de controle (customtkinter) — Terminal UI
Uso: python ui.py  |  python sbwaa.py /ui
"""

import os
import sys
import json
import threading
import subprocess
from datetime import date, datetime, timedelta
from pathlib import Path

import customtkinter as ctk

os.environ["PYTHONUTF8"] = "1"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR    = PROJECT_ROOT / "scripts" / "data" / "cache"

_exe = Path(sys.executable)
PYTHON_EXE = str(_exe.parent / "python.exe") if _exe.name.lower() == "pythonw.exe" else sys.executable

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

TIPOS_ATIVO = [
    "acao-on", "acao-pn", "fii", "etf-br", "etf-intl",
    "renda-fixa", "tesouro", "debenture", "cri-cra",
]

# ── Versão ────────────────────────────────────────────────────────────────────
try:
    _ver_raw = (PROJECT_ROOT / "VERSION.md").read_text(encoding="utf-8").strip()
    VERSION  = next((l.strip("# ").strip() for l in _ver_raw.splitlines() if l.strip()), "—")
except Exception:
    VERSION = "2.8.9"

# ── Paleta terminal ───────────────────────────────────────────────────────────
BG      = "#09090F"   # fundo principal
SURF    = "#0D0D18"   # sidebar / header
ELEV    = "#131320"   # inputs / botões
BORDER  = "#1C1C2C"   # separadores
ACC     = "#00D4FF"   # ciano accent
ACC_DIM = "#008EA8"   # accent hover
ACC_BG  = "#001C24"   # accent fundo sutil
NAV_ACT = "#12122A"   # sidebar item ativo
TXT     = "#C8C8DC"   # texto primário
TXT2    = "#46465E"   # texto secundário
POS     = "#00CC66"   # positivo
NEG     = "#FF3355"   # negativo

# Fontes criadas em App.__init__ após a janela Tk existir
MONO_SM = MONO = MONO_B = MONO_LG = MONO_XL = None


class App(ctk.CTk):

    def __init__(self):
        super().__init__()
        # Fontes exigem janela Tk ativa
        global MONO_SM, MONO, MONO_B, MONO_LG, MONO_XL
        MONO_SM = ctk.CTkFont(family="Consolas", size=11)
        MONO    = ctk.CTkFont(family="Consolas", size=12)
        MONO_B  = ctk.CTkFont(family="Consolas", size=12, weight="bold")
        MONO_LG = ctk.CTkFont(family="Consolas", size=14, weight="bold")
        MONO_XL = ctk.CTkFont(family="Consolas", size=15, weight="bold")

        self.configure(fg_color=BG)
        self.title("SBWAA")
        self.geometry("1400x900")
        self.minsize(1050, 700)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._active_page = None
        self._nav_buttons: dict = {}
        self._pages:       dict = {}
        self._toast_job         = None

        self._build_header()
        self._build_body()
        self._build_toast()
        self._nav_select("portfolio")
        self._tick()
        self.after(400, self._load_header_data)
        self.after(700, self._check_tese_queue)

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = ctk.CTkFrame(self, height=52, corner_radius=0, fg_color=SURF)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(99, weight=1)   # empurra relógio p/ direita

        ctk.CTkLabel(hdr, text="◆ SBWAA", font=MONO_XL,
                     text_color=ACC).grid(row=0, column=0, padx=(16, 28), pady=8)

        self._hdr_ibov  = self._hdr_widget(hdr, col=1,  label="IBOV")
        self._hdr_brl   = self._hdr_widget(hdr, col=2,  label="BRL/USD")
        self._hdr_selic = self._hdr_widget(hdr, col=3,  label="SELIC")
        self._hdr_pat   = self._hdr_widget(hdr, col=4,  label="PATRIMÔNIO")
        self._hdr_prov  = self._hdr_widget(hdr, col=5,  label="PROVENTOS")

        # Separador direito
        ctk.CTkFrame(hdr, width=1, height=34, fg_color=BORDER
                     ).grid(row=0, column=98, padx=16)

        ver_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        ver_frame.grid(row=0, column=99, padx=(0, 16), sticky="e")
        ctk.CTkLabel(ver_frame, text=f"v{VERSION}", font=MONO_SM,
                     text_color=TXT2).pack(side="top")
        self._clock_lbl = ctk.CTkLabel(ver_frame, text="--:--:--",
                                        font=MONO_B, text_color=TXT2)
        self._clock_lbl.pack(side="top")

    def _hdr_widget(self, parent, col: int, label: str) -> ctk.CTkLabel:
        """Cria um widget de dado no header; retorna o label de valor."""
        sep = ctk.CTkFrame(parent, width=1, height=34, fg_color=BORDER)
        sep.grid(row=0, column=col * 2 - 1, padx=0)
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=0, column=col * 2, padx=16, pady=4)
        ctk.CTkLabel(f, text=label, font=MONO_SM, text_color=TXT2).pack()
        val = ctk.CTkLabel(f, text="—", font=MONO_B, text_color=TXT)
        val.pack()
        return val

    def _tick(self):
        self._clock_lbl.configure(text=datetime.now().strftime("%H:%M:%S"))
        self.after(1000, self._tick)

    def _load_header_data(self):
        today = datetime.now().strftime("%Y-%m-%d")

        # Selic
        try:
            bcb_f = CACHE_DIR / f"bcb_{today}.json"
            if bcb_f.exists():
                d = json.loads(bcb_f.read_text(encoding="utf-8"))
                s = d.get("selic_anual_pct")
                if s is not None:
                    self._hdr_selic.configure(text=f"{s:.2f}%", text_color=TXT)
        except Exception:
            pass

        # IBOV
        try:
            bvsp_f = next(CACHE_DIR.glob(f"yahoo_INDICE_BVSP_{today}.json"), None)
            if bvsp_f and bvsp_f.exists():
                d = json.loads(bvsp_f.read_text(encoding="utf-8"))
                val = d.get("cotacao_atual")
                var = d.get("variacao_dia_pct")
                if val is not None:
                    sign  = "▲" if var and var >= 0 else "▼"
                    color = POS  if var and var >= 0 else NEG
                    txt = f"{val:,.0f}  {sign}{abs(var):.2f}%" if var is not None else f"{val:,.0f}"
                    self._hdr_ibov.configure(text=txt, text_color=color)
        except Exception:
            pass

        # BRL/USD
        try:
            brl_f = next(CACHE_DIR.glob(f"yahoo_BRL_X_{today}.json"), None)
            if brl_f and brl_f.exists():
                d = json.loads(brl_f.read_text(encoding="utf-8"))
                val = d.get("cotacao_atual")
                if val is not None:
                    self._hdr_brl.configure(text=f"{val:.4f}", text_color=TXT)
        except Exception:
            pass

        self.after(300_000, self._load_header_data)   # atualiza a cada 5 min

    # ── Body ──────────────────────────────────────────────────────────────────

    def _build_body(self):
        body = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)
        self._build_sidebar(body)
        self._build_main(body)

    def _build_sidebar(self, parent):
        side = ctk.CTkFrame(parent, width=162, corner_radius=0, fg_color=SURF)
        side.grid(row=0, column=0, sticky="nsew")
        side.grid_propagate(False)
        side.grid_columnconfigure(0, weight=1)

        ctk.CTkFrame(side, height=1, fg_color=BORDER
                     ).grid(row=0, column=0, sticky="ew")

        NAV = [
            ("portfolio",  "◈  Portfólio"),
            ("analise",    "⊕  Análise"),
            ("mercado",    "◉  Mercado"),
            ("relatorios", "▤  Relatórios"),
            ("knowledge",  "◎  Knowledge"),
        ]
        for i, (key, label) in enumerate(NAV, start=1):
            btn = ctk.CTkButton(
                side, text=label, anchor="w",
                font=MONO, height=40, corner_radius=0,
                fg_color="transparent", hover_color=NAV_ACT,
                text_color=TXT2, border_width=0,
                command=lambda k=key: self._nav_select(k),
            )
            btn.grid(row=i, column=0, sticky="ew")
            self._nav_buttons[key] = btn

        ctk.CTkFrame(side, height=1, fg_color=BORDER
                     ).grid(row=len(NAV) + 1, column=0, sticky="ew", pady=(8, 0))

        ctk.CTkButton(
            side, text="◈  Status Sistema", anchor="w",
            font=MONO_SM, height=36, corner_radius=0,
            fg_color="transparent", hover_color=NAV_ACT,
            text_color=TXT2, border_width=0,
            command=lambda: self._local(["/status"]),
        ).grid(row=len(NAV) + 2, column=0, sticky="ew")

    def _build_main(self, parent):
        main = ctk.CTkFrame(parent, corner_radius=0, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(0, weight=0)   # banner (oculto por padrão)
        main.grid_rowconfigure(1, weight=1)   # content_host
        main.grid_rowconfigure(2, weight=0)   # output

        # Banner de alertas (oculto até ter sinais COMPRAR)
        self._banner = ctk.CTkFrame(
            main, corner_radius=0,
            fg_color=ACC_BG, border_width=1, border_color=ACC,
        )
        # Não chama grid() — oculto até _check_tese_queue popular

        self._content_host = ctk.CTkFrame(main, corner_radius=0,
                                           fg_color="transparent")
        self._content_host.grid(row=1, column=0, sticky="nsew")
        self._content_host.grid_columnconfigure(0, weight=1)
        self._content_host.grid_rowconfigure(0, weight=1)

        self._pages["portfolio"]  = self._make_page_portfolio()
        self._pages["analise"]    = self._make_page_analise()
        self._pages["mercado"]    = self._make_page_mercado()
        self._pages["relatorios"] = self._make_page_relatorios()
        self._pages["knowledge"]  = self._make_page_knowledge()

        self._build_output(main, row=2)

    def _nav_select(self, key: str):
        if self._active_page and self._active_page in self._pages:
            self._pages[self._active_page].grid_remove()
        for k, btn in self._nav_buttons.items():
            if k == key:
                btn.configure(fg_color=NAV_ACT, text_color=ACC)
            else:
                btn.configure(fg_color="transparent", text_color=TXT2)
        self._pages[key].grid(row=0, column=0, sticky="nsew")
        self._active_page = key

    # ── Output ────────────────────────────────────────────────────────────────

    def _build_output(self, parent, row: int):
        wrap = ctk.CTkFrame(parent, corner_radius=0,
                            fg_color=SURF, height=230)
        wrap.grid(row=row, column=0, sticky="ew")
        wrap.grid_propagate(False)
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_rowconfigure(1, weight=1)

        bar = ctk.CTkFrame(wrap, fg_color="transparent", height=26)
        bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(6, 0))
        bar.grid_propagate(False)
        ctk.CTkLabel(bar, text="▸ OUTPUT", font=MONO_B,
                     text_color=ACC).pack(side="left")
        ctk.CTkButton(bar, text="limpar", width=52, height=18,
                      font=MONO_SM, fg_color=ELEV, hover_color=BORDER,
                      text_color=TXT2, corner_radius=3,
                      command=self._clear_output).pack(side="right")

        self.output = ctk.CTkTextbox(
            wrap, font=MONO_SM, wrap="none",
            fg_color=BG, text_color=TXT,
            border_width=1, border_color=BORDER,
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=ACC_DIM,
        )
        self.output.grid(row=1, column=0, sticky="nsew", padx=8, pady=(2, 8))
        self.output.configure(state="disabled")

    # ── Toast ─────────────────────────────────────────────────────────────────

    def _build_toast(self):
        self._toast = ctk.CTkFrame(self, fg_color=ACC_BG,
                                    border_width=1, border_color=ACC,
                                    corner_radius=6)
        self._toast_lbl = ctk.CTkLabel(self._toast, text="",
                                        font=MONO_SM, text_color=ACC)
        self._toast_lbl.pack(padx=14, pady=7)

    def _show_toast(self, msg: str, ms: int = 2500):
        if self._toast_job:
            self.after_cancel(self._toast_job)
        self._toast_lbl.configure(text=msg)
        self._toast.place(relx=0.985, rely=0.065, anchor="ne")
        self._toast_job = self.after(ms, self._hide_toast)

    def _hide_toast(self):
        self._toast.place_forget()
        self._toast_job = None

    # ── Banner de teses ───────────────────────────────────────────────────────

    def _check_tese_queue(self):
        """Lê fila de teses e exibe banner se houver sinais COMPRAR."""
        logs_dir = PROJECT_ROOT / "logs"
        queue_path = None
        for delta in range(2):
            d = (date.today() - timedelta(days=delta)).strftime("%Y-%m-%d")
            p = logs_dir / f"tese_queue_{d}.json"
            if p.exists():
                queue_path = p
                break
        if not queue_path:
            return

        try:
            data = json.loads(queue_path.read_text(encoding="utf-8"))
        except Exception:
            return

        comprar = []
        for ativo in data.get("ativos", []):
            if ativo.get("veredicto") != "COMPRAR":
                continue
            ticker  = ativo["ticker"]
            status  = ativo.get("status", "novo")
            tese_dt = ativo.get("tese_data", "")
            label   = ativo.get("label", "—")
            try:
                dias = (date.today() - datetime.strptime(tese_dt, "%Y-%m-%d").date()).days
            except Exception:
                dias = 999
            cmd = f"/analisar {ticker}" if (dias >= 60 or status == "novo") else f"/pm {ticker}"
            comprar.append({"ticker": ticker, "label": label, "status": status, "cmd": cmd})

        if not comprar:
            return

        self._populate_banner(comprar)

    def _populate_banner(self, sinais: list):
        for w in self._banner.winfo_children():
            w.destroy()

        n = len(sinais)

        # Título + fechar
        title_bar = ctk.CTkFrame(self._banner, fg_color="transparent")
        title_bar.pack(fill="x", padx=12, pady=(8, 4))
        ctk.CTkLabel(
            title_bar,
            text=f"⚡  Teses de hoje — {n} sinal{'is' if n > 1 else ''} COMPRAR",
            font=MONO_B, text_color=ACC,
        ).pack(side="left")
        ctk.CTkButton(
            title_bar, text="×", width=26, height=22,
            font=MONO_B, fg_color="transparent", hover_color=ELEV,
            text_color=TXT2, corner_radius=4,
            command=self._hide_banner,
        ).pack(side="right")

        # Linha por ativo
        for sinal in sinais:
            row = ctk.CTkFrame(self._banner, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=(0, 7))

            ctk.CTkLabel(row, text=sinal["ticker"],
                         font=MONO_B, text_color=TXT,
                         width=72, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=sinal["label"],
                         font=MONO_SM, text_color=TXT2,
                         width=90, anchor="w").pack(side="left")
            status_color = POS if sinal["status"] == "carteira" else ACC_DIM
            ctk.CTkLabel(row, text=sinal["status"],
                         font=MONO_SM, text_color=status_color,
                         width=72, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=f"→  {sinal['cmd']}",
                         font=MONO_SM, text_color=TXT,
                         width=210, anchor="w").pack(side="left", padx=(10, 0))
            ctk.CTkButton(
                row, text="📋 Copiar", width=82, height=24,
                font=MONO_SM, fg_color=ELEV, hover_color=BORDER,
                text_color=ACC, corner_radius=4,
                command=lambda c=sinal["cmd"]: self._clipboard(c),
            ).pack(side="left", padx=(8, 0))

        self._banner.grid(row=0, column=0, sticky="ew")

    def _hide_banner(self):
        self._banner.grid_remove()

    # ── Páginas ───────────────────────────────────────────────────────────────

    def _make_page_portfolio(self) -> ctk.CTkScrollableFrame:
        p = ctk.CTkScrollableFrame(self._content_host, corner_radius=0,
                                    fg_color="transparent",
                                    scrollbar_button_color=BORDER,
                                    scrollbar_button_hover_color=ACC_DIM)
        p.grid_columnconfigure(0, weight=1)

        self._section(p, "AÇÕES RÁPIDAS — LOCAL", row=0)

        r1 = self._row(p, row=1)
        for label, slug in [
            ("Carteira", "/carteira"), ("Watchlist", "/watchlist"),
            ("Risco Carteira", "/risco-carteira"), ("Dividendos", "/dividendos"),
            ("IPS", "/ips"),
        ]:
            self._btn_local(r1, label, lambda s=slug: self._local([s]))
        self._btn_local(r1, "Rever Watchlist", lambda: self._local(["/watchlist", "--rever"]))
        self._btn_ia(r1, "Editar IPS", lambda: self._clipboard("/ips --editar"))

        r2 = self._row(p, row=2)
        for label, slug in [
            ("Snapshot Mercado", "/snapshot"), ("Metas", "/metas"),
            ("Otimizar Expansão", "/otimizar-expansao"),
        ]:
            self._btn_local(r2, label, lambda s=slug: self._local([s]))

        self._sep(p, row=3)
        self._section(p, "SIMULAÇÃO MONTE CARLO — LOCAL", row=4)

        rsim = self._row(p, row=5)
        ctk.CTkLabel(rsim, text="Patrimônio (R$):", font=MONO_SM,
                     text_color=TXT2).pack(side="left", padx=(0, 4))
        self.sim_pat = ctk.CTkEntry(rsim, placeholder_text="opcional", width=100,
                                     font=MONO_SM, fg_color=ELEV,
                                     border_color=BORDER, text_color=TXT)
        self.sim_pat.pack(side="left", padx=(0, 14))
        ctk.CTkLabel(rsim, text="Aporte (R$):", font=MONO_SM,
                     text_color=TXT2).pack(side="left", padx=(0, 4))
        self.sim_ap = ctk.CTkEntry(rsim, placeholder_text="opcional", width=100,
                                    font=MONO_SM, fg_color=ELEV,
                                    border_color=BORDER, text_color=TXT)
        self.sim_ap.pack(side="left", padx=(0, 14))
        self.sim_ng = ctk.CTkCheckBox(rsim, text="Sem gráficos", font=MONO_SM,
                                       text_color=TXT2, fg_color=ACC,
                                       hover_color=ACC_DIM, border_color=BORDER,
                                       checkmark_color=BG)
        self.sim_ng.pack(side="left", padx=(0, 14))
        self._btn_local(rsim, "Simular", self._simulacao)

        self._sep(p, row=6)
        self._section(p, "ADICIONAR ATIVO", row=7)

        form = self._row(p, row=8)
        self.f_ticker = self._field(form, col=0, label="Ticker",   ph="PETR4",  w=88)
        self.f_tipo   = self._combo(form, col=2, label="Tipo",     vals=TIPOS_ATIVO, default="acao-on", w=120)
        self.f_qtd    = self._field(form, col=4, label="Qtd",      ph="100",    w=72)
        self.f_pm     = self._field(form, col=6, label="P. Médio", ph="45.50",  w=80)
        self.f_setor  = self._field(form, col=8, label="Setor",    ph="energia",w=100)

        rf_form = self._row(p, row=9)
        INDEXADORES = ["—", "CDI", "IPCA", "Selic", "PRE", "IGPM"]
        self.f_idx  = self._combo(rf_form, col=0, label="Indexador (RF)", vals=INDEXADORES, default="—", w=108)
        self.f_taxa = self._field(rf_form, col=2, label="Taxa (%)",    ph="110",         w=72)
        self.f_venc = self._field(rf_form, col=4, label="Vencimento",  ph="2027-12-01",  w=104)

        r3 = self._row(p, row=10)
        self.f_skip = ctk.CTkCheckBox(r3, text="Skip validação", font=MONO_SM,
                                       text_color=TXT2, fg_color=ACC,
                                       hover_color=ACC_DIM, border_color=BORDER,
                                       checkmark_color=BG)
        self.f_skip.pack(side="left", padx=(0, 14))
        ctk.CTkLabel(r3, text="Data entrada", font=MONO_SM,
                     text_color=TXT2).pack(side="left", padx=(0, 4))
        self.f_data = ctk.CTkEntry(r3, placeholder_text=datetime.now().strftime("%Y-%m-%d"),
                                    width=110, font=MONO_SM,
                                    fg_color=ELEV, border_color=BORDER, text_color=TXT)
        self.f_data.pack(side="left", padx=(0, 14))
        ctk.CTkLabel(r3, text="Nome (RF)", font=MONO_SM,
                     text_color=TXT2).pack(side="left", padx=(0, 4))
        self.f_nome = ctk.CTkEntry(r3, placeholder_text="CDB XP 110% CDI",
                                    width=180, font=MONO_SM,
                                    fg_color=ELEV, border_color=BORDER, text_color=TXT)
        self.f_nome.pack(side="left", padx=(0, 12))
        ctk.CTkButton(r3, text="ADICIONAR ▸", width=112, height=30,
                       font=MONO_B, fg_color=ACC, hover_color=ACC_DIM,
                       text_color=BG, corner_radius=4,
                       command=self._adicionar).pack(side="left")

        ctk.CTkLabel(p, text="tipos: acao-on | acao-pn | fii | etf-br | etf-intl | renda-fixa | tesouro | debenture | cri-cra",
                     font=MONO_SM, text_color=TXT2,
                     ).grid(row=11, column=0, sticky="w", padx=14, pady=(0, 4))

        self._sep(p, row=12)
        self._section(p, "REGISTRAR VENDA", row=13)

        vform = self._row(p, row=14)
        self.v_ticker = self._field(vform, col=0, label="Ticker",  ph="PETR4",  w=88)
        self.v_qtd    = self._field(vform, col=2, label="Qtd",     ph="50",     w=72)
        self.v_preco  = self._field(vform, col=4, label="Preço",   ph="45.00",  w=80)
        self.v_data   = self._field(vform, col=6, label="Data",    ph=datetime.now().strftime("%Y-%m-%d"), w=104)

        r4 = self._row(p, row=15)
        ctk.CTkButton(r4, text="VENDER ▸", width=95, height=30,
                       font=MONO_B, fg_color="#180808", hover_color="#220E0E",
                       text_color=NEG, border_width=1, border_color=NEG,
                       corner_radius=4, command=self._vender).pack(side="left")
        return p

    def _make_page_analise(self) -> ctk.CTkScrollableFrame:
        p = ctk.CTkScrollableFrame(self._content_host, corner_radius=0,
                                    fg_color="transparent",
                                    scrollbar_button_color=BORDER,
                                    scrollbar_button_hover_color=ACC_DIM)
        p.grid_columnconfigure(0, weight=1)

        self._section(p, "ANÁLISE DE ATIVO — IA", row=0)

        r1 = self._row(p, row=1)
        ctk.CTkLabel(r1, text="Ticker:", font=MONO_SM,
                     text_color=TXT2).pack(side="left", padx=(0, 5))
        self.a_ticker = ctk.CTkEntry(r1, placeholder_text="PETR4", width=90,
                                      font=MONO_B, fg_color=ELEV,
                                      border_color=BORDER, text_color=ACC)
        self.a_ticker.pack(side="left", padx=(0, 14))

        for label, slash in [
            ("Analisar — pipeline completo", "analisar"),
            ("Tese rápida", "tese"),
            ("Earnings", "earnings"),
            ("PM — Decisão", "pm"),
        ]:
            self._btn_ia(r1, label, lambda s=slash: self._ia_ticker(s, self.a_ticker))

        self._sep(p, row=2)
        self._section(p, "APORTE DE CAPITAL — IA", row=3)

        r_aporte = self._row(p, row=4)
        ctk.CTkLabel(r_aporte, text="Valor (R$):", font=MONO_SM,
                     text_color=TXT2).pack(side="left", padx=(0, 6))
        self.aporte_valor = ctk.CTkEntry(r_aporte, placeholder_text="700",
                                          width=80, font=MONO_B,
                                          fg_color=ELEV, border_color=BORDER,
                                          text_color=ACC)
        self.aporte_valor.pack(side="left", padx=(0, 12))
        self._btn_ia(r_aporte, "PM — Modo Aporte", self._pm_aporte)
        self._btn_ia(r_aporte, "PM — Aporte (sem valor)", lambda: self._ia_noarg("pm"))

        self._sep(p, row=5)
        self._section(p, "COMPARAR ATIVOS — IA", row=6)

        r2 = self._row(p, row=7)
        self.c_t1 = ctk.CTkEntry(r2, placeholder_text="PETR4", width=88,
                                   font=MONO_B, fg_color=ELEV,
                                   border_color=BORDER, text_color=ACC)
        self.c_t1.pack(side="left", padx=(0, 6))
        ctk.CTkLabel(r2, text="vs", font=MONO_B, text_color=TXT2).pack(side="left", padx=4)
        self.c_t2 = ctk.CTkEntry(r2, placeholder_text="VALE3", width=88,
                                   font=MONO_B, fg_color=ELEV,
                                   border_color=BORDER, text_color=ACC)
        self.c_t2.pack(side="left", padx=(6, 14))
        self._btn_ia(r2, "Comparar", self._comparar)

        self._ia_note(p, row=8)
        return p

    def _make_page_mercado(self) -> ctk.CTkScrollableFrame:
        p = ctk.CTkScrollableFrame(self._content_host, corner_radius=0,
                                    fg_color="transparent",
                                    scrollbar_button_color=BORDER,
                                    scrollbar_button_hover_color=ACC_DIM)
        p.grid_columnconfigure(0, weight=1)

        self._section(p, "DIÁRIO / MACRO — IA", row=0)
        r1 = self._row(p, row=1)
        for label, slash in [
            ("Morning Call", "morning-call"),
            ("Mundo Econômico", "mundo-economico"),
        ]:
            self._btn_ia(r1, label, lambda s=slash: self._ia_noarg(s))

        r1b = self._row(p, row=2)
        ctk.CTkLabel(r1b, text="Investimento do Dia:", font=MONO_SM,
                     text_color=TXT2).pack(side="left", padx=(0, 6))
        INV_CATS = ["qualquer", "fii", "acao", "etf-br", "etf-intl", "rf", "td"]
        self.inv_cat = ctk.CTkComboBox(
            r1b, values=INV_CATS, width=112, font=MONO_SM,
            fg_color=ELEV, border_color=BORDER,
            button_color=BORDER, button_hover_color=ACC_DIM,
            text_color=TXT, dropdown_fg_color=SURF,
            dropdown_text_color=TXT, dropdown_hover_color=ELEV,
        )
        self.inv_cat.set("qualquer")
        self.inv_cat.pack(side="left", padx=(0, 8))
        self._btn_ia(r1b, "Buscar", self._investimento_dia)

        self._sep(p, row=3)
        self._section(p, "STRESS TEST — LOCAL", row=4)

        r2 = self._row(p, row=5)
        for label, arg in [
            ("Todos os cenários", None), ("Crise 2008", "crise-2008"),
            ("COVID-2020", "covid-2020"), ("Eleições 2022", "eleicoes-2022"),
            ("Lula 2002", "lula-2002"),
        ]:
            extra = [arg] if arg else []
            self._btn_local(r2, label, lambda e=extra: self._local(["/stress-test"] + e))

        r3 = self._row(p, row=6)
        ctk.CTkLabel(r3, text="choque custom:", font=MONO_SM,
                     text_color=TXT2).pack(side="left", padx=(0, 6))
        self.stress_val = ctk.CTkEntry(r3, placeholder_text="-20", width=68,
                                        font=MONO_B, fg_color=ELEV,
                                        border_color=BORDER, text_color=TXT)
        self.stress_val.pack(side="left", padx=(0, 4))
        ctk.CTkLabel(r3, text="%", font=MONO_SM,
                     text_color=TXT2).pack(side="left", padx=(0, 8))
        self._btn_local(r3, "Simular", self._stress_custom)

        self._ia_note(p, row=7)
        return p

    def _make_page_relatorios(self) -> ctk.CTkScrollableFrame:
        p = ctk.CTkScrollableFrame(self._content_host, corner_radius=0,
                                    fg_color="transparent",
                                    scrollbar_button_color=BORDER,
                                    scrollbar_button_hover_color=ACC_DIM)
        p.grid_columnconfigure(0, weight=1)

        self._section(p, "RELATÓRIOS — IA", row=0)
        r1 = self._row(p, row=1)
        for label, slash in [
            ("Relatório Semanal", "relatorio-semanal"),
            ("Relatório Mensal", "relatorio-mensal"),
            ("Rebalancear vs IPS", "rebalancear"),
            ("Revisar Carteira", "revisar-carteira"),
        ]:
            self._btn_ia(r1, label, lambda s=slash: self._ia_noarg(s))

        self._ia_note(p, row=2)
        return p

    def _make_page_knowledge(self) -> ctk.CTkScrollableFrame:
        p = ctk.CTkScrollableFrame(self._content_host, corner_radius=0,
                                    fg_color="transparent",
                                    scrollbar_button_color=BORDER,
                                    scrollbar_button_hover_color=ACC_DIM)
        p.grid_columnconfigure(0, weight=1)

        self._section(p, "BASE DE CONHECIMENTO — LOCAL", row=0)
        r1 = self._row(p, row=1)
        for label, args in [
            ("Status",      ["/knowledge", "--status"]),
            ("Coletar RSS", ["/knowledge", "--coletar-rss"]),
            ("Listar",      ["/knowledge", "--listar"]),
        ]:
            self._btn_local(r1, label, lambda a=args: self._local(a))

        self._sep(p, row=2)
        self._section(p, "BUSCAR", row=3)
        r2 = self._row(p, row=4)
        ctk.CTkLabel(r2, text="query:", font=MONO_SM,
                     text_color=TXT2).pack(side="left", padx=(0, 6))
        self.k_busca = ctk.CTkEntry(r2, placeholder_text="valuation petróleo Brasil",
                                     width=320, font=MONO_SM,
                                     fg_color=ELEV, border_color=BORDER, text_color=TXT)
        self.k_busca.pack(side="left", padx=(0, 10))
        self._btn_local(r2, "Buscar", self._kb_buscar)

        self._sep(p, row=5)
        self._section(p, "INDEXAR DOCUMENTO", row=6)
        r3 = self._row(p, row=7)
        ctk.CTkLabel(r3, text="path:", font=MONO_SM,
                     text_color=TXT2).pack(side="left", padx=(0, 6))
        self.k_path = ctk.CTkEntry(r3, placeholder_text=r"C:\caminho\arquivo.pdf",
                                    width=320, font=MONO_SM,
                                    fg_color=ELEV, border_color=BORDER, text_color=TXT)
        self.k_path.pack(side="left", padx=(0, 10))
        self._btn_local(r3, "Adicionar", self._kb_add)

        return p

    # ── Ações ─────────────────────────────────────────────────────────────────

    def _local(self, args: list):
        cmd = [PYTHON_EXE, str(PROJECT_ROOT / "sbwaa.py")] + args
        self._clear_output()
        self._append(f"▸ {' '.join(args)}\n\n")
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
            self.after(0, self._append,
                       f"\n▸ concluído [{proc.returncode}]  {datetime.now().strftime('%H:%M:%S')}\n")
        except Exception as e:
            self.after(0, self._append, f"erro: {e}\n")

    def _ia_ticker(self, slash: str, entry: ctk.CTkEntry):
        ticker = entry.get().strip().upper()
        if not ticker:
            self._show_toast("⚠  Informe o ticker antes de continuar.")
            return
        self._clipboard(f"/{slash} {ticker}")

    def _ia_noarg(self, slash: str):
        self._clipboard(f"/{slash}")

    def _pm_aporte(self):
        valor = self.aporte_valor.get().strip()
        if valor:
            self._clipboard(f"/pm {valor}")
        else:
            self._clipboard("/pm")

    def _comparar(self):
        t1 = self.c_t1.get().strip().upper()
        t2 = self.c_t2.get().strip().upper()
        if not t1 or not t2:
            self._show_toast("⚠  Informe os dois tickers.")
            return
        self._clipboard(f"/comparar {t1} {t2}")

    def _adicionar(self):
        ticker    = self.f_ticker.get().strip().upper()
        tipo      = self.f_tipo.get().strip()
        qtd       = self.f_qtd.get().strip()
        pm        = self.f_pm.get().strip()
        setor     = self.f_setor.get().strip()
        data      = self.f_data.get().strip()
        nome      = self.f_nome.get().strip()
        indexador = self.f_idx.get().strip()
        taxa      = self.f_taxa.get().strip()
        venc      = self.f_venc.get().strip()
        if not all([ticker, tipo, qtd, pm, setor]):
            self._show_toast("⚠  Preencha todos os campos obrigatórios.")
            return
        args = ["/adicionar", "--ticker", ticker, "--tipo", tipo,
                "--quantidade", qtd, "--preco-medio", pm, "--setor", setor]
        if data:
            args += ["--data", data]
        if nome:
            args += ["--nome", nome]
        if indexador and indexador != "—":
            args += ["--indexador", indexador]
        if taxa:
            args += ["--taxa", taxa]
        if venc:
            args += ["--vencimento", venc]
        if self.f_skip.get():
            args.append("--skip-validacao")
        self._local(args)

    def _vender(self):
        ticker = self.v_ticker.get().strip().upper()
        qtd    = self.v_qtd.get().strip()
        preco  = self.v_preco.get().strip()
        data   = self.v_data.get().strip()
        if not all([ticker, qtd, preco]):
            self._show_toast("⚠  Preencha Ticker, Qtd e Preço.")
            return
        args = ["/vender", "--ticker", ticker, "--quantidade", qtd, "--preco", preco]
        if data:
            args += ["--data", data]
        self._local(args)

    def _simulacao(self):
        args = ["/simulacao"]
        pat = self.sim_pat.get().strip()
        ap  = self.sim_ap.get().strip()
        if pat:
            args += ["--patrimonio", pat]
        if ap:
            args += ["--aporte", ap]
        if self.sim_ng.get():
            args.append("--no-graficos")
        self._local(args)

    def _investimento_dia(self):
        cat = self.inv_cat.get().strip()
        if cat and cat != "qualquer":
            self._clipboard(f"/investimento-do-dia {cat}")
        else:
            self._clipboard("/investimento-do-dia")

    def _stress_custom(self):
        val = self.stress_val.get().strip()
        if not val:
            self._show_toast("⚠  Informe o choque (ex: -20).")
            return
        try:
            float(val)
        except ValueError:
            self._show_toast("⚠  Valor inválido — use número (ex: -20).")
            return
        self._local(["/stress-test", "custom", val])

    def _kb_buscar(self):
        q = self.k_busca.get().strip()
        if not q:
            self._show_toast("⚠  Informe a query de busca.")
            return
        self._local(["/knowledge", "--buscar", q])

    def _kb_add(self):
        p = self.k_path.get().strip()
        if not p:
            self._show_toast("⚠  Informe o caminho do arquivo.")
            return
        self._local(["/knowledge", "--adicionar", p])

    def _clipboard(self, cmd: str):
        self._clear_output()
        try:
            self.clipboard_clear()
            self.clipboard_append(cmd)
            self.update()
            self._append(f"◈  comando IA copiado:\n\n    {cmd}\n\n    → cole no chat do Claude Code\n")
            self._show_toast(f"✓  Copiado:  {cmd}")
        except Exception:
            self._append(f"◈  comando:  {cmd}\n")

    def _append(self, text: str):
        self.output.configure(state="normal")
        self.output.insert("end", text)
        self.output.see("end")
        self.output.configure(state="disabled")

    def _clear_output(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    # ── Helpers de layout ─────────────────────────────────────────────────────

    def _section(self, parent, title: str, row: int):
        ctk.CTkLabel(parent, text=title, font=MONO_B, text_color=ACC
                     ).grid(row=row, column=0, sticky="w", padx=14, pady=(14, 4))

    def _sep(self, parent, row: int):
        ctk.CTkFrame(parent, height=1, fg_color=BORDER
                     ).grid(row=row, column=0, sticky="ew", padx=8, pady=6)

    def _row(self, parent, row: int) -> ctk.CTkFrame:
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 4))
        return f

    def _ia_note(self, parent, row: int):
        ctk.CTkLabel(
            parent,
            text="[IA]  botões de IA copiam o comando pro clipboard — cole no chat do Claude Code.",
            font=MONO_SM, text_color=TXT2,
        ).grid(row=row, column=0, sticky="w", padx=14, pady=(14, 4))

    def _btn_local(self, parent, label: str, cmd, px=(0, 6)):
        ctk.CTkButton(
            parent, text=label, font=MONO_SM, height=30,
            fg_color=ELEV, hover_color=BORDER, text_color=TXT,
            corner_radius=4, border_width=1, border_color=BORDER,
            command=cmd,
        ).pack(side="left", padx=px, pady=2)

    def _btn_ia(self, parent, label: str, cmd, px=(0, 6)):
        ctk.CTkButton(
            parent, text=f"[IA] {label}", font=MONO_SM, height=30,
            fg_color=ACC_BG, hover_color="#002A34", text_color=ACC,
            corner_radius=4, border_width=1, border_color=ACC_DIM,
            command=cmd,
        ).pack(side="left", padx=px, pady=2)

    def _field(self, parent, col, label, ph, w) -> ctk.CTkEntry:
        ctk.CTkLabel(parent, text=label, font=MONO_SM,
                     text_color=TXT2).grid(row=0, column=col, padx=(8, 2), sticky="w")
        e = ctk.CTkEntry(parent, placeholder_text=ph, width=w, font=MONO_SM,
                         fg_color=ELEV, border_color=BORDER, text_color=TXT)
        e.grid(row=0, column=col + 1, padx=(0, 4))
        return e

    def _combo(self, parent, col, label, vals, default, w) -> ctk.CTkComboBox:
        ctk.CTkLabel(parent, text=label, font=MONO_SM,
                     text_color=TXT2).grid(row=0, column=col, padx=(8, 2), sticky="w")
        cb = ctk.CTkComboBox(
            parent, values=vals, width=w, font=MONO_SM,
            fg_color=ELEV, border_color=BORDER,
            button_color=BORDER, button_hover_color=ACC_DIM,
            text_color=TXT, dropdown_fg_color=SURF,
            dropdown_text_color=TXT, dropdown_hover_color=ELEV,
        )
        cb.set(default)
        cb.grid(row=0, column=col + 1, padx=(0, 4))
        return cb


if __name__ == "__main__":
    App().mainloop()
