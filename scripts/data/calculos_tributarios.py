"""
calculos_tributarios.py — Motor tributário do SBWAA.
Aplica IR e IOF conforme legislação brasileira vigente (2026).
Importável por qualquer script ou agente do sistema.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, timedelta

# ── Tabelas Legais ─────────────────────────────────────────────────────────────

# IOF regressivo sobre rendimentos de RF (Decreto 6.306/2007)
# Índice = dia - 1 (dia 1 → índice 0). Dia 30+ = 0%.
IOF_RF: list[float] = [
    96, 93, 90, 86, 83, 80, 76, 73, 70, 66,  # dias 1-10
    63, 60, 56, 53, 50, 46, 43, 40, 36, 33,  # dias 11-20
    30, 26, 23, 20, 16, 13, 10,  6,  3,  0,  # dias 21-30
]

# IR regressivo RF/TD/DEB (Lei 11.033/2004) — (prazo_max, aliquota_pct)
IR_RF_TABELA: list[tuple[int, float]] = [
    (180, 22.5),
    (360, 20.0),
    (720, 17.5),
    (999_999, 15.0),
]

# IR renda variável
IR_ACOES_SWING   = 15.0   # ganho de capital swing trade
IR_ACOES_DAY     = 20.0   # day trade
IR_FII_GANHO     = 20.0   # ganho de capital FII na venda
IR_FII_DIVIDENDO = 0.0    # dividendos FII: isentos para PF (Lei 8.668/93)
IR_ETF_BR        = 15.0   # ETF renda variável listado no Brasil
IR_ETF_INTL      = 15.0   # ETF internacional listado no Brasil (IVVB11, etc.)
ISENCAO_ACOES_MES = 20_000.0  # isenção IR ações se vendas mensais <= R$20k

# CDI anual estimado (referência para cálculos; atualizar conforme Selic)
CDI_ANUAL_DEFAULT = 0.1475  # 14.75% a.a. (maio/2026)
DIAS_UTEIS_ANO    = 252


# ── Helpers ────────────────────────────────────────────────────────────────────

def _feriados_nacionais(ano: int) -> set:
    """Feriados nacionais brasileiros (fixos + móveis via Páscoa)."""
    def _pascoa(y: int) -> date:
        a = y % 19; b = y // 100; c = y % 100
        d = b // 4; e = b % 4; f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4; k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        mes = (h + l - 7 * m + 114) // 31
        dia = ((h + l - 7 * m + 114) % 31) + 1
        return date(y, mes, dia)

    p = _pascoa(ano)
    return {
        date(ano, 1, 1),   date(ano, 4, 21),  date(ano, 5, 1),
        date(ano, 9, 7),   date(ano, 10, 12), date(ano, 11, 2),
        date(ano, 11, 15), date(ano, 12, 25),
        p - timedelta(days=48), p - timedelta(days=47),  # Carnaval
        p - timedelta(days=2),                            # Sexta Santa
        p + timedelta(days=60),                           # Corpus Christi
    }


def dias_uteis_brasil(data_inicio: date | str, data_fim: date | str | None = None) -> int:
    """Dias úteis brasileiros de data_inicio (inclusive) até data_fim (exclusive)."""
    if isinstance(data_inicio, str):
        data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
    if data_fim is None:
        data_fim = date.today()
    elif isinstance(data_fim, str):
        data_fim = datetime.strptime(data_fim, "%Y-%m-%d").date()
    if data_fim <= data_inicio:
        return 0
    cache: dict[int, set] = {}
    count = 0
    current = data_inicio
    while current < data_fim:
        if current.weekday() < 5:
            ano = current.year
            if ano not in cache:
                cache[ano] = _feriados_nacionais(ano)
            if current not in cache[ano]:
                count += 1
        current += timedelta(days=1)
    return count


def dias_corridos(data_inicio: date | str, data_fim: date | str | None = None) -> int:
    """Retorna dias corridos entre data_inicio e data_fim (padrão: hoje)."""
    if isinstance(data_inicio, str):
        data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
    if data_fim is None:
        data_fim = date.today()
    elif isinstance(data_fim, str):
        data_fim = datetime.strptime(data_fim, "%Y-%m-%d").date()
    return max(0, (data_fim - data_inicio).days)


def aliquota_iof_rf(dias: int) -> float:
    """Retorna alíquota IOF (%) aplicável ao prazo em dias corridos."""
    if dias <= 0:
        return 100.0
    if dias >= 30:
        return 0.0
    return float(IOF_RF[dias - 1])


def aliquota_ir_rf(dias: int) -> float:
    """Retorna alíquota IR (%) aplicável ao prazo em dias corridos."""
    for prazo_max, aliquota in IR_RF_TABELA:
        if dias <= prazo_max:
            return aliquota
    return 15.0


def estimar_rendimento_rdb(
    principal: float,
    dias: int,
    pct_cdi: float = 1.0,
    cdi_anual: float = CDI_ANUAL_DEFAULT,
) -> float:
    """
    Estima rendimento bruto acumulado de RDB/CDB (capitalização diária).
    pct_cdi: fração do CDI (ex: 1.0 = 100% CDI, 1.10 = 110% CDI).
    """
    if dias <= 0:
        return 0.0
    taxa_diaria = (1 + cdi_anual * pct_cdi) ** (1 / DIAS_UTEIS_ANO) - 1
    rendimento = principal * ((1 + taxa_diaria) ** dias - 1)
    return round(rendimento, 2)


# ── Motor RF ───────────────────────────────────────────────────────────────────

@dataclass
class ResultadoTributarioRF:
    principal: float
    rendimento_bruto: float
    iof_valor: float
    iof_aliquota_pct: float
    ir_valor: float
    ir_aliquota_pct: float
    liquido: float
    total_bruto: float
    dias: int           # dias corridos (IOF)
    dias_uteis: int = 0  # dias úteis (CDI)

    def linha_resumo(self, label: str = "") -> str:
        pfx = f"{label}: " if label else ""
        return (
            f"{pfx}bruto R$ {self.total_bruto:,.2f} | "
            f"IOF R$ {self.iof_valor:,.2f} ({self.iof_aliquota_pct:.0f}%) | "
            f"IR R$ {self.ir_valor:,.2f} ({self.ir_aliquota_pct:.1f}%) | "
            f"líquido R$ {self.liquido:,.2f}"
        )


def calcular_tributario_rf(
    principal: float,
    rendimento_bruto: float,
    dias: int,
    dias_uteis: int = 0,
) -> ResultadoTributarioRF:
    """Calcula IOF + IR sobre posição de RF. dias = corridos (IOF); dias_uteis = úteis (CDI)."""
    al_iof = aliquota_iof_rf(dias)
    iof    = round(rendimento_bruto * al_iof / 100, 2)
    rend_apos_iof = rendimento_bruto - iof
    al_ir  = aliquota_ir_rf(dias)
    ir     = round(rend_apos_iof * al_ir / 100, 2)
    liquido = round(principal + rend_apos_iof - ir, 2)
    return ResultadoTributarioRF(
        principal=principal,
        rendimento_bruto=rendimento_bruto,
        iof_valor=iof,
        iof_aliquota_pct=al_iof,
        ir_valor=ir,
        ir_aliquota_pct=al_ir,
        liquido=liquido,
        total_bruto=round(principal + rendimento_bruto, 2),
        dias=dias,
        dias_uteis=dias_uteis,
    )


def calcular_rdb_nubank(
    saldo_bruto: float,
    data_deposito: str,
    pct_cdi: float = 1.0,
    cdi_anual: float = CDI_ANUAL_DEFAULT,
    data_referencia: str | None = None,
) -> ResultadoTributarioRF:
    """
    Calcula tributos estimados do RDB Nubank (Caixinha).
    saldo_bruto: saldo atual (principal + rendimentos acumulados).
    data_deposito: YYYY-MM-DD da aplicação mais recente (base para IOF/IR).
    """
    ref = datetime.strptime(data_referencia, "%Y-%m-%d").date() if data_referencia else date.today()
    dep = datetime.strptime(data_deposito, "%Y-%m-%d").date()
    d        = max(0, (ref - dep).days)           # dias corridos — para IOF
    d_uteis  = dias_uteis_brasil(dep, ref)         # dias úteis — para CDI

    # Estimativa reversa: saldo_bruto ≈ principal * (1 + taxa_diaria)^d_uteis
    taxa_diaria = (1 + cdi_anual * pct_cdi) ** (1 / DIAS_UTEIS_ANO) - 1
    if d_uteis > 0 and taxa_diaria > 0:
        fator = (1 + taxa_diaria) ** d_uteis
        principal_est = saldo_bruto / fator
        rendimento_est = saldo_bruto - principal_est
    else:
        principal_est = saldo_bruto
        rendimento_est = 0.0

    return calcular_tributario_rf(
        principal=round(principal_est, 2),
        rendimento_bruto=round(rendimento_est, 2),
        dias=d,
        dias_uteis=d_uteis,
    )


# ── Motor Renda Variável ───────────────────────────────────────────────────────

@dataclass
class ResultadoTributarioRV:
    ticker: str
    tipo: str  # acao | fii | etf-br | etf-intl
    ganho_bruto: float
    ir_aliquota_pct: float
    ir_valor: float
    ganho_liquido: float
    nota: str = ""

    def linha_resumo(self) -> str:
        return (
            f"{self.ticker}: ganho bruto R$ {self.ganho_bruto:,.2f} → "
            f"IR {self.ir_aliquota_pct:.0f}% = R$ {self.ir_valor:,.2f} → "
            f"líquido R$ {self.ganho_liquido:,.2f}"
            + (f"  ({self.nota})" if self.nota else "")
        )


def calcular_ir_renda_variavel(
    ticker: str,
    tipo: str,
    ganho_bruto: float,
    vendas_mes: float = 0.0,
    day_trade: bool = False,
) -> ResultadoTributarioRV:
    """
    Calcula IR sobre ganho de capital em renda variável.
    tipo: 'acao-on' | 'acao-pn' | 'fii' | 'etf-br' | 'etf-intl'
    ganho_bruto: diferença (preço_venda - PM) * qtd
    vendas_mes: total vendido no mês para verificar isenção de ações
    """
    if ganho_bruto <= 0:
        return ResultadoTributarioRV(ticker, tipo, ganho_bruto, 0, 0, ganho_bruto, "prejuízo — sem IR")

    tipo_base = tipo.replace("-on", "").replace("-pn", "")

    if tipo_base == "acao":
        if day_trade:
            al = IR_ACOES_DAY
            nota = "day trade"
        elif vendas_mes <= ISENCAO_ACOES_MES:
            return ResultadoTributarioRV(ticker, tipo, ganho_bruto, 0, 0, ganho_bruto,
                                         f"isento (vendas mês R$ {vendas_mes:,.0f} ≤ R$ 20k)")
        else:
            al = IR_ACOES_SWING
            nota = "swing trade"

    elif tipo_base == "fii":
        al   = IR_FII_GANHO
        nota = "ganho capital FII"

    elif tipo in ("etf-br", "etf-intl"):
        al   = IR_ETF_BR
        nota = "ETF — sem isenção R$20k"

    else:
        al   = 15.0
        nota = "alíquota padrão"

    ir  = round(ganho_bruto * al / 100, 2)
    liq = round(ganho_bruto - ir, 2)
    return ResultadoTributarioRV(ticker, tipo, ganho_bruto, al, ir, liq, nota)


# ── Formatação para output de agentes ─────────────────────────────────────────

def bloco_rf_oportunidade(
    saldo_bruto: float,
    data_deposito: str,
    aporte_solicitado: float,
    pct_cdi: float = 1.0,
    cdi_anual: float = CDI_ANUAL_DEFAULT,
) -> str:
    """
    Retorna bloco formatado para o PM exibir no fluxo de aporte.
    """
    trib = calcular_rdb_nubank(saldo_bruto, data_deposito, pct_cdi, cdi_anual)
    d    = trib.dias
    iof_status = "✅ zerado" if trib.iof_valor == 0 else f"⚠️ R$ {trib.iof_valor:,.2f} ({trib.iof_aliquota_pct:.0f}%)"
    iof_dias   = f"{d} dias >{30 if d >= 30 else d}" if d >= 30 else f"{d} dias"

    disponivel_ok = "✅" if trib.liquido >= aporte_solicitado else "⚠️ insuficiente"
    saldo_apos = round(saldo_bruto - aporte_solicitado, 2)

    linhas = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "💰 RF OPORTUNIDADE — CAIXINHA NUBANK",
        "────────────────────────────────────────────────────",
        f"  Saldo bruto:          R$ {saldo_bruto:>10,.2f}",
        f"  Rendimento est.*:     R$ {trib.rendimento_bruto:>10,.2f}  ({iof_dias})",
        f"  IOF estimado:         R$ {trib.iof_valor:>10,.2f}  {iof_status}",
        f"  IR estimado*:         R$ {trib.ir_valor:>10,.2f}  ({trib.ir_aliquota_pct:.1f}%)",
        f"  Líquido disponível:   R$ {trib.liquido:>10,.2f}",
        "────────────────────────────────────────────────────",
        f"  Aporte solicitado:    R$ {aporte_solicitado:>10,.2f}  {disponivel_ok}",
        "────────────────────────────────────────────────────",
        "  Movimentação:",
        f"    − R$ {aporte_solicitado:,.2f}  RF Oportunidade",
        f"    + R$ {aporte_solicitado:,.2f}  {{TICKER}}",
        f"  Saldo bruto após:     R$ {saldo_apos:>10,.2f}",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "  * CDI {:.2f}% a.a. — IR realizado apenas no resgate.".format(cdi_anual * 100),
    ]
    return "\n".join(linhas)


def tabela_ir_por_classe() -> str:
    """Retorna tabela markdown de alíquotas de IR por classe de ativo."""
    return """| Classe | Produto | IR Ganho Capital | IR Renda | IOF | Observação |
|--------|---------|-----------------|----------|-----|------------|
| 🟦 AÇÃO | ON/PN | 15% (swing) / 20% (day trade) | — | — | Isento se vendas ≤ R$20k/mês |
| 🟩 FII | FII | 20% | **Isento** para PF | — | Dividendos isentos (Lei 8.668/93) |
| 🟨 ETF BR | ETF Brasil | 15% | — | — | Sem isenção de R$20k |
| 🟥 ETF INTL | ETF Internacional | 15% | — | — | Listados no Brasil (ex: IVVB11) |
| ⬜ RF | CDB / RDB / DEB | Tab. regressiva¹ | — | Regressivo² | IOF incide apenas <30 dias |
| 🟪 TD | Tesouro Direto | Tab. regressiva¹ | — | Regressivo² | IR incide sobre ganho nominal |
| 🟧 CRI/CRA | CRI / CRA | Tab. regressiva¹ | **Isento** | — | Isentos de IR para PF |

**¹ IR RF regressivo:** até 180d = 22,5% · 181-360d = 20% · 361-720d = 17,5% · >720d = 15%
**² IOF RF regressivo:** 96% (D1) → 3% (D29) → 0% (D30+) — incide sobre o rendimento"""
