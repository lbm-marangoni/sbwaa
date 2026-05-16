# SBWAA — FASE 7: RAG — KNOWLEDGE BASE
**Prompt para execução no Claude Code**
**Versão:** 1.7.0
**Fase:** 7 de 8
**Pré-requisito:** Fases 0–6 concluídas (investments v1.6.0 | heartbeat v1.0.0)

---

## CONTEXTO

A Fase 7 constrói a **base de conhecimento do SBWAA** — o que transforma
os agentes de analistas genéricos em especialistas com contexto profundo.

O RAG (Retrieval-Augmented Generation) permite que qualquer agente, ao
analisar um ativo ou cenário, recupere automaticamente trechos relevantes
de livros, equity research, cartas de gestoras, relatórios de bancos e
fontes confiáveis indexadas localmente.

**Tudo fica local. Nenhum documento sai do vault.**

Modelo para indexação e síntese: `claude-sonnet-4-6`, effort `medium`.
Engine de embeddings e busca: `chromadb` + `sentence-transformers` (local,
sem chamada externa para embeddings).

---

## REGRAS GERAIS — LER ANTES DE EXECUTAR

1. Instalar dependências:
```bash
pip install chromadb sentence-transformers pypdf2 python-docx \
            beautifulsoup4 requests feedparser --break-system-packages
```
2. O banco de vetores fica em `/sbwaa/knowledge/.chromadb/` — local,
   nunca sincronizado externamente
3. Adicionar ao `.gitignore`:
   ```
   knowledge/.chromadb/
   knowledge/raw/
   ```
4. Documentos brutos ficam em `/sbwaa/knowledge/raw/` — não no vault
5. Sínteses geradas pelos agentes ficam em `vault/04-knowledge/`
6. Ao finalizar: `investments` → v1.7.0 e `knowledge-base` → v1.0.0

---

## PARTE 1 — ESTRUTURA DE PASTAS

Criar dentro de `/sbwaa/knowledge/`:

```
knowledge/
├── .chromadb/          ← banco de vetores (local, no .gitignore)
├── raw/                ← documentos brutos antes de indexar
│   ├── books/          ← PDFs de livros
│   ├── research/       ← equity research, relatórios de bancos
│   ├── gestoras/       ← cartas de gestoras BR
│   └── macro/          ← relatórios macro (BC, IBGE, FMI, etc.)
├── indexed/            ← log de documentos já indexados
│   └── index_log.json
└── sources/            ← configuração de fontes RSS/web
    └── sources.json
```

---

## PARTE 2 — INDEXADOR DE DOCUMENTOS

### Script: `knowledge/indexer.py`

**Função:** Processa e indexa documentos no ChromaDB local.
Aceita PDF, DOCX, TXT e markdown.

```python
"""
SBWAA — Knowledge Base Indexer
Indexa documentos locais no ChromaDB para RAG.

Uso:
  python knowledge/indexer.py --file caminho/para/documento.pdf
  python knowledge/indexer.py --pasta knowledge/raw/gestoras/
  python knowledge/indexer.py --status
"""
```

**O script deve:**

1. Aceitar um arquivo ou pasta como input
2. Para cada documento:
   - Detectar tipo (PDF, DOCX, TXT, MD)
   - Extrair texto com a biblioteca adequada:
     - PDF → `PyPDF2`
     - DOCX → `python-docx`
     - TXT/MD → leitura direta
   - Dividir em chunks de 500 tokens com overlap de 50 tokens
   - Gerar embeddings com `sentence-transformers`
     (modelo: `paraphrase-multilingual-MiniLM-L12-v2` — suporta PT-BR)
   - Salvar no ChromaDB com metadados:
     ```python
     metadata = {
         "fonte": "nome_do_arquivo",
         "tipo": "livro|research|gestora|macro|outro",
         "autor": "extraído ou 'desconhecido'",
         "ano": "extraído ou 'desconhecido'",
         "idioma": "pt|en",
         "chunk_id": N,
         "total_chunks": N
     }
     ```
