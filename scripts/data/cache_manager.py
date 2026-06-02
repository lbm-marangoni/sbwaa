"""
cache_manager.py — Cache centralizado com TTL configurável por tipo.

TTL padrão (sobreposto via .env):
  CACHE_TTL_COTACAO_MIN=15          cotações em tempo quase-real
  CACHE_TTL_MACRO_MIN=60            índices e macro global
  CACHE_TTL_DIVIDENDOS_MIN=360      dividendos e proventos (6h)
  CACHE_TTL_FUNDAMENTALS_MIN=1440   múltiplos e consenso (24h)
  CACHE_TTL_HISTORICO_MIN=1440      séries OHLCV (24h)
  CACHE_TTL_BCB_MIN=1440            Banco Central (24h)
  CACHE_TTL_MODELOS_MIN=1440        DCF, quant, risco, econometria (24h)

Uso direto:
    python cache_manager.py --status             # todos os tipos
    python cache_manager.py --status cotacao     # filtra um tipo
    python cache_manager.py --clear stale        # remove stale de todos os tipos
    python cache_manager.py --clear historico    # remove stale de histórico
    python cache_manager.py --force-clear cotacao # remove tudo (stale + fresh)

Via sbwaa.py:
    python sbwaa.py /cache --status
    python sbwaa.py /cache --clear stale
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    from dotenv import load_dotenv
    _env = Path(__file__).parent.parent.parent / ".env"
    if _env.exists():
        load_dotenv(_env)
except ImportError:
    pass

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# ── TTL por tipo (em minutos) — configurável via .env ────────────────────────
CACHE_TYPES: dict[str, dict] = {
    "cotacao": {
        "label": "Cotação",
        "ttl_min": int(os.getenv("CACHE_TTL_COTACAO_MIN", "15")),
        "description": "Preços em tempo quase-real (yahoo, brapi)",
    },
    "macro": {
        "label": "Macro",
        "ttl_min": int(os.getenv("CACHE_TTL_MACRO_MIN", "60")),
        "description": "Índices globais e macro (IBOV, S&P, DXY…)",
    },
    "dividendos": {
        "label": "Dividendos",
        "ttl_min": int(os.getenv("CACHE_TTL_DIVIDENDOS_MIN", "360")),
        "description": "Proventos e dados Investidor10",
    },
    "fundamentals": {
        "label": "Fundamentais",
        "ttl_min": int(os.getenv("CACHE_TTL_FUNDAMENTALS_MIN", "1440")),
        "description": "Múltiplos, consenso e valuation",
    },
    "historico": {
        "label": "Histórico",
        "ttl_min": int(os.getenv("CACHE_TTL_HISTORICO_MIN", "1440")),
        "description": "Séries OHLCV (yfinance)",
    },
    "macro_bcb": {
        "label": "BCB/Macro",
        "ttl_min": int(os.getenv("CACHE_TTL_BCB_MIN", "1440")),
        "description": "Selic, IPCA, IBC-Br (Banco Central)",
    },
    "modelos": {
        "label": "Modelos",
        "ttl_min": int(os.getenv("CACHE_TTL_MODELOS_MIN", "1440")),
        "description": "DCF, econometria, quant e risco",
    },
    "outros": {
        "label": "Outros",
        "ttl_min": int(os.getenv("CACHE_TTL_OUTROS_MIN", "240")),
        "description": "Arquivos não categorizados",
    },
}

_MODELO_PREFIXES = ("dcf_", "econometria_", "quant_", "risk_")


# ── Classificação de arquivos ────────────────────────────────────────────────

def tipo_do_arquivo(nome: str) -> str:
    """Determina o tipo de cache com base no prefixo do nome do arquivo.

    Para yahoo_*: tickers brasileiros têm sufixo .SA_ no nome (ex: yahoo_PETR4.SA_).
    Tickers macro (índices, câmbio, commodities) não têm .SA_, e.g.:
      yahoo_INDICE_BVSP_, yahoo_BRL_X_, yahoo_DX_Y.NYB_, yahoo_CL_F_, yahoo_GC_F_
    """
    if nome.startswith("hist_"):
        return "historico"
    if nome.startswith("bcb_"):
        return "macro_bcb"
    if nome.startswith(_MODELO_PREFIXES):
        return "modelos"
    if nome.startswith(("fundamentals_", "consensus_")):
        return "fundamentals"
    if nome.startswith("investidor10_"):
        return "dividendos"
    if nome.startswith("yahoo_"):
        return "cotacao" if ".SA_" in nome else "macro"
    if nome.startswith("brapi_"):
        return "cotacao"
    return "outros"


def ttl_para_arquivo(nome: str) -> timedelta:
    """Retorna o TTL configurado para o tipo do arquivo."""
    return timedelta(minutes=CACHE_TYPES[tipo_do_arquivo(nome)]["ttl_min"])


# ── API pública — drop-in para cache_valido() nos fetchers ──────────────────

def is_valid(caminho: Path) -> bool:
    """Retorna True se o arquivo de cache ainda está dentro do TTL configurado."""
    if not caminho.exists():
        return False
    modificado = datetime.fromtimestamp(caminho.stat().st_mtime)
    return datetime.now() - modificado < ttl_para_arquivo(caminho.name)


# ── Helpers de formatação ────────────────────────────────────────────────────

def _idade_str(segundos: float) -> str:
    if segundos < 60:
        return f"{int(segundos)}s"
    if segundos < 3600:
        return f"{int(segundos / 60)}min"
    if segundos < 86400:
        return f"{segundos / 3600:.1f}h"
    return f"{segundos / 86400:.1f}d"


def _tamanho_str(total_bytes: int) -> str:
    if total_bytes < 1024:
        return f"{total_bytes} B"
    if total_bytes < 1024 ** 2:
        return f"{total_bytes / 1024:.1f} KB"
    return f"{total_bytes / 1024 ** 2:.1f} MB"


def _ttl_str(minutos: int) -> str:
    if minutos < 60:
        return f"{minutos}min"
    if minutos < 1440:
        return f"{minutos // 60}h"
    return f"{minutos // 1440}d"


# ── Status ────────────────────────────────────────────────────────────────────

def status(filtro: str | None = None) -> None:
    """Exibe tabela de status de todos os caches, agrupada por tipo."""
    agora = datetime.now()

    tipos_validos = list(CACHE_TYPES)
    if filtro:
        match = [t for t in tipos_validos if t == filtro or CACHE_TYPES[t]["label"].lower() == filtro.lower()]
        if not match:
            print(f"\n❌ Tipo '{filtro}' não reconhecido.")
            print(f"   Tipos válidos: {', '.join(tipos_validos)}\n")
            return
        tipos_validos = match

    grupos: dict[str, dict] = {k: {"fresh": [], "stale": [], "bytes": 0} for k in tipos_validos}

    for f in CACHE_DIR.iterdir():
        if f.is_dir():
            continue
        tipo = tipo_do_arquivo(f.name)
        if tipo not in grupos:
            continue
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        idade_s = (agora - mtime).total_seconds()
        ttl_s = ttl_para_arquivo(f.name).total_seconds()
        grupos[tipo]["bytes"] += f.stat().st_size
        entry = {"nome": f.name, "idade_s": idade_s, "ttl_s": ttl_s, "path": f}
        if idade_s <= ttl_s:
            grupos[tipo]["fresh"].append(entry)
        else:
            grupos[tipo]["stale"].append(entry)

    total_fresh = total_stale = total_bytes = 0
    linhas = []
    for tipo in tipos_validos:
        g = grupos[tipo]
        nf, ns, nb = len(g["fresh"]), len(g["stale"]), g["bytes"]
        if nf == 0 and ns == 0:
            continue
        cfg = CACHE_TYPES[tipo]
        ttl_label = _ttl_str(cfg["ttl_min"])
        tam_label = _tamanho_str(nb)
        status_icon = "✅" if ns == 0 else f"⚠️  {ns} stale"
        linhas.append((cfg["label"], ttl_label, nf, ns, tam_label, status_icon))
        total_fresh += nf
        total_stale += ns
        total_bytes += nb

    print(f"\n{'═' * 68}")
    print(f"  SBWAA — Cache Status · {agora.strftime('%Y-%m-%d %H:%M')}")
    print(f"{'═' * 68}")

    if not linhas:
        print("\n  Nenhum arquivo de cache encontrado.\n")
        return

    print(f"\n  {'Tipo':<14} {'TTL':<7} {'Fresh':>6} {'Stale':>6}  {'Tamanho':>9}  Status")
    print(f"  {'─' * 62}")
    for label, ttl_label, nf, ns, tam, icon in linhas:
        print(f"  {label:<14} {ttl_label:<7} {nf:>6} {ns:>6}  {tam:>9}  {icon}")
    print(f"  {'─' * 62}")
    print(f"  {'TOTAL':<14} {'':7} {total_fresh:>6} {total_stale:>6}  {_tamanho_str(total_bytes):>9}")

    if total_stale > 0:
        print(f"\n  💡 python sbwaa.py /cache --clear stale")
        print(f"     python sbwaa.py /cache --clear <tipo>  (ex: historico, cotacao)")

    # Detalhe dos stale quando filtrado por tipo
    if filtro:
        for tipo in tipos_validos:
            stale_list = sorted(grupos[tipo]["stale"], key=lambda x: x["idade_s"], reverse=True)
            if stale_list:
                print(f"\n  Arquivos stale em '{CACHE_TYPES[tipo]['label']}':")
                for e in stale_list[:15]:
                    ttl_min = int(e["ttl_s"] // 60)
                    print(f"    {e['nome']}  (idade: {_idade_str(e['idade_s'])}, TTL: {_ttl_str(ttl_min)})")
                if len(stale_list) > 15:
                    print(f"    … e mais {len(stale_list) - 15} arquivo(s)")

    print()


# ── Clear ─────────────────────────────────────────────────────────────────────

def clear(filtro: str, force: bool = False) -> None:
    """Remove caches stale (ou todos com force=True) de um tipo ou de 'stale'."""
    agora = datetime.now()
    removidos = 0
    bytes_removidos = 0

    if filtro != "stale" and filtro not in CACHE_TYPES:
        print(f"\n❌ Tipo '{filtro}' não reconhecido.")
        print(f"   Use 'stale' ou um tipo válido: {', '.join(CACHE_TYPES)}\n")
        return

    for f in list(CACHE_DIR.iterdir()):
        if f.is_dir():
            continue
        tipo = tipo_do_arquivo(f.name)
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        idade = agora - mtime
        ttl = ttl_para_arquivo(f.name)
        eh_stale = idade > ttl

        if filtro == "stale":
            alvo = eh_stale
        elif force:
            alvo = tipo == filtro
        else:
            alvo = tipo == filtro and eh_stale

        if alvo:
            bytes_removidos += f.stat().st_size
            f.unlink()
            removidos += 1

    acao = "forçada" if force else "stale"
    print(f"\n  ✅ {removidos} arquivo(s) removido(s) ({_tamanho_str(bytes_removidos)}) — limpeza {acao}\n")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    args = sys.argv[1:]

    if not args or "--status" in args:
        filtro = next((a for a in args if not a.startswith("-")), None)
        status(filtro)

    elif "--clear" in args:
        idx = args.index("--clear")
        filtro = args[idx + 1] if idx + 1 < len(args) else "stale"
        clear(filtro, force=False)

    elif "--force-clear" in args:
        idx = args.index("--force-clear")
        filtro = args[idx + 1] if idx + 1 < len(args) else "stale"
        clear(filtro, force=True)

    else:
        print(__doc__)


if __name__ == "__main__":
    main()
