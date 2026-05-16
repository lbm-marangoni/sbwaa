# SBWAA — PROMPT DE TESTES COMPLETOS
**Executar APÓS o prompt de correções (v2.1.0)**
**Objetivo: validar 100% do sistema sem deixar nenhum erro pendente**

---

## INSTRUÇÃO AO CLAUDE CODE

Execute esta bateria de testes completa e sistemática.
Para cada teste, registre: PASSOU ✅ / FALHOU ❌ / PARCIAL ⚠️
Qualquer falha deve ser corrigida imediatamente — não registre e continue.
Corrija, depois re-execute o teste, só então avance.
Ao final, apresente o relatório completo de testes.

---

## BLOCO 0 — PRÉ-REQUISITOS

```bash
echo "=== BLOCO 0: PRÉ-REQUISITOS ==="

# 0.1 Python disponível
python --version && echo "✅ Python OK" || echo "❌ Python não encontrado"

# 0.2 Todas as dependências instaladas
python -c "
deps = [
    ('anthropic', 'anthropic'),
    ('pandas', 'pandas'),
    ('numpy', 'numpy'),
    ('yfinance', 'yfinance'),
    ('requests', 'requests'),
    ('docx', 'python-docx'),
    ('openpyxl', 'openpyxl'),
    ('chromadb', 'chromadb'),
    ('sentence_transformers', 'sentence-transformers'),
    ('streamlit', 'streamlit'),
    ('plotly', 'plotly'),
    ('bs4', 'beautifulsoup4'),
    ('feedparser', 'feedparser'),
    ('dotenv', 'python-dotenv'),
    ('scipy', 'scipy'),
    ('PyPDF2', 'PyPDF2'),
]
falhou = []
for modulo, nome in deps:
    try:
        __import__(modulo)
        print(f'  ✅ {nome}')
    except ImportError:
        print(f'  ❌ {nome} — NÃO INSTALADO')
        falhou.append(nome)
if falhou:
    print(f'\n❌ Instalar: pip install {chr(32).join(falhou)} --break-system-packages')
else:
    print('\n✅ Todas as dependências OK')
"

# 0.3 ANTHROPIC_API_KEY configurada
python -c "
from dotenv import load_dotenv
import os
from pathlib import Path
load_dotenv(Path('.' ) / '.env')
key = os.environ.get('ANTHROPIC_API_KEY', '')
if key and len(key) > 10:
    print(f'✅ ANTHROPIC_API_KEY configurada ({key[:8]}...)')
else:
    print('❌ ANTHROPIC_API_KEY não configurada — configure em .env')
"

# 0.4 Estrutura de pastas raiz
for pasta in ".claude/agents" ".claude/commands" "scripts/data" "scripts/heartbeat" \
             "scripts/alerts" "knowledge" "vault/00-portfolio" "vault/01-ativos" \
             "vault/02-relatorios" "vault/03-macro" "vault/04-knowledge" \
             "vault/05-risk" "logs" "interface"; do
    [ -d "$pasta" ] && echo "  ✅ $pasta" || echo "  ❌ $pasta — PASTA FALTANDO"
done

# 0.5 Arquivos base críticos
for arq in "CLAUDE.md" "VERSION.md" "CHANGELOG.md" "README.md" \
           "requirements.txt" "sbwaa.py" ".env" \
           "vault/00-portfolio/carteira.md" "vault/00-portfolio/ips.md" \
           "vault/00-portfolio/historico-trades.md"; do
    [ -f "$arq" ] && echo "  ✅ $arq" || echo "  ❌ $arq — ARQUIVO FALTANDO"
done
```

---

## BLOCO 1 — SBWAA.PY (PONTO DE ENTRADA)