3. Registrar documento indexado em `knowledge/indexed/index_log.json`
4. Nunca reindexar documento já presente no log (verificar hash MD5)
5. Exibir progresso: `[X/Y chunks] Indexando: nome_do_arquivo...`

**Configuração do ChromaDB:**
```python
import chromadb
from sentence_transformers import SentenceTransformer

# Modelo multilingual que funciona bem em português
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# ChromaDB local — nunca em servidor remoto
client = chromadb.PersistentClient(
    path="knowledge/.chromadb"
)
collection = client.get_or_create_collection(
    name="sbwaa_knowledge",
    metadata={"hnsw:space": "cosine"}
)
```

**Função de chunking:**
```python
def chunk_texto(texto: str, chunk_size: int = 500,
                overlap: int = 50) -> list[str]:
    """
    Divide texto em chunks com overlap para preservar contexto.
    chunk_size e overlap em palavras (aproximação de tokens).
    """
    palavras = texto.split()
    chunks = []
    i = 0
    while i < len(palavras):
        chunk = palavras[i:i + chunk_size]
        chunks.append(" ".join(chunk))
        i += chunk_size - overlap
    return chunks
```

---

## PARTE 3 — SISTEMA DE BUSCA (RETRIEVER)

### Script: `knowledge/retriever.py`

**Função:** Interface de busca no ChromaDB. Usado por todos os agentes
para recuperar contexto relevante antes de uma análise.

```python
"""
SBWAA — Knowledge Retriever
Interface de busca semântica na base de conhecimento.
Chamado pelos agentes para enriquecer análises com contexto.
"""

def buscar(query: str, n_resultados: int = 5,
           filtro_tipo: str = None) -> list[dict]:
    """
    Busca semântica na base de conhecimento.

    Args:
        query: pergunta ou contexto para buscar
        n_resultados: número de chunks a retornar
        filtro_tipo: filtrar por tipo (livro, research, gestora, macro)

    Returns:
        Lista de dicts com: texto, fonte, tipo, score de relevância
    """
    modelo = SentenceTransformer(EMBEDDING_MODEL)
    query_embedding = modelo.encode([query]).tolist()

    where = {"tipo": filtro_tipo} if filtro_tipo else None

    resultados = collection.query(
        query_embeddings=query_embedding,
        n_results=n_resultados,
        where=where
    )

    chunks = []
    for i, doc in enumerate(resultados["documents"][0]):
        chunks.append({
            "texto": doc,
            "fonte": resultados["metadatas"][0][i]["fonte"],
            "tipo": resultados["metadatas"][0][i]["tipo"],
            "score": 1 - resultados["distances"][0][i]  # cosine → similaridade
        })

    return sorted(chunks, key=lambda x: x["score"], reverse=True)


def formatar_contexto_para_agente(chunks: list[dict],
                                   max_tokens: int = 2000) -> str:
    """
    Formata os chunks recuperados em texto estruturado
    para inserir no prompt do agente.
    """
    if not chunks:
        return "Nenhum contexto relevante encontrado na base de conhecimento."

    linhas = ["## Contexto da Base de Conhecimento\n"]
    tokens_usados = 0

    for chunk in chunks:
        bloco = (
            f"**Fonte:** {chunk['fonte']} "
            f"(relevância: {chunk['score']:.0%})\n"
            f"{chunk['texto']}\n"
            f"---\n"
        )
        tokens_estimados = len(bloco.split()) * 1.3
        if tokens_usados + tokens_estimados > max_tokens:
            break
        linhas.append(bloco)
        tokens_usados += tokens_estimados

    return "\n".join(linhas)
```

---

## PARTE 4 — INTEGRAÇÃO COM OS AGENTES

### Atualizar cada SKILL.md para incluir seção de RAG

Adicionar ao final de cada `SKILL.md` dos agentes (Fases 2-5)
a seguinte seção padronizada:

```markdown
## BASE DE CONHECIMENTO (RAG)

Antes de iniciar a análise, o sistema recupera automaticamente
trechos relevantes da base de conhecimento local.

Quando contexto RAG for fornecido no prompt:
- Priorizar informações da base sobre seu conhecimento geral
- Citar a fonte ao usar uma informação da base:
  (Fonte: nome_do_documento)
- Se a base contradiz dados de mercado atuais, usar dados de mercado
  e registrar a contradição como observação
- Se a base não trouxer contexto relevante, prosseguir normalmente
```

### Atualizar `run_market_researcher.py` (Fase 2)

Adicionar chamada ao retriever antes de montar o prompt:

```python
from knowledge.retriever import buscar, formatar_contexto_para_agente

# Buscar contexto macro relevante
query_macro = f"cenário macroeconômico Brasil {setor_principal} {datetime.now().year}"
chunks_macro = buscar(query_macro, n_resultados=4, filtro_tipo="macro")
contexto_rag = formatar_contexto_para_agente(chunks_macro, max_tokens=1500)

# Inserir no prompt
contexto_do_dia = f"""
DATA: {hoje}
SNAPSHOT MACRO: {conteudo_snapshot}
SETORES: {lista_de_setores}
TICKERS: {lista_de_tickers}

{contexto_rag}
"""
```

### Atualizar `run_earnings_reviewer.py` (Fase 2)

```python
# Buscar contexto específico do setor e empresa
query_earnings = f"análise resultados {ticker} {setor} margem EBITDA receita"
chunks = buscar(query_earnings, n_resultados=3)
contexto_rag = formatar_contexto_para_agente(chunks, max_tokens=1000)
```

### Atualizar `run_model_builder.py` (Fase 3)

```python
# Buscar premissas e benchmarks de valuation do setor
query_dcf = f"DCF valuation {setor} WACC custo capital beta Brasil"
chunks = buscar(query_dcf, n_resultados=4, filtro_tipo="research")
contexto_rag = formatar_contexto_para_agente(chunks, max_tokens=1500)
```

### Atualizar `run_pm.py` (Fase 5)

```python
# Buscar contexto amplo: macro + setor + tese de investimento
query_pm = f"investimento {ticker} {setor} risco retorno portfólio"
chunks = buscar(query_pm, n_resultados=5)
contexto_rag = formatar_contexto_para_agente(chunks, max_tokens=2000)
```

---

## PARTE 5 — COLETOR DE FONTES LIVE (RSS)

### Script: `knowledge/rss_collector.py`

**Função:** Coleta artigos de fontes confiáveis via RSS, processa
e indexa automaticamente. Chamado pelo heartbeat diariamente.

**Arquivo de configuração** `/sbwaa/knowledge/sources/sources.json`:

```json
{
  "rss_feeds": [
    {
      "nome": "Valor Econômico",
      "url": "https://valor.globo.com/rss/financas",
      "tipo": "macro",
      "idioma": "pt",
      "ativo": true
    },
    {
      "nome": "InfoMoney",
      "url": "https://www.infomoney.com.br/feed/",
      "tipo": "macro",
      "idioma": "pt",
      "ativo": true
    },
    {
      "nome": "Banco Central — Notas de Política Monetária",
      "url": "https://www.bcb.gov.br/api/feed/sitebcb/noticias/pt-br",
      "tipo": "macro",
      "idioma": "pt",
      "ativo": true
    },
    {
      "nome": "Bloomberg Markets",
      "url": "https://feeds.bloomberg.com/markets/news.rss",
      "tipo": "macro",
      "idioma": "en",
      "ativo": true
    },
    {
      "nome": "Reuters Business",
      "url": "https://feeds.reuters.com/reuters/businessNews",
      "tipo": "macro",
      "idioma": "en",
      "ativo": true
    }
  ],
  "coleta_max_artigos_por_feed": 5,
  "coleta_max_idade_dias": 3
}
```

