# MFC Studio — base científica e contrato do produto v0.1

Data: 16 de outubro de 2026. Estado: pesquisa inicial estruturada e infraestrutura de dados; preditor não treinado; solver acoplado não implementado; Site não publicado neste incremento.

## 1. Objetivo e decisões consolidadas

Explorar quantitativamente configurações MFC que podem não ter sido testadas na literatura, ajudando a selecionar hipóteses para ensaios físicos. A previsão deve resultar da combinação de constituição física, dados de caracterização, condições de operação e parâmetros calibrados. O objetivo de baixo erro é um critério a demonstrar por validação independente, nunca uma propriedade presumida por haver muitos artigos.

O produto será independente do METREV completo. A experiência escolhida é montagem guiada: SVG dominante, onze etapas destacadas, física/equações/legendas/resultados concentrados em um painel expansível. Landing page explicativa e simulador são páginas distintas. Login pelo ChatGPT protege o simulador e cenários pertencem a cada usuário. Não há chat, agente ou plugin MCP no produto solicitado.

Ordem obrigatória: câmara anódica; meio anódico; ânodo; catalisador anódico; biofilme; membrana; circuito e alimentação/coleta; câmara catódica; meio catódico; cátodo; catalisador catódico.

## 2. Fatos, proposta e lacunas

**Fatos recuperados:** a base HTML v0.5 contém um surrogate 0D, controles de onze componentes, curvas e cenários em memória. Diversos atributos são descritivos; o seletor nominal de material não identifica uma curva constitutiva. O HTML original e sua cópia anexada são idênticos. Os oito arquivos da pasta foram lidos na etapa anterior desta conversa, inclusive os quatro previews. A preferência pela montagem guiada foi confirmada pelo usuário.

**Proposta de engenharia:** motor híbrido mecanístico e estatístico; descritores dos materiais ajudam a estimar relações constitutivas e parâmetros locais, e um solver calcula os estados acoplados. Estatística também representa variação entre estudos e incerteza. Esta proposta é nossa síntese, não um sistema já validado por um dos artigos.

**Lacunas atuais:** faltam curvas brutas, caracterização cruzada suficiente, modelos selecionados com parâmetros identificáveis e conjunto externo de validação. Os dezesseis registros de fontes incluem candidatos ainda não lidos integralmente, duas páginas de datasets e uma documentação oficial. Isso não constitui um corpus de dezesseis estudos integralmente extraídos. As sete linhas de evidências são resumos candidatos, não sete experimentos completos e independentes.

## 3. Por que valores estáticos por material são inadequados

S01 relaciona propriedades de três materiais SiOC a resposta de bioânodos em BES de três eletrodos, sob potencial imposto. Seu valor para este projeto é associar caracterização e condições; corrente de bioânodo nesse ensaio não é potência disponível em uma MFC completa. BET, área geométrica e área eletroquímica precisam permanecer distintos. As três linhas extraídas preservam essa separação.

S02 fornece um contraste de topologia: para glicose, a retirada da PEM aumenta a potência máxima reportada de 262 para 494 mW/m², enquanto a faixa de recuperação coulômbica diminui de 40–55% para 9–12%. Os resultados sustentam considerar efeitos concorrentes, mas não autorizam multiplicar a potência de toda célula sem membrana por uma razão fixa. As condições completas e a base exata de área ainda devem ser recuperadas.

S03 usa inclinações EPS e mostra dependência das resistências dos eletrodos em relação ao meio. Inclinação de polarização, resistência de transferência obtida por EIS e resistência puramente ôhmica não são intercambiáveis. S06 mostra que espécies iônicas além de H+ participam do transporte pela membrana e podem alterar o pH catódico. S07 motiva registrar composição e envelhecimento do catalisador separadamente.

## 4. O que será aprendido e o que será resolvido