```bash
echo "=== BLOCO 1: SBWAA.PY ==="

# 1.1 Sintaxe do arquivo
python -c "
import ast
code = open('sbwaa.py').read()
try:
    ast.parse(code)
    print('✅ sbwaa.py — sintaxe válida')
except SyntaxError as e:
    print(f'❌ sbwaa.py — erro de sintaxe: {e}')
"

# 1.2 /help funciona
python sbwaa.py /help | head -5 && echo "✅ /help OK" || echo "❌ /help falhou"

# 1.3 /status funciona e lista comandos
python sbwaa.py /status && echo "✅ /status OK" || echo "❌ /status falhou"

# 1.4 Comando inválido não quebra
python sbwaa.py /comando-inexistente 2>&1 | grep -q "não reconhecido" && \
    echo "✅ Comando inválido tratado OK" || echo "❌ Comando inválido não tratado"

# 1.5 Todos os scripts mapeados existem
python -c "
import sys
from pathlib import Path
ROOT = Path('.')

erros = []
# Importar o mapa de comandos do sbwaa.py
exec(open('sbwaa.py').read().split('def exibir_help')[0])
for cmd, path in COMANDOS.items():
    if path and not Path(str(path)).exists():
        erros.append(f'❌ {cmd} → {path}')
    elif path:
        print(f'  ✅ {cmd}')
if erros:
    for e in erros:
        print(e)
    print(f'\n❌ {len(erros)} scripts faltando')
else:
    print('\n✅ Todos os scripts mapeados existem')
"
```

---

## BLOCO 2 — FASE 1: PIPELINE DE DADOS

```bash
echo "=== BLOCO 2: PIPELINE DE DADOS ==="

# 2.1 fetch_brapi.py — buscar dados de PETR4
echo "Testando fetch_brapi com PETR4..."
python scripts/data/fetch_brapi.py PETR4 2>&1
ls scripts/data/cache/brapi_PETR4_*.json 2>/dev/null && \
    echo "✅ Cache Brapi gerado" || echo "❌ Cache Brapi não gerado"

# 2.2 fetch_yahoo.py — buscar dados macro
echo "Testando fetch_yahoo..."
python scripts/data/fetch_yahoo.py 2>&1
ls scripts/data/cache/yahoo_*.json 2>/dev/null && \
    echo "✅ Cache Yahoo gerado" || echo "❌ Cache Yahoo não gerado"

# 2.3 market_snapshot.py — gerar snapshot do dia
echo "Testando market_snapshot..."
python scripts/data/market_snapshot.py 2>&1
DATA=$(date +%Y-%m-%d)
ls "vault/02-relatorios/diarios/snapshot-${DATA}.md" 2>/dev/null && \
    echo "✅ Snapshot do dia gerado" || echo "❌ Snapshot não gerado"

# 2.4 add_ativo.py — adicionar ativo de teste
echo "Testando add_ativo com PETR4 (ação-pn)..."
python scripts/data/add_ativo.py --ticker TESTE11 --tipo fii \
    --quantidade 100 --preco-medio 10.00 --setor teste 2>&1
ls "vault/01-ativos/TESTE11/tese.md" 2>/dev/null && \
    echo "✅ Ativo TESTE11 adicionado" || echo "❌ add_ativo falhou"

# 2.5 update_carteira.py — atualizar cotações
echo "Testando update_carteira..."
python scripts/data/update_carteira.py 2>&1 && \
    echo "✅ update_carteira OK" || echo "❌ update_carteira falhou"

# Limpar ativo de teste
rm -rf vault/01-ativos/TESTE11 2>/dev/null
```

---

## BLOCO 3 — FASE 2: AGENTES DE RESEARCH

```bash
echo "=== BLOCO 3: AGENTES DE RESEARCH ==="

# 3.1 SKILL.md dos agentes existem e têm conteúdo
for agente in "market-researcher" "earnings-reviewer"; do
    skill=".claude/agents/${agente}/SKILL.md"
    if [ -f "$skill" ] && [ $(wc -c < "$skill") -gt 100 ]; then
        echo "  ✅ ${agente}/SKILL.md OK ($(wc -w < $skill) palavras)"
    else
        echo "  ❌ ${agente}/SKILL.md — ausente ou vazio"
    fi
done

# 3.2 run_market_researcher.py — sintaxe e execução
python -c "import ast; ast.parse(open('.claude/agents/market-researcher/run_market_researcher.py').read()); print('✅ market-researcher sintaxe OK')" 2>&1 || echo "❌ market-researcher erro de sintaxe"

echo "Rodando Market Researcher (pode levar 30s)..."
python .claude/agents/market-researcher/run_market_researcher.py 2>&1
DATA=$(date +%Y-%m-%d)
ls "vault/03-macro/market-researcher-${DATA}.md" 2>/dev/null && \
    echo "✅ Market Researcher gerou output" || echo "❌ Market Researcher sem output"

# 3.3 run_earnings_reviewer.py — sintaxe
python -c "import ast; ast.parse(open('.claude/agents/earnings-reviewer/run_earnings_reviewer.py').read()); print('✅ earnings-reviewer sintaxe OK')" 2>&1 || echo "❌ earnings-reviewer erro de sintaxe"

echo "Rodando Earnings Reviewer para PETR4..."
python .claude/agents/earnings-reviewer/run_earnings_reviewer.py PETR4 2>&1
ls vault/01-ativos/PETR4/earnings-*.md 2>/dev/null && \
    echo "✅ Earnings Reviewer gerou output" || echo "⚠️  Earnings Reviewer — sem output (pode não ter dados)"
```

