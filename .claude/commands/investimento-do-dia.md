---
description: Sugestão de 1-2 ativos para explorar análise hoje, com base no IPS e no cenário macro. Categoria opcional: fii, acao, etf, rf, td
---

# /investimento-do-dia $ARGUMENTS

## Detecção de categoria

Verifique `$ARGUMENTS`:
- **Vazio** → sugerir qualquer tipo de ativo (comportamento padrão)
- **Valor presente** → restringir sugestões ao tipo correspondente:

| Argumento | Restringe para |
|-----------|---------------|
| `fii` | Fundos Imobiliários (🟩 FII) |
| `acao` | Ações ON e PN (🟦 AÇÃO ON / 🟦 AÇÃO PN) |
| `etf` | ETFs brasileiros e internacionais (🟨 ETF BR / 🟥 ETF INTL) |
| `etf-br` | Somente ETFs brasileiros (🟨 ETF BR) |
| `etf-intl` | Somente ETFs internacionais (🟥 ETF INTL) |
| `rf` | Renda Fixa e CRI/CRA (⬜ RF / 🟧 CRI/CRA) |
| `td` | Tesouro Direto (🟪 TD) |

Se `$ARGUMENTS` não corresponder a nenhuma categoria acima, ignorar e usar comportamento padrão.

---

## Passo 1 — Coletar contexto

```powershell
$env:PYTHONUTF8 = "1"; cd "C:\Users\lbmma\Downloads\Local\SBWAA"
python scripts/data/fetch_yahoo.py --macro
```

Leia:
- Todos os `scripts/data/cache/yahoo_*.json` do dia
- `vault/00-portfolio/ips.md`
- `vault/00-portfolio/carteira.md`

## Passo 2 — Sugestão

Leia `.claude/agents/market-researcher/SKILL.md`.

Com base no cenário macro do dia e no perfil do IPS, sugira **1 ou 2 ativos** para explorar análise — não é recomendação de compra, é uma indicação de onde vale a pena gastar atenção hoje.

Para cada sugestão:
- **Ticker** e tipo (🟦 AÇÃO / 🟩 FII / 🟥 ETF INTL etc.)
- **Setor**
- **Por que hoje** — 2 linhas conectando o cenário macro à oportunidade
- **Pré-condição** — o que você precisaria ver nos dados para considerar a entrada

Termine com:
> Execute `/tese TICKER` para análise rápida ou `/analisar TICKER` para pipeline completo.

Não salva arquivo — resposta direta no chat.
