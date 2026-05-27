"""
carteira.py — Snapshot completo e atualizado da carteira.
Uso: python sbwaa.py /carteira
"""

import json
import math
import re
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

PROJECT_ROOT    = Path(__file__).parent.parent.parent
VAULT_ROOT      = PROJECT_ROOT / "vault"
SCRIPTS_DATA    = PROJECT_ROOT / "scripts" / "data"
CARTEIRA_PATH   = VAULT_ROOT / "00-portfolio" / "carteira.md"
HISTORICO_PATH  = VAULT_ROOT / "00-portfolio" / "historico-trades.md"
IPS_PATH        = VAULT_ROOT / "00-portfolio" / "ips.md"
METAS_PATH      = VAULT_ROOT / "00-portfolio" / "metas.md"
PROVENTOS_CACHE = VAULT_ROOT / "00-portfolio" / ".proventos-cache.json"


def ler_proventos_cache() -> dict | None:
    if not PROVENTOS_CACHE.exists():
        return None
    try:
        return json.loads(PROVENTOS_CACHE.read_text(encoding="utf-8"))
    except Exception:
        return None

LABELS = {
    "ON": "🟦 AÇÃO ON", "PN": "🟦 AÇÃO PN", "FII": "🟩 FII",
    "ETF BR": "🟨 ETF BR", "ETF INTL": "🟥 ETF INTL",
    "RF": "⬜ RF", "TD": "🟪 TD", "DEB": "🟫 DEB", "CRI/CRA": "🟧 CRI/CRA",
}


def parse_ips_alvo() -> dict:
    """Lê alocação alvo do IPS."""
    if not IPS_PATH.exists():
        return {}
    conteudo = IPS_PATH.read_text(encoding="utf-8")
    resultado = {}
    dentro = False
    for linha in conteudo.splitlines():
        stripped = linha.strip()
        if stripped.startswith("| Classe"):
            dentro = True
            continue
        if dentro and stripped.startswith("|---"):
            continue
        if dentro and stripped.startswith("|"):
            cols = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(cols) >= 2 and cols[0] and cols[1]:
                try:
                    resultado[cols[0]] = float(cols[1].replace("%", "").replace(",", "."))
                except ValueError:
                    pass
        elif dentro and not stripped.startswith("|"):
            break
    return resultado


def parse_carteira() -> tuple[list[dict], dict]:
    """Retorna (posições, resumo) da carteira."""
    if not CARTEIRA_PATH.exists():
        return [], {}
    conteudo = CARTEIRA_PATH.read_text(encoding="utf-8")
    posicoes = []
    dentro = False
    for linha in conteudo.splitlines():
        stripped = linha.strip()
        if stripped.startswith("| Ticker"):
            dentro = True
            continue
        if dentro and stripped.startswith("|---"):
            continue
        if dentro and stripped.startswith("|"):
            cols = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(cols) >= 7 and cols[0] and cols[0] not in ("", "Ticker"):
                posicoes.append({
                    "ticker": cols[0],
                    "tipo": cols[1],
                    "setor": cols[2] if len(cols) > 2 else "",
                    "qtd": cols[3] if len(cols) > 3 else "",
                    "pm": cols[4] if len(cols) > 4 else "",
                    "pa": cols[5] if len(cols) > 5 else "",
                    "pl_rs": cols[7] if len(cols) > 7 else "",
                    "pl_pct": cols[8] if len(cols) > 8 else "",
                })
        elif dentro and not stripped.startswith("|"):
            break

    # Resumo
    resumo = {}
    for linha in conteudo.splitlines():
        m = re.search(r"Patrimônio Total.*?R\$\s*([\d\.,]+)", linha)
        if m:
            resumo["patrimonio"] = m.group(1)
        m = re.search(r"Total Investido.*?R\$\s*([\d\.,]+)", linha)
        if m:
            resumo["investido"] = m.group(1)
        m = re.search(r"P&L Total.*?R\$\s*([\d\.,\-\+]+)", linha)
        if m:
            resumo["pl"] = m.group(1)
        m = re.search(r"Última atualização[^0-9]*(\d{4}-\d{2}-\d{2}[^\n]+)", linha)
        if m:
            resumo["ultima_atualizacao"] = m.group(1).strip()

    return posicoes, resumo