O corpus não será uma tabela de receitas e respectivas potências. Ele deverá conter quatro tipos de evidência: caracterização do material; ensaio eletroquímico de componente; operação da célula completa; dinâmica e envelhecimento. Simulações publicadas ficam em uma classe própria. Modelos estatísticos poderão usar dados sintéticos para treinamento auxiliar quando justificado, mas a validação externa continuará experimental e separada.

Uma primeira formulação abstrata é:

`p(theta | descritores, condições, topologia, dados)`

`F(x, dx/dt, I, theta, configuração) = 0`

`y = H(x, I, configuração)`

`theta` contém parâmetros de transporte, reações, crescimento e perdas. `x` contém estados como concentrações, biomassa, pH e inventário gasoso. `I` é a corrente. `y` contém observáveis declarados: tensão, potência, carga, remoção e eficiência.

Aprender parâmetros fisicamente interpretáveis costuma ser um ponto de partida mais auditável do que prever diretamente a potência de qualquer combinação. Isso não exclui modelos diretos como comparação. A escolha entre regressão hierárquica, processo gaussiano, ensemble ou outra abordagem será feita após avaliar cobertura, dependência entre entradas e tamanho efetivo do conjunto. Não há justificativa atual para escolher uma rede profunda por padrão.

Um ajuste de resíduos pode ser avaliado se reduzir o erro externo sem violar balanços, sinais, unidades ou limites. Não se deve permitir que ele esconda um processo físico ausente.

## 5. Topologia: variáveis independentes

O número de câmaras não determina sozinho a condição catódica. O contrato separa:

- Uma ou duas câmaras.
- Cátodo em líquido, ar ambiente ou gás em volume controlado.
- Membrana CEM, AEM, separador ou ausência.
- Batelada, alimentação periódica ou operação contínua.
- Carga elétrica resistiva, e posteriormente coleta/armazenamento explicitamente modelados.

Em uma câmara com cátodo imerso, o líquido pode ser compartilhado. Não se cria um segundo volume independente apenas para preencher a etapa “meio catódico”. Em cátodo exposto ao ar, a etapa continua no guia, identificando que um católito independente não se aplica. Uma membrana ausente elimina o domínio correspondente e altera os caminhos iônicos e de crossover; não se limita a tornar sua resistência zero.

Gás em headspace fechado exige inventário de oxigênio e balanço de gás. Ar ambiente corresponde a uma condição de contorno diferente. Compor duas câmaras gráficas não pode implicar reservatórios infinitos de reagentes. A alimentação nesta MFC significa alimentação do meio/substrato; tensão externa de eletrólise mudaria o escopo energético.

## 6. Catálogo inicial por etapa

O arquivo `parameter_catalog.json` contém 110 campos propostos, com identificador, símbolo e unidade. Todos estão marcados como **planejados e ainda não conectados a um preditor**. A contagem não mede maturidade e a interface inicial não precisa mostrar todos de uma vez.

