#!/usr/bin/env python3
"""
SBWAA — Second Brain Wealth + Asset + Assessor Individual
Ponto de entrada único para todos os comandos.

Uso:
    python sbwaa.py /carteira
    python sbwaa.py /stress-test
    python sbwaa.py /adicionar --ticker PETR4 --tipo acao-pn --quantidade 100 --preco-medio 45.00 --setor energia
    python sbwaa.py /help

Comandos com IA (sem API key): use diretamente no chat do Claude Code
    /analisar PETR4        /tese VALE3         /morning-call
    /earnings MXRF11       /comparar A B       /pm PETR4
    /mundo-economico       /investimento-do-dia
    /relatorio-semanal     /relatorio-mensal   /rebalancear
"""

import sys
import os
import subprocess
from datetime import datetime
from pathlib import Path

# Forçar UTF-8 no stdout/stderr e em todos os subprocessos (Windows)
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).parent

# Modo atual: Claude Code (sem API key)
# Para reativar modo API key, consulte _standby/README.md
MODO_CLAUDE_CODE = True

# Comandos que rodam localmente (sem IA / sem API key)
COMANDOS_LOCAIS = {
    "/carteira":        ".claude/commands/carteira.py",
    "/watchlist":       ".claude/commands/watchlist.py",
    "/adicionar":       "scripts/data/add_ativo.py",
    "/vender":          "scripts/data/vender_ativo.py",
    "/risco-carteira":  ".claude/commands/risco_carteira.py",
    "/dividendos":      ".claude/commands/dividendos.py",
    "/stress-test":     ".claude/commands/stress_test.py",
    "/simulacao":       "scripts/simulacao_carteira.py",
    "/ips":             ".claude/commands/ips.py",
    "/snapshot":            "scripts/data/market_snapshot.py",
    "/knowledge":           "knowledge/knowledge_cmd.py",
    "/otimizar-expansao":   "scripts/data/optimize_expansao.py",
}

# Comandos de IA — redirecionados para Claude Code (sem API key)
COMANDOS_IA = {
    "/analisar":            "analisar",
    "/tese":                "tese",
    "/pm":                  "pm",
    "/decidir":             "pm",
    "/earnings":            "earnings",
    "/comparar":            "comparar",
    "/morning-call":        "morning-call",
    "/mundo-economico":     "mundo-economico",
    "/investimento-do-dia": "investimento-do-dia",
    "/relatorio-semanal":   "relatorio-semanal",
    "/relatorio-mensal":    "relatorio-mensal",
    "/rebalancear":         "rebalancear",
    "/revisar-carteira":    "revisar-carteira",
    "/metas":               "metas",
}

TODOS_COMANDOS = {**COMANDOS_LOCAIS, **{k: None for k in COMANDOS_IA}, "/ui": None, "/help": None, "/status": None}


