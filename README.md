# MFC Studio

Laboratório digital de células a combustível microbianas. Montagem guiada em onze etapas, evidências rastreáveis e núcleo físico exploratório. Aplicação independente do METREV completo.

**Comece pelo [guia de engenharia, materiais e modelagem](docs/GUIA_MFC_STUDIO.md).** Ele reúne os documentos anteriores em uma leitura explicativa: funcionamento da célula, onze etapas, materiais, equações, exemplos, dados e calibração. Os registros originais de auditoria ficam em anexos recolhíveis no mesmo guia.

**Estado v0.2:** núcleo mecanístico não calibrado; nenhum preditor treinado nem erro experimental externo demonstrado. Defaults são hipóteses de engenharia, não valores de literatura aprendidos.

## Aplicação

- Landing `/` e Studio autenticado `/studio` separados.
- SVG selecionável, onze etapas em ordem fixa e painel científico minimizável.
- Curvas, perdas, sensibilidade determinística e balanços de batelada.
- Cenários privados versionados no D1 por identidade ChatGPT; execuções registradas com hash e versão.
- Base `/evidence`: artigos completos, suplemento, condições, observações e pendências nas onze etapas.
- Sem chat, agente, MCP ou simulação espacial no aplicativo.

O núcleo resolve monocâmara sem membrana, acetato, consórcio misto, ar ambiente, batelada, pH 7 e 25 °C. Configurações restantes podem ser registradas e salvas, mas retornam previsão indisponível. Os parâmetros padrão aguardam calibração experimental.

## Corpus

Corpus 0.4.0: 29 fontes indexadas de tipos distintos (inclui documentação da plataforma e nove fontes comerciais), seis artigos completos CC BY 4.0 e dois suplementos, 206 registros, 423 observações numéricas e quatro células ausentes, além de 13 pontos de uma curva digitalizada. São 16 variantes comerciais, 46 propriedades e 31 ofertas datadas. Preços, caracterização e resultados experimentais têm escopos separados. **Zero registros aprovados para treinamento.** As 110 propriedades do catálogo não equivalem a propriedades já modeladas.

Documentos originais, autores, DOIs, licenças, hashes e localizadores em `research/corpus-v0.2/`. Redistribuição dos documentos segue a licença individual CC BY; não se aplica uma licença de código aos artigos. A curva S18 mantém a base de área pendente e não é convertida silenciosamente em corrente absoluta.

A rodada 0.4.0 integra oito atribuições revisadas às etapas e a recuperação de S02 em cópia integral hospedada pelos autores. Os fatos revisados em `research/corpus-v0.4/` acrescentam 26 valores publicados e quatro derivados. A cópia integral S02 não foi redistribuída no repositório por ausência de licença aberta identificada. As seis cópias integrais CC BY e os dois suplementos publicados permanecem os mesmos. Os dois novos coeficientes descrevem entrada de O₂ em líquido agitado e não são parâmetros de ORR do kernel.

O incremento em `research/corpus-v0.3/` acrescenta S29 com 115 pares publicados por reator (pico/tempo), mantendo dois pares ausentes e a mesma família conservadora de S18. `research/materials-v0.1/` separa material/variante, caracterização, oferta e vínculo experimental. Fabricantes sem licença de redistribuição têm fatos e proveniência preservados, sem cópia integral pública. A [seção de curadoria do guia](docs/GUIA_MFC_STUDIO.md#dados) explica decisões, normalização e admissões ainda bloqueadas.

O catálogo único reúne **7.599 publicações deduplicadas**, das quais **185** têm leitura integral dos métodos documentada e **45** têm um controle admitido em F1–F6. [Catálogo de literatura](research/conventional-arms/catalog/) · [Conferência dos cinco percentuais](docs/GUIA_MFC_STUDIO.md#meta-cobertura)

## Desenvolvimento

Node >=22.13 e pnpm. `pnpm install --frozen-lockfile`, `pnpm run check`, `pnpm test`, `pnpm run build`. Migrações geradas em `drizzle/` são somente esquema. D1/R2 são declarados em `.openai/hosting.json` e provisionados pelo ChatGPT Sites.

`python3 scripts/build-corpus.py` gera o seed determinístico dos arquivos preservados. `/api/seed` aplica o corpus imutável de modo idempotente; `/api/corpus-assets/:id` aceita apenas os bytes exatos de PDFs conhecidos, por SHA-256. Esses endpoints compartilham corpus público licenciado e dependem do acesso privado do Site; cenários e execuções exigem identidade em toda operação. PDFs completos ficam em R2; textos completos e metadados ficam em D1. Seed e backfill não estão nas migrações.

Antes de gerar o corpus, `python3 scripts/build-materials.py`, `python3 scripts/build-s02.py` e `python3 scripts/audit-s29.py` regeneram os produtos de curadoria. `python3 -m unittest discover -s tests -p 'test_*.py'` verifica conversões, restrições de admissão e alinhamento dos dados. Não há transferência automática de nome comercial, BET, ASR, preço ou ensaio PEMFC para cinética de MFC.

O adaptador de autenticação é o nativo do Sites. Nunca configure OAuth independente ou confie em um identificador de usuário enviado no corpo da requisição. `/qa` é exclusivamente desenvolvimento e retorna 404 na produção.

## Ciência, verificação e continuidade

- [Guia único](docs/GUIA_MFC_STUDIO.md): explicação de engenharia, equações, exemplos, estado científico, histórico, inventários e auditorias originais.
- `research/corpus-v0.2/RESEARCH_STATUS.md`: inspeção dos artigos, conflitos e admissões pendentes.
- `science/validation.mjs`: agrupamento transitivo de estudos/reatores/famílias e métricas sem erros perfeitos fabricados.

As rotinas `seed-hosted-corpus.py` e `verify-database.py` atualizam seus blocos de auditoria no guia por meio de `scripts/document_audits.py`. Os relatórios continuam legíveis por máquina nos blocos JSON, sem recriar documentos separados em `docs`.

`python3 scripts/audit-conventional-arms.py --check` verifica a triagem, a origem dos braços e as contagens por estudo e linhagem. O levantamento fica na camada bibliográfica de pesquisa.

A integração 0.4.0 usa comparação com o registro anterior para aplicar revisões de escopo. Edições divergentes interrompem a aplicação e permanecem preservadas. `node scripts/audit-corpus.mjs` confere a integridade e a cobertura; `node scripts/review-stage-coverage.mjs` confere as atribuições revisadas. O preenchimento e `/api/seed` verificam o conteúdo completo das linhas, os trechos de texto e os hashes dos arquivos. `python3 scripts/acquire-s02.py <diretório-privado-fora-do-repositório>` reproduz a aquisição com verificação de versão; a transcrição dos fatos foi manual, conferida nas páginas, e está explicitamente identificada como tal.