| Etapa | Famílias de propriedades | Relações físicas a identificar | Observáveis afetados |
|---|---|---|---|
| Câmara anódica | Volumes líquido/gás, geometria, mistura, percurso e seção iônica, vazão, parede | Balanços, distribuição de tempos de residência, transporte e entrada de O2 | Concentrações, corrente, recuperação de elétrons |
| Meio anódico | Substrato identificado, DQO/fração biodegradável, tampão, pH, condutividade, íons, nutrientes, inibidores | Cinética, especiação ácido-base, condução, competição microbiana | Tensão, remoção, crescimento, carga |
| Ânodo | Áreas distintas, condutividade direcional, contato, poros, tortuosidade, molhabilidade, química superficial, capacitância | Condução, colonização, acessibilidade, transferência de massa | Corrente, perdas, tempo de resposta |
| Catalisador anódico | Composição, carga, cobertura, ligante, espessura, estabilidade | Transferência de elétrons e adesão; contribuição eletrônica separada | Ativação, colonização, estabilidade |
| Biofilme | Biomassa ativa, fração eletroativa, idade, espessura hidratada, crescimento, consumo, difusão e condução | Reação-transporte, limitação por substrato/potencial, competição | Corrente, consumo, eficiência, evolução temporal |
| Membrana | Tipo, área, espessura hidratada, ASR/condutividade, água, IEC/carga fixa, seletividade e crossover | Transporte iônico, espécies, pH, difusão de O2/substrato | Perdas, pH, recuperação de elétrons |
| Circuito e alimentação/coleta | Carga/contatos, regime de alimentação, eventos, coletor, armazenamento, consumos auxiliares | Fechamento elétrico, balanço de alimentação, energia útil | Ponto de operação, energia líquida, dinâmica |
| Câmara catódica | Volume líquido/gasoso, pressão, composição, renovação, temperatura, umidade | Disponibilidade e reposição de reagentes | Limitação por O2, água, estabilidade |
| Meio catódico | O2 dissolvido, aceptor, pH, tampão, condutividade e transferência gás-líquido | Reação catódica, especiação, transporte | Potencial catódico, perdas, limitação |
| Cátodo | Área, condução, camada difusora, porosidade, tortuosidade e saturação de água | Transporte de elétrons/O2, inundação e secagem | Corrente limite, tensão, durabilidade |
| Catalisador catódico | Composição, carga, ECSA, cinética, via ORR/peróxido, ligante e idade | Cinética e seletividade da reação, desativação | Ativação, consumo de O2, potência |

Cada campo também precisa de método de medição, estado seco/molhado, direção de medição, incerteza e condições de validade. Uma distribuição de poros não deve ser reduzida a um diâmetro sem convenção. DQO não determina uma concentração molar de acetato sem composição e conversão justificadas. Parâmetros ausentes são `null`, nunca zero.

## 7. Núcleo de equações candidato

As equações abaixo organizam a implementação futura. Não estão implementadas como solver neste pacote. Cada uma terá testes de unidades, condições, convenções e limites. Não se somarão duas descrições do mesmo efeito.

### Fechamento eletroquímico

`V = E_c,eq - E_a,eq - eta_a - eta_c - I*R_ohm - outras_perdas_declaradas`

`V = I*R_ext` para carga resistiva. `P = I*V` e `E_el = integral(P dt)`.

O mesmo termo de transporte não pode ser incluído ao mesmo tempo como sobrepotencial, resistência EPS e correção aprendida. Eletrodos com cinética efetiva ajustada por polarização não recebem outra Rct em série sem identificação separada.

### Condução

`R_e = L_e/(sigma_e*A_e)`; seção eletrônica `A_e` e área de interface não são necessariamente iguais.

`R_sol = L_sol/(kappa_sol*A_ion)` na aproximação unidimensional de percurso uniforme. Em geometria complexa, o fator geométrico precisa ser calculado ou calibrado. `R_mem = ASR_mem/A_mem` **ou** `L_mem/(kappa_mem*A_mem)`; não somar as duas formas.

### Reação e biologia

Uma relação de Monod pode representar a dependência do consumo em relação ao substrato, condicionada ao consórcio e ao regime. Dependência de potencial pode seguir uma formulação Nernst–Monod apropriada ao mecanismo. Butler–Volmer ou uma relação efetiva catódica exigem referência de potencial, base de área e validade experimental. Não se misturam parâmetros de eletrodo metálico abiótico e bioânodo sem verificar o modelo.

### Balanço do substrato

`d(V*S)/dt = Q_in*S_in - Q_out*S - V*r_e - V*r_comp`

As taxas devem usar a mesma base química de S. Crescimento, manutenção, decaimento e retenção de biomassa são processos separados. A corrente precisa ser consistente com os elétrons transferidos pela taxa eletrogênica. Substrato consumido por rotas concorrentes não pode reaparecer como corrente útil.

### Oxigênio e água

