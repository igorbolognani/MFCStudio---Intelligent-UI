# MFC Studio

Laboratório digital de células a combustível microbianas. Montagem guiada em onze etapas, evidências rastreáveis e núcleo físico exploratório. Aplicação independente do METREV completo.

**Estado v0.2:** núcleo mecanístico não calibrado; nenhum preditor treinado nem erro experimental externo demonstrado. Defaults são hipóteses de engenharia, não valores de literatura aprendidos.

## Aplicação

- Landing `/` e Studio autenticado `/studio` separados.
- SVG selecionável, onze etapas em ordem fixa e painel científico minimizável.
- Curvas, perdas, sensibilidade determinística e balanços de batelada.
- Cenários privados versionados no D1 por identidade ChatGPT; execuções registradas com hash e versão.
- Base `/evidence`: artigos completos, suplemento, condições, observações e pendências nas onze etapas.
- Sem chat, agente, MCP ou simulação espacial no aplicativo.

O núcleo resolve monocâmara sem membrana, acetato, consórcio misto, ar ambiente, batelada, pH 7 e 25 °C. Configurações restantes podem ser registradas e salvas, mas retornam previsão indisponível. A família experimental S18 é um candidato distinto; parâmetros padrão não foram calibrados nesse estudo.

## Corpus

Corpus 0.3.0: 29 fontes indexadas de tipos distintos (inclui documentação da plataforma e nove fontes comerciais), seis artigos completos CC BY 4.0 e dois suplementos, 198 registros, 393 observações numéricas e quatro células ausentes, além de 13 pontos de uma curva digitalizada. São 16 variantes comerciais, 46 propriedades e 31 ofertas datadas. Preços, caracterização e resultados experimentais têm escopos separados. **Zero registros aprovados para treinamento.** As 110 propriedades do catálogo não equivalem a propriedades já modeladas.

Documentos originais, autores, DOIs, licenças, hashes e localizadores em `research/corpus-v0.2/`. Redistribuição dos documentos segue a licença individual CC BY; não se aplica uma licença de código aos artigos. A curva S18 mantém a base de área pendente e não é convertida silenciosamente em corrente absoluta.

O incremento em `research/corpus-v0.3/` acrescenta S29 com 115 pares publicados por reator (pico/tempo), mantendo dois pares ausentes e a mesma família conservadora de S18. `research/materials-v0.1/` separa material/variante, caracterização, oferta e vínculo experimental. Fabricantes sem licença de redistribuição têm fatos e proveniência preservados, sem cópia integral pública. `docs/DATA_CURATION_2026-10-26.md` registra decisões, normalização, onze etapas e admissões ainda bloqueadas.

## Desenvolvimento

Node >=22.13 e pnpm. `pnpm install --frozen-lockfile`, `pnpm run check`, `pnpm test`, `pnpm run build`. Migrações geradas em `drizzle/` são somente esquema. D1/R2 são declarados em `.openai/hosting.json` e provisionados pelo ChatGPT Sites.

`python3 scripts/build-corpus.py` gera o seed determinístico dos arquivos preservados. `/api/seed` aplica o corpus imutável de modo idempotente; `/api/corpus-assets/:id` aceita apenas os bytes exatos de PDFs conhecidos, por SHA-256. Esses endpoints compartilham corpus público licenciado e dependem do acesso privado do Site; cenários e execuções exigem identidade em toda operação. PDFs completos ficam em R2; textos completos e metadados ficam em D1. Seed e backfill não estão nas migrações.

Antes de gerar o corpus, `python3 scripts/build-materials.py` e `python3 scripts/audit-s29.py` regeneram os produtos de curadoria. `python3 -m unittest discover -s tests -p 'test_*.py'` verifica conversões, restrições de admissão e alinhamento dos dados. Não há transferência automática de nome comercial, BET, ASR, preço ou ensaio PEMFC para cinética de MFC.

O adaptador de autenticação é o nativo do Sites. Nunca configure OAuth independente ou confie em um identificador de usuário enviado no corpo da requisição. `/qa` é exclusivamente desenvolvimento e retorna 404 na produção.

## Ciência, verificação e continuidade

- `docs/CONTEXT_RECONCILIATION.md`: fatos, inferências, lacunas e limites da recuperação.
- `docs/context-inventory.json`: inventário e hashes dos originais.
- `docs/MODEL_V02.md`: equações e domínio do núcleo.
- `docs/verification.json`: conservação e convergência; não é validação preditiva.
- `research/corpus-v0.2/RESEARCH_STATUS.md`: inspeção dos artigos, conflitos e admissões pendentes.
- `science/validation.mjs`: agrupamento transitivo de estudos/reatores/famílias e métricas sem erros perfeitos fabricados.

Próximo trabalho científico: resolver área/condições S18, recuperar réplicas e curvas comparáveis, identificar parâmetros separadamente e obter família externa intocada. Só então medir MAE/RMSE, cobertura de intervalos e generalização. Não ajustar todos os coeficientes numa curva e declarar aprendizado dos onze componentes.
