# SBWAA — PROMPT MASTER: CORREÇÕES + INSTALAÇÃO + RESOLUÇÃO TOTAL
**Versão alvo: v2.1.0**
**Prioridade: MÁXIMA — não encerrar sem resolver 100% dos problemas**

---

## INSTRUÇÃO GERAL AO CLAUDE CODE

Você vai executar uma auditoria e correção completa do sistema SBWAA.
Leve o tempo que precisar. Não encerre esta sessão sem que:

1. Todos os scripts existam e estejam implementados
2. Todos os comandos funcionem sem erro
3. Todas as dependências estejam instaladas
4. O sistema inicie sem erros
5. README, CHANGELOG e VERSION estejam atualizados

Se encontrar um erro durante a execução, resolva-o antes de continuar.
Não pule etapas. Não deixe erros pendentes para "resolver depois".
Registre cada problema encontrado e cada correção aplicada.

---

## ETAPA 0 — MAPEAMENTO DA ESTRUTURA ATUAL

Antes de qualquer coisa, execute:

```bash
# 1. Verificar estrutura de pastas completa
find /sbwaa -type f -name "*.py" | sort
find /sbwaa -type f -name "*.md" | sort
find /sbwaa -type f -name "*.json" | sort

# 2. Verificar Python e pip disponíveis
python --version || python3 --version
pip --version || pip3 --version

# 3. Verificar o que já está instalado
pip list

# 4. Verificar se sbwaa.py existe e tem conteúdo
cat /sbwaa/sbwaa.py 2>/dev/null || echo "ARQUIVO NÃO ENCONTRADO"
```

Registre o resultado. Com base no que encontrar, prossiga para as etapas seguintes.

---

## ETAPA 1 — CRIAR `requirements.txt` COMPLETO

Criar `/sbwaa/requirements.txt` com TODAS as dependências:

```txt
# SBWAA — Requirements
# Instalar com: pip install -r requirements.txt

# === DADOS DE MERCADO ===
requests==2.31.0
yfinance==0.2.38
pandas==2.2.2
numpy==1.26.4

# === PROCESSAMENTO DE DOCUMENTOS ===
PyPDF2==3.0.1
python-docx==1.1.0
openpyxl==3.1.2

# === RAG / KNOWLEDGE BASE ===
chromadb==0.5.0
sentence-transformers==3.0.1
beautifulsoup4==4.12.3
feedparser==6.0.11

# === INTERFACE VISUAL ===
streamlit==1.35.0
plotly==5.22.0
watchdog==4.0.1

# === ANTHROPIC ===
anthropic==0.28.0

# === UTILITÁRIOS ===
python-dotenv==1.0.1
scipy==1.13.1
```

Após criar o arquivo, executar a instalação completa:

```bash
cd /sbwaa
pip install -r requirements.txt --break-system-packages
```

Se algum pacote falhar, tentar alternativas:
```bash
pip install --upgrade pip --break-system-packages
pip install -r requirements.txt --break-system-packages --no-cache-dir
```

Verificar instalação:
```bash
python -c "import anthropic; print('anthropic OK')"
python -c "import yfinance; print('yfinance OK')"
python -c "import chromadb; print('chromadb OK')"
python -c "import streamlit; print('streamlit OK')"
python -c "import pandas; print('pandas OK')"
python -c "import docx; print('python-docx OK')"
python -c "import openpyxl; print('openpyxl OK')"
python -c "import sentence_transformers; print('sentence-transformers OK')"
```

Qualquer falha de importação deve ser resolvida antes de continuar.

---

## ETAPA 2 — RECRIAR `sbwaa.py` CORRIGIDO

Substituir completamente `/sbwaa/sbwaa.py`:

```python
#!/usr/bin/env python3
"""
SBWAA — Second Brain Wealth + Asset + Assessor Individual
Ponto de entrada único. v2.1.0
"""
import sys
import os
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.resolve()

COMANDOS = {
    "/analisar":            ROOT/".claude/agents/portfolio-manager/run_analisar.py",
    "/pm":                  ROOT/".claude/agents/portfolio-manager/run_pm.py",
    "/decidir":             ROOT/".claude/agents/portfolio-manager/run_pm.py",
    "/earnings":            ROOT/".claude/agents/earnings-reviewer/run_earnings_reviewer.py",
    "/tese":                ROOT/".claude/commands/tese.py",
    "/comparar":            ROOT/".claude/commands/comparar.py",
    "/carteira":            ROOT/".claude/commands/carteira.py",
    "/adicionar":           ROOT/"scripts/data/add_ativo.py",
    "/risco-carteira":      ROOT/".claude/commands/risco_carteira.py",
    "/rebalancear":         ROOT/".claude/commands/rebalancear.py",
    "/dividendos":          ROOT/".claude/commands/dividendos.py",
    "/ips":                 ROOT/".claude/commands/ips.py",
    "/morning-call":        ROOT/".claude/commands/morning_call.py",
    "/mundo-economico":     ROOT/".claude/commands/mundo_economico.py",
    "/investimento-do-dia": ROOT/".claude/commands/investimento_do_dia.py",
    "/relatorio-semanal":   ROOT/".claude/commands/relatorio_semanal.py",
    "/relatorio-mensal":    ROOT/".claude/commands/relatorio_mensal.py",
    "/stress-test":         ROOT/".claude/commands/stress_test.py",
    "/knowledge":           ROOT/"knowledge/knowledge_cmd.py",
    "/ui":                  None,
    "/help":                None,
    "/status":              None,
}

def exibir_help():
    print("""
╔══════════════════════════════════════════════════════════╗
║           SBWAA v2.1.0 — Comandos disponíveis           ║
╠══════════════════════════════════════════════════════════╣
║ ANÁLISE                                                  ║
║  /analisar [TICKER]          Pipeline completo (8 etapas)║
║  /tese [TICKER] [--completo] Research+DCF+PM rápido      ║
║  /earnings [TICKER]          Só Earnings Reviewer        ║
║  /comparar [TKR1] [TKR2]     Análise lado a lado         ║
║  /pm [TICKER]                PM direto                   ║
╠══════════════════════════════════════════════════════════╣
║ PORTFÓLIO                                                ║
║  /carteira                   Snapshot da carteira        ║
║  /adicionar TKR TIPO QTD PX  Adicionar ativo             ║
║  /risco-carteira             VaR, CVaR, Sharpe           ║
║  /rebalancear                Ajuste vs IPS               ║
║  /dividendos                 Calendário e histórico      ║
║  /ips [--editar]             Exibir ou editar IPS        ║
╠══════════════════════════════════════════════════════════╣
║ DIÁRIO                                                   ║
║  /morning-call               Briefing pré-abertura       ║
║  /mundo-economico            Macro do dia                ║
║  /investimento-do-dia        Oportunidade do dia         ║
╠══════════════════════════════════════════════════════════╣
║ RELATÓRIOS                                               ║
║  /relatorio-semanal          P&L da semana               ║
║  /relatorio-mensal           Relatório completo do mês   ║
║  /stress-test [CENÁRIO]      Simular choque              ║
╠══════════════════════════════════════════════════════════╣
║ KNOWLEDGE                                                ║
║  /knowledge --status         Status da base              ║
║  /knowledge --adicionar ARQ  Indexar documento           ║
║  /knowledge --buscar QUERY   Busca semântica             ║
║  /knowledge --coletar-rss    Forçar coleta RSS           ║
╠══════════════════════════════════════════════════════════╣
║ SISTEMA                                                  ║
║  /ui                         Interface visual            ║
║  /status                     Versões do sistema          ║
║  /help                       Este menu                   ║
╚══════════════════════════════════════════════════════════╝
""")

def exibir_status():
    print(f"\n{'='*56}")
    print(f"SBWAA — Status | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*56}")
    vf = ROOT/"VERSION.md"
    print(vf.read_text() if vf.exists() else "VERSION.md não encontrado")
    print(f"\nScripts disponíveis:")
    for cmd, path in COMANDOS.items():
        if path:
            status = "✅" if path.exists() else "❌"
            print(f"  {status} {cmd}")
    print(f"{'='*56}\n")

def main():
    if len(sys.argv) < 2:
        exibir_help()
        return
    cmd = sys.argv[1].lower()
    args = sys.argv[2:]
    if cmd == "/help": exibir_help(); return
    if cmd == "/status": exibir_status(); return
    if cmd == "/ui":
        app = ROOT/"interface"/"app.py"
        if not app.exists():
            print("\n❌ Interface não encontrada (Fase 8).\n"); return
        os.system(f"streamlit run {app}")
        return
    if cmd not in COMANDOS:
        print(f"\n❌ Comando '{cmd}' não reconhecido. Use /help.\n"); return
    path = COMANDOS[cmd]
    if not path or not path.exists():
        print(f"\n❌ Script não encontrado: {path}")
        print("   Verifique se todas as fases foram concluídas.\n"); return
    subprocess.run([sys.executable, str(path)] + args)

if __name__ == "__main__":
    main()
```

Testar imediatamente:
```bash
cd /sbwaa
python sbwaa.py /help
python sbwaa.py /status
```

---

## ETAPA 3 — VERIFICAR E CRIAR TODOS OS SCRIPTS FALTANTES

Execute este script de diagnóstico para identificar o que falta:

```python
# Salvar como /sbwaa/scripts/diagnostico.py e executar
from pathlib import Path
ROOT = Path(__file__).parent.parent

scripts_necessarios = {
    # Fase 1
    "scripts/data/fetch_brapi.py": "Busca dados BR via Brapi",
    "scripts/data/fetch_yahoo.py": "Busca dados globais via Yahoo",
    "scripts/data/update_carteira.py": "Atualiza cotações na carteira",
    "scripts/data/add_ativo.py": "Adiciona ativo à carteira",
    "scripts/data/market_snapshot.py": "Snapshot diário de mercado",
    # Fase 2
    ".claude/agents/market-researcher/SKILL.md": "SKILL do Market Researcher",
    ".claude/agents/market-researcher/run_market_researcher.py": "Runner Market Researcher",
    ".claude/agents/earnings-reviewer/SKILL.md": "SKILL do Earnings Reviewer",
    ".claude/agents/earnings-reviewer/run_earnings_reviewer.py": "Runner Earnings Reviewer",
    # Fase 3
    ".claude/agents/model-builder/SKILL.md": "SKILL do Model Builder",
    ".claude/agents/model-builder/run_model_builder.py": "Runner Model Builder",
    ".claude/agents/valuation-reviewer/SKILL.md": "SKILL Valuation Reviewer",
    ".claude/agents/valuation-reviewer/run_valuation_reviewer.py": "Runner Valuation",
    # Fase 4
    ".claude/agents/quant-data-engineer/SKILL.md": "SKILL Quant",
    ".claude/agents/quant-data-engineer/run_quant.py": "Runner Quant",
    ".claude/agents/quant-data-engineer/calculators/returns.py": "Calculadora retornos",
    ".claude/agents/quant-data-engineer/calculators/portfolio_metrics.py": "Métricas portfólio",
    ".claude/agents/quant-data-engineer/calculators/correlation.py": "Correlação",
    ".claude/agents/risk-engineer/SKILL.md": "SKILL Risk Engineer",
    ".claude/agents/risk-engineer/run_risk_engineer.py": "Runner Risk",
    ".claude/agents/risk-engineer/calculators/var.py": "Calculadora VaR/CVaR",
    ".claude/agents/risk-engineer/calculators/stress_test.py": "Stress test",
    # Fase 5
    ".claude/agents/portfolio-manager/SKILL.md": "SKILL Portfolio Manager",
    ".claude/agents/portfolio-manager/run_pm.py": "Runner PM",
    ".claude/agents/portfolio-manager/run_analisar.py": "Orquestrador /analisar",
    # Fase 6 — comandos
    ".claude/commands/morning_call.py": "Comando /morning-call",
    ".claude/commands/mundo_economico.py": "Comando /mundo-economico",
    ".claude/commands/investimento_do_dia.py": "Comando /investimento-do-dia",
    ".claude/commands/carteira.py": "Comando /carteira",
    ".claude/commands/risco_carteira.py": "Comando /risco-carteira",
    ".claude/commands/relatorio_semanal.py": "Comando /relatorio-semanal",
    ".claude/commands/relatorio_mensal.py": "Comando /relatorio-mensal",
    ".claude/commands/stress_test.py": "Comando /stress-test",
    ".claude/commands/rebalancear.py": "Comando /rebalancear",
    ".claude/commands/dividendos.py": "Comando /dividendos",
    ".claude/commands/tese.py": "Comando /tese",
    ".claude/commands/ips.py": "Comando /ips",
    ".claude/commands/comparar.py": "Comando /comparar",
    # Fase 6 — heartbeat
    "scripts/heartbeat/heartbeat.py": "Heartbeat automático",
    "scripts/heartbeat/schedule_heartbeat.py": "Agendador heartbeat",
    "scripts/alerts/check_alerts.py": "Sistema de alertas",
    "scripts/run_research_pipeline.py": "Pipeline integrado",
    # Fase 7 — RAG
    "knowledge/indexer.py": "Indexador RAG",
    "knowledge/retriever.py": "Retriever RAG",
    "knowledge/rss_collector.py": "Coletor RSS",
    "knowledge/knowledge_cmd.py": "Comando /knowledge",
    "knowledge/save_synthesis.py": "Salvador de sínteses",
    "knowledge/sources/sources.json": "Config fontes RSS",
    # Fase 8 — Interface
    "interface/app.py": "Dashboard Streamlit",
    "interface/pages/01_carteira.py": "Página carteira",
    "interface/pages/02_analisar.py": "Página análise",
    "interface/pages/03_morning_call.py": "Página morning call",
    "interface/pages/04_risco.py": "Página risco",
    "interface/pages/05_relatorios.py": "Página relatórios",
    "interface/pages/06_knowledge.py": "Página knowledge",
    "interface/pages/07_agentes.py": "Página agentes",
    "interface/components/metricas_hf.py": "Componente métricas HF",
    "interface/components/pixel_art.py": "Componente pixel art",
    "interface/components/alerts_bar.py": "Barra alertas",
    "interface/components/sidebar.py": "Sidebar",
    "interface/style/sbwaa.css": "CSS customizado",
}

print(f"\n{'='*60}")
print("SBWAA — DIAGNÓSTICO DE SCRIPTS")
print(f"{'='*60}")
faltando = []
existindo = []
for path_rel, descricao in scripts_necessarios.items():
    path_abs = ROOT / path_rel
    if path_abs.exists() and path_abs.stat().st_size > 10:
        existindo.append((path_rel, descricao))
    else:
        faltando.append((path_rel, descricao))

print(f"\n✅ EXISTEM ({len(existindo)} scripts):")
for p, d in existindo:
    print(f"   {p}")

print(f"\n❌ FALTANDO ({len(faltando)} scripts):")
for p, d in faltando:
    print(f"   {p} — {d}")

print(f"\n{'='*60}")
print(f"Total: {len(existindo)}/{len(scripts_necessarios)} presentes")
print(f"{'='*60}\n")
```

```bash
python scripts/diagnostico.py
```

