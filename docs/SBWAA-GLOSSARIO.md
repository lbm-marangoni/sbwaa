# SBWAA — Glossário de Termos e Siglas

> Referência para leitura dos outputs do sistema, relatórios e documentação.
> Organizado por tema. Termos do sistema SBWAA estão marcados com ⚙️.

**Versão: v2.10.3**

---

## Sistema SBWAA ⚙️

| Termo | Significado |
|-------|-------------|
| **SBWAA** | Second Brain Wealth + Asset + Assessor Individual — nome do sistema |
| **Pipeline** | Sequência ordenada de análises executadas pelos agentes. Ex: Market Researcher → Earnings → DCF → Valuation → Quant → Econometrician → Risk → PM |
| **Agente** | Módulo de IA com função especializada dentro do pipeline (ver seção Agentes abaixo) |
| **Vault** | Repositório de arquivos `.md` gerenciado pelo Obsidian — onde ficam análises, decisões e relatórios |
| **Wikilink** | Referência cruzada entre notas no formato `[[nome-do-arquivo]]` — padrão Obsidian |
| **Cache** | Arquivo JSON gerado pelos scripts após buscar dados, evitando chamadas repetidas à mesma API no mesmo dia |
| **TTL** | Time-to-Live — tempo de validade de um cache antes de ser buscado novamente (padrão: 4 horas) |
| **RAG** | Retrieval-Augmented Generation — técnica em que o agente busca trechos relevantes da base de conhecimento local antes de responder |
| **ChromaDB** | Banco de dados vetorial local que armazena e recupera documentos para o RAG |
| **IPS** | Investment Policy Statement — documento que define perfil de risco, limites e alocação alvo do investidor |
| **Carteira** | Posições que o investidor **possui** — com quantidade, custo médio e P&L registrados |
| **Watchlist** | Ativos **analisados mas não comprados** — aguardando gatilho de entrada ou melhor timing |
| **Circuit Breaker** | Limite automático do IPS que dispara alerta quando VaR, drawdown ou concentração ultrapassam o máximo tolerado |
| **Regra dos 60 dias** | Análise com mais de 60 dias é considerada defasada — usar `/analisar` em vez de `/pm` para recalibrar |
| **Sizing** | Tamanho sugerido da posição em % do portfólio ou em R$ |
| **Veredicto** | Decisão final do PM: COMPRAR, AGUARDAR, EVITAR (ativo novo) ou AUMENTAR, MANTER, REDUZIR, SAIR (posição existente) |

---

## Agentes do Pipeline ⚙️

| Agente | Função |
|--------|--------|
| **Market Researcher** | Analisa o contexto macro do dia e o posicionamento setorial do ativo |
| **Earnings Reviewer** | Revisa os resultados trimestrais — receita, margens, DPA, surpresas vs estimativa |
| **Model Builder** | Constrói o modelo de valuation — DCF para ações, Gordon para FIIs |
| **Valuation Reviewer** | Critica o DCF, triangula com múltiplos e emite veredicto: BARATO / JUSTO / CARO |
| **Quant / Data Engineer** | Calcula métricas quantitativas da carteira — Sharpe, volatilidade, beta, correlações |
| **Econometrician** | Modelos avançados: GARCH, beta dinâmico, Fama-French, sensibilidade macro, drawdown avançado |
| **Risk Engineer** | Calcula VaR, CVaR, stress tests e verifica circuit breakers do IPS |
| **Portfolio Manager (PM)** | Agente final — sintetiza tudo, confronta com o portfólio real e emite o veredicto de investimento |

---

## Mercado Financeiro Brasileiro

| Sigla / Termo | Significado |
|---------------|-------------|
| **IBOV / Ibovespa** | Índice Bovespa — principal índice de ações da bolsa brasileira (B3). Referência de benchmark |
| **CDI** | Certificado de Depósito Interbancário — taxa de referência para renda fixa no Brasil, próxima à Selic |
| **Selic** | Taxa básica de juros da economia brasileira, definida pelo COPOM |
| **COPOM** | Comitê de Política Monetária do Banco Central do Brasil — define a Selic a cada 45 dias |
| **BCB** | Banco Central do Brasil |
| **IPCA** | Índice de Preços ao Consumidor Amplo — inflação oficial do Brasil, medida pelo IBGE |
| **IBC-Br** | Índice de Atividade Econômica do Banco Central — proxy mensal do PIB brasileiro |
| **NTN-B** | Nota do Tesouro Nacional série B — título público indexado ao IPCA. A NTN-B 10a (10 anos) é usada como taxa de desconto base para FIIs |
| **B3** | Brasil, Bolsa, Balcão — bolsa de valores brasileira onde ações, FIIs e ETFs são negociados |
| **BDR** | Brazilian Depositary Receipt — recibo de ativo estrangeiro negociado na B3 |
| **CRI** | Certificado de Recebíveis Imobiliários — renda fixa lastreada em créditos imobiliários |
| **CRA** | Certificado de Recebíveis do Agronegócio — renda fixa lastreada em créditos do agronegócio |
| **Debênture** | Título de dívida emitido por empresas — renda fixa privada |
| **Tesouro Direto (TD)** | Programa de compra de títulos públicos federais diretamente pelo investidor |