`d(V*C_O2)/dt = kLa*V*(C_star-C_O2) - I/(n_ORR*F) - consumo_adicional - crossover`

Essa forma só vale para os termos e domínios declarados. A condição de gás finito requer equação adicional para os mols de O2 no gás e relação de equilíbrio apropriada. Seletividade ORR altera `n_ORR`. Um cátodo a ar precisa de disponibilidade de O2 e saturação/água próprias.

### DQO, carga e energia

Quando DQO estiver expressa em **gramas equivalentes de O2**, a carga teórica da DQO removida é `Q_COD = F*Delta_m_COD/8`, em coulombs. A divisão por 8 usa 8 g O2 por mol de elétrons equivalentes. Eficiência coulômbica é `CE = integral(I dt)/Q_COD`. Em sistemas com inventário prévio, cross-feeding ou outras entradas, o balanço precisa explicar o denominador; valores experimentais aparentes acima de 100% são sinalizados, não cortados silenciosamente.

Energia líquida deve descontar aeração, bombeamento e eletrônica quando tais componentes existirem. Energia bruta da célula e energia após o coletor são observáveis diferentes.

## 8. Legenda científica e rastreabilidade

| Símbolo | Significado | Unidade |
|---|---|---|
| I | Corrente elétrica | A |
| V | Tensão terminal | V |
| E_c,eq / E_a,eq | Potenciais de equilíbrio das semirreações | V, com referência declarada |
| E0 / OCV | Símbolos a distinguir: potencial padrão de reação e tensão em circuito aberto não são sinônimos automáticos | V |
| eta_a / eta_c | Sobrepotenciais anódico e catódico | V |
| R_ext / R_ohm / R_mem | Resistências externa, ôhmica interna e de membrana | Ω |
| ASR_mem | Resistência específica de área da membrana | Ω·m² |
| sigma_e / kappa_sol | Condutividades eletrônica e iônica | S/m |
| A_e / A_ion / A_mem | Seções/áreas associadas a cada caminho | m² |
| S / C_O2 | Concentração de substrato identificado / oxigênio | mol/m³ |
| r_e / r_comp | Taxas volumétricas eletrogênica e concorrente | mol/(m³·s), na base de S |
| Q_in / Q_out | Vazões de entrada/saída | m³/s |
| kLa | Coeficiente volumétrico de transferência | s⁻¹ |
| F | Constante de Faraday, 96485.33212 nesta convenção numérica | C/mol de elétrons |
| n_ORR | Número de elétrons por molécula de O2 para a via considerada | adimensional |
| P / E_el | Potência / energia elétrica | W / J |

O painel relacionará cada símbolo com nome, unidade, valor atual, origem e papel (entrada, estado ou saída). Expandir uma equação mostrará substituição numérica, hipóteses, referências e resíduos do fechamento quando disponíveis. A explicação conceitual de um fenômeno terá identificação diferente de uma equação efetivamente resolvida.

## 9. Estrutura e admissão das evidências

Registrar estudo, fonte original, grupo de experimentos, reator, réplica, ciclo, tempo, protocolo, tratamento do material, condições e normalização. DOI de dataset e DOI de artigo não representam necessariamente experimentos independentes. A identidade de grupo deve reunir republicações e derivados do mesmo ensaio.

Separar medido, derivado de medição, ajustado, simulado e assumido. Toda observação preserva unidade original, localização e transformação; correções permanecem auditáveis. As sete linhas do seed são demonstração dessa estrutura e ficam como candidatas.

Não transformar resumos, picos de potência ou pontos digitalizados de uma única curva em amostras independentes de “novos materiais”. Não treinar uma previsão de potência usando como entrada a corrente observada na mesma condição e depois alegar capacidade de prever uma célula ainda não construída. Histórico medido é uma entrada legítima para previsão temporal, mas define outra tarefa.

