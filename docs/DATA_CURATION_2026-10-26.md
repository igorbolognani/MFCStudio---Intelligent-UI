# Aquisição e tratamento — materiais comerciais e dados por reator

## Decisões e escopo

Igor confirmou em 26/10/2026: selecionar materiais comerciais; trabalhar com literatura e fichas técnicas; priorizar custo e disponibilidade. O incremento aprofunda o corpus, o tratamento e a admissão de dados da aplicação existente. Não acrescenta telas, configurações, novas topologias ou relações constitutivas ao solver.

## Fatos encontrados

- Nove fontes comerciais primárias: fabricante do suporte W1S1011, fabricante do GDE Pt/C, listagem H23C6, fabricante Toray, pack Toray, fichas SGL GDL/feltro, ofertas Redox Flow e fabricante CMI/CXM.
- Dezesseis variantes distintas, 46 observações de propriedades e 31 ofertas de 26/10/2026. As 29 ofertas com opção e preço exatos permanecem diferentes de duas chamadas “a partir de”. Há 30 normalizações possíveis por área bruta comprada, uma delas apenas como limite mínimo anunciado; nenhuma é orçamento entregue confirmado.
- Quarenta e quatro propriedades têm conversão dimensional admitida. Duas conversões estão bloqueadas: a unidade impressa do H23C6 é dimensionalmente ambígua e a carga nominal do GDE comercial não explicita inequivocamente massa de Pt versus Pt/C. Nos artigos S18/S29, a carga está explicitamente em mgPt/cm². S19 também tem base Pt/PtC pendente, preservada como qualificação vinculada ao registro original.
- O suporte GDL W1S1011, o GDE completo Pt/C e o H23C6 com revestimento preparado pelos autores são entidades diferentes. Igualdade de grade ou formulação nominal não prova igualdade do lote histórico nem do eletrodo final.
- S29, Salvian et al., npj Clean Water 7:53 (2024), DOI 10.1038/s41545-024-00350-5, acrescenta artigo integral de 12 páginas e suplemento de 13 páginas, CC BY 4.0. Tabelas 1/2: 39 linhas de alimentação × três reatores = 117 registros, dos quais 115 pares corrente máxima/tempo medidos e dois pares ausentes por falha de equipamento. São 230 respostas numéricas, não 230 experimentos.

## Inferências explícitas

S18/S29 foram agrupados conservadoramente na família `Salvian2024-Surrey-30mL`: compartilham laboratório, enriquecimento, construção e histórico compatível. A identidade dos reatores individuais entre os artigos não foi comprovada. Não usar um como holdout independente do outro. A ligação entre GDE atual e artigos é nominal; o SKU/lote final não consta dos artigos.

O anúncio Redox Flow contém `5.0x.5.0cm`. A interpretação 5×5 cm foi revisada contra a descrição do mesmo produto; o texto original e a revisão ficam juntos. Ofertas de folhas, packs e cortes não são escaladas como se o vendedor cobrasse um preço linear por área.

## Tratamento implementado

`science/material_data.py` separa normalização SI, inversão de resistividade direcional, admissão para parâmetro e avaliação comercial. Limites `<`/`>` são preservados, inclusive com inversão da desigualdade em σ=1/ρ. ASR não vira resistividade, BET não vira ECSA e Gurley/Darcy não vira coeficiente efetivo de transporte de O₂. Valores típicos, nominais e tolerâncias mantêm seu papel original.

A admissão exige revisão explícita, variante, estado, direção, método, condições e geometria compatíveis. Nenhuma observação desta coleta passou a preencher automaticamente um parâmetro do kernel. Condutividades dimensionalmente derivadas continuam não calibradas. O preço por área usa a área comprada, não área ativa instalada; frete, IVA, importação, câmbio e perdas de corte desconhecidos ficam nulos.

`scripts/build-materials.py` gera a curadoria determinística e os registros que entram nas tabelas existentes de fontes, evidências e observações. `scripts/audit-s29.py` confere todos os pares contra as linhas tabuladas, registra faltantes e produz faixas/medianas descritivas separadas por meio. A ordem da tabela não vira timestamp. DBO é calculada pelos autores a partir da DQO; não é nova medição independente em cada linha.

O corpus 0.3.0 contém 29 fontes de tipos distintos, seis artigos completos e dois suplementos, 198 registros e 397 células de observação: 393 numéricas e quatro ausentes. Parte dos números é comercial ou de caracterização. Nenhum registro aprovado para treino, preditor treinado ou erro experimental externo demonstrado. As 110 propriedades propostas e as equações do kernel permanecem como antes.

## Onze etapas integradas

O plano de aquisição em `research/materials-v0.1/catalog.json` mantém as onze etapas na ordem fechada. Materiais de eletrodos/camadas são aprofundados junto com geometria, meios, enriquecimento, carga, alimentação e condições do lado do ar. O Nafion do revestimento não cria membrana separadora. Câmara/medio catódicos a ar não criam segundo reservatório líquido. Etapa de catalisador anódico identifica ausência reportada, sem inventar carga.

Continuam pendentes fichas comerciais suficientemente específicas para corpo/selos/coletores e reagentes, preços entregues e caracterizações hidratadas pareadas. O plano não afirma que todas as propriedades das onze etapas já foram medidas ou resolvidas.

## Lacunas para modelagem e calibração

S29 não calibra diretamente o kernel atual: usa SWW/RWW, substituição de meio e pH 7,4; o kernel é acetato/batelada/pH 7/25 °C. Temperatura operacional de S29 não foi explicitada. A área numérica de normalização continua sem resolução, assim como em S18; não converter densidade em corrente absoluta. Picos e tempos de resposta não substituem séries de corrente/DQO pareadas.

Não há variação controlada dos materiais nas 117 linhas nem nova família externa independente. O próximo incremento científico deve procurar comparações comerciais de montagem equivalente, caracterização em condições relevantes e curvas/replicações que permitam identificar parâmetros e reservar estudos inteiros. Não ajustar coeficientes de material a estes números para fabricar uma calibração.

## Inventário e limites de acesso

Novos artefatos licenciados e hashes em `research/corpus-v0.3/documents_manifest.json`; fichas/URLs/retrievals e fatos estruturados em `research/materials-v0.1/`. S29 foi recuperado integralmente em bytes/texto; métodos e tabelas de interesse foram inspecionados. As figuras e a análise microbiômica completa não foram reextraídas nem declaradas integralmente revisadas. Os dois PDFs completos e os textos são publicados na base existente.

Downloads brutos dos dois PDFs SGL deram HTTP 504; texto e páginas renderizadas foram acessíveis pela busca. A abertura web do HTML Nature sofreu redirecionamento bloqueado, mas HTML/PDF/suplemento foram recuperados por download e conferidos. O endereço curto de Nafion na loja redirecionou a uma categoria e foi rejeitado como ficha do produto. Suplemento S19, preços atuais de Pt/AC e catálogo atual Phychemi não foram recuperados nesta rodada. Documentos completos de fabricantes não têm redistribuição liberada; foram usados apenas para inspeção, com fatos, links e hashes preservados. O acesso às conversas anteriores permanece limitado aos trechos e resumos já inventariados.

Scripts de ingestão e testes não constituem validação preditiva. Histórico, IDs, PDFs originais CC BY, faltantes e bases ambíguas foram preservados.