def exibir_help():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║            SBWAA — Referência de Comandos  v2.11.2               ║
╚══════════════════════════════════════════════════════════════════╝

  Uso:  python sbwaa.py /COMANDO [argumentos]
  Dica: use PowerShell — Git Bash pode quebrar argumentos com /

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PORTFÓLIO  (local — sem IA, sem API key)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  python sbwaa.py /carteira
      Atualiza cotações e exibe posições, P&L% e alocação vs IPS.

  python sbwaa.py /watchlist
      Lista todos os ativos analisados + carteira com último veredicto,
      data da análise e frescor (✅ atual / ⚠️ defasado / 🔴 rever).
      Flag: --rever   (mostra apenas os que precisam de nova análise)

  python sbwaa.py /adicionar --ticker PETR4 --tipo acao-on \\
                             --quantidade 100 --preco-medio 38.50 \\
                             --setor energia
      Adiciona ativo à carteira, cria pasta em vault/01-ativos/.
      Flag opcional: --skip-validacao       (pula checagem nas APIs)
      Flag opcional: --data 2024-03-15      (data de entrada; padrão: hoje)
      Se ticker já existe: recalcula P.M. ponderado e mostra P&L antes.
      Tipos: acao-on | acao-pn | fii | etf-br | etf-intl
             renda-fixa | tesouro | debenture | cri-cra

  Para renda fixa (renda-fixa | tesouro | debenture | cri-cra):
      --setor é o emissor (XP, BTG, Nubank, Tesouro Nacional...)
      Flags opcionais exclusivas de RF:
        --nome "CDB XP 110% CDI"     nome do produto
        --indexador CDI              CDI | IPCA | Selic | PRE | IGPM
        --taxa "110%"                taxa (110% CDI, +6% IPCA, 13.5% PRE)
        --vencimento 2027-12-01      data de vencimento
      Validação de API pulada automaticamente (sem ticker em bolsa).

  Exemplos RF:
    python sbwaa.py /adicionar --ticker CDB001 --tipo renda-fixa \\
                               --quantidade 1 --preco-medio 5000 \\
                               --setor XP --nome "CDB XP 110% CDI" \\
                               --indexador CDI --taxa "110%" --vencimento 2027-12-01
    python sbwaa.py /adicionar --ticker NTNB35 --tipo tesouro \\
                               --quantidade 1 --preco-medio 3500 \\
                               --setor "Tesouro Nacional" \\
                               --indexador IPCA --taxa "+6.12%" --vencimento 2035-05-15

  python sbwaa.py /vender --ticker PETR4 --quantidade 50 --preco 45.00
      Registra venda parcial ou total. Calcula P&L realizado.
      Remove ativo da carteira se quantidade chegar a zero.
      Flag opcional: --data 2024-03-15      (data da venda; padrão: hoje)

  python sbwaa.py /dividendos
      Próximos dividendos (60 dias), histórico do ano e Yield on Cost.

  python sbwaa.py /risco-carteira
      VaR 95%, CVaR, Sharpe 12m, volatilidade, drawdown, beta IBOV,
      concentração e circuit breakers do IPS.

  python sbwaa.py /otimizar-expansao
      Compara fronteira eficiente da carteira atual vs carteira + watchlist.
      Ranking de candidatos da watchlist: Sharpe próprio, correlação, impacto
      marginal, peso no portfólio ótimo. Indica quais ativos MELHORA / NEUTRO / PIORA.
      Salva cache para /rebalancear e /revisar-carteira consumirem.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  MERCADO  (local — sem IA, sem API key)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  python sbwaa.py /snapshot
      Macro global (IBOV, S&P500, DXY, petróleo, ouro, BRL/USD...)
      + cotações da carteira. Salva em vault/02-relatorios/diarios/.

  python sbwaa.py /stress-test
      Todos os cenários: Crise 2008, COVID-2020, Eleições 2022, Lula 2002.

  python sbwaa.py /stress-test covid-2020
      Cenário específico (busca por nome parcial).
      Opções: crise-2008 | covid-2020 | eleicoes-2022 | lula-2002

  python sbwaa.py /stress-test custom -25
      Choque personalizado: qualquer percentual positivo ou negativo.

  python sbwaa.py /simulacao
      Backtest histórico (5 anos) + Monte Carlo (10/20/30 anos) com gráficos.
      Salva PNGs em logs/simulacao/ e atualiza parâmetros para o /carteira.
      Flags opcionais: --patrimonio 50000  --aporte 1000  --no-graficos

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  KNOWLEDGE BASE  (local — sem IA, sem API key)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  python sbwaa.py /knowledge --status
      Total de documentos indexados, tamanho da base, última atualização.

  python sbwaa.py /knowledge --adicionar "C:\\relatorios\\resultado.pdf"
      Indexa arquivo (PDF, DOCX, TXT, MD) ou pasta inteira recursivamente.

  python sbwaa.py /knowledge --buscar "valuation petróleo Brasil"
      Busca semântica — retorna chunks relevantes rankeados por score.

  python sbwaa.py /knowledge --coletar-rss
      Coleta notícias dos feeds RSS (Valor, InfoMoney, BCB, Bloomberg...).

  python sbwaa.py /knowledge --listar
      Lista todos os documentos indexados na base.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ANÁLISE COM IA  (digitar no chat do Claude Code)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /analisar PETR4
      Pipeline completo: 8 agentes em sequência do dado ao veredicto (10 etapas).
      Researcher → Earnings → DCF → Valuation → Quant → Econometrician → Risk → PM.
      Aceita múltiplos tickers: /analisar PETR4 VALE3 (batch com tabela comparativa).
      Output em vault/01-ativos/PETR4/.

  /tese PETR4
      Versão rápida: Research + DCF + decisão do PM. Sem Quant/Risk standalone.

  /earnings PETR4
      Revisão do último resultado trimestral: receita, EBITDA, dívida, guidance.

  /comparar PETR4 VALE3
      Análise lado a lado: valuation, qualidade, risco, retorno e alocação relativa.

  /pm PETR4
      Só o Portfolio Manager, com dados já cacheados. Retorna COMPRAR/AGUARDAR/EVITAR.

  /pm
  /pm 700
      Modo Aporte: PM distribui capital entre múltiplos ativos da watchlist.
      Sem ticker → perguntas interativas (valor, classe, nº de ativos, restrições).
      Com valor  → atalho: pula a pergunta de valor e vai direto às demais.
      Requisito: ativos devem ter análise via /analisar (ou mín. /pm TICKER).
      Se faltar análise: PM avisa, oferece rodar /analisar e retoma automaticamente.

  /morning-call
      Briefing pré-abertura: snapshot macro + análise + alertas ativos.

  /mundo-economico
      Panorama do cenário econômico global e impactos no Brasil.

  /investimento-do-dia [categoria]
      Sugere 1-2 ativos com base no IPS e cenário macro atual.
      Categorias opcionais: fii | acao | etf | etf-br | etf-intl | rf | td

  /metas
      Dashboard de progresso das metas financeiras (renda passiva, reserva,
      patrimônio total e metas livres). Configure em vault/00-portfolio/metas.md.

  /relatorio-semanal
      P&L da semana, métricas e outlook. Gera .md e .docx.

  /relatorio-mensal
      Relatório completo do mês com benchmarks. Gera .md e .docx.

  /rebalancear
      Desvios vs IPS e sugestão de compras/vendas para reequilibrar.

  /revisar-carteira
      PM revisa cada posição em carteira: MANTER / AUMENTAR / REDUZIR / SAIR.
      Painel consolidado com sizing alvo, justificativa e alertas de IPS.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  SISTEMA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  python sbwaa.py /ips
      Exibe o Investment Policy Statement (perfil, alocações, limites).

  python sbwaa.py /ui
      Abre o painel visual (customtkinter) com todos os comandos em botões.

  python sbwaa.py /status
      Versão atual, modo de operação e data/hora do sistema.

  python sbwaa.py /help
      Este menu.