Para CADA script listado como FALTANDO, criá-lo com implementação completa e funcional.
Os scripts das Fases 1–8 já foram especificados nos prompts anteriores.
Recriar qualquer um que estiver ausente ou vazio seguindo as especificações originais.

---

## ETAPA 4 — CRIAR SCRIPTS AUSENTES IDENTIFICADOS

### 4.1 Verificar e corrigir scripts da Fase 1

Executar cada script individualmente e verificar se funciona:

```bash
# Testar fetch_brapi
python scripts/data/fetch_brapi.py PETR4
# Esperado: JSON gerado em scripts/data/cache/brapi_PETR4_{DATA}.json

# Testar fetch_yahoo
python scripts/data/fetch_yahoo.py
# Esperado: JSON dos indicadores macro gerados no cache

# Testar market_snapshot
python scripts/data/market_snapshot.py
# Esperado: nota markdown gerada em vault/02-relatorios/diarios/
```

Se qualquer um falhar, analisar o erro e corrigir o script antes de continuar.

### 4.2 Verificar imports e paths dentro de cada script

Padrão obrigatório no topo de TODOS os scripts:

```python
import sys
from pathlib import Path

# Garantir que o diretório raiz do SBWAA está no sys.path
ROOT = Path(__file__).resolve()
# Subir níveis até chegar em /sbwaa/
while ROOT.name != "sbwaa" and ROOT.parent != ROOT:
    ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
```

Adicionar esse bloco no topo de qualquer script que importe de outros módulos do projeto (ex: retriever, calculators).

### 4.3 Corrigir imports relativos quebrados

Verificar se os seguintes imports funcionam de qualquer diretório:

```python
# Em run_risk_engineer.py
from agents.quant_data_engineer.calculators.var import var_historico, cvar
# SE QUEBRAR, usar path absoluto:
sys.path.insert(0, str(ROOT / ".claude" / "agents" / "risk-engineer"))
from calculators.var import var_historico, cvar
```

---

## ETAPA 5 — VERIFICAR VARIÁVEL DE AMBIENTE ANTHROPIC

```bash
# Verificar se ANTHROPIC_API_KEY está configurada
echo $ANTHROPIC_API_KEY

# Se não estiver, verificar se existe .env
cat /sbwaa/.env 2>/dev/null

# Se não existir .env, criar template
cat > /sbwaa/.env << 'EOF'
# SBWAA — Variáveis de Ambiente
# NUNCA commitar este arquivo (está no .gitignore)
ANTHROPIC_API_KEY=sua_chave_aqui
EOF

echo "⚠️  Configure ANTHROPIC_API_KEY no arquivo .env antes de continuar"
```

Adicionar ao topo de todos os scripts que chamam a API Anthropic:

```python
from dotenv import load_dotenv
import os

load_dotenv(ROOT / ".env")
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("\n❌ ANTHROPIC_API_KEY não configurada.")
    print("   Configure em /sbwaa/.env")
    sys.exit(1)
```

Adicionar `.env` ao `.gitignore` se ainda não estiver.

---

## ETAPA 6 — CRIAR SCRIPTS FALTANTES DE COMANDOS

Para cada script de comando ausente, criar implementação funcional mínima.
Abaixo estão os que mais provavelmente estão faltando:

### `commands/morning_call.py` — se ausente

```python
#!/usr/bin/env python3
"""SBWAA — /morning-call"""
import sys, json, subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent
while ROOT.name != "sbwaa" and ROOT.parent != ROOT: ROOT = ROOT.parent
VAULT = ROOT / "vault"
CACHE = ROOT / "scripts" / "data" / "cache"
hoje = datetime.now().strftime("%Y-%m-%d")
hora = datetime.now().strftime("%H:%M")

def main():
    print(f"\n{'='*55}")
    print(f"SBWAA — Morning Call | {hoje} | {hora}")
    print(f"{'='*55}\n")

    # 1. Atualizar snapshot
    snapshot_script = ROOT / "scripts" / "data" / "market_snapshot.py"
    if snapshot_script.exists():
        print("📊 Atualizando dados de mercado...")
        subprocess.run([sys.executable, str(snapshot_script)],
                       capture_output=True)

    # 2. Rodar Market Researcher
    mr_script = ROOT / ".claude" / "agents" / "market-researcher" / "run_market_researcher.py"
    if mr_script.exists():
        print("🌍 Gerando análise macro...")
        subprocess.run([sys.executable, str(mr_script)])

    # 3. Carregar snapshot para exibir tabela macro
    snapshots = sorted(CACHE.glob("yahoo_*.json"), reverse=True)
    macro_data = {}
    for s in snapshots[:8]:
        try:
            d = json.loads(s.read_text())
            macro_data[d.get("nome", s.stem)] = d
        except: pass

    if macro_data:
        print(f"\n{'─'*55}")
        print("MACRO GLOBAL")
        print(f"{'Indicador':<20} {'Valor':>12} {'Variação':>10}")
        print(f"{'─'*45}")
        for nome, d in macro_data.items():
            valor = d.get("cotacao_atual", "—")
            var = d.get("variacao_dia_pct", "—")
            var_str = f"{var:+.1f}%" if isinstance(var, float) else "—"
            print(f"{nome:<20} {str(valor):>12} {var_str:>10}")

    # 4. Verificar alertas
    alertas_log = ROOT / "logs" / "alerts.log"
    if alertas_log.exists():
        alertas_hoje = [l.strip() for l in alertas_log.read_text().split("\n")
                        if hoje in l and ("CRÍTICO" in l or "ALTO" in l)]
        if alertas_hoje:
            print(f"\n{'─'*55}")
            print("⚡ ALERTAS ATIVOS")
            for a in alertas_hoje[:5]:
                partes = a.split("|")
                print(f"  {'🚨' if 'CRÍTICO' in a else '⚠️ '} {partes[-1].strip()}")

    # Salvar no vault
    saida = VAULT/"02-relatorios"/"diarios"/f"morning-call-{hoje}.md"
    saida.parent.mkdir(parents=True, exist_ok=True)
    if not saida.exists():
        saida.write_text(
            f"---\ntags: [relatorio, morning-call]\n"
            f"cssclasses: [node-relatorio]\ndata: {hoje}\n---\n\n"
            f"# Morning Call — {hoje}\n\n"
            f"Ver vault/03-macro/market-researcher-{hoje}.md para análise completa.\n\n"
            f"## Links\n- [[market-researcher-{hoje}]]\n- [[snapshot-{hoje}]]\n"
        )

    print(f"\n{'='*55}")
    print(f"✅ Morning Call concluído | {hora}")
    print(f"   Relatório: vault/02-relatorios/diarios/morning-call-{hoje}.md")
    print(f"{'='*55}\n")

if __name__ == "__main__":
    main()
```

