# MFC Studio — recuperação científica e seeding v0.2

Data de consulta: 2026-10-25. Este incremento acrescenta documentos completos e extrações auditáveis. Não declara preditor treinado nem erro externo demonstrado.

## Fatos verificados

- Catálogo anterior: 110 propriedades propostas em 11 etapas; 16 fontes de tipos mistos; 7 registros candidatos. Os arquivos anteriores de metadados/código/contratos foram consultados, com JSONs integralmente analisados. Nenhum desses sete candidatos foi promovido automaticamente.
- Índice v0.2: 19 fontes. Cinco artigos possuem texto completo e PDF recuperados do editor: S08, S09, S17, S18, S19. As licenças CC BY 4.0 foram conferidas nas declarações de copyright dos artigos. Todas as versões locais têm hashes no manifesto. A numeração preserva S01–S16.
- Novas extrações: 24 registros e 75 observações numéricas. São caracterização, contexto de métodos e resultados de célula/componente, com escopos e localizadores separados. `training_eligible:false` em todos eles: revisão não equivale a admissão em um dataset de uma tarefa específica.
- Suplemento S18: link `https://www.mdpi.com/article/10.3390/en17143574/s1` devolveu ZIP com `energies-3078330-supplementary.pdf` (6 páginas). Texto das legendas extraído e página3 inspecionada visualmente. Contém figuras S1–S10 e médias/erros; não contém CSV de reatores individuais.
- S18 Figura4: imagem lossless incorporada ao PDF extraída por `pdfimages`. `digitize_s18.py` reproduz a digitalização de 13 pontos da curva CC com cátodo fresco. CSV e JSON preservam pixels, eixos e limites de leitura. São dados digitalizados, não séries brutas; não há interpolação de pontos faltantes. Todos os pontos pertencem a uma família de origem.
- S09 foi publicado em 21/01/2025 apesar do DOI/volume conterem 2024. A correção de metadados está explicitada no índice.

## Inferência e proposta de família inicial

A família mais bem documentada deste incremento é a MFC monocâmara de 30 mL do estudo S18 (Salvian et al., 2024): acetato em meio mínimo, ânodo de feltro de carbono, cátodo a ar com Pt/C em tecido/papel, 1 kΩ durante os ciclos, temperatura21±2°C, quatro réplicas biológicas por braço mais controle estéril e três alimentações por concentração em cada reator.

Essa escolha é uma proposta de engenharia baseada em acessibilidade/métodos/replicação, não prova de superioridade universal. Não há membrana separada descrita nos métodos; tratar sua ausência como hipótese explícita da família, preservando o contrato para CEM/AEM/separador. O lado do ar e a etapa do meio catódico não criam outro volume líquido. A etapa do catalisador anódico permanece no guia e identifica ausência de catalisador artificial reportado.

Primeiro trabalho sustentável: reprodução de curva em densidade e fechamento elétrico, acoplados a inventário de acetato, disponibilidade de O2 e consumo não eletrogênico declarados. Uma curva não identifica de modo único cinética, transporte, competição microbiana e perdas de ambos os eletrodos. Não ajustar todos esses coeficientes à mesma curva e alegar que foram aprendidos. Parâmetros ainda não observados devem permanecer assumidos ou indisponíveis.

S17 fornece caracterização BET, RRDE, materiais e resultado de célula com membrana em urina; S19 fornece balanços e competição por nitrato/alteração de topologia. Esses domínios devem permanecer separados do acetato/O2 de S18. S08 é um modelo dinâmico de outra família, com cátodo assumido não limitante e componentes desprezados; S09 é previsão temporal de solo-MFC que usa históricos medidos. Simulação, previsão temporal e experimentos completos não são amostras intercambiáveis.

## Lacunas e conflitos preservados

