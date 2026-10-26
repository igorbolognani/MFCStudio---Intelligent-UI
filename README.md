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

19 fontes indexadas (inclui documentação da plataforma), cinco artigos completos CC BY 4.0 e um suplemento, 32 registros de evidência, 86 observações e 13 pontos de uma curva digitalizada. **Zero registros aprovados para treinamento.** As 110 propriedades do catálogo não equivalem a propriedades já modeladas.

Documentos originais, autores, DOIs, licenças, hashes e localizadores em `research/corpus-v0.2/`. Redistribuição dos documentos segue a licença individual CC BY; não se aplica uma licença de código aos artigos. A curva S18 mantém a base de área pendente e não é convertida silenciosamente em corrente absoluta.

## Desenvolvimento

Node >=22.13 e pnpm. `pnpm install --frozen-lockfile`, `pnpm run check`, `pnpm test`, `pnpm run build`. Migrações geradas em `drizzle/` são somente esquema. D1/R2 são declarados em `.openai/hosting.json` e provisionados pelo ChatGPT Sites.

`python3 scripts/build-corpus.py` gera o seed determinístico dos arquivos preservados. `/api/seed` aplica o corpus imutável de modo idempotente; `/api/corpus-assets/:id` aceita apenas os bytes exatos de PDFs conhecidos, por SHA-256. Esses endpoints compartilham corpus público licenciado e dependem do acesso privado do Site; cenários e execuções exigem identidade em toda operação. PDFs completos ficam em R2; textos completos e metadados ficam em D1. Seed e backfill não estão nas migrações.

O adaptador de autenticação é o nativo do Sites. Nunca configure OAuth independente ou confie em um identificador de usuário enviado no corpo da requisição. `/qa` é exclusivamente desenvolvimento e retorna 404 na produção.

## Ciência, verificação e continuidade

- `docs/CONTEXT_RECONCILIATION.md`: fatos, inferências, lacunas e limites da recuperação.
- `docs/context-inventory.json`: inventário e hashes dos originais.
- `docs/MODEL_V02.md`: equações e domínio do núcleo.
- `docs/verification.json`: conservação e convergência; não é validação preditiva.
- `research/corpus-v0.2/RESEARCH_STATUS.md`: inspeção dos artigos, conflitos e admissões pendentes.
- `science/validation.mjs`: agrupamento transitivo de estudos/reatores/famílias e métricas sem erros perfeitos fabricados.

Próximo trabalho científico: resolver área/condições S18, recuperar réplicas e curvas comparáveis, identificar parâmetros separadamente e obter família externa intocada. Só então medir MAE/RMSE, cobertura de intervalos e generalização. Não ajustar todos os coeficientes numa curva e declarar aprendizado dos onze componentes.