### `commands/carteira.py` — se ausente

```python
#!/usr/bin/env python3
"""SBWAA — /carteira"""
import sys, subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent
while ROOT.name != "sbwaa" and ROOT.parent != ROOT: ROOT = ROOT.parent
hoje = datetime.now().strftime("%Y-%m-%d")
hora = datetime.now().strftime("%H:%M")

def main():
    print(f"\n{'='*65}")
    print(f"SBWAA — Carteira | {hoje} {hora}")
    print(f"{'='*65}\n")

    # Atualizar cotações
    update_script = ROOT / "scripts" / "data" / "update_carteira.py"
    if update_script.exists():
        print("🔄 Atualizando cotações...")
        subprocess.run([sys.executable, str(update_script)], capture_output=True)

    # Ler e exibir carteira.md
    carteira = ROOT / "vault" / "00-portfolio" / "carteira.md"
    if not carteira.exists():
        print("❌ carteira.md não encontrada. Execute Fase 0.")
        return

    conteudo = carteira.read_text(encoding="utf-8")
    # Remover frontmatter
    linhas = conteudo.split("\n")
    em_yaml = False
    for linha in linhas:
        if linha.strip() == "---":
            em_yaml = not em_yaml
            continue
        if not em_yaml:
            print(linha)

    print(f"{'='*65}\n")

if __name__ == "__main__":
    main()
```

### `commands/risco_carteira.py` — se ausente

```python
#!/usr/bin/env python3
"""SBWAA — /risco-carteira"""
import sys, json, subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent
while ROOT.name != "sbwaa" and ROOT.parent != ROOT: ROOT = ROOT.parent
CACHE = ROOT / "scripts" / "data" / "cache"
hoje = datetime.now().strftime("%Y-%m-%d")

def main():
    print(f"\n{'='*55}")
    print(f"SBWAA — Risco da Carteira | {hoje}")
    print(f"{'='*55}\n")

    # Rodar Quant + Risk
    quant = ROOT/".claude"/"agents"/"quant-data-engineer"/"run_quant.py"
    risk  = ROOT/".claude"/"agents"/"risk-engineer"/"run_risk_engineer.py"

    print("[1/2] 📐 Calculando métricas quantitativas...")
    if quant.exists():
        subprocess.run([sys.executable, str(quant)])
    else:
        print("  ⚠️  run_quant.py não encontrado")

    print("\n[2/2] 🛡️  Calculando métricas de risco...")
    if risk.exists():
        subprocess.run([sys.executable, str(risk)])
    else:
        print("  ⚠️  run_risk_engineer.py não encontrado")

    # Exibir snapshot de risco do cache
    risk_caches = sorted(CACHE.glob("risk_*.json"), reverse=True)
    if risk_caches:
        data = json.loads(risk_caches[0].read_text())
        cb = data.get("circuit_breakers", {})
        print(f"\n{'─'*55}")
        print("MÉTRICAS HF DA CARTEIRA")
        print(f"{'─'*55}")
        print(f"  VaR 95% (1d) histórico:    {data.get('var_historico_95_pct',0):.2%}")
        print(f"  VaR 95% (1d) paramétrico:  {data.get('var_parametrico_95_pct',0):.2%}")
        print(f"  CVaR 95% (1d):             {data.get('cvar_95_pct',0):.2%}")
        print(f"  Drawdown atual:            {data.get('drawdown_atual_pct',0):.2%}")
        print(f"  Concentração máxima:       {data.get('concentracao_maxima_pct',0):.1f}% "
              f"({data.get('concentracao_maxima_ticker','')})")
        print(f"\n  Circuit Breakers:")
        for k, v in cb.items():
            icon = "✅" if v else "🚨"
            print(f"    {icon} {k}")

    print(f"\n{'='*55}\n")

if __name__ == "__main__":
    main()
```