---

## BLOCO 4 — FASE 3: MODEL BUILDER + VALUATION

```bash
echo "=== BLOCO 4: MODEL BUILDER + VALUATION ==="

# 4.1 Verificar calculadoras da Fase 3
for script in ".claude/agents/model-builder/SKILL.md" \
              ".claude/agents/model-builder/run_model_builder.py" \
              ".claude/agents/valuation-reviewer/SKILL.md" \
              ".claude/agents/valuation-reviewer/run_valuation_reviewer.py"; do
    [ -f "$script" ] && echo "  ✅ $script" || echo "  ❌ $script — FALTANDO"
done

# 4.2 Sintaxe dos scripts
for script in ".claude/agents/model-builder/run_model_builder.py" \
              ".claude/agents/valuation-reviewer/run_valuation_reviewer.py"; do
    [ -f "$script" ] && python -c "import ast; ast.parse(open('$script').read()); print('  ✅ $script sintaxe OK')" 2>&1 || true
done

# 4.3 Model Builder — executar com PETR4
echo "Rodando Model Builder para PETR4 (pode levar 60s com Opus)..."
python .claude/agents/model-builder/run_model_builder.py PETR4 2>&1
DATA=$(date +%Y-%m-%d)
ls "vault/01-ativos/PETR4/dcf-PETR4-v1.xlsx" 2>/dev/null && \
    echo "✅ DCF XLSX gerado" || echo "❌ DCF XLSX não gerado"
ls "scripts/data/cache/dcf_PETR4_${DATA}.json" 2>/dev/null && \
    echo "✅ Cache DCF JSON gerado" || echo "❌ Cache DCF JSON não gerado"

# 4.4 Valuation Reviewer — versão curta
echo "Rodando Valuation Reviewer para PETR4 (curta)..."
python .claude/agents/valuation-reviewer/run_valuation_reviewer.py PETR4 --versao curta 2>&1
ls vault/01-ativos/PETR4/equity-research-PETR4-*-curta.md 2>/dev/null && \
    echo "✅ Equity research curto gerado" || echo "❌ Equity research curto não gerado"
ls vault/01-ativos/PETR4/equity-research-PETR4-*-curta.docx 2>/dev/null && \
    echo "✅ DOCX curto gerado" || echo "❌ DOCX curto não gerado"

# 4.5 Flag --tipo fii funciona
echo "Testando flag --tipo fii..."
python .claude/agents/model-builder/run_model_builder.py MXRF11 --tipo fii 2>&1 | \
    grep -q "FII\|Gordon\|Dividend" && \
    echo "✅ Flag --tipo fii reconhecida" || echo "⚠️  Flag --tipo fii não detectada"
```

---

## BLOCO 5 — FASE 4: QUANT + RISK ENGINEER