---

## Tipos de Ativo

| Label SBWAA | Tipo |
|-------------|------|
| 🟦 AÇÃO ON | Ação Ordinária — dá direito a voto na empresa |
| 🟦 AÇÃO PN | Ação Preferencial — prioridade no recebimento de dividendos |
| 🟩 FII | Fundo de Investimento Imobiliário — fundo que investe em imóveis ou títulos imobiliários |
| 🟨 ETF BR | Exchange-Traded Fund brasileiro — fundo negociado em bolsa que replica um índice nacional |
| 🟥 ETF INTL | ETF internacional — fundo negociado na B3 que replica índices estrangeiros (S&P 500, Nasdaq etc.) |
| ⬜ RF | Renda Fixa — CDB, LCI, LCA, poupança e similares |
| 🟪 TD | Tesouro Direto — títulos públicos federais |
| 🟫 DEB | Debênture |
| 🟧 CRI/CRA | Certificados de recebíveis |

**Tipos de FII:**
| Termo | Significado |
|-------|-------------|
| **FII de Tijolo** | Fundo que investe diretamente em imóveis físicos (shoppings, galpões, lajes, hotéis) |
| **FII de Papel** | Fundo que investe em títulos imobiliários (CRI, LCI) — renda atrelada a índices (CDI, IPCA) |
| **FII Híbrido** | Combinação de tijolo e papel |
| **FOF** | Fund of Funds — FII que investe em cotas de outros FIIs |

---

## Indicadores Fundamentalistas

| Sigla / Termo | Fórmula / Significado |
|---------------|----------------------|
| **P/L** | Preço dividido pelo Lucro Por Ação (LPA) — quantas vezes o mercado paga pelo lucro anual. Quanto menor, mais barato |
| **P/VP** | Preço dividido pelo Valor Patrimonial por Ação/Cota (VPA) — se < 1, ativo cota abaixo do patrimônio líquido |
| **EV/EBITDA** | Enterprise Value dividido pelo EBITDA — múltiplo de valuation que ignora estrutura de capital e impostos |
| **P/FFO** | Preço dividido pelo FFO por cota — múltiplo específico de FIIs, equivale ao P/L para empresas |
| **DY** | Dividend Yield — dividendos pagos nos últimos 12 meses dividido pela cotação atual, em % |
| **LPA** | Lucro Por Ação — lucro líquido dividido pelo número de ações |
| **VPA** | Valor Patrimonial por Ação/Cota — patrimônio líquido dividido pelo número de ações/cotas |
| **DPA** | Dividendo Por Ação/Cota — valor pago por cota em cada distribuição |
| **DPA anualizado** | Soma dos DPAs dos últimos 12 meses — base para calcular o DY real e o preço teto Bazin |
| **ROE** | Return on Equity — lucro líquido dividido pelo patrimônio líquido, em %. Mede eficiência no uso do capital |
| **EBITDA** | Earnings Before Interest, Taxes, Depreciation and Amortization — lucro operacional antes de juros, impostos, depreciação e amortização |
| **FFO** | Funds from Operations — resultado operacional do FII ajustado para depreciações contábeis. Equivale ao "lucro real" do fundo |
| **FCL / FCF** | Fluxo de Caixa Livre (Free Cash Flow) — caixa gerado após investimentos necessários para manter o negócio |
| **Payout** | Percentual do lucro distribuído como dividendo |
| **EV** | Enterprise Value — valor total da empresa (Market Cap + dívida líquida) |

---

## Valuation e Modelos