### `commands/mundo_economico.py` — se ausente

```python
#!/usr/bin/env python3
"""SBWAA — /mundo-economico"""
import sys, subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent
while ROOT.name != "sbwaa" and ROOT.parent != ROOT: ROOT = ROOT.parent
VAULT = ROOT / "vault"
hoje = datetime.now().strftime("%Y-%m-%d")

def main():
    print(f"\n{'='*55}")
    print(f"SBWAA — Mundo Econômico | {hoje}")
    print(f"{'='*55}\n")

    # Garantir snapshot atualizado
    snap = ROOT/"scripts"/"data"/"market_snapshot.py"
    if snap.exists():
        subprocess.run([sys.executable, str(snap)], capture_output=True)

    # Exibir último relatório do market researcher
    macro_dir = VAULT / "03-macro"
    relatorios = sorted(macro_dir.glob(f"market-researcher-{hoje}*.md"), reverse=True)

    if relatorios:
        conteudo = relatorios[0].read_text(encoding="utf-8")
        linhas = conteudo.split("\n")
        em_yaml = False
        for linha in linhas:
            if linha.strip() == "---":
                em_yaml = not em_yaml
                continue
            if not em_yaml:
                print(linha)
    else:
        print("Gerando análise macro do dia...")
        mr = ROOT/".claude"/"agents"/"market-researcher"/"run_market_researcher.py"
        if mr.exists():
            subprocess.run([sys.executable, str(mr)])
        else:
            print("❌ Market Researcher não encontrado.")

    print(f"\n{'='*55}\n")

if __name__ == "__main__":
    main()
```

### `commands/investimento_do_dia.py` — se ausente

```python
#!/usr/bin/env python3
"""SBWAA — /investimento-do-dia"""
import sys, json, os
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent
while ROOT.name != "sbwaa" and ROOT.parent != ROOT: ROOT = ROOT.parent
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")
import anthropic

VAULT = ROOT / "vault"
CACHE = ROOT / "scripts" / "data" / "cache"
hoje = datetime.now().strftime("%Y-%m-%d")

def main():
    print(f"\n{'='*55}")
    print(f"SBWAA — Investimento do Dia | {hoje}")
    print(f"{'='*55}\n")

    ips_path = VAULT / "00-portfolio" / "ips.md"
    ips = ips_path.read_text() if ips_path.exists() else "IPS não configurado"

    snap_caches = sorted(CACHE.glob("yahoo_*.json"), reverse=True)
    macro_resumo = f"{len(snap_caches)} indicadores macro disponíveis"

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        messages=[{"role": "user", "content": f"""
Você é o Market Researcher do SBWAA. Com base no IPS do usuário e no cenário de hoje,
sugira 1-2 ativos ou classes de ativo para explorar análise — NÃO é recomendação de compra.

IPS:
{ips}

Contexto macro hoje: {macro_resumo}

Formato: para cada sugestão, informar ticker (se ação/FII/ETF), tipo, setor,
e em 2 linhas por que faz sentido explorar hoje.
Terminar com: "Execute /analisar TICKER para análise completa."
"""}]
    )
    print(response.content[0].text)
    print(f"\n{'='*55}\n")

if __name__ == "__main__":
    main()
```

### `commands/stress_test.py` — se ausente