**O script deve:**
- Ler `sources.json`
- Para cada feed ativo: buscar os últimos N artigos (máx 5)
- Filtrar artigos com menos de 3 dias
- Verificar se já foi indexado (pelo URL como ID único)
- Extrair texto do artigo via `requests` + `BeautifulSoup`
- Indexar via `indexer.py`
- Registrar em `index_log.json`

---

## PARTE 6 — COMANDO `/knowledge`

Adicionar ao `sbwaa.py` o comando `/knowledge`:

```python
"/knowledge": "knowledge/knowledge_cmd.py",
```

### Script: `knowledge/knowledge_cmd.py`

**Subcomandos:**
```bash
python sbwaa.py /knowledge --status
# Exibe: total de documentos, total de chunks, tipos indexados

python sbwaa.py /knowledge --adicionar caminho/arquivo.pdf
# Indexa um novo documento

python sbwaa.py /knowledge --buscar "valuation petróleo Brasil"
# Busca semântica manual — útil para testar a base

python sbwaa.py /knowledge --listar
# Lista todos os documentos indexados com data e tipo

python sbwaa.py /knowledge --coletar-rss
# Força coleta RSS imediata (sem esperar heartbeat)
```

**Output de `/knowledge --status`:**
```
═══════════════════════════════════════════════
SBWAA — Knowledge Base | {DATA}
═══════════════════════════════════════════════
Total de documentos:  XX
Total de chunks:      X.XXX
─────────────────────────────────────────────
Por tipo:
  📚 Livros:          XX docs | XXX chunks
  📊 Research:        XX docs | XXX chunks
  📝 Gestoras:        XX docs | XXX chunks
  🌍 Macro/RSS:       XX docs | XXX chunks
─────────────────────────────────────────────
Modelo de embedding:  paraphrase-multilingual-MiniLM-L12-v2
Banco de vetores:     ChromaDB local
Última atualização:   {DATA} {HORA}
═══════════════════════════════════════════════
```

---

## PARTE 7 — SÍNTESES NO VAULT

Quando um agente usar contexto RAG em uma análise, criar nota de síntese
em `vault/04-knowledge/` se o conteúdo for relevante o suficiente:

**Script: `knowledge/save_synthesis.py`**

```python
def salvar_sintese(titulo: str, conteudo: str,
                   ticker: str = None, tipo: str = "geral"):
    """
    Salva síntese gerada a partir do RAG no vault/04-knowledge/.
    Cria wikilinks automáticos para o ativo se ticker fornecido.
    """
```

**Formato da nota de síntese:**
```markdown
---
tags: [knowledge, sintese, {tipo}]
cssclasses: [node-knowledge]
data: {DATA}
ticker: {ticker ou null}
fontes: [lista das fontes usadas]
---

# Síntese: {titulo}

{conteudo gerado pelo agente}

## Fontes Consultadas
- {fonte 1} (relevância: XX%)
- {fonte 2} (relevância: XX%)

## Links
- [[{ticker}/tese]] (se ticker presente)
- [[market-researcher-{DATA}]]
```

---

## PARTE 8 — DOCUMENTOS RECOMENDADOS PARA INDEXAR

Guia de prioridade para alimentar a base de conhecimento:

### Prioridade Alta — Indexar primeiro

**Livros (colocar PDFs em `knowledge/raw/books/`):**
- Security Analysis — Graham & Dodd
- The Intelligent Investor — Benjamin Graham
- Damodaran on Valuation — Aswath Damodaran
- Expected Returns — Antti Ilmanen
- Principles of Corporate Finance — Brealey, Myers, Allen

**Research BR (colocar em `knowledge/raw/research/`):**
- Relatórios de equity research: XP, BTG Pactual, Itaú BBA
- Relatório de Estabilidade Financeira — Banco Central
- Relatório de Inflação — Banco Central (trimestral)
- Boletim Focus — Banco Central (semanal)