| Termo | Significado |
|-------|-------------|
| **DCF** | Discounted Cash Flow — modelo que projeta fluxos de caixa futuros e os traz a valor presente usando uma taxa de desconto |
| **WACC** | Weighted Average Cost of Capital — custo médio ponderado de capital, usado como taxa de desconto no DCF |
| **Taxa g** | Taxa de crescimento na perpetuidade — crescimento esperado do fluxo de caixa para sempre após o período de projeção |
| **Cenário base** | Premissas mais prováveis do modelo — WACC e g normais |
| **Cenário pessimista** | WACC +2% e g -1% vs o base — mede margem de segurança real do valuation |
| **Cenário otimista** | WACC -2% e g +1% vs o base |
| **Upside** | Potencial de valorização em % — (preço justo - cotação atual) / cotação atual |
| **Downside** | Potencial de queda em % — quando cotação atual > preço justo |
| **Margem de Segurança** | Desconto da cotação atual em relação ao valor justo. Margem de 15% = comprar R$ 100 por R$ 85 |
| **Gordon Growth Model** | Modelo de valuation para FIIs: Valor Justo = DPA anualizado / (taxa de desconto − g) |
| **Preço Teto Graham** | Fórmula de Benjamin Graham para ações: √(22,5 × LPA × VPA) — nível máximo a pagar |
| **Preço Teto Bazin** | Para FIIs: DPA anualizado / 0,08 — cotação máxima para um DY mínimo de 8% |
| **Preço Chão Bazin** | DPA anualizado / 0,12 — cotação abaixo da qual o DY implícito > 12% (zona de compra forte) |
| **Cap Rate** | Capitalization Rate — receita operacional líquida do imóvel dividida pelo valor de mercado. Equivale ao yield do imóvel físico |
| **Vacância** | Percentual da área de um FII que está desocupada — vacância alta pressiona receita e DPA |
| **ABL** | Área Bruta Locável — metragem total disponível para locação num FII |
| **Yield on Cost** | DY calculado sobre o preço médio de compra — retorno real sobre o capital investido, independente da cotação atual |

---

## Risco e Métricas Quantitativas

| Sigla / Termo | Significado |
|---------------|-------------|
| **VaR** | Value at Risk — perda máxima esperada num dia com um dado nível de confiança. Ex: VaR 95% = perda que só é superada em 5% dos dias |
| **CVaR** | Conditional Value at Risk (também chamado Expected Shortfall) — perda média nos piores dias além do VaR. Mais conservador que o VaR |
| **Drawdown** | Queda da cotação/portfólio desde o último pico histórico, em %. Drawdown atual = quanto está abaixo do máximo recente |
| **Max Drawdown** | Maior queda histórica registrada entre um pico e o vale seguinte |
| **Calmar Ratio** | Retorno anual dividido pelo Max Drawdown — mede o retorno obtido por unidade de risco de queda. Calmar ≥ 1,0 é saudável |
| **Ulcer Index** | Mede a profundidade e duração dos drawdowns — quanto tempo o ativo fica "embaixo do pico" |
| **Pain Index** | Média ponderada dos drawdowns ao longo do tempo — similar ao Ulcer mas com peso uniforme |
| **Sharpe Ratio** | (Retorno do portfólio − taxa livre de risco) / volatilidade — mede retorno por unidade de risco total. Quanto maior, melhor |
| **Beta** | Sensibilidade do ativo à variação do mercado (IBOV). Beta 1,5 = ativo sobe/cai 1,5× o mercado. Beta < 1 = menos volátil |
| **Beta dinâmico** | Beta recalculado em janelas de tempo diferentes (60, 126, 252 dias) para detectar mudanças recentes de sensibilidade |
| **Alpha** | Retorno acima do esperado pelo modelo de risco — geração de valor além do beta de mercado |
| **Volatilidade** | Desvio padrão dos retornos, anualizado em %. Mede dispersão dos resultados |
| **Correlação** | Medida de quanto dois ativos se movem juntos — varia de -1 (oposto) a +1 (idêntico). 0 = sem relação |
| **Correlação rolling** | Correlação calculada em janela móvel (ex: 60 dias) para detectar mudanças de comportamento ao longo do tempo |
| **HHI** | Herfindahl-Hirschman Index — medida de concentração do portfólio. HHI alto = portfólio concentrado em poucos ativos |
| **Nº Ativos Efetivos** | 1 / HHI — número equivalente de ativos igualmente diversificados que produziriam a mesma concentração |
| **Fronteira Eficiente** | Conjunto de portfólios que maximizam retorno esperado para cada nível de risco — base da teoria de Markowitz |

---

## Econometria e Modelos Avançados

| Sigla / Termo | Significado |
|---------------|-------------|
| **GARCH** | Generalized Autoregressive Conditional Heteroskedasticity — modelo que estima volatilidade variável no tempo. Detecta períodos de alta e baixa volatilidade |
| **Regime GARCH** | Classificação do momento atual de volatilidade: BAIXA (estável), MÉDIA ou ALTA (choques persistentes) |
| **Persistência de choque** | No GARCH, mede quanto tempo um choque de volatilidade demora para se dissipar. Persistência próxima a 1 = choque dura muito |
| **Half-life** | Tempo para o efeito de um choque de volatilidade cair pela metade — derivado do modelo GARCH |
| **Fama-French 3 Fatores** | Modelo que explica retornos por: 1) mercado (beta), 2) tamanho (SMB) e 3) valor (HML) |
| **SMB** | Small Minus Big — fator de tamanho no modelo Fama-French. Premia ações de empresas menores |
| **HML** | High Minus Low — fator de valor no Fama-French. Premia ações com P/VP baixo (valor) vs alto (crescimento) |
| **Sensibilidade macro** | Impacto estimado no retorno do ativo para cada variação de 1% em Selic, IPCA, BRL/USD e IBC-Br |
| **Stress test** | Simulação de como o portfólio se comportaria em cenários históricos extremos (Crise 2008, COVID 2020, Eleições 2022) |