1. **Base de área S18:** ânodo descrito como2×3cm, ou6cm² de projeção por face; pares365µA/304mA m⁻² e130µA/108mA m⁻² implicam normalização de aproximadamente12cm². Duas faces molhadas são uma hipótese plausível, mas o texto usa “área geométrica projetada”. `area_m2:null` na curva; não converterj→I silenciosamente.
2. **CE S18:** texto3.2 troca os valores entre braços e contradiz o ranking. FiguraS5 mostra CC azul com CE maior que CP laranja. Nenhum valor de CE foi admitido como alvo nesse seed. Registrar uma eventual correção como derivada/revisada com ambas as fontes.
3. **Unidades S18:** legendaS2 diz0,6mg/L e métodos dizem0,6g/L. Há outros erros de unidades no texto. O método é preservado e o conflito sinalizado.
4. **Caracterização seca/molhada:** espessuraCL medida por SEM após fixação/desidratação/secagem não é espessura hidratada em operação. BET de pó não é ECSA ou área geométrica. CargasPt usam área do cátodo, não a base de normalização do ânodo.
5. **Polarização S18:** LSV0,5mV/s após3h OCP; curvasCP apresentam trecho não monotônico/histerese. Replicação específica das curvas não é explicitada; quatro reatores no biossensor não autorizam criar erro de réplica para cada ponto digitalizado.
6. **S17:** mesmos reatores recebem primeiroMPL e depoisAC; tratamento está confundido com ordem/idade. HRT reportado37min difere de6,25mL/9,52mLh≈39,4min. Equação7 de resistividade publicada requer revisão dimensional; não foi copiada para um solver.
7. **Referências de potencial:** Ag/AgCl3M KCl e3,5M KCl aparecem em protocolos distintosS18. Não converter aSHE sem temperatura/composição e convenção adequadas. S17RRDE/LSV de componente não representa potência deMFC.
8. **Generalização:** há três novos estudos experimentais com famílias diferentes; não há par treinamento/holdout compatível pronto para demonstrar predição de novas configurações. Manter estudo, reator, braço e curvas relacionadas no mesmo grupo de origem. Não separar pontos de uma curva entre treino e teste para alegar generalização.
9. **Incerteza:** limites da digitalização≈±15,7mV e±1,75mA/m² representam somente leitura de raster. Não são intervalo preditivo ou variância biológica.
10. **Dados originais:** não foram recuperadas séries individuais de réplicas deS18. Dados deS09 estão vinculados a repositório de código e armazenamentoHuggingFace; StanfordZIP≈1,47GB/UCSCZIP≈4,7MB. Licença específica de dados não exposta na página de arquivos; nenhumZIP foi redistribuído. S10Mendeley possuiCC BY4 mas recuperação de arquivos ainda não concluída.
11. **Acesso:** S01Wiley403 ao baixar bytes nesta execução, apesar de trechos disponíveis na busca; não há documento completo localS01. S03KAUST devolveu challengeHTML212bytes comHTTP200; foi rejeitado e removido, não contado comoPDF. S03ACS temAuthorChoice não comercial; nenhum fulltext foi redistribuído. Esses bloqueios não significam que os documentos não existam.
12. **Escopo de leitura:** textos completos foram recuperados dos cinco artigos; S08/S17/S18 tiveram corpo principal consultado, S09/S19 tiveram métodos/resultados/licença consultados. Não afirmo inspeção manual de todas as imagens, referências ou linhas dos cinco artigos. Manifesto distingue recuperação de texto e prontidão experimental.

## Inventário para integração

| Arquivo/pasta | Conteúdo |
|---|---|
| `index_sources.json` | 19 fontes e estado atual de acesso/direitos |
| `documents_manifest.json` | Artefatos CC BY com SHA256,tamanho,DOI,URL e papel |
| `fulltext/*.txt` e `*.txt.gz` | 5 textos completos com atribuição, prontos para chunking/indexação |
| `documents/*.pdf` | 5 PDFs completos dos editores |
| `documents/S18_supplement.zip` | Suplemento original completo |
| `documents/S18_supplement/` | PDF extraído doZIP |
| `observations.json` / `.jsonl` | 24 novos registros/75 observações; nenhum automaticamente aprovado para treino |
| `stage_evidence_map.json` | Mapa simultâneo das11etapas, aplicação/gaps/IDs |
| `S18_CC_curve_digitized.*` | Curva digitalizada com bounds/proveniência/área pendente |
| `digitize_s18.py` | Reprodução da digitalização por amostragem de pixels |
| `retrievals.json` | Downloads e falhas de acesso/conteúdo |
| `test_research.py` | 8 testes de integridade/proveniência, sem reivindicação preditiva |

## Próximas admissões necessárias

Resolver área deS18; digitalização cruzada independente das curvas e figurasS4/S5; obter valores de réplicas/métodosbrutos dos autores ou dataset licenciado. Caracterizar separadamente O2crossover, condutividade hidratada, pH/tampão e cinética deambos eletrodos. Conseguir pelo menos uma segunda família experimental comparável para holdout intacto. Medir erroMAE/RMSE em unidades físicas, conservação/carga/massa, cobertura deintervalos e limites dodomínio antes de dizer “baixoerro”.