```bash
echo "=== BLOCO 5: QUANT + RISK ENGINEER ==="

# 5.1 Calculadoras existem
for calc in ".claude/agents/quant-data-engineer/calculators/returns.py" \
            ".claude/agents/quant-data-engineer/calculators/portfolio_metrics.py" \
            ".claude/agents/quant-data-engineer/calculators/correlation.py" \
            ".claude/agents/risk-engineer/calculators/var.py" \
            ".claude/agents/risk-engineer/calculators/stress_test.py"; do
    [ -f "$calc" ] && echo "  ✅ $calc" || echo "  ❌ $calc — FALTANDO"
done

# 5.2 Testar calculadoras individualmente
python -c "
import sys
sys.path.insert(0, '.claude/agents/quant-data-engineer')
import numpy as np
import pandas as pd
from calculators.returns import retorno_total, volatilidade_anualizada, sharpe

prices = pd.Series([100, 102, 101, 105, 103, 108])
rt = retorno_total(prices)
vol = volatilidade_anualizada(prices)
sh = sharpe(0.15, 0.20, 0.1275)
print(f'✅ Calculadora returns OK: retorno={rt:.2%}, vol={vol:.2%}, sharpe={sh:.2f}')
" 2>&1 || echo "❌ Calculadora returns falhou"

python -c "
import sys
sys.path.insert(0, '.claude/agents/risk-engineer')
import pandas as pd
import numpy as np
from calculators.var import var_historico, var_parametrico, cvar

retornos = pd.Series(np.random.normal(0.001, 0.02, 252))
vh = var_historico(retornos)
vp = var_parametrico(0.02/252**0.5 * 252**0.5)
cv = cvar(retornos)
assert cv >= vh, 'CVaR deve ser >= VaR'
print(f'✅ Calculadora VaR OK: VaR={vh:.2%}, CVaR={cv:.2%}')
" 2>&1 || echo "❌ Calculadora VaR falhou"

# 5.3 Rodar Quant completo
echo "Rodando Quant/Data Engineer..."
python .claude/agents/quant-data-engineer/run_quant.py 2>&1
DATA=$(date +%Y-%m-%d)
ls "scripts/data/cache/quant_${DATA}.json" 2>/dev/null && \
    echo "✅ Cache Quant gerado" || echo "⚠️  Cache Quant não gerado (carteira pode estar vazia)"

# 5.4 Rodar Risk Engineer
echo "Rodando Risk Engineer..."
python .claude/agents/risk-engineer/run_risk_engineer.py 2>&1
ls "scripts/data/cache/risk_${DATA}.json" 2>/dev/null && \
    echo "✅ Cache Risk gerado" || echo "⚠️  Cache Risk não gerado"
ls "vault/05-risk/snapshots/risk-${DATA}.md" 2>/dev/null && \
    echo "✅ Nota de risco gerada no vault" || echo "⚠️  Nota de risco não gerada"
```

---

## BLOCO 6 — FASE 5: PORTFOLIO MANAGER + /ANALISAR

```bash
echo "=== BLOCO 6: PORTFOLIO MANAGER ==="

# 6.1 Arquivos existem
for arq in ".claude/agents/portfolio-manager/SKILL.md" \
           ".claude/agents/portfolio-manager/run_pm.py" \
           ".claude/agents/portfolio-manager/run_analisar.py"; do
    [ -f "$arq" ] && echo "  ✅ $arq" || echo "  ❌ $arq — FALTANDO"
done

# 6.2 decisoes.md existe
[ -f "vault/00-portfolio/decisoes.md" ] && \
    echo "✅ decisoes.md existe" || echo "❌ decisoes.md não existe"

# 6.3 Verificar que SKILL.md do PM tem as seções críticas
python -c "
skill = open('.claude/agents/portfolio-manager/SKILL.md').read()
checks = [
    ('Personalidade crítica', 'NÃO é um assistente' in skill or 'não é um assistente' in skill.lower()),
    ('Veredictos definidos', 'COMPRAR' in skill),
    ('Fluxo interativo', 'AGUARDAR' in skill),
    ('Métricas HF', 'Sharpe' in skill and 'VaR' in skill),
    ('Sizing', 'sizing' in skill.lower() or 'Sizing' in skill),
]
for nome, ok in checks:
    print(f'  {\"✅\" if ok else \"❌\"} {nome}')
" 2>&1

# 6.4 run_analisar.py — verificar se tem as 8 etapas
python -c "
code = open('.claude/agents/portfolio-manager/run_analisar.py').read()
etapas = ['market_snapshot', 'market_researcher', 'earnings_reviewer',
          'model_builder', 'valuation_reviewer', 'quant', 'risk', 'run_pm']
for etapa in etapas:
    ok = etapa in code or etapa.replace('_', '-') in code
    print(f'  {\"✅\" if ok else \"❌\"} {etapa}')
" 2>&1 || echo "❌ run_analisar.py com problemas"
```