══════════════════════════════════════════════════════════════════════
""")


def exibir_status():
    versao_path = PROJECT_ROOT / "VERSION.md"
    print(f"\n{'═'*55}")
    print(f"SBWAA — Status do Sistema")
    print(f"Modo: {'Claude Code (sem API key)' if MODO_CLAUDE_CODE else 'API key (anthropic)'}")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'═'*55}")
    if versao_path.exists():
        print(versao_path.read_text(encoding="utf-8"))
    print(f"{'═'*55}\n")


def redirecionar_claude_code(comando, args_extra):
    slash = COMANDOS_IA[comando]
    ticker = " ".join(args_extra).upper() if args_extra else ""
    exemplo = f"/{slash} {ticker}".strip()
    print(f"""
  Este comando usa IA e roda no Claude Code (sem API key).

  → Digite no chat do Claude Code:
    {exemplo}

  O Claude Code vai executar os scripts de dados e fazer
  a análise completa sem precisar de ANTHROPIC_API_KEY.
""")


def main():
    if len(sys.argv) < 2:
        exibir_help()
        return

    raw = sys.argv[1]
    # Git Bash no Windows expande /cmd para C:/Program Files/Git/cmd
    # Normaliza extraindo só o nome base e prefixando com /
    if not raw.startswith("/") and "/" in raw:
        raw = "/" + Path(raw).name
    comando = raw.lower()
    args_extra = sys.argv[2:]

    if comando == "/help":
        exibir_help()
        return

    if comando == "/status":
        exibir_status()
        return

    if comando == "/ui":
        interface_path = PROJECT_ROOT / "interface" / "ui.py"
        if not interface_path.exists():
            print("\n❌ Interface não encontrada.\n")
            return
        subprocess.run([sys.executable, str(interface_path)])
        return

    # Comandos de IA — redirecionar para Claude Code
    if comando in COMANDOS_IA:
        redirecionar_claude_code(comando, args_extra)
        return

    # Comandos locais
    if comando not in COMANDOS_LOCAIS:
        print(f"\n❌ Comando '{comando}' não reconhecido.")
        print("   Use /help para ver todos os comandos disponíveis.\n")
        return

    script_rel = COMANDOS_LOCAIS[comando]
    script_path = PROJECT_ROOT / script_rel

    if not script_path.exists():
        print(f"\n❌ Script não encontrado: {script_rel}\n")
        return

    subprocess.run([sys.executable, "-u", str(script_path)] + args_extra)


if __name__ == "__main__":
    main()