def calcular_aporte_medio() -> tuple[float, int]:
    """
    Calcula aporte mensal médio a partir das compras no historico-trades.md.
    Retorna (aporte_medio, n_meses_com_compra).
    """
    if not HISTORICO_PATH.exists():
        return 0.0, 0
    compras_por_mes: dict[str, float] = {}
    for linha in HISTORICO_PATH.read_text(encoding="utf-8").splitlines():
        s = linha.strip()
        if not s.startswith("|") or "Data" in s or s.startswith("|---"):
            continue
        cols = [c.strip() for c in s.split("|")[1:-1]]
        if len(cols) < 7:
            continue
        data_str, operacao, total_str = cols[0], cols[3].upper(), cols[6]
        if "COMPRA" not in operacao or len(data_str) < 7:
            continue
        try:
            mes = data_str[:7]
            # Formato Python {:,.2f}: vírgula = separador de milhar, ponto = decimal
            total = float(total_str.replace(",", "").replace("R$", "").strip())
            compras_por_mes[mes] = compras_por_mes.get(mes, 0.0) + total
        except (ValueError, IndexError):
            continue
    if not compras_por_mes:
        return 0.0, 0
    return sum(compras_por_mes.values()) / len(compras_por_mes), len(compras_por_mes)


def parse_metas() -> dict:
    """Lê metas.md e retorna dict com patrimônio_alvo, renda_passiva_alvo, metas_livres."""
    if not METAS_PATH.exists():
        return {}
    conteudo = METAS_PATH.read_text(encoding="utf-8")
    resultado: dict = {}

    m = re.search(r"## Patrimônio Total.*?```(.*?)```", conteudo, re.DOTALL)
    if m:
        b = m.group(1)
        av = re.search(r"alvo:\s*(\d+)", b)
        da = re.search(r"data_alvo:\s*(\d{4}-\d{2}-\d{2})", b)
        if av:
            resultado["patrimonio_alvo"] = float(av.group(1))
            resultado["patrimonio_data_alvo"] = da.group(1) if da else None

    m = re.search(r"## Renda Passiva Mensal.*?```(.*?)```", conteudo, re.DOTALL)
    if m:
        b = m.group(1)
        av = re.search(r"alvo_mensal:\s*(\d+)", b)
        da = re.search(r"data_alvo:\s*(\d{4}-\d{2}-\d{2})", b)
        if av:
            resultado["renda_passiva_alvo"] = float(av.group(1))
            resultado["renda_passiva_data_alvo"] = da.group(1) if da else None

    m = re.search(r"## Metas Livres.*?```yaml(.*?)```", conteudo, re.DOTALL)
    if m:
        metas_livres: list[dict] = []
        meta_atual: dict = {}
        for linha in m.group(1).splitlines():
            l = linha.strip()
            if l.startswith("- nome:"):
                if "nome" in meta_atual:
                    metas_livres.append(meta_atual)
                meta_atual = {"nome": re.sub(r'["\']', "", l.split(":", 1)[1].strip())}
            elif l.startswith("alvo:") and "nome" in meta_atual:
                try:
                    meta_atual["alvo"] = float(l.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif l.startswith("atual:") and "nome" in meta_atual:
                try:
                    meta_atual["atual"] = float(l.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif l.startswith("data_alvo:") and "nome" in meta_atual:
                v = l.split(":", 1)[1].strip()
                meta_atual["data_alvo"] = v if re.match(r"\d{4}-\d{2}", v) else None
        if "nome" in meta_atual:
            metas_livres.append(meta_atual)
        resultado["metas_livres"] = [m for m in metas_livres if "alvo" in m]

    return resultado


def _anos_para_atingir_mc(patrimonio: float, meta_val: float,
                           mu_anual: float, sigma_anual: float,
                           aporte_mensal: float, max_anos: int = 50) -> float | None:
    """Anos para P50 atingir meta_val via MC com aporte mensal. None se não atingir."""
    if patrimonio >= meta_val:
        return 0.0
    if aporte_mensal <= 0:
        return None
    mu_d   = (1 + mu_anual) ** (1 / 252) - 1
    sigma_d = sigma_anual / np.sqrt(252)
    drift   = mu_d - 0.5 * sigma_d ** 2
    n_sim   = 1_000
    rng     = np.random.default_rng(seed=99)
    wealth  = np.full(n_sim, patrimonio, dtype=np.float64)
    for d in range(max_anos * 252):
        wealth *= np.exp(drift + sigma_d * rng.standard_normal(n_sim))
        if (d + 1) % 22 == 0:
            wealth += aporte_mensal
        if (d + 1) % 252 == 0 and np.percentile(wealth, 50) >= meta_val:
            return float((d + 1) // 252)
    return None


def _fmt_projecao(anos: float | None, data_alvo: str | None, hoje: datetime) -> str:
    """Formata resultado de projeção com status vs prazo."""
    if anos is None:
        return "nao projeta atingir nos proximos 50 anos"
    if anos < 1 / 12:
        return "ja atingida"
    anos_int  = int(anos)
    meses_dec = round((anos % 1) * 12)
    ano_prev  = hoje.year + anos_int + (1 if hoje.month + meses_dec > 12 else 0)
    mes_prev  = (hoje.month + meses_dec - 1) % 12 + 1
    resultado = f"~{anos:.1f} anos  ({ano_prev}-{mes_prev:02d})"
    if data_alvo:
        try:
            da = datetime.strptime(data_alvo[:10], "%Y-%m-%d")
            anos_prazo = (da - hoje).days / 365.25
            diff = anos - anos_prazo
            if diff <= -0.5:
                resultado += f"  [OK — {abs(diff):.1f} a antes do prazo]"
            elif diff <= 0.5:
                resultado += "  [OK — dentro do prazo]"
            else:
                resultado += f"  [ATENCAO — {diff:.1f} a apos o prazo]"
        except ValueError:
            pass
    return resultado


def exibir_projecao_metas(patrimonio: float, mu_anual: float, sigma_anual: float,
                           aporte_mensal: float, proventos_cache: dict | None):
    """Projeta quando cada meta de metas.md será atingida, usando os params do MC."""
    metas = parse_metas()
    if not metas:
        return

    hoje        = datetime.now()
    drift_anual = mu_anual - 0.5 * sigma_anual ** 2

    def sem_aporte(meta_val: float) -> float | None:
        if patrimonio <= 0 or drift_anual <= 0:
            return None
        if patrimonio >= meta_val:
            return 0.0
        return math.log(meta_val / patrimonio) / drift_anual

    def barra(pct: float, largura: int = 15) -> str:
        preench = min(int(pct / 100 * largura), largura)
        return "#" * preench + "-" * (largura - preench)

    _fmtv = lambda v: f"R${v/1e6:.2f}M" if v >= 1e6 else f"R${v/1e3:.0f}k"

    print(f"\n{'─'*55}")
    print("METAS — PROJECAO")
    print(f"{'─'*55}")

    # ── Patrimônio Total ──────────────────────────────────────
    if "patrimonio_alvo" in metas:
        alvo   = metas["patrimonio_alvo"]
        da_str = metas.get("patrimonio_data_alvo")
        pct    = min(patrimonio / alvo * 100, 100) if alvo > 0 else 0

        header = f"  Patrimonio {_fmtv(alvo)}"
        if da_str:
            header += f"  (prazo: {da_str[:7]})"
        print(header)
        print(f"    Atual: {_fmtv(patrimonio)}  [{barra(pct)}] {pct:.0f}%")
        print(f"    Sem aporte:  {_fmt_projecao(sem_aporte(alvo), da_str, hoje)}")
        if aporte_mensal > 0:
            a_com = _anos_para_atingir_mc(patrimonio, alvo, mu_anual, sigma_anual, aporte_mensal)
            print(f"    Com aporte:  {_fmt_projecao(a_com, da_str, hoje)}")

    # ── Renda Passiva Mensal ──────────────────────────────────
    if "renda_passiva_alvo" in metas:
        alvo_mensal = metas["renda_passiva_alvo"]
        da_str      = metas.get("renda_passiva_data_alvo")

        # Renda atual: total_no_ano / 12 — anualizado com base nos dividendos reais deste ano
        # Yield: total_no_ano / patrimônio — correto porque total_no_ano já é ≈ 1 ano de dados
        renda_atual: float | None = None
        yield_anual  = 0.06
        yield_fonte  = "estimado 6% a.a."
        if proventos_cache and patrimonio > 0:
            total_ano = proventos_cache.get("total_no_ano", 0)
            if total_ano > 0:
                renda_atual = total_ano / 12
                y = total_ano / patrimonio
                if 0.005 <= y <= 0.30:
                    yield_anual = y
                    yield_fonte = f"carteira {y*100:.1f}% a.a. ({hoje.year})"

        patrimonio_necessario = (alvo_mensal * 12) / yield_anual

        header = f"  Renda Passiva R${alvo_mensal:,.0f}/mes"
        if da_str:
            header += f"  (prazo: {da_str[:7]})"
        print(f"\n{header}")

        if renda_atual is not None:
            pct_rp = min(renda_atual / alvo_mensal * 100, 100) if alvo_mensal > 0 else 0
            print(f"    Atual: R${renda_atual:,.0f}/mes  [{barra(pct_rp)}] {pct_rp:.0f}%")
        else:
            print(f"    Atual: execute /dividendos para calcular renda mensal real")

        print(f"    Yield {yield_fonte}  ->  precisa de {_fmtv(patrimonio_necessario)}")
        print(f"    Sem aporte:  {_fmt_projecao(sem_aporte(patrimonio_necessario), da_str, hoje)}")
        if aporte_mensal > 0:
            a_com = _anos_para_atingir_mc(patrimonio, patrimonio_necessario, mu_anual, sigma_anual, aporte_mensal)
            print(f"    Com aporte:  {_fmt_projecao(a_com, da_str, hoje)}")

    # ── Metas Livres ──────────────────────────────────────────
    for meta in metas.get("metas_livres", []):
        nome   = meta.get("nome", "Meta")
        alvo   = meta.get("alvo", 0.0)
        atual  = meta.get("atual", 0.0)
        da_str = meta.get("data_alvo")
        faltam = max(0.0, alvo - atual)
        pct_ml = min(atual / alvo * 100, 100) if alvo > 0 else 0

        header = f"\n  {nome}  R${alvo:,.0f}"
        if da_str:
            header += f"  prazo: {da_str[:7]}"
        print(header)
        print(f"    Atual: R${atual:,.0f}  [{barra(pct_ml)}] {pct_ml:.0f}%")

        if faltam <= 0:
            print("    Ja atingida!")
        elif aporte_mensal > 0:
            meses = math.ceil(faltam / aporte_mensal)
            data_prev = hoje + timedelta(days=meses * 30)
            linha = f"    Via aporte:  ~{meses} meses  ({data_prev.strftime('%Y-%m')})"
            if da_str:
                try:
                    da = datetime.strptime(da_str[:10], "%Y-%m-%d")
                    meses_prazo = (da - hoje).days / 30
                    diff = meses - meses_prazo
                    if diff <= -1:
                        linha += f"  [OK — {int(abs(diff))} meses antes]"
                    elif diff <= 1:
                        linha += "  [OK — dentro do prazo]"
                    else:
                        linha += f"  [ATENCAO — {int(diff)} meses apos o prazo]"
                except ValueError:
                    pass
            print(linha)
        else:
            print(f"    Faltam: R${faltam:,.0f}  (sem historico de aportes para projetar)")

    print(f"{'─'*55}")


def _mc_finais(patrimonio: float, mu_d: float, sigma_d: float,
               drift: float, anos: int, n_sim: int,
               aporte_mensal: float, rng) -> np.ndarray:
    """Roda Monte Carlo para um horizonte e retorna array de valores finais."""
    dias = int(anos * 252)
    Z = rng.standard_normal((n_sim, dias))
    if aporte_mensal <= 0:
        return patrimonio * np.exp(np.sum(drift + sigma_d * Z, axis=1))
    wealth = np.full(n_sim, patrimonio, dtype=np.float64)
    for d in range(dias):
        wealth *= np.exp(drift + sigma_d * Z[:, d])
        if (d + 1) % 22 == 0:
            wealth += aporte_mensal
    return wealth


def exibir_projecao(patrimonio_str: str):
    """Projeção Monte Carlo rápida usando parâmetros cacheados da última simulação."""
    cache_path = PROJECT_ROOT / "logs" / "simulacao" / "params_cache.json"
    print(f"\n{'─'*55}")
    print("PROJECAO DE LONGO PRAZO")
    print(f"{'─'*55}")

    if not cache_path.exists():
        print("  Sem dados de simulacao. Execute primeiro:")
        print("  python sbwaa.py /simulacao")
        print(f"{'─'*55}")
        return

    try:
        params      = json.loads(cache_path.read_text(encoding="utf-8"))
        mu_anual    = params["mu_anual"]
        sigma_anual = params["sigma_anual"]
        data_calc   = params.get("data", "—")

        pat_str    = patrimonio_str.replace(".", "").replace(",", ".")
        patrimonio = float(pat_str) if pat_str else 0.0
        exemplo    = False
        if patrimonio <= 0:
            patrimonio = 10_000.0
            exemplo = True

        aporte_medio, n_meses = calcular_aporte_medio()

        N_SIM      = 5_000
        ANOS_LISTA = [10, 20, 30]
        rng        = np.random.default_rng(seed=42)
        mu_d       = (1 + mu_anual) ** (1 / 252) - 1
        sigma_d    = sigma_anual / np.sqrt(252)
        drift      = mu_d - 0.5 * sigma_d ** 2

        def _fmt(v: float) -> str:
            if v >= 1e6:
                return f"R${v/1e6:.2f}M"
            return f"R${v/1e3:.0f}k"

        if exemplo:
            print("  (Carteira vazia — exemplo com R$ 10.000)")
        else:
            print(f"  Patrimonio atual: R$ {patrimonio:,.2f}")

        print(f"  mu: {mu_anual*100:.1f}%  |  sigma: {sigma_anual*100:.1f}%  |  {N_SIM:,} simulacoes  |  base: {data_calc}")

        # ── Cenário sem aporte ────────────────────────────────────────────
        print()
        print("  Sem aportes adicionais:")
        print(f"  {'Anos':<6} {'P10 (pessim.)':>14} {'P50 (esperado)':>15} {'P90 (otimist.)':>15}")
        print(f"  {'─'*6} {'─'*14} {'─'*15} {'─'*15}")
        p50_sem = {}
        for anos in ANOS_LISTA:
            finais = _mc_finais(patrimonio, mu_d, sigma_d, drift, anos, N_SIM, 0.0, rng)
            p10, p50, p90 = np.percentile(finais, [10, 50, 90])
            p50_sem[anos] = p50
            print(f"  {anos:<6} {_fmt(p10):>14} {_fmt(p50):>15} {_fmt(p90):>15}")

        # ── Cenário com aporte ────────────────────────────────────────────
        if aporte_medio > 0:
            print()
            print(f"  Mantendo aporte medio de R$ {aporte_medio:,.0f}/mes ({n_meses} meses de historico):")
            print(f"  {'Anos':<6} {'P10 (pessim.)':>14} {'P50 (esperado)':>15} {'P90 (otimist.)':>15} {'Ganho vs sem':>14}")
            print(f"  {'─'*6} {'─'*14} {'─'*15} {'─'*15} {'─'*14}")
            rng2 = np.random.default_rng(seed=42)
            for anos in ANOS_LISTA:
                finais = _mc_finais(patrimonio, mu_d, sigma_d, drift, anos, N_SIM, aporte_medio, rng2)
                p10, p50, p90 = np.percentile(finais, [10, 50, 90])
                ganho = p50 - p50_sem[anos]
                print(f"  {anos:<6} {_fmt(p10):>14} {_fmt(p50):>15} {_fmt(p90):>15} {'+'+_fmt(ganho):>14}")
        else:
            print()
            if n_meses == 0:
                print("  Sem historico de aportes ainda.")
            print("  Para ver projecao com aportes: adicione compras e o calculo sera automatico.")

        print()
        print("  Graficos + backtest historico:  python sbwaa.py /simulacao")
        print(f"{'─'*55}")

        # Projeção das metas
        proventos = ler_proventos_cache()
        exibir_projecao_metas(patrimonio, mu_anual, sigma_anual, aporte_medio, proventos)

    except Exception as e:
        print(f"  Projecao indisponivel: {e}")
        print(f"{'─'*55}")


def exibir_alocacao_vs_ips(posicoes: list[dict], ips_alvo: dict):
    """Calcula e exibe alocação atual vs alvo IPS."""
    if not ips_alvo or not posicoes:
        return

    tipo_map = {
        "AÇÃO ON": "Ações BR", "AÇÃO PN": "Ações BR",
        "FII": "FIIs", "ETF BR": "ETFs BR", "ETF INTL": "ETFs Internac.",
        "RF": "Renda Fixa", "TD": "Tesouro Direto",
        "DEB": "Renda Fixa", "CRI/CRA": "Renda Fixa",
    }

    print(f"\n{'─'*55}")
    print("ALOCAÇÃO vs IPS")
    print(f"{'─'*55}")
    print(f"  {'Classe':<22} {'Atual%':>7}  {'Alvo%':>6}  Status")
    print(f"  {'─'*22} {'─'*7}  {'─'*6}  {'─'*6}")

    for classe, alvo in ips_alvo.items():
        if not alvo:
            continue
        status = "—"
        print(f"  {classe:<22} {'N/D':>7}  {alvo:>5.1f}%  {status}")


def main():
    hoje = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n{'═'*55}")
    print(f"  SBWAA — Carteira | {hoje}")
    print(f"{'═'*55}")

    # Atualizar cotações
    print("Atualizando cotações...")
    subprocess.run(
        [sys.executable, "-u", str(SCRIPTS_DATA / "update_carteira.py")],
        text=True,
    )

    posicoes, resumo = parse_carteira()
    ips_alvo = parse_ips_alvo()

    if not posicoes:
        print("\n  Carteira vazia. Use /adicionar para incluir ativos.")
        exibir_projecao("0")
        print(f"{'═'*55}\n")
        return

    # Tabela de posições
    print(f"\n{'─'*55}")
    print("POSIÇÕES")
    print(f"{'─'*55}")
    print(f"  {'Ticker':<8} {'Tipo':<12} {'Qtd':>8}  {'P.Méd':>9}  {'P.Atual':>9}  {'P&L%':>7}")
    print(f"  {'─'*8} {'─'*12} {'─'*8}  {'─'*9}  {'─'*9}  {'─'*7}")
    for p in posicoes:
        tipo_label = p["tipo"][:12]
        print(f"  {p['ticker']:<8} {tipo_label:<12} {p['qtd']:>8}  {p['pm']:>9}  {p['pa']:>9}  {p['pl_pct']:>7}")

    # Resumo
    print(f"\n{'─'*55}")
    print("RESUMO")
    print(f"{'─'*55}")
    print(f"  Patrimônio Total:  R$ {resumo.get('patrimonio', '—')}")
    print(f"  Total Investido:   R$ {resumo.get('investido', '—')}")
    print(f"  P&L Total:         R$ {resumo.get('pl', '—')}")

    proventos = ler_proventos_cache()
    if proventos:
        total_prov = proventos.get("total_recebido", 0)
        atualizado = proventos.get("atualizado_em", "—")
        print(f"  Proventos Recebidos: R$ {total_prov:,.2f}  (atualizado: {atualizado})")
        try:
            pat_str = resumo.get("patrimonio", "0").replace(".", "").replace(",", ".")
            total_com_prov = float(pat_str) + total_prov
            print(f"  Total c/ Proventos:  R$ {total_com_prov:,.2f}")
        except (ValueError, AttributeError):
            pass
    else:
        print(f"  Proventos Recebidos: — (execute /dividendos para calcular)")

    print(f"  Última atualização: {resumo.get('ultima_atualizacao', '—')}")

    # Alocação vs IPS
    exibir_alocacao_vs_ips(posicoes, ips_alvo)

    # Projeção de longo prazo
    exibir_projecao(resumo.get("patrimonio", "0"))

    print(f"\n  📄 Visão visual completa: vault/00-portfolio/carteira.md")
    print(f"{'═'*55}\n")


if __name__ == "__main__":
    main()