---

## BLOCO 7 — FASE 6: COMANDOS

```bash
echo "=== BLOCO 7: COMANDOS ==="

COMANDOS_LISTA=(
    "/carteira" "/morning-call" "/mundo-economico"
    "/investimento-do-dia" "/risco-carteira" "/dividendos"
    "/ips" "/stress-test" "/relatorio-semanal"
    "/comparar PETR4 VALE3" "/tese PETR4"
)

for cmd in "${COMANDOS_LISTA[@]}"; do
    echo "Testando: python sbwaa.py $cmd (5s timeout)..."
    timeout 30 python sbwaa.py $cmd 2>&1 | head -3
    echo "  ---"
done

# Teste específico do /adicionar
echo "Testando /adicionar..."
python sbwaa.py /adicionar --ticker TSTT11 --tipo fii \
    --quantidade 50 --preco-medio 100.00 --setor teste 2>&1
[ -d "vault/01-ativos/TSTT11" ] && echo "✅ /adicionar OK" || echo "❌ /adicionar falhou"
rm -rf vault/01-ativos/TSTT11 2>/dev/null

echo "Testando /ips..."
python sbwaa.py /ips 2>&1 | head -5 && echo "✅ /ips OK" || echo "❌ /ips falhou"

echo "Testando /ips --editar (só verificar se abre sem crash)..."
echo "q" | timeout 5 python sbwaa.py /ips --editar 2>&1 || true
echo "✅ /ips --editar não travou"
```

---

## BLOCO 8 — FASE 6: HEARTBEAT E ALERTAS

```bash
echo "=== BLOCO 8: HEARTBEAT E ALERTAS ==="

# 8.1 Scripts existem
for arq in "scripts/heartbeat/heartbeat.py" \
           "scripts/heartbeat/schedule_heartbeat.py" \
           "scripts/alerts/check_alerts.py"; do
    [ -f "$arq" ] && echo "  ✅ $arq" || echo "  ❌ $arq — FALTANDO"
done

# 8.2 Heartbeat roda sem erro
echo "Testando heartbeat manualmente..."
timeout 60 python scripts/heartbeat/heartbeat.py 2>&1 | tail -5
[ -f "logs/heartbeat.log" ] && echo "✅ Log do heartbeat criado" || echo "⚠️  Log não criado"

# 8.3 Alertas
echo "Testando sistema de alertas..."
python scripts/alerts/check_alerts.py 2>&1 | head -10
[ -f "logs/alerts.log" ] && echo "✅ Log de alertas criado" || echo "⚠️  Log não criado (normal se sem alertas)"

# 8.4 schedule_heartbeat exibe instruções
python scripts/heartbeat/schedule_heartbeat.py --status 2>&1 | head -5 && \
    echo "✅ schedule_heartbeat OK" || echo "❌ schedule_heartbeat falhou"
```

---

## BLOCO 9 — FASE 7: KNOWLEDGE BASE

```bash
echo "=== BLOCO 9: KNOWLEDGE BASE ==="

# 9.1 Scripts existem
for arq in "knowledge/indexer.py" "knowledge/retriever.py" \
           "knowledge/rss_collector.py" "knowledge/knowledge_cmd.py" \
           "knowledge/save_synthesis.py" "knowledge/sources/sources.json"; do
    [ -f "$arq" ] && echo "  ✅ $arq" || echo "  ❌ $arq — FALTANDO"
done

# 9.2 ChromaDB inicializa
python -c "
import chromadb
client = chromadb.PersistentClient(path='knowledge/.chromadb')
col = client.get_or_create_collection('sbwaa_knowledge')
print(f'✅ ChromaDB OK — {col.count()} documentos na base')
" 2>&1 || echo "❌ ChromaDB falhou"

# 9.3 Modelo de embedding carrega
python -c "
from sentence_transformers import SentenceTransformer
modelo = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
embedding = modelo.encode(['teste de embedding em português'])
print(f'✅ Modelo OK — embedding shape: {embedding.shape}')
" 2>&1 || echo "❌ Modelo de embedding falhou"

# 9.4 Retriever funciona (busca vazia)
python -c "
import sys
sys.path.insert(0, '.')
from knowledge.retriever import buscar
resultados = buscar('análise fundamentalista valuation Brasil', n_resultados=3)
print(f'✅ Retriever OK — {len(resultados)} resultados para busca vazia')
" 2>&1 || echo "❌ Retriever falhou"

# 9.5 Comando /knowledge --status
echo "Testando /knowledge --status..."
python sbwaa.py /knowledge --status 2>&1 | head -10 && \
    echo "✅ /knowledge --status OK" || echo "❌ /knowledge --status falhou"

# 9.6 Indexar um documento de teste pequeno
echo "Testando indexação de documento..."
echo "Análise fundamentalista: Sharpe Ratio mede retorno ajustado ao risco. VaR mede perda potencial." \
    > /tmp/teste_sbwaa.txt
python sbwaa.py /knowledge --adicionar /tmp/teste_sbwaa.txt 2>&1 | head -5
rm /tmp/teste_sbwaa.txt

# 9.7 Busca semântica funciona após indexação
python sbwaa.py /knowledge --buscar "Sharpe Ratio risco" 2>&1 | head -10 && \
    echo "✅ Busca semântica OK" || echo "❌ Busca semântica falhou"
```