O código `evidence.py` verifica metadados essenciais, algumas relações semânticas, conversões e separação por famílias de origem. Ele **não é um schema científico completo nem certifica a elegibilidade final para um dataset específico**. Revisão de métodos, condições, estrutura de variância e definição da tarefa continuam necessárias.

## 10. Validação que corresponde à pergunta do usuário

Dividir curvas e observações por reator/estudo/família original antes de pré-processar. Ajustar imputação, transformação, seleção e hiperparâmetros só dentro do conjunto de treinamento. Usar validação interna agrupada e um conjunto externo intocado.

Avaliações distintas: novo ponto no reator conhecido; novo reator da mesma família; nova combinação de materiais conhecidos; novo material; nova topologia; nova escala. Desempenho de uma dessas tarefas não comprova as demais.

S09 é um exemplo de mudança de regime: erros baixos na previsão temporal de solo-MFC não se mantiveram quando modelos treinados em operação estabelecida foram aplicados à incubação. Esse estudo ilustra a necessidade de avaliar domínios separadamente; não fornece um modelo direto para o Studio.

Medir MAE/RMSE em unidades físicas, erro de curvas, erro em potência máxima, localização do máximo, energia integrada e remoção quando houver dados. MAPE exige tratamento explícito perto de zero; R² sozinho é insuficiente. Para intervalos, verificar cobertura e largura em grupos externos. A faixa mostrada ao usuário só será chamada calibrada depois dessa verificação.

Testes físicos: fechamento de corrente/carga/massa, sinais e limites, caso em circuito aberto, carga extrema, ausência de substrato, limitação catódica, conservação entre volumes e consistência das unidades. Sensibilidade e identificabilidade ajudam a evitar ajustar vários coeficientes que produzem a mesma curva. A camada precisa poder retornar previsão indisponível quando falta informação essencial.

## 11. Prever uma configuração nova

Uma nova combinação de componentes já caracterizados pode ser abordada por montagem de relações locais e solução do conjunto. Ela continua a exigir avaliação de interações e incerteza. Um material totalmente novo e sem descritores suficientes não recebe precisão apenas por pertencer à família “carbono”.

Os resultados terão domínio de aplicabilidade associado: suporte experimental próximo; combinação nova dentro de famílias representadas; extrapolação; ou informação insuficiente. Distâncias estatísticas isoladas não provam validade física. A detecção deve combinar descritores, topologia, condições e mecanismos presentes.

Para descoberta, comparar cenários com incertezas correlacionadas, buscar combinações promissoras e selecionar experimentos que reduzam ambiguidade entre hipóteses. Não é necessário declarar um “ótimo” quando várias configurações são indistinguíveis dentro do erro. O produto pode reduzir o espaço de testes sem substituir a confirmação experimental.

## 12. Experiência do Site

**Landing:** apresentação do propósito; diagrama e explicação dos onze componentes em sequência; exemplos de relações físicas; capacidades e maturidade; acesso ao Studio. O conteúdo diferencia experiência prevista, observação experimental e hipótese.

**Studio:** cabeçalho com início, cenários e sair; etapas maiores com navegação anterior/próxima e seleção direta; SVG amplo; editor contextual; painel científico único com equações, glossário, hipóteses, evidências, resultados, balanços e diagnósticos em seções expansíveis; tabelas e gráficos interativos de resultados abaixo ou em área própria.

A seleção usa contorno/halo separado do preenchimento material e identificação textual. Componentes finos terão alvos de toque maiores, sem esconder camadas vizinhas. Ordem e visibilidade seguem a topologia. O desenho permanece esquemático até existir correspondência geométrica explicitamente modelada.

Popup flutuante não deve esconder entradas ou prender o foco. No desktop, painel acoplável/minimizável; em tela estreita, painel abaixo do SVG. Componente ativo, foco de teclado e resultado alterado são estados distintos.