```python
#!/usr/bin/env python3
"""SBWAA — /stress-test [CENÁRIO] [VALOR%]"""
import sys, json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent
while ROOT.name != "sbwaa" and ROOT.parent != ROOT: ROOT = ROOT.parent
CACHE = ROOT / "scripts" / "data" / "cache"
hoje = datetime.now().strftime("%Y-%m-%d")

CENARIOS = {
    "crise-2008":   {"nome": "Crise Financeira 2008",   "ibov": -41.0, "desc": "IBOV -41% no ano"},
    "covid-2020":   {"nome": "COVID Março 2020",         "ibov": -30.0, "desc": "IBOV -30% em 30 dias"},
    "eleicoes-2022":{"nome": "Incerteza Eleitoral 2022", "ibov": -15.0, "desc": "IBOV -15%"},
    "lula1-2002":   {"nome": "Crise de Confiança 2002",  "ibov": -17.0, "desc": "Spread soberano +800bps"},
}

def rodar_cenario(nome_cenario, cenario, beta, n_ativos):
    impacto_pct = beta * (cenario["ibov"] / 100)
    print(f"\n  📌 {cenario['nome']}")
    print(f"     {cenario['desc']}")
    print(f"     Impacto estimado carteira: {impacto_pct:.1%}")
    print(f"     (em R$100k normalizados: R$ {impacto_pct * 100000:,.0f})")

def main():
    print(f"\n{'='*55}")
    print(f"SBWAA — Stress Test | {hoje}")
    print(f"{'='*55}")

    # Carregar dados de risco para pegar beta
    risk_caches = sorted(CACHE.glob("risk_*.json"), reverse=True)
    quant_caches = sorted(CACHE.glob("quant_*.json"), reverse=True)

    beta = 0.9  # default
    n_ativos = 1

    if quant_caches:
        q = json.loads(quant_caches[0].read_text())
        beta = q.get("carteira", {}).get("beta_ibov", 0.9)
        n_ativos = len(q.get("ativos", {}))

    print(f"\nBeta da carteira vs IBOV: {beta:.2f}")
    print(f"Número de ativos: {n_ativos}")

    # Determinar cenários a rodar
    args = sys.argv[1:]
    cenario_especifico = args[0].lower() if args else None
    valor_custom = None

    if cenario_especifico == "custom" and len(args) > 1:
        try:
            valor_custom = float(args[1])
        except:
            pass

    print(f"\n{'─'*55}")
    print("RESULTADOS DOS STRESS TESTS")
    print(f"{'─'*55}")

    if valor_custom is not None:
        cenario_custom = {"nome": f"Choque customizado {valor_custom:+.0f}%",
                          "ibov": valor_custom, "desc": f"IBOV {valor_custom:+.0f}%"}
        rodar_cenario("custom", cenario_custom, beta, n_ativos)
    elif cenario_especifico and cenario_especifico in CENARIOS:
        rodar_cenario(cenario_especifico, CENARIOS[cenario_especifico], beta, n_ativos)
    else:
        for key, cenario in CENARIOS.items():
            rodar_cenario(key, cenario, beta, n_ativos)

    print(f"\n{'─'*55}")
    print("* Baseado em beta da carteira. Impacto real varia por ativo.")
    print("* Use /risco-carteira para métricas completas.")
    print(f"{'='*55}\n")

if __name__ == "__main__":
    main()
```

### `commands/relatorio_semanal.py` — se ausente

```python
#!/usr/bin/env python3
"""SBWAA — /relatorio-semanal"""
import sys, json, os
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parent.parent.parent
while ROOT.name != "sbwaa" and ROOT.parent != ROOT: ROOT = ROOT.parent
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")
import anthropic

VAULT = ROOT / "vault"
CACHE = ROOT / "scripts" / "data" / "cache"
hoje = datetime.now()
num_semana = hoje.strftime("%V")
ano = hoje.strftime("%Y")

def main():
    print(f"\n{'='*55}")
    print(f"SBWAA — Relatório Semanal | Semana {num_semana}/{ano}")
    print(f"{'='*55}\n")
    print("⏳ Gerando relatório semanal (1-2 min)...\n")

    quant_caches = sorted(CACHE.glob("quant_*.json"), reverse=True)
    risk_caches  = sorted(CACHE.glob("risk_*.json"),  reverse=True)

    quant = json.loads(quant_caches[0].read_text()) if quant_caches else {}
    risk  = json.loads(risk_caches[0].read_text())  if risk_caches  else {}

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        messages=[{"role": "user", "content": f"""
Você é o Portfolio Manager do SBWAA. Gere o relatório semanal da Semana {num_semana}/{ano}.

DADOS QUANTITATIVOS:
{json.dumps(quant, indent=2, ensure_ascii=False)[:2500]}

DADOS DE RISCO:
{json.dumps(risk, indent=2, ensure_ascii=False)[:1500]}

Inclua: sumário da semana, performance por ativo (retorno 1M disponível),
comparação vs IBOV, métricas HF da semana, top 3 melhores/piores,
dividendos recebidos se disponível, outlook próxima semana.
Tom direto. Máximo 500 palavras.
"""}]
    )

    conteudo = response.content[0].text
    print(conteudo)

    # Salvar no vault
    saida = VAULT/"02-relatorios"/"semanais"/f"semana-{ano}-W{num_semana}.md"
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(
        f"---\ntags: [relatorio, semanal]\ncssclasses: [node-relatorio]\n"
        f"semana: {num_semana}\nano: {ano}\n---\n\n"
        f"# Relatório Semanal — Semana {num_semana}/{ano}\n\n{conteudo}\n\n"
        f"## Links\n- [[carteira]]\n- [[ips]]\n"
    )

    # Gerar DOCX
    try:
        from docx import Document
        doc = Document()
        doc.add_heading(f"SBWAA — Relatório Semanal | Semana {num_semana}/{ano}", 0)
        doc.add_paragraph(conteudo)
        doc.save(str(saida.with_suffix(".docx")))
        print(f"\n📄 DOCX gerado")
    except Exception as e:
        print(f"\n⚠️  DOCX: {e}")

    print(f"\n✅ Salvo em: vault/02-relatorios/semanais/semana-{ano}-W{num_semana}.md\n")

if __name__ == "__main__":
    main()
```

---

## ETAPA 7 — VERIFICAR HEARTBEAT E ALERTAS

```bash
# Testar heartbeat manualmente
python scripts/heartbeat/heartbeat.py

# Testar sistema de alertas
python scripts/alerts/check_alerts.py
```

Se ausentes, criar versões mínimas funcionais.

---