---

## BLOCO 10 — FASE 8: INTERFACE STREAMLIT

```bash
echo "=== BLOCO 10: INTERFACE STREAMLIT ==="

# 10.1 Todos os arquivos existem
for arq in "interface/app.py" \
           "interface/pages/01_carteira.py" \
           "interface/pages/02_analisar.py" \
           "interface/pages/03_morning_call.py" \
           "interface/pages/04_risco.py" \
           "interface/pages/05_relatorios.py" \
           "interface/pages/06_knowledge.py" \
           "interface/pages/07_agentes.py" \
           "interface/components/metricas_hf.py" \
           "interface/components/pixel_art.py" \
           "interface/components/alerts_bar.py" \
           "interface/components/sidebar.py" \
           "interface/style/sbwaa.css"; do
    [ -f "$arq" ] && echo "  ✅ $arq" || echo "  ❌ $arq — FALTANDO"
done

# 10.2 Verificar sintaxe de todos os arquivos Python da interface
for py in interface/app.py interface/pages/*.py interface/components/*.py; do
    [ -f "$py" ] && python -c "
import ast
try:
    ast.parse(open('$py').read())
    print('  ✅ $py — sintaxe OK')
except SyntaxError as e:
    print('  ❌ $py — ERRO: ' + str(e))
"
done

# 10.3 Streamlit pode importar o app sem erro
python -c "
import subprocess, sys
result = subprocess.run(
    [sys.executable, '-m', 'streamlit', 'run', 'interface/app.py',
     '--headless', '--server.headless=true', '--server.port=8599'],
    timeout=10, capture_output=True, text=True
)
# Streamlit vai tentar iniciar — esperamos timeout (normal)
print('✅ Streamlit inicia sem erro de sintaxe')
" 2>&1 || echo "⚠️  Verificar interface manualmente: python sbwaa.py /ui"

# 10.4 Componentes importáveis
python -c "
import sys
sys.path.insert(0, 'interface')
# Não pode importar direto pois usa st.* — verificar apenas sintaxe
import ast
for comp in ['components/metricas_hf.py', 'components/pixel_art.py',
             'components/alerts_bar.py', 'components/sidebar.py']:
    ast.parse(open(f'interface/{comp}').read())
    print(f'  ✅ {comp} — sintaxe OK')
" 2>&1 || echo "❌ Componentes com problemas"
```

---

## BLOCO 11 — TESTE DE INTEGRAÇÃO COMPLETO