---

## Indicadores Macro Globais

| Sigla / Termo | Significado |
|---------------|-------------|
| **S&P 500** | Índice das 500 maiores empresas dos EUA — principal referência de mercado americano |
| **Nasdaq** | Índice das empresas de tecnologia listadas na bolsa Nasdaq (EUA) |
| **DXY** | Dollar Index — mede a força do dólar americano contra uma cesta de moedas (EUR, JPY, GBP, CAD, SEK, CHF) |
| **BRL/USD** | Taxa de câmbio real brasileiro por dólar americano |
| **Juros EUA 10Y** | Rendimento do título do Tesouro americano de 10 anos — referência global de "taxa livre de risco" e custo de capital |
| **WTI** | West Texas Intermediate — referência de preço do petróleo americano (em US$ por barril) |
| **Brent** | Referência de preço do petróleo do Mar do Norte — mais usada globalmente que o WTI |
| **Ouro (XAU/USD)** | Preço do ouro em dólares por onça troy — ativo de proteção (hedge) em momentos de incerteza |

---

## Termos Operacionais

| Sigla / Termo | Significado |
|---------------|-------------|
| **Ex-date** | Data em que o investidor precisa ser titular do ativo para ter direito ao próximo dividendo/provento. Comprar após essa data não dá direito ao dividendo do período |
| **QoQ** | Quarter over Quarter — variação em relação ao trimestre imediatamente anterior |
| **YoY** | Year over Year — variação em relação ao mesmo período do ano anterior |
| **YTD** | Year to Date — variação desde o início do ano até hoje |
| **Guidance** | Projeção ou meta divulgada pela própria empresa para receita, EBITDA ou lucro de períodos futuros |
| **Consenso** | Média dos price targets e recomendações de analistas de sell-side que cobrem o ativo |
| **Price target** | Preço alvo estimado por analistas de mercado para os próximos 12 meses |
| **Spread** | Diferença entre duas taxas ou preços. Ex: spread do FII sobre a NTN-B = DY do FII − taxa do título público |
| **Rebalanceamento** | Ajuste das posições para reconduzi-las às alocações alvo definidas no IPS |
| **Concentração** | Peso de um único ativo no portfólio total, em % |
| **Contribuição ao risco** | Quanto da volatilidade total do portfólio é explicada por um ativo específico |
| **P&L** | Profit & Loss — lucro ou prejuízo de uma posição. P&L realizado = posição vendida. P&L latente = posição ainda aberta |
| **ADTV** | Average Daily Trading Volume — volume médio diário negociado. Indica liquidez do ativo |
| **Liquidez diária** | Volume financeiro médio negociado por dia em R$ — quanto menor, mais difícil entrar e sair sem impactar o preço |

---

## Conceitos de Investimento

| Termo | Significado |
|-------|-------------|
| **Tese de investimento** | Conjunto de razões que justificam comprar e manter um ativo — o "por quê" da posição |
| **Trigger / Gatilho** | Evento ou condição que, quando atingida, leva à ação: entrar, sair ou aumentar uma posição |
| **Stop** | Preço ou condição que invalida a tese — ponto a partir do qual a posição deve ser encerrada |
| **Renda passiva** | Dividendos, aluguéis ou juros recebidos sem necessidade de vender o ativo — base da estratégia de FIIs |
| **Acumulação** | Fase em que o investidor aporta regularmente para aumentar o patrimônio — oposta à fase de uso (saque) |
| **Independência financeira** | Estado em que a renda passiva do portfólio cobre as despesas sem necessidade de trabalho ativo |
| **Benchmark** | Referência de comparação de performance. Os mais comuns no contexto BR: IBOV (ações), CDI (renda fixa) |
| **Diversificação** | Estratégia de distribuir capital entre ativos com baixa correlação para reduzir risco sem sacrificar retorno |
| **Magic Number (FII)** | Número de cotas necessárias para que os dividendos paguem uma nova cota a cada ciclo — efeito bola de neve |
| **FIRE** | Financial Independence, Retire Early — movimento que busca independência financeira antecipada via acumulação agressiva |