## ETAPA 8 — VERIFICAR KNOWLEDGE BASE

```bash
# Verificar ChromaDB e sentence-transformers
python -c "
import chromadb
from sentence_transformers import SentenceTransformer
print('Carregando modelo (pode demorar na 1ª vez)...')
modelo = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
print('✅ Modelo carregado com sucesso')
client = chromadb.PersistentClient(path='knowledge/.chromadb')
print('✅ ChromaDB inicializado')
col = client.get_or_create_collection('sbwaa_knowledge')
print(f'✅ Coleção: {col.count()} documentos')
"
```

Se falhar, diagnosticar e resolver o problema específico.

---

## ETAPA 9 — VERIFICAR INTERFACE STREAMLIT

```bash
# Verificar se app.py existe e não tem erros de sintaxe
python -c "
import ast, sys
from pathlib import Path
app = Path('interface/app.py')
if not app.exists():
    print('❌ interface/app.py não encontrado')
    sys.exit(1)
try:
    ast.parse(app.read_text())
    print('✅ interface/app.py — sintaxe OK')
except SyntaxError as e:
    print(f'❌ Erro de sintaxe: {e}')
    sys.exit(1)
"

# Verificar todas as páginas
for f in interface/pages/*.py; do
    python -c "import ast; ast.parse(open('$f').read()); print(f'✅ $f')" 2>&1 || echo "❌ $f"
done
```

---

## ETAPA 10 — ATUALIZAR README, VERSION E CHANGELOG

### `VERSION.md` — atualizar para v2.1.0:

```markdown
# SBWAA — VERSION CONTROL

## Global
**v2.1.0** — Auditoria completa, correção de todos os erros, requirements.txt

## Módulos
| Módulo          | Versão  | Status       |
|-----------------|---------|--------------|
| investments     | v1.7.1  | ✅ Operacional|
| heartbeat       | v1.0.1  | ✅ Operacional|
| knowledge-base  | v1.0.0  | ✅ Operacional|
| interface       | v1.0.0  | ✅ Beta       |
```

### `CHANGELOG.md` — adicionar entrada:

```markdown
## [2.1.0] — DATA_DE_HOJE

### Fixed
- requirements.txt criado com todas as dependências
- sbwaa.py: resolução de paths corrigida para todos os comandos
- Todos os scripts de comandos faltantes criados e implementados
- Imports quebrados corrigidos com sys.path explícito
- ANTHROPIC_API_KEY carregada via .env em todos os scripts
- Scripts de Fases 1-4 verificados e corrigidos
- Pipeline integrado consolidado em versão final

### Added
- requirements.txt completo
- .env template para configuração da API key
- scripts/diagnostico.py para auditoria futura
- Fallback gracioso quando scripts não encontrados
```

### `README.md` — atualizar status de todas as fases:

```markdown
# SBWAA — Second Brain Wealth + Asset + Assessor Individual

Sistema multi-agente de análise financeira pessoal.
Operação 100% local. Dados 100% privados.
**Versão: v2.1.0**

## Início rápido

```bash
cd /sbwaa
pip install -r requirements.txt
cp .env.template .env  # configurar ANTHROPIC_API_KEY
python sbwaa.py /help
```

## Status das Fases

| Fase | Descrição                     | Status        | Versão  |
|------|-------------------------------|---------------|---------|
| 0    | Base do sistema               | ✅ Completo   | v1.0.0  |
| 1    | Pipeline de dados             | ✅ Completo   | v1.1.0  |
| 2    | Market Researcher + Earnings  | ✅ Completo   | v1.2.0  |
| 3    | Model Builder + Valuation     | ✅ Completo   | v1.3.0  |
| 4    | Quant + Risk Engineer         | ✅ Completo   | v1.4.0  |
| 5    | Portfolio Manager             | ✅ Completo   | v1.5.0  |
| 6    | Comandos + Heartbeat          | ✅ Completo   | v1.6.0  |
| 7    | RAG — Knowledge Base          | ✅ Completo   | v1.7.0  |
| 8    | Interface Visual              | ✅ Beta       | v1.0.0  |

## Comandos principais

```bash
python sbwaa.py /analisar PETR4      # Pipeline completo
python sbwaa.py /morning-call         # Briefing do dia
python sbwaa.py /carteira             # Ver portfólio
python sbwaa.py /risco-carteira       # Métricas HF
python sbwaa.py /ui                   # Interface visual
python sbwaa.py /help                 # Todos os comandos
```

## Segurança
Dados privados nunca saem do vault local.
APIs recebem apenas tickers públicos.
Consulte CLAUDE.md — Seção Security Policy.
```

---

## INSTRUÇÃO FINAL AO CLAUDE CODE

Após executar todas as etapas acima:

1. Execute `python sbwaa.py /status` e confirme que TODOS os comandos mostram ✅
2. Execute `python scripts/diagnostico.py` e confirme 0 scripts faltando
3. Se ainda houver qualquer ❌, resolva antes de encerrar
4. Confirme com: **"SBWAA v2.1.0 — Todos os erros resolvidos"**

**NÃO encerre esta sessão com qualquer script ausente ou erro não resolvido.**