```bash
echo "=== BLOCO 11: INTEGRAÇÃO COMPLETA ==="

# 11.1 Adicionar um ativo real de teste
echo "Adicionando VALE3 para teste de integração..."
python sbwaa.py /adicionar --ticker VALE3 --tipo acao-on \
    --quantidade 50 --preco-medio 60.00 --setor mineracao 2>&1
[ -d "vault/01-ativos/VALE3" ] && echo "✅ VALE3 adicionado" || echo "❌ Falha ao adicionar"

# 11.2 Atualizar carteira
echo "Atualizando carteira..."
python scripts/data/update_carteira.py 2>&1 | tail -3

# 11.3 Ver carteira
echo "Visualizando carteira..."
python sbwaa.py /carteira 2>&1 | head -20

# 11.4 Pipeline /tese (mais rápido que /analisar)
echo "Executando /tese VALE3 (pode levar 2-3 min)..."
timeout 300 python sbwaa.py /tese VALE3 2>&1
ls vault/01-ativos/VALE3/equity-research*.md 2>/dev/null && \
    echo "✅ /tese gerou relatório" || echo "❌ /tese sem output"

# 11.5 Risco da carteira
echo "Calculando risco..."
python sbwaa.py /risco-carteira 2>&1 | head -20

# 11.6 Morning call
echo "Morning call..."
timeout 120 python sbwaa.py /morning-call 2>&1 | head -20

# 11.7 Verificar que wikilinks foram gerados
echo "Verificando wikilinks nos outputs..."
python -c "
from pathlib import Path
vault = Path('vault')
arquivos_md = list(vault.rglob('*.md'))
com_links = [f for f in arquivos_md if '[[' in f.read_text(errors='ignore')]
print(f'✅ {len(com_links)}/{len(arquivos_md)} arquivos .md têm wikilinks')
" 2>&1
```

---

## BLOCO 12 — RELATÓRIO FINAL

Após executar todos os blocos, gerar relatório:

```python
# Salvar como scripts/gerar_relatorio_testes.py e executar
from pathlib import Path
from datetime import datetime

ROOT = Path(".")
VAULT = ROOT / "vault"
CACHE = ROOT / "scripts" / "data" / "cache"
hoje = datetime.now().strftime("%Y-%m-%d")

print(f"\n{'='*65}")
print(f"SBWAA — RELATÓRIO DE TESTES | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"{'='*65}")

# Scripts presentes
scripts = list(ROOT.rglob("*.py"))
print(f"\n📁 Scripts Python: {len(scripts)} arquivos")

# Cache gerado
caches = list(CACHE.glob("*.json"))
print(f"💾 Cache de dados: {len(caches)} arquivos")

# Vault preenchido
mds = list(VAULT.rglob("*.md"))
print(f"📝 Notas no vault: {len(mds)} arquivos")

# DOCX gerados
docxs = list(VAULT.rglob("*.docx"))
print(f"📄 DOCXs gerados: {len(docxs)} arquivos")

# XLSX gerados
xlsxs = list(VAULT.rglob("*.xlsx"))
print(f"📊 XLSXs gerados: {len(xlsxs)} arquivos")

# Agentes com SKILL.md
agentes = list((ROOT/".claude"/"agents").glob("*/SKILL.md"))
print(f"🤖 Agentes com SKILL.md: {len(agentes)}/7")

# Comandos com script
cmds = list((ROOT/".claude"/"commands").glob("*.py"))
print(f"⌨️  Scripts de comandos: {len(cmds)}/13")

# ChromaDB
try:
    import chromadb
    client = chromadb.PersistentClient(path="knowledge/.chromadb")
    col = client.get_or_create_collection("sbwaa_knowledge")
    print(f"🧠 Knowledge base: {col.count()} chunks indexados")
except:
    print("🧠 Knowledge base: não inicializado")

print(f"\n{'='*65}")
print("VERSION ATUAL:")
vf = ROOT / "VERSION.md"
if vf.exists():
    print(vf.read_text())
print(f"{'='*65}\n")
```

```bash
python scripts/gerar_relatorio_testes.py
```

---

## INSTRUÇÃO FINAL AO CLAUDE CODE

Após executar todos os 12 blocos:

1. Qualquer teste que retornou ❌ deve ser corrigido e re-executado
2. Testes ⚠️ devem ser investigados — se são limitações reais (ex: carteira vazia), documentar; se são bugs, corrigir
3. Executar `python sbwaa.py /status` — deve mostrar ✅ em todos os comandos
4. Atualizar VERSION.md, CHANGELOG.md e README.md com data e status final
5. Confirmar com: **"SBWAA v2.1.0 — Testes concluídos. X/Y testes passaram."**

**NÃO encerre sem que pelo menos 90% dos testes passem.**
Para os demais, documentar limitação conhecida com causa e workaround.