**Cartas de gestoras (colocar em `knowledge/raw/gestoras/`):**
- Cartas mensais: Verde Asset, SPX Capital, Truxt, Absolute,
  Ibiuna, Legacy, Kinea, Giant Steps
- Relatórios anuais das gestoras acima

### Prioridade Média — Indexar em seguida

**Macro internacional:**
- IMF World Economic Outlook (anual)
- BIS Annual Economic Report
- Fed Minutes (trimestral)

**Relatórios setoriais:**
- Relatórios ANP (petróleo/gás)
- Relatórios ABEV, ANBIMA (fundos)
- Relatórios CVM relevantes

### Como adicionar um documento:

```bash
# Adicionar PDF de livro
python sbwaa.py /knowledge --adicionar knowledge/raw/books/security_analysis.pdf

# Adicionar pasta inteira de research
python sbwaa.py /knowledge --adicionar knowledge/raw/research/

# Verificar resultado
python sbwaa.py /knowledge --status
```

---

## PARTE 9 — INTEGRAÇÃO COM HEARTBEAT

Adicionar ao `scripts/heartbeat/heartbeat.py` (Fase 6):

```python
# Passo adicional no heartbeat: coletar RSS diariamente
from knowledge.rss_collector import coletar_todos_feeds

# Roda coleta RSS antes do morning-call
novos_artigos = coletar_todos_feeds()
if novos_artigos > 0:
    log(f"RSS: {novos_artigos} novos artigos indexados")
```

---

## PARTE 10 — VALIDAÇÃO FINAL

- [ ] ChromaDB instalado e pasta `.chromadb/` criada
- [ ] `sentence-transformers` instalado com modelo multilingual baixado
- [ ] `indexer.py` criado e testado com 1 documento PDF
- [ ] `retriever.py` criado — busca retornando resultados relevantes
- [ ] `index_log.json` sendo atualizado corretamente
- [ ] `rss_collector.py` criado e testado com ao menos 1 feed
- [ ] `sources.json` configurado com todos os feeds
- [ ] `knowledge_cmd.py` criado com todos os subcomandos
- [ ] `/knowledge --status` exibindo métricas corretas
- [ ] `/knowledge --buscar "..."` retornando resultados formatados
- [ ] Agentes atualizados com chamada ao retriever (Fases 2, 3, 5)
- [ ] `save_synthesis.py` criado — sínteses sendo salvas em vault
- [ ] Heartbeat atualizado para coletar RSS diariamente
- [ ] `.gitignore` atualizado (`.chromadb/`, `raw/`)
- [ ] `VERSION.md` atualizado: `investments` → v1.7.0,
      `knowledge-base` → v1.0.0
- [ ] `CHANGELOG.md` com entrada da Fase 7

Ao finalizar, confirme: **"SBWAA Fase 7 concluída — investments v1.7.0 | knowledge-base v1.0.0"**

---

## OBSERVAÇÕES IMPORTANTES

1. O download do modelo `paraphrase-multilingual-MiniLM-L12-v2` (~400MB)
   acontece automaticamente na primeira execução do indexer. Pode demorar
   dependendo da conexão — informar o usuário.

2. Livros com DRM (proteção) não podem ser extraídos por PyPDF2.
   Se um PDF retornar texto vazio, avisar: "PDF protegido — extraia
   o texto manualmente e salve como .txt"

3. O RAG não substitui os dados de mercado em tempo real — ele
   complementa com contexto histórico e teórico. Agentes devem sempre
   priorizar dados frescos da Brapi/Yahoo sobre o que está na base.

4. Chunks de 500 palavras com overlap de 50 é o padrão — funciona bem
   para documentos financeiros. Não alterar sem testar impacto na
   qualidade das buscas.

5. A coleta RSS respeita o `max_idade_dias` — artigos velhos não são
   reindexados para não poluir a base com conteúdo desatualizado.

6. Não criar interface visual ainda — isso é Fase 8 (última fase).