Gráficos: eixos/unidades legíveis, legenda, ponto operacional, valores sob interação e bandas quando justificadas. Tabelas: resumo compacto e expansão para unidades, fontes e condições. “Voltar” preserva o cenário, “fechar painel” fecha só a inspeção e “sair” encerra a sessão. Persistência deve ocorrer no servidor, separada do estado temporário de navegação.

A documentação oficial S15 descreve landing pública, autenticação ChatGPT e autorização de registros no servidor. O caminho de publicação e a configuração do público serão implementados quando avançarmos para o Site; não foi necessária uma conexão MCP para esse objetivo.

## 13. Incrementos com entregas verificáveis

1. **Base atual:** contrato das onze etapas; catálogo; fontes com limites de acesso; seed rastreável; compilador de topologia e verificações de admissão. Entregue neste pacote.
2. **Corpus de calibração:** recuperar métodos/suplementos/dados; extrair curvas e réplicas; definir tarefas; completar descritores e grupos; separar validação externa. Não concluído.
3. **Núcleo físico:** escolher uma família inicial demonstrável; implementar fechamento eletroquímico, substrato/biomassa, O2 e caminhos iônicos compatíveis; calibrar e testar balanços. Não concluído.
4. **Transferência entre configurações:** relacionar descritores a parâmetros com efeito entre estudos; avaliar novas combinações/topologias em grupos externos; calibrar intervalos. Não concluído.
5. **Studio persistente:** landing, autenticação, SVG/guias/painel, cenários e gráficos; publicação via Sites. A interface pode ser desenvolvida antes da validação universal, mas só exibirá a capacidade numérica realmente implementada.

O primeiro domínio científico não precisa ser o único domínio configurável do produto: a topologia completa pode existir no contrato, enquanto a cobertura numérica avança com evidência. Isso permite crescimento real sem simular validação de todas as combinações.

## 14. Conteúdo do pacote e verificação

- `sources.json`: dezesseis registros, incluindo candidatos e limites de acesso.
- `parameter_catalog.json`: onze etapas e 110 propriedades planejadas, com unidades.
- `evidence_seed.jsonl`: sete resumos candidatos de três estudos, sem treinamento.
- `evidence.py`: conversões explícitas, compilação de topologia, verificações iniciais e partição por grupo.
- `test_evidence.py`: dezenove testes de integridade dos contratos e falhas cientificamente relevantes.
- `build_registry.py`: reprodução do seed e do catálogo a partir das transcrições curtas verificáveis.
- `validation.json`: resultados de execução e hash do seed.

Execução: `python3 build_registry.py`; `python3 -m unittest -v`; `python3 evidence.py`. Todos os dezenove testes passaram nesta entrega. Isso valida os contratos implementados; não mede erro preditivo de uma MFC.

## 15. Inventário e acesso

Contexto anterior: oito arquivos da pasta Intelligent UI - GPT e trechos das conversas recuperáveis; sessão completa de criação da v0.5 não recuperada. O HTML e previews foram lidos na etapa anterior; não houve motivo para repetir o download.

Nesta pesquisa: S01, S08 e S09 tiveram texto integral acessível e seções relevantes consultadas. S02, S03, S04, S05, S06 e S07 foram usados em nível de resumo; S10 e S11 em nível de página de dataset; S15 como documentação oficial. S12–S14 e S16 permanecem identificação/discovery ou metadados. Os PDFs/manuscritos de ACS, UWE e outros repositórios tentados tiveram falhas de acesso; isso não foi contornado nem tratado como ausência de conteúdo.

Os arquivos brutos dos dois datasets não foram baixados ou inspecionados. Fichas técnicas de produtos específicos, relatórios de campo e dados de escala maior ainda não compõem o seed. Não há corpus exaustivo, big data, modelo treinado, validação universal, deploy ou autenticação testada nesta entrega.

As fontes, URLs, DOIs e restrições específicas estão em `sources.json`. Os achados embasam a direção; as relações constitutivas e a precisão ainda serão demonstradas por dados e código adicionais.
