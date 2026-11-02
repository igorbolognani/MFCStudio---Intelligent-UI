# MFC Studio — guia de engenharia, materiais e modelagem

**Uma leitura para entender a célula, acompanhar seus balanços e saber até onde confiar em uma previsão.**

Revisão editorial: **2 de novembro de 2026**. Código científico conferido: `mfc-kernel/0.2.0`; base de evidências: `mfc-corpus/0.3.0`. Os registros de publicação e auditoria reunidos aqui são de **25 e 26 de outubro de 2026**. Esta revisão organiza e explica o trabalho existente; não representa uma nova calibração ou uma nova auditoria da aplicação em produção.

Este guia reúne o conteúdo dos onze arquivos que antes estavam separados em `docs`. O texto principal foi reescrito para uma leitura de engenharia. Inventários, números de verificação e registros originais ficam em anexos recolhíveis no final, dentro deste mesmo documento.

## Como usar esta leitura

Se você está retomando o assunto, leia primeiro as seções 1 a 6. Elas ligam a experiência em materiais ao funcionamento eletroquímico e biológico. Depois avance para as equações, na seção 8, acompanhando o exemplo da seção 9. Para trabalhar diretamente com artigos e fichas, comece pelas seções 11 e 12. O roteiro da seção 14 propõe exercícios sem exigir programação.

Não é necessário decorar todas as fórmulas. A primeira meta é conseguir responder: **o que está se movendo, por onde passa, o que limita esse movimento e qual medição sustentaria a relação que estou usando?**

### Sumário

1. [A pergunta que o Studio procura responder](#objetivo)
2. [O que existe hoje e o que continua em aberto](#estado)
3. [Como uma MFC funciona](#funcionamento)
4. [Arquiteturas: o desenho muda os balanços](#arquiteturas)
5. [As onze etapas e suas relações](#etapas)
6. [Materiais: da fabricação ao comportamento da célula](#materiais)
7. [Como transformar uma pergunta de engenharia em um modelo](#construir-modelo)
8. [As equações que o núcleo atual resolve](#equacoes)
9. [Um exemplo de cálculo explicado](#exemplo)
10. [Como ler curvas, perdas e diagnósticos](#resultados)
11. [Como transformar literatura e fichas em dados utilizáveis](#dados)
12. [O que os estudos já reunidos permitem aprender](#estudos)
13. [Calibração, validação e confiança na previsão](#validacao)
14. [Roteiro de aprendizado e exercícios](#aprendizado)
15. [Próximas decisões científicas](#continuidade)
16. [Referências e localização dos materiais de apoio](#referencias)
17. [História do projeto, preservação e limites de acesso](#historico)
18. [Glossário de consulta](#glossario)
19. [Anexos de parâmetros e rastreabilidade](#anexos)

<a id="objetivo"></a>
## 1. A pergunta que o Studio procura responder

O MFC Studio é um laboratório digital de **células a combustível microbianas**, chamadas de MFCs pela sigla em inglês. A intenção é investigar configurações, compreender por que uma escolha altera o resultado e selecionar hipóteses que mereçam um protótipo ou ensaio pequeno.

Uma pergunta útil seria: “Se eu usar este feltro comercial como ânodo, nesta geometria, com este meio e este cátodo, qual perda provavelmente será importante? Qual propriedade preciso conhecer antes de comprar ou montar a célula?”. A resposta depende do conjunto. O material mais condutor pode trazer pouca melhora se o transporte iônico no líquido ou a reação no cátodo dominar as perdas.

O recorte definido para esta fase é **selecionar materiais comerciais usando literatura e fichas técnicas, com atenção a custo e disponibilidade**. Isso aproveita a formação em engenharia de materiais e estabelece uma entrada concreta para estudar a eletroquímica e a microbiologia necessárias.

O objetivo de longo prazo inclui investigar combinações ainda não ensaiadas diretamente em artigos. Para isso, será preciso conectar composição, fabricação, microestrutura e propriedades medidas às relações físicas da célula. Não basta atribuir um coeficiente a cada nome de material ou copiar o pico de potência de um artigo.

Há três perguntas diferentes que devem acompanhar qualquer resultado:

| Pergunta | Exemplo |
|---|---|
| O que sabemos a partir de uma fonte ou medição? | A ficha informa resistência em determinada direção e pressão. |
| O que estamos propondo como representação? | Representar o percurso eletrônico por uma resistência equivalente. |
| O que ainda precisa ser demonstrado? | Que essa resistência e as demais relações reproduzem uma célula real, inclusive fora dos dados usados no ajuste. |

O baixo erro é uma meta de validação. A quantidade de artigos reunidos, o número de propriedades cadastradas e a aparência da interface não demonstram essa precisão.

<a id="estado"></a>
## 2. O que existe hoje e o que continua em aberto

### 2.1 Uma aplicação utilizável e um modelo ainda exploratório

O Studio é independente do METREV completo. A aplicação possui uma página inicial explicativa, um simulador com acesso pela conta ChatGPT, montagem guiada em onze etapas, desenho selecionável, painel científico e persistência dos cenários. As explicações, equações, hipóteses e diagnósticos devem permanecer reunidos no painel científico, que pode ser minimizado e expandido.

O produto foi definido sem chat ou agente dentro da aplicação e sem plugin MCP para conversar com ela. A interface deve permitir voltar ao início, avançar e retornar entre etapas, fechar painéis, retornar ao desenho e sair da sessão. O desenho precisa manter componentes identificáveis e selecionáveis sem esconder os vizinhos. São decisões de uso do laboratório, preservadas nesta consolidação.

O núcleo de cálculo representa uma família específica: **monocâmara, sem membrana separadora, acetato como substrato, consórcio microbiano misto, cátodo a ar ambiente, batelada, pH 7 tamponado e 25 °C**. Ele calcula perdas elétricas, limitações de corrente e evolução de DQO, carga e energia. Seus parâmetros iniciais são hipóteses de exploração. Ainda não houve ajuste experimental que transforme esse conjunto em um preditor validado.

Configurações fora dessa família podem ser registradas, mas a previsão é declarada indisponível quando faltam as relações correspondentes. Essa distinção evita que uma configuração de duas câmaras, por exemplo, receba números produzidos por balanços de outra arquitetura.

### 2.2 O significado dos números da base

| Conteúdo no corpus 0.3.0 | Quantidade | Como interpretar |
|---|---:|---|
| Etapas de configuração | 11 | Estrutura do sistema. |
| Propriedades propostas no catálogo | 110 | Perguntas e campos pertinentes; não são 110 leis físicas implementadas. |
| Campos numéricos do núcleo | 39 | Incluem entradas de cálculo, condições fixas, limites de uso e propriedades apenas registradas. |
| Fontes indexadas | 29 | Misturam estudos, modelos, dados, fornecedores e uma referência de plataforma. |
| Artigos completos recuperados | 6 | Arquivos integrais com licença de redistribuição conferida. |
| Suplementos completos | 2 | Incluem métodos, figuras e dados adicionais. |
| Registros de evidência | 198 | Incluem contextos, especificações, ofertas e resultados; não são 198 experimentos independentes. |
| Células de observação | 397 | 393 numéricas e quatro ausentes. Parte dos números é comercial. |
| Variantes comerciais | 16 | Suportes, tratamentos e componentes completos separados. |
| Propriedades comerciais extraídas | 46 | 44 normalizadas dimensionalmente; duas com conversão bloqueada. |
| Ofertas datadas | 31 | Capturas de 26/10/2026; não são preços atuais garantidos nem custos entregues. |
| Pontos digitalizados de uma curva S18 | 13 | Pontos relacionados, provenientes da mesma curva. |
| Pares experimentais de pico e tempo S29 | 115 | Medidos em três reatores reutilizados; dois pares adicionais estão ausentes. |
| Registros aprovados para treinamento | 0 | Nenhum preditor foi treinado com essa base. |

Na auditoria de produção de outubro, os oito PDFs estavam presentes e os textos estavam organizados em 49 trechos no banco. Os quinze grupos de proveniência daquela auditoria incluem grupos comerciais e experimentais. Não devem ser lidos como quinze famílias independentes de validação.

### 2.3 Três níveis de relação com a ciência

**Fenômeno explicado:** sabemos que pode afetar a célula e explicamos seu mecanismo. É o caso do desequilíbrio de pH ou do alagamento de um cátodo poroso.

**Propriedade registrada:** guardamos valor, unidade, condição e fonte. A espessura do biofilme e a carga de catalisador são exemplos de campos que ainda não determinam, sozinhos, uma resposta física no núcleo.

**Relação resolvida:** existe uma equação implementada que participa do cálculo. É o caso da resistência do líquido a partir de sua condutividade e da geometria do percurso iônico.

Esses níveis podem coexistir na mesma etapa. Uma etapa estar presente na montagem ou na base bibliográfica não significa que todas as suas interações já estejam calculadas.

<a id="funcionamento"></a>
## 3. Como uma MFC funciona

### 3.1 O material orgânico é a fonte de elétrons

Na região anódica, certos microrganismos oxidam compostos orgânicos e conseguem transferir parte dos elétrons dessa oxidação ao ânodo. O eletrodo funciona como um destino para esses elétrons. A comunidade microbiana usa o metabolismo para obter energia e manter sua atividade; nem todo elétron disponível no alimento acaba no circuito.

Um modo de escrever o balanço da oxidação completa do acetato é:

$$
\mathrm{CH_3COO^- + 2H_2O \rightarrow 2CO_2 + 7H^+ + 8e^-}
$$

Essa escrita mostra os oito elétrons por molécula de acetato e conserva átomos e carga. É uma representação estequiométrica. Próximo de pH neutro, o carbono inorgânico se distribui entre espécies como CO₂ e bicarbonato, e parte do carbono pode ser incorporada à biomassa. A equação não descreve todas as etapas metabólicas ou toda a composição do líquido.

### 3.2 Há um percurso eletrônico e um percurso iônico

Os elétrons seguem do ânodo pelo coletor e pelo circuito externo até o cátodo. A passagem pela carga externa permite entregar energia elétrica. No cátodo a ar, o oxigênio recebe elétrons. Para a rota de quatro elétrons, uma escrita em meio neutro/alcalino é:

$$
\mathrm{O_2 + 2H_2O + 4e^- \rightarrow 4OH^-}
$$

Ao mesmo tempo, o meio líquido e, quando presente, a membrana precisam transportar carga iônica. Sem essa redistribuição, as regiões acumulariam carga e a passagem sustentada de corrente seria impedida. O circuito da célula depende desses dois percursos.

```mermaid
flowchart TB
    M["Meio com matéria orgânica e biofilme"]
    A["Ânodo"]
    R["Circuito externo e carga"]
    C["Cátodo com acesso ao oxigênio"]
    L["Caminho iônico no líquido e eventual separador"]
    M -->|"oxidação e transferência de elétrons"| A
    A -->|"elétrons"| R
    R -->|"elétrons"| C
    A --- L
    L --- C
```

O desenho é conceitual: não fixa o sentido de transporte de cada espécie iônica nem cria um segundo líquido. Na monocâmara com cátodo a ar, o líquido em contato com os eletrodos pode ser o mesmo. O sentido indicado pelas setas externas é o fluxo de elétrons; o sentido convencional da corrente elétrica é o oposto.

### 3.3 A tensão depende das duas extremidades e das perdas

A tensão da célula é a diferença entre os potenciais dos dois eletrodos, descontadas as perdas quando há corrente. Um potencial de eletrodo precisa ser referido a uma referência: por exemplo, Ag/AgCl com composição de eletrólito especificada. Já a tensão terminal é medida entre os dois terminais da célula.

A composição e o pH podem alterar potenciais de equilíbrio. A relação de Nernst expressa essa dependência em termos de temperatura e atividades das espécies. “Atividade” é a concentração efetiva do ponto de vista termodinâmico; não é sempre igual à concentração nominal. Uma DQO total de efluente não pode ser colocada diretamente no lugar da atividade de uma espécie nessa relação.

O Studio atual recebe uma tensão de circuito aberto **efetiva**, mantida como parâmetro. Ele não calcula a especiação química nem recalcula essa tensão por Nernst a cada mudança de meio. Essa diferença entre a explicação física e a implementação precisa acompanhar qualquer interpretação.

### 3.4 A corrente atravessa um conjunto de limitações

Para sustentar corrente, é necessário haver substrato acessível, microrganismos ativos, transferência de elétrons ao ânodo, condução pelo material e pelos contatos, transporte iônico e reação catódica com acesso ao oxidante. Melhorar um percurso pode deslocar a importância para outro.

Uma comparação familiar à engenharia de materiais ajuda: melhorar a condutividade de um componente de uma montagem não elimina uma interface mal conectada. Na MFC, ainda há interfaces com líquidos, gases e um biofilme que muda com a história de operação. Por isso, a avaliação precisa acompanhar o conjunto.

<a id="arquiteturas"></a>
## 4. Arquiteturas: o desenho muda os balanços

Antes de escolher equações, desenhe os volumes de controle: quais regiões contêm líquido, quais contêm gás, quais meios são compartilhados e o que pode atravessar cada fronteira. Esse desenho define o que precisa ser conservado.

| Arquitetura | O que deve ser acompanhado | Consequência para a modelagem |
|---|---|---|
| Uma câmara, cátodo a ar | Um inventário líquido; entrada de O₂ pelo lado do ar e possível ingresso no líquido. | Não somar um católito independente ao volume anódico. É a família atualmente calculada, nas condições restritas da seção 2. |
| Uma câmara, cátodo imerso | Um meio líquido compartilhado; transporte de oxidante até o cátodo. | A disponibilidade de O₂ dissolvido exige seu próprio balanço. Não duplicar o mesmo líquido. |
| Duas câmaras com meios separados | Inventário e composição de cada líquido; transporte entre regiões. | Exige balanços acoplados e descrição do separador, quando houver. |
| Cátodo exposto a gás em volume controlado | Quantidade inicial de gás, consumo, eventual alimentação e saída. | A concentração ou pressão pode variar. Um reservatório fechado não se comporta como ar ambiente aberto. |
| Presença de membrana ou separador | Transporte de espécies, resistência, mistura e passagem de reagentes. | Acrescentar apenas uma resistência elétrica não descreve todas essas funções. |

O ar ambiente é tratado no núcleo como uma **fronteira aberta**, com fração de O₂ e pressão informadas. Isso é uma hipótese de contorno declarada. Não significa que o programa tenha calculado ventilação, depleção em uma caixa fechada ou transporte em um volume finito de gás.

A alimentação também altera o problema. Na **batelada**, parte-se de um inventário e acompanha-se seu consumo. Em **bateladas alimentadas**, há adição ou substituição de meio; os eventos e a idade do sistema importam. Em **fluxo contínuo**, entram vazão, concentração de entrada e saída. O tempo de residência nominal é volume dividido pela vazão, mas não descreve sozinho mistura, zonas mortas ou distribuição dos tempos de permanência.

As onze etapas permanecem na montagem em todas essas configurações. Algumas identificam ausência, compartilhamento ou não aplicabilidade. Um espaço no guia não obriga a existência física de uma peça ou de um reservatório.

<a id="etapas"></a>
## 5. As onze etapas e suas relações

### 5.1 Câmara anódica

A câmara define o volume de líquido, a forma da região reacional, a posição do ânodo e os caminhos até o cátodo. Também participa da vedação e das trocas indesejadas com o ambiente. Sua geometria influencia o percurso iônico e o transporte de substrato.

Para um engenheiro de materiais, vale observar o material das paredes, a fabricação, a rugosidade, as juntas e a estabilidade em contato com o meio. Uma peça impressa pode apresentar poros, aditivos ou acabamentos diferentes de uma placa usinada. Compatibilidade, liberação de substâncias e permeação precisam de evidência para o produto e as condições utilizados; o nome do polímero não resolve todas essas perguntas.

No modelo atual, o volume determina o inventário de DQO e a geometria entra por um comprimento e uma seção iônicos efetivos. Não há cálculo do escoamento ou de gradientes dentro da câmara. A pergunta prática é: “Que volume está realmente disponível e qual percurso estou representando com estes números?”.

### 5.2 Meio anódico

O meio anódico, ou anólito, contém substrato, água, nutrientes, sais e os componentes que controlam o pH. Alimentar carbono e conduzir íons são funções diferentes. Aumentar a concentração de um sal pode alterar a condutividade sem acrescentar alimento biodegradável.

DQO é uma medida de equivalentes de oxigênio necessários à oxidação química. DBO é uma medida associada ao consumo biológico de oxigênio em um ensaio definido. Ambas costumam aparecer em mg O₂/L, mas não são intercambiáveis. Dois meios de mesma DQO podem ter frações biodegradáveis e velocidades de consumo diferentes.

O pH afeta a fisiologia e as reações; o tampão ajuda a resistir às alterações de pH. A condutividade do líquido afeta a perda ôhmica. Mais sais, porém, também mudam o ambiente químico e biológico. Uma melhora elétrica não autoriza presumir que a comunidade tolerará qualquer concentração.

O núcleo usa uma única concentração de DQO na base de acetato e uma condutividade informada. Mantém pH e temperatura no caso de referência. Não resolve mistura de substratos, especiação, consumo de tampão ou metabolismo específico de cada composto.

### 5.3 Ânodo

O ânodo reúne a superfície onde o biofilme se estabelece e o caminho pelo qual os elétrons chegam ao coletor. Feltro, tecido, papel e outros materiais porosos podem oferecer arranjos muito diferentes de área acessível, conectividade e transporte.

Há pelo menos três perguntas de área: qual é a área geométrica exposta, qual é a seção atravessada pelos elétrons e qual superfície interna é efetivamente acessível? Elas não são iguais. Uma grande área BET de pó não demonstra que microrganismos colonizem todos os poros ou que toda a área participe da transferência eletroquímica.

Tratamentos térmicos e químicos podem alterar condução, grupos superficiais, molhabilidade e estabilidade. A compressão pode melhorar contato e, simultaneamente, modificar porosidade e passagens para o líquido. O efeito depende do percurso de corrente e da montagem.

O núcleo distingue área geométrica anódica, condutividade eletrônica e geometria da condução. Ainda não converte automaticamente porosidade, BET, tratamento ou nome comercial em capacidade eletroativa. Para usar uma ficha, comece verificando direção de medição, estado, pressão e identidade da variante.

### 5.4 Catalisador anódico

Esta etapa identifica um eventual revestimento ou material adicional aplicado ao ânodo. Não deve ser confundida com o próprio biofilme, que é o biocatalisador tratado na etapa seguinte.

Uma camada adicionada pode mudar a superfície, o contato com as células, a transferência eletrônica, o acesso aos poros e a estabilidade. Sua influência depende de composição, carga, aderência, preparação e compatibilidade com o meio. Depositar mais material não garante que ele permaneça eletricamente conectado e acessível.

Na família atual, não há catalisador anódico artificial adicionado. Selecionar uma camada ativa leva à previsão indisponível porque sua relação constitutiva não foi implementada. A etapa preserva essa possibilidade no contrato, sem inventar uma contribuição numérica para ela.

### 5.5 Biofilme

O biofilme é uma comunidade aderida, com células e uma matriz extracelular. Nela ocorrem consumo de substrato, crescimento, competição e transferência de elétrons. Algumas espécies podem produzir compostos que outras utilizam. A comunidade e sua atividade dependem do inóculo, do enriquecimento, do alimento e da história de operação.

Um biofilme mais espesso pode conter mais biomassa, mas também estabelecer percursos maiores para substrato, produtos e carga. Espessura não determina sozinha a capacidade de corrente. É preciso saber que parte está ativa, como os elétrons são transferidos e quais limitações internas aparecem.

Para estudar a bioquímica inicialmente, concentre-se em quatro relações: **quem fornece elétrons, quem os recebe, quais rotas competem pelo substrato e como o meio afeta a atividade**. A identificação de um organismo ou de um gene não fornece diretamente uma constante cinética.

O núcleo atual representa uma capacidade eletroativa fixa, limitada pelo substrato, e duas rotas efetivas de consumo concorrente. Não calcula crescimento, distribuição de espécies ou difusão dentro do biofilme. A espessura pode ser registrada, mas ainda não é a origem matemática dessa capacidade.

### 5.6 Membrana

Uma membrana pode separar meios e controlar o transporte de espécies. Precisa conciliar condução de carga com limitação de misturas ou passagens indesejadas. Hidratação, grupo funcional, contraíon, espessura, eletrólito e temperatura importam para suas propriedades.

“Membrana de troca catiônica” não significa “só passam prótons”. Em condições de MFC, íons como Na⁺, K⁺ e NH₄⁺ podem contribuir para o transporte. Isso pode acompanhar diferenças de composição e pH entre os lados. O estudo de Rozendal, Hamelers e Buisman, [S06](https://doi.org/10.1021/es060387r), mostra por que essa distinção é necessária.

Uma resistência por área medida em ácido ou solução salina especificada não é uma constante universal para qualquer meio. A forma em que a membrana é fornecida e o procedimento de pré-hidratação também devem ser registrados.

O núcleo atual calcula somente a configuração sem membrana separadora. A expressão resistência = ASR/área é explicada, mas não constitui um modelo de transporte membranar implementado. O Nafion presente como ionômero ou revestimento de um eletrodo também não cria, por si só, uma membrana separadora na arquitetura.

### 5.7 Circuito e alimentação/coleta

A resistência externa define a carga elétrica conectada à célula. Ela participa da determinação do ponto de operação. Uma carga muito alta aproxima a condição de circuito aberto; uma carga muito baixa aproxima o curto-circuito. Em ambos os extremos, a potência útil pode ser pequena, por motivos diferentes.

Contatos, fios e coletores acrescentam perdas. Uma boa condutividade do eletrodo pode ser pouco aproveitada se a ligação com o coletor for ruim. Pressão, corrosão, área de contato e posição da coleta precisam ser considerados na montagem.

Alimentação e coleta são reunidas nesta etapa para registrar como o inventário entra, é renovado e sai. Na leitura de um artigo, identifique intervalos de alimentação, volumes substituídos, momentos de amostragem e critério para considerar o substrato esgotado. Esses eventos podem alterar a resposta temporal.

O núcleo resolve uma carga resistiva e uma resistência de contato informada. A dinâmica implementada é de batelada; não inclui balanço de alimentação contínua, trocas periódicas de meio ou consumo energético de bombas e instrumentação. A energia elétrica calculada é bruta da célula.

### 5.8 Câmara catódica

Quando existe uma câmara catódica separada, sua geometria e seu meio influenciam composição, transporte e acúmulo de produtos. Ela exige um inventário próprio, conforme a arquitetura.

Na monocâmara com cátodo a ar, esta etapa descreve principalmente a exposição ao gás, a abertura útil, a vedação e o suporte mecânico. Não representa obrigatoriamente outro reservatório líquido. Uma área de folha comprada também não é igual à área circular deixada exposta por uma abertura.

A pergunta de modelagem é: “De onde vem o oxidante e que fronteira estou assumindo?”. No caso suportado, a fronteira é o ar ambiente. Uma caixa fechada com quantidade finita de O₂ precisaria acompanhar o consumo do gás ao longo do tempo.

### 5.9 Meio catódico

O católito é o líquido da região catódica quando há um meio próprio. Seu pH, composição, condutividade e disponibilidade de oxidante podem mudar durante a operação. Na monocâmara com cátodo imerso, esse líquido pode ser o mesmo anólito.

No cátodo a ar, não se deve adicionar um católito independente apenas para preencher um campo. Há uma região de reação associada ao eletrodo e ao líquido/filme hidratado que o alcança, além do gás no lado exposto. Descrever essas interfaces é diferente de inventar outro volume de solução.

O núcleo mantém a distinção entre meio compartilhado, meio independente e etapa não aplicável. Ainda não resolve um inventário separado de católito ou um campo de oxigênio dissolvido.

### 5.10 Cátodo

O cátodo precisa receber elétrons, manter contato iônico com o meio e permitir que o oxidante alcance regiões reativas. Em um cátodo poroso a ar, a organização das fases sólida, líquida e gasosa é central.

Uma camada muito molhada pode dificultar o acesso de gás; uma região excessivamente seca pode perder contato iônico. O tratamento hidrofóbico e a camada microporosa, ou MPL, ajudam a controlar essa distribuição, mas seu efeito depende da estrutura e das condições de uso. É uma questão de transporte e de interfaces, além de composição química.

É necessário distinguir **suporte poroso**, **suporte com MPL/tratamento** e **eletrodo completo com catalisador e ligante**. O tecido W1S1011 nu e um eletrodo pronto que usa esse tecido são produtos diferentes. O preço e o comportamento de um não substituem automaticamente os do outro.

O núcleo usa área catódica, condução eletrônica e um coeficiente efetivo de acesso de O₂. Não calcula alagamento, secagem ou distribuição da reação entre poros. Essas explicações físicas continuam importantes para interpretar e selecionar dados, mesmo quando a relação ainda não está resolvida.

### 5.11 Catalisador catódico

O catalisador influencia a velocidade e a rota da redução do oxigênio. A camada real contém, além do material ativo, suporte e frequentemente ligantes ou ionômeros. Carga, dispersão, acessibilidade, contato e estabilidade atuam em conjunto.

“0,5 mg de Pt por cm²” é diferente de “0,5 mg de Pt/C por cm²”. Se o pó tem uma fração de platina, é necessário especificar a base de massa antes de comparar cargas e custos. A massa de tinta, que também contém solvente e ligante, é outra grandeza.

Uma camada mais carregada pode ter mais material ativo e, ao mesmo tempo, maior espessura ou resistência ao transporte. Uma atividade medida em eletrodo rotatório também não equivale ao desempenho de uma MFC completa. O eletrólito, o potencial e a organização das fases mudam.

O modelo atual usa parâmetros cinéticos efetivos e adota redução de O₂ por quatro elétrons. Essa rota não deve ser generalizada automaticamente a todos os carbonos: S17 relata resultados compatíveis com participação de rota de dois elétrons/peróxido nas condições ensaiadas. Carga e nome do catalisador ainda não geram os parâmetros cinéticos do núcleo.

<a id="materiais"></a>
## 6. Materiais: da fabricação ao comportamento da célula

### 6.1 A pergunta intermediária que liga material e previsão

Entre “escolhi um feltro” e “a potência aumentou” existem várias relações. A fabricação estabelece fibras, poros, contatos e superfície. O tratamento muda algumas dessas características. A montagem impõe compressão, exposição e conexão ao coletor. O meio altera molhabilidade e estado químico. A operação ainda pode causar envelhecimento, incrustação ou mudança do biofilme.

Para construir uma previsão, cada ligação precisa de uma medição, de uma relação física adequada ou de uma hipótese claramente identificada.

| Escolha ou tratamento | O que pode mudar fisicamente | O que procurar para sustentar a relação |
|---|---|---|
| Carbonização, grafitização ou tratamento térmico | Conectividade eletrônica, química superficial e estrutura. | Condutividade direcional e caracterização da variante efetivamente usada. |
| Oxidação ou ativação superficial | Molhabilidade, grupos superficiais e superfície acessível. | Método de tratamento, medidas superficiais e ensaio eletroquímico compatível. |
| Compressão de feltro ou papel | Contatos entre fibras, espessura e caminhos de líquido/gás. | Propriedades medidas sob a mesma compressão da montagem. |
| PTFE, MPL ou outro tratamento hidrofóbico | Distribuição de fases e transporte até a reação. | Carga, fabricação, permeabilidade, molhabilidade e ensaio do componente. |
| Deposição de catalisador/ionômero | Sítios ativos conectados, acesso iônico e espessura da camada. | Bases de massa, formulação, método de deposição e caracterização do eletrodo final. |
| Alteração do coletor e de sua posição | Distância eletrônica e perdas de contato. | Geometria, pressão de contato e resistência da montagem. |

As relações dessa tabela são caminhos de investigação. O Studio não calcula automaticamente todos eles. Hoje, selecionar uma designação comercial não preenche uma cadeia já calibrada de composição até desempenho.

### 6.2 Quatro distinções que evitam erros grandes

**Condutividade eletrônica e iônica.** A primeira descreve a condução de elétrons no sólido e em seus contatos; a segunda, a condução de íons no líquido ou em materiais apropriados. O mesmo símbolo de unidade, S/m, não torna os mecanismos ou valores intercambiáveis.

**Resistividade e resistência por área.** Resistividade tem unidade Ω·m e entra na relação entre comprimento e seção. Resistência específica por área, ASR, tem unidade Ω·m² e deve ser dividida pela área correspondente para produzir Ω. O valor informado pode incluir contato e condição de compressão. Não se deve transformá-lo em propriedade volumétrica sem esclarecer isso.

**Área geométrica, BET e área eletroquimicamente ativa.** A primeira descreve uma referência de geometria. BET é uma área específica obtida por adsorção, usualmente na base de massa e com preparação definida. ECSA é uma medida de área eletroquimicamente ativa segundo um método. Igualar essas áreas pode introduzir erros de muitas ordens de grandeza.

**Seco, hidratado e comprimido.** Espessura observada após preparação para microscopia não é necessariamente a espessura em operação. Uma ficha de material seco e uma resistência medida comprimida não descrevem automaticamente o mesmo estado. O estado faz parte do dado.

### 6.3 Como ler uma ficha com uma pergunta de engenharia

Comece pela identidade: fabricante, família, grau, SKU, tratamento e lote, quando disponíveis. SKU é o código comercial de uma variante; não comprova sozinho igualdade entre o produto atual e o lote de um estudo antigo.

Depois procure a direção de medição. *In-plane* significa ao longo do plano; *through-plane*, atravessando a espessura. Um tecido ou feltro é anisotrópico: não se pode escolher a maior condutividade da tabela sem relacioná-la ao percurso da corrente na montagem.

Por fim, leia condições e notas: pressão, temperatura, hidratação, eletrólito, método e se os números são típicos, limites ou valores garantidos. Um valor típico não traz automaticamente uma distribuição de incerteza. Um sinal “menor que” deve continuar sendo um limite, mesmo depois da conversão de unidade.

Na base atual, a unidade de uma resistência do H23C6 está ambígua e a base de massa de uma carga nominal comercial precisa de confirmação. Essas observações continuam registradas, com a conversão bloqueada. Isso permite retomar a fonte sem preencher uma lacuna com uma suposição silenciosa.

### 6.4 Custo e disponibilidade fazem parte da comparação

Para escolher comercialmente, compare produtos que entreguem funções e níveis de acabamento equivalentes. Um suporte barato ainda pode exigir catalisador, ligante, solventes, tratamento, montagem e perdas. Um eletrodo pronto pode incluir parte disso, mas precisa ter dimensões e condições adequadas ao ensaio.

Há três custos diferentes: preço anunciado, custo do material efetivamente aproveitado e custo entregue/montado. A base atual registra ofertas e permite algumas comparações por área bruta comprada. Não presume aproveitamento de corte, frete, IVA ou importação iguais a zero.

**Exemplo apenas didático:** uma folha de 10 × 10 cm tem 100 cm². Se custa 30 unidades monetárias, o preço bruto é 0,30 por cm². Caso só 60 cm² possam ser aproveitados na montagem, o custo de material por área aproveitada passa a 0,50. Os valores deste exemplo não são uma cotação.

Um anúncio “a partir de” só permite um limite de preço por área quando se sabe a que dimensão e quantidade ele se refere. Botão de compra, indicação de estoque e prazo anunciado são informações do vendedor; a entrega e o custo final precisam de confirmação. As 31 ofertas do corpus são capturas históricas de 26/10/2026.

<a id="construir-modelo"></a>
## 7. Como transformar uma pergunta de engenharia em um modelo

### 7.1 Defina primeiro a decisão e a grandeza de interesse

“Qual é o melhor material?” é uma pergunta incompleta. Melhor para qual montagem, qual meio e qual critério? Potência máxima, energia acumulada, estabilidade e sensibilidade de um biossensor são resultados diferentes. Um produto pode ser adequado a um deles e pouco interessante a outro.

Nesta fase, uma pergunta mais bem delimitada seria: “Entre componentes comerciais que consigo adquirir, quais têm dados suficientes para comparar o custo e as perdas esperadas nesta família de MFC?”. A primeira saída pode ser uma lista de comparações admissíveis e de medições faltantes, antes de existir uma classificação confiável de desempenho.

### 7.2 Separe entradas, estados, parâmetros e resultados

| Tipo de informação | O que significa | Exemplo |
|---|---|---|
| Entrada de operação ou montagem | Algo definido para o caso estudado. | Volume de líquido, carga externa e área exposta. |
| Estado do sistema | Grandeza que muda com a evolução representada. | DQO restante na batelada. |
| Parâmetro de uma relação | Número que caracteriza a resposta dentro de condições e de uma formulação. | Condutividade, capacidade anódica ou parâmetro cinético efetivo. |
| Resultado | Grandeza obtida depois de resolver as relações em conjunto. | Corrente, tensão, energia e DQO final. |
| Descritor registrado | Informação pertinente sem relação quantitativa implementada para aquela saída. | Nome comercial ou espessura do biofilme no núcleo atual. |

Um parâmetro pode ser medido, calculado a partir de uma medição, ajustado a dados ou assumido. A origem deve acompanhar o valor. A mesma condutividade pode servir como entrada do cálculo elétrico e, ao mesmo tempo, ter sido obtida de um ensaio de material.

### 7.3 Escolha volumes de controle e balanços

Depois da decisão, desenhe o sistema como na seção 4. Conte matéria que entra, sai, reage e se acumula. Identifique as espécies necessárias à pergunta: uma descrição simplificada pode acompanhar apenas DQO; uma previsão de pH exige composição, equilíbrio e transporte adicionais.

O modelo atual é de **parâmetros concentrados**, frequentemente chamado de 0D. Usa valores representativos para cada região e perdas equivalentes. Não fornece um mapa de concentração ou potencial dentro dos poros. “0D” não significa ausência de geometria: comprimentos, áreas e volume continuam participando do cálculo.

Uma descrição espacial 1D, 2D ou 3D passaria a resolver variações ao longo de uma ou mais direções. Exigiria propriedades e condições de contorno que sustentem essas variações. O projeto não estabelece visualização espacial como requisito inicial; o avanço depende de modelo, dados e verificação correspondentes.

### 7.4 Escreva relações e só então procure seus parâmetros

Para uma perda condutiva, a pergunta é como comprimento, seção e condutividade produzem resistência. Para uma limitação de substrato, a pergunta é como a disponibilidade do alimento restringe a capacidade de corrente. Para um cátodo a ar, é como representar acesso ao oxidante e velocidade de reação.

O material fornece parte das propriedades, mas nem todos os parâmetros são propriedades intrínsecas. Um coeficiente **efetivo** pode reunir fenômenos não separados pela representação. Nesse caso, um valor obtido para uma montagem pode não ser transportável para outra espessura, hidratação ou estrutura.

Antes de inserir um número, confira se a unidade fecha, se a condição corresponde ao sistema e se esse número é realmente o parâmetro da equação. Uma potência máxima publicada não fornece, por renomeação, a corrente de troca do catalisador ou a resistência puramente ôhmica da solução.

### 7.5 Resolva o conjunto e confronte suas consequências

Nas relações elétricas atuais, a corrente participa de todas as perdas. A soma precisa ser compatível com a tensão disponível e com a carga externa. Ao mudar a corrente, também muda a taxa de consumo eletrogênico de DQO. Com o consumo, a concentração diminui e altera a capacidade de corrente nos instantes seguintes.

Esse é o acoplamento essencial: as saídas emergem da solução simultânea e da evolução dos balanços. Somar “bônus” independentes a cada peça não representa esse comportamento.

Uma boa revisão pergunta se a solução respeita os limites: corrente nula sem substrato ou sem O₂ na família representada, inventário não negativo, fechamento de tensão e compatibilidade entre carga elétrica e consumo equivalente de matéria. Depois é necessário comparar com experimentos. As duas verificações têm funções distintas.

<a id="equacoes"></a>
## 8. As equações que o núcleo atual resolve

As expressões abaixo são as relações efetivamente presentes no núcleo 0.2.0. As leis de ativação e limitação constituem uma **hipótese de engenharia ainda não calibrada**. Não são apresentadas como reprodução completa de um artigo específico.

Use unidades coerentes durante o cálculo. O programa trabalha principalmente com metros, metros quadrados, metros cúbicos, segundos, ampères e volts. A concentração de substrato é expressa em **g de equivalentes de O₂ por m³**, numericamente igual a mg O₂/L.

### 8.1 Condução iônica no líquido

$$
R_{\mathrm{sol}}=\frac{L_i}{\kappa A_i}
$$

| Símbolo | Nome e unidade | Papel |
|---|---|---|
| $R_{\mathrm{sol}}$ | Resistência do caminho líquido, Ω. | Perda condutiva representada. |
| $L_i$ | Comprimento iônico efetivo, m. | Percurso médio equivalente. |
| $\kappa$ | Condutividade iônica, S/m. | Capacidade de condução do meio nas condições informadas. |
| $A_i$ | Seção iônica efetiva, m². | Seção disponível para a condução equivalente. |

Mantidas as outras condições, dobrar o comprimento dobra essa resistência; dobrar a condutividade ou a seção a reduz à metade. Isso descreve uma representação uniforme. Uma geometria com distribuição não uniforme pode exigir outro comprimento/seção efetivos ou um modelo espacial.

**Exemplo com os valores iniciais assumidos do núcleo:**

$$
R_{\mathrm{sol}}=\frac{0{,}03\ \mathrm{m}}{0{,}5\ \mathrm{S/m}\times0{,}0007\ \mathrm{m^2}}
\approx85{,}71\ \Omega
$$

Esse número não é uma resistência medida de um reator publicado. Ele mostra o significado das entradas do caso de exploração.

### 8.2 Condução eletrônica e contatos

Para cada eletrodo, a representação é:

$$
R_e=\frac{L_e}{\sigma A_e}
$$

$R_e$ é a resistência eletrônica, em Ω; $L_e$, o percurso eletrônico em m; $\sigma$, a condutividade eletrônica direcional em S/m; e $A_e$, a seção normal a esse percurso em m². Há um conjunto desses valores para o ânodo e outro para o cátodo.

Se os elétrons atravessam a espessura, a geometria do caminho difere de uma coleta ao longo do plano. Na segunda situação, a seção pode envolver largura e espessura, e o comprimento acompanha a distância até o coletor. A área reacional exposta não deve substituir automaticamente essa seção.

A resistência ôhmica total representada é:

$$
R_\Omega=R_{\mathrm{sol}}+R_{e,a}+R_{e,c}+R_{\mathrm{cont}}
$$

$R_{e,a}$ e $R_{e,c}$ são as resistências eletrônicas anódica e catódica. $R_{\mathrm{cont}}$ é a resistência de contatos, informada em Ω. Cada parcela participa da queda de tensão $I R$, em volts. Não se deve somar novamente uma resistência de célula inteira que já englobe essas perdas.

### 8.3 Capacidade anódica limitada pelo substrato

$$
I_{\mathrm{cap},a}=j_{\max,a}A_a\frac{S}{K_S+S}
$$

| Símbolo | Nome e unidade | Papel |
|---|---|---|
| $I_{\mathrm{cap},a}$ | Capacidade de corrente anódica, A. | Limite efetivo dependente do substrato. |
| $j_{\max,a}$ | Capacidade por área sob substrato saturante, A/m² geométrico. | Inclui a atividade fixa representada do bioânodo. |
| $A_a$ | Área geométrica anódica, m². | Base de área usada nessa relação. |
| $S$ | DQO disponível na base de acetato, g O₂/m³. | Estado de concentração da batelada. |
| $K_S$ | Constante de meia saturação, g O₂/m³. | Concentração na qual o fator de disponibilidade vale 0,5. |

Quando $S=K_S$, a capacidade vale metade de $j_{\max,a}A_a$. Quando $S$ é muito maior que $K_S$, acrescentar mais substrato tem um efeito cada vez menor sobre esse fator. Se $S=0$, a capacidade é zero.

É uma lei de saturação de tipo Monod, usada aqui como representação efetiva de capacidade. Não calcula crescimento da comunidade. Também não torna uma DQO de efluente complexo equivalente à de acetato.

A aproximação ao limite acrescenta uma perda:

$$
\eta_S=-b_S\ln\left(1-\frac{I}{I_{\mathrm{cap},a}}\right)
$$

$\eta_S$ é a perda em V; $b_S$ é sua escala em V; e $I$ é a corrente em A. A razão dentro do logaritmo é adimensional. A perda cresce quando a corrente solicitada se aproxima da capacidade. Esse termo e a lei de capacidade devem ser identificados por dados adequados, sem contar duas vezes a mesma limitação.

### 8.4 Ativação efetiva nos eletrodos

$$
\eta_a=b_a\operatorname{asinh}\left(\frac{I}{2j_{0,a}A_a}\right)
\qquad
\eta_c=b_c\operatorname{asinh}\left(\frac{I}{2j_{0,c}A_c}\right)
$$

Os sobrepotenciais $\eta_a$ e $\eta_c$ são expressas em volts. Elas representam a parcela de tensão associada à cinética efetiva nos eletrodos. Os parâmetros $b_a$ e $b_c$ têm unidade V. As densidades de troca efetivas $j_{0,a}$ e $j_{0,c}$ têm unidade A/m² na base geométrica adotada. $A_a$ e $A_c$ são as áreas dos respectivos eletrodos em m².

A função $\operatorname{asinh}$ é a inversa do seno hiperbólico, uma função matemática não linear; não é uma nova propriedade do material. Seu argumento é uma razão de correntes. Para a mesma corrente e geometria, aumentar a densidade de troca reduz a perda calculada por essa expressão.

Esses parâmetros reúnem uma resposta efetiva da montagem nas condições consideradas. Ainda não são calculados a partir do tipo de carbono, da carga de Pt ou da espessura da camada. Também não devem ser igualados diretamente a um parâmetro obtido por qualquer ajuste de impedância.

### 8.5 Disponibilidade de oxigênio no cátodo a ar

$$
c_{\mathrm{O_2},g}=\frac{y_{\mathrm{O_2}}p}{R_gT}
$$

$c_{\mathrm{O_2},g}$ é a concentração molar de O₂ no gás, em mol/m³. O símbolo refere-se a oxigênio, não a CO₂. $y_{\mathrm{O_2}}$ é sua fração molar, adimensional; $p$ é a pressão em Pa; $T$, a temperatura em K; e $R_g=8{,}314462618$ J/(mol·K), a constante dos gases. A relação usa a aproximação de gás ideal.

O limite de corrente correspondente é:

$$
I_{\mathrm{lim,O_2}}=4F A_c k_{\mathrm{O_2},g}c_{\mathrm{O_2},g}
$$

$F=96485{,}33212$ C/mol de elétrons é a constante de Faraday. O fator 4 corresponde aos quatro elétrons por molécula de O₂ na rota adotada. $A_c$ é a área catódica em m². O coeficiente $k_{\mathrm{O_2},g}$ tem unidade m/s e reúne a transferência efetiva **referida à concentração no gás**.

Concentração vezes coeficiente vezes área resulta em mol/s de O₂; multiplicar por $4F$ produz A. Essa conferência de unidades ajuda a perceber por que um tempo de Gurley, uma permeabilidade em m² ou um $k_La$ aquoso em s⁻¹ não podem ser colocados no lugar de $k_{\mathrm{O_2},g}$.

A perda próxima a esse limite é:

$$
\eta_{\mathrm{O_2}}=-\frac{R_gT}{4F}\ln\left(1-\frac{I}{I_{\mathrm{lim,O_2}}}\right)
$$

O resultado é em V e cresce quando a corrente se aproxima do limite de transporte. A formulação não resolve concentração local nos poros, dissolução detalhada, alagamento ou uma reserva fechada de gás. A temperatura aparece nas expressões, mas o domínio atualmente permitido continua fixo em 25 °C.

### 8.6 O fechamento elétrico que determina a corrente

$$
E_{\mathrm{oc}}=I R_{\mathrm{ext}}+I R_\Omega+\eta_a+\eta_c+\eta_S+\eta_{\mathrm{O_2}}
$$

$E_{\mathrm{oc}}$ é a tensão de circuito aberto efetiva em V. $R_{\mathrm{ext}}$ é a resistência externa em Ω. Todos os termos da soma são tensões. A corrente $I$ é a incógnita comum que deve satisfazer a igualdade e respeitar os limites de capacidade.

O cálculo procura a corrente em que a tensão restante depois das perdas coincide com a tensão na carga. Como as perdas dependem da própria corrente, não basta usar uma resistência interna fixa para todos os pontos.

Depois de encontrar $I$:

$$
V_t=I R_{\mathrm{ext}}
\qquad
P=I V_t
$$

$V_t$ é a tensão terminal em V e $P$, a potência elétrica bruta em W. A maior corrente possível não é necessariamente o ponto de maior potência. Em um curto ideal, a tensão terminal é zero; em circuito aberto, a corrente é zero. A potência entregue à carga é zero nos dois extremos.

### 8.7 Evolução da DQO na batelada

Com volume líquido constante, a massa equivalente é $m_{\mathrm{DQO}}=V_aS$, em g de equivalentes de O₂. Sua evolução é:

$$
\frac{d(V_aS)}{dt}=-\frac{8I}{F}-k_{\mathrm{comp}}V_aS-k_{\mathrm{cross}}\frac{c_{\mathrm{O_2},g}}{c_{\mathrm{O_2},g,\mathrm{ref}}}V_aS
$$

O tempo $t$ está em s; $V_a$ é o volume em m³. Todos os termos do lado direito têm unidade g/s. A expressão distingue três saídas do inventário representado:

1. **Rota eletrogênica:** $8I/F$, ligada à corrente coletada. O fator 8 é 8 g de equivalentes de O₂ por mol de elétrons.
2. **Consumo concorrente:** $k_{\mathrm{comp}}V_aS$, uma perda efetiva de substrato sem coleta correspondente de elétrons. A taxa $k_{\mathrm{comp}}$ tem unidade s⁻¹.
3. **Perda efetiva associada ao ingresso de O₂:** o último termo, com $k_{\mathrm{cross}}$ em s⁻¹. A razão de concentrações é adimensional.

A concentração de referência do gás corresponde a O₂ de 20,95%, 101325 Pa e 298,15 K. O termo de ingresso é uma aproximação de consumo de DQO, não uma solução do transporte espacial de oxigênio dissolvido. Os mecanismos concorrentes não foram separados experimentalmente nesse conjunto de parâmetros.

A cada avanço de tempo, o modelo atualiza $S$, recalcula a capacidade e resolve o ponto elétrico. Em circuito aberto, a parcela eletrogênica é zero, mas as rotas concorrentes representadas ainda podem consumir substrato.

Este é um balanço de equivalentes de oxigênio. Ele não fecha automaticamente balanços separados de carbono, nitrogênio ou de cada espécie iônica, nem calcula a evolução do pH. Essas descrições exigiriam estados e relações adicionais.

### 8.8 Carga, energia e eficiência coulômbica

$$
Q=\int I\,dt
\qquad
E_{\mathrm{el}}=\int I V_t\,dt
$$

$Q$ é a carga acumulada em C e $E_{\mathrm{el}}$, a energia elétrica em J. A corrente e a tensão podem variar; usar apenas o valor do instante inicial multiplicado pela duração é uma aproximação que precisa ser verificada.

$$
\mathrm{CE}=\frac{Q}{\Delta m_{\mathrm{DQO}}F/8}
\qquad
n_{\mathrm{O_2}}=\frac{Q}{4F}
$$

CE é a eficiência coulômbica, adimensional, calculada sobre a DQO total removida no período. $\Delta m_{\mathrm{DQO}}$ é essa massa removida em g de equivalentes de O₂. $n_{\mathrm{O_2}}$ é a quantidade em mol de oxigênio correspondente à reação catódica de quatro elétrons. Ela não representa todo consumo de O₂ que possa existir na célula real.

CE responde que fração dos equivalentes de elétrons removidos apareceu no circuito. Não é a eficiência energética global. Para avaliar energia líquida de uma montagem, ainda seria necessário considerar alimentação, bombeamento, controle, aquisição e outros consumos auxiliares, que o núcleo não calcula.

### 8.9 A relação de membrana que é apenas explicada

$$
R_m=\frac{\mathrm{ASR}_m}{A_m}
$$

$R_m$ é resistência em Ω; $\mathrm{ASR}_m$ é a resistência específica por área em Ω·m²; e $A_m$, a área correspondente em m². Essa relação ajuda a ler uma especificação nas condições em que ela foi obtida. **Ela não está acoplada como um solver completo de MFC com membrana.** Transporte iônico, seletividade, composição e passagem de reagentes continuam necessários para essa configuração.

<a id="exemplo"></a>
## 9. Um exemplo de cálculo explicado

### 9.1 Um caso numérico, com origem declarada

Os resultados abaixo foram reproduzidos diretamente com o núcleo existente durante a revisão. **São consequências de entradas assumidas; não são resultados experimentais ou uma recomendação de compra.**

O caso inicial tem 28 mL de líquido, 1000 mg O₂/L de DQO na base de acetato, áreas geométricas de 7 cm² e carga externa de 1000 Ω. Usa pH 7 e 25 °C, além das demais hipóteses do núcleo.

A massa inicial de DQO é:

$$
1000\ \mathrm{mg/L}\times0{,}028\ \mathrm{L}=28\ \mathrm{mg}=0{,}028\ \mathrm{g}
$$

A resistência equivalente do líquido é aproximadamente 85,71 Ω. As resistências eletrônicas assumidas são cerca de 0,0143 Ω no ânodo e 0,0286 Ω no cátodo; os contatos acrescentam 5 Ω. A soma ôhmica é aproximadamente **90,76 Ω**.

Ao fechar o circuito com as perdas não lineares, o ponto calculado é:

| Grandeza | Resultado aproximado | Leitura física |
|---|---:|---|
| Corrente | 0,46184 mA | Corrente que concilia carga, perdas e capacidades. |
| Tensão terminal | 0,46184 V | Queda na resistência externa de 1000 Ω. |
| Potência bruta | 0,21330 mW | Produto da corrente pela tensão. |

Confira as unidades: 0,00046184 A × 1000 Ω = 0,46184 V. Multiplicando corrente e tensão, obtém-se cerca de 0,00021330 W. O fato de a conta fechar é uma verificação necessária; não demonstra que uma célula montada forneceria esses valores.

### 9.2 Por que melhorar um material pode mudar pouco o resultado

Mantendo todas as demais entradas, foram feitos três exercícios separados:

| Alteração hipotética | Corrente, mA | Potência bruta, mW | O que o exercício ilustra |
|---|---:|---:|---|
| Caso de referência | 0,46184 | 0,21330 | Ponto inicial assumido. |
| Dobrar a condutividade iônica | 0,47749 | 0,22800 | A resistência do líquido cai à metade, mas outras perdas continuam presentes. |
| Dobrar a condutividade eletrônica anódica | 0,461842 | 0,213298 | A resistência eletrônica anódica já é muito pequena neste caso. |
| Dobrar a densidade de troca catódica efetiva | 0,48631 | 0,23650 | Reduzir uma perda cinética altera o ponto, mesmo sem mudar a soma ôhmica. |

A pequena influência da condutividade anódica neste exemplo não significa que ela seja irrelevante em toda montagem. Um eletrodo comprido, uma seção estreita ou um coletor mal posicionado poderiam mudar a participação dessa perda. O diagnóstico precisa acompanhar os valores e a geometria.

Também não se deve traduzir a última linha como “comprar o dobro de catalisador”. Dobrar $j_{0,c}$ foi uma mudança de parâmetro efetivo; ainda falta a relação experimental que ligaria uma escolha concreta de material ou fabricação a esse parâmetro.

### 9.3 O balanço de um dia

Para a batelada de 24 horas com as entradas de referência, o núcleo obtém aproximadamente:

| Parcela | Valor |
|---|---:|
| DQO inicial | 28,000 mg |
| DQO final | 17,016 mg |
| DQO removida total | 10,984 mg |
| Remoção atribuída à rota eletrogênica | 3,308 mg |
| Remoção concorrente efetiva | 5,757 mg |
| Remoção efetiva associada ao ingresso de O₂ | 1,919 mg |
| Carga acumulada | 39,896 C |
| Energia elétrica bruta | 18,422 J, aproximadamente 5,12 mWh |
| Eficiência coulômbica | 30,12% |

A soma das três rotas de remoção corresponde à diferença entre inventário inicial e final, dentro do arredondamento. O baixo resíduo do cálculo mostra consistência da contabilidade implementada. As proporções entre as rotas continuam dependentes das taxas assumidas.

Esse exercício mostra por que corrente, remoção de matéria orgânica e eficiência coulômbica precisam ser acompanhadas juntas. Remover DQO por uma rota concorrente pode melhorar a remoção total e reduzir a fração recuperada como carga elétrica.

<a id="resultados"></a>
## 10. Como ler curvas, perdas e diagnósticos

### 10.1 Curva de polarização e curva de potência

Na polarização, observe tensão no eixo vertical e corrente ou densidade de corrente no horizontal, sempre com unidades. A curva de potência usa $P=IV$. O ponto de operação é aquele associado à carga externa escolhida.

Para comparar curvas de densidade, a base de área precisa ser a mesma ou ser convertida de forma justificável. Potência por área do cátodo e corrente por área do ânodo não podem ser combinadas sem informar essa diferença. A área comprada de uma folha também não é a área exposta na célula.

O pico da curva calculada é obtido de pontos amostrados e tem a resolução dessa amostragem. A curva atual é quase estática, na DQO inicial. Não é uma medição de batelada nem uma previsão validada de envelhecimento.

Em curvas experimentais, confira velocidade de varredura, tempo de estabilização, pré-condicionamento, idade e sentido da varredura. Uma resposta que depende da história ou apresenta histerese pode não ser bem representada por uma curva estacionária única.

### 10.2 Perdas e “resistência interna”

Pergunte o que a resistência publicada ou exibida representa. Pode ser uma parcela ôhmica, uma resposta de impedância, uma inclinação em determinada região ou a resistência externa no ponto de potência máxima, conforme a convenção dos autores.

Essas grandezas não são automaticamente equivalentes. Em particular, a soma ôhmica do núcleo não inclui toda a cinética como resistores fixos. A regra de máxima transferência de potência com resistência externa igual à resistência interna vale para uma fonte equivalente linear nas condições apropriadas; não deve substituir a análise das perdas não lineares de toda MFC.

### 10.3 Sensibilidade e incerteza

A sensibilidade atual muda uma entrada por vez e recalcula a resposta. Ela responde: “Perto deste caso, o resultado muda quanto se esta entrada mudar?”. É útil para priorizar medições e verificar o mecanismo representado.

Um intervalo de confiança ou de previsão exige outra análise: incerteza de medição, variação entre reatores, parâmetros correlacionados e erros da própria formulação. A faixa obtida variando uma entrada em ±10% não é automaticamente um intervalo preditivo de 90% ou 95%.

### 10.4 Quando a resposta é indisponível

A previsão é bloqueada para duas câmaras, membrana presente, cátodo imerso ou gás controlado, alimentação contínua ou em bateladas alimentadas, outro substrato/cultura, revestimento anódico ativo ou condições de pH e temperatura fora da família implementada. Há também verificações contra números inválidos e geometrias incompatíveis.

Isso indica uma relação ou condição ainda não atendida. Não é uma demonstração de que a arquitetura real seja impossível. Uma membrana com baixa resistência, por exemplo, continua exigindo balanços de espécies que o modelo atual não resolve.

Quando um número é apresentado, observe conjuntamente sua origem, as condições permitidas e a situação da calibração. Um resultado com muitas casas decimais pode ser apenas uma solução numérica precisa de hipóteses ainda incertas.

<a id="dados"></a>
## 11. Como transformar literatura e fichas em dados utilizáveis

### 11.1 Classifique o que foi realmente observado

Uma base útil mantém separados os diferentes níveis de ensaio:

| Tipo de evidência | Pergunta que ajuda a responder | O que não demonstra sozinha |
|---|---|---|
| Caracterização do material | Como são estrutura, superfície, composição e condução? | Desempenho da célula montada. |
| Ensaio eletroquímico de componente | Como um eletrodo reage naquele eletrólito e protocolo? | A resposta de uma MFC com biofilme e transporte diferentes. |
| Ensaio de célula completa | Como a montagem operou nas condições descritas? | Efeito isolado de cada componente. |
| Simulação publicada | Quais relações foram assumidas e que consequências produziram? | Uma nova medição experimental. |
| Previsão temporal baseada em histórico | Como extrapolar uma série de um sistema observado? | Como funcionará uma combinação inédita de materiais. |
| Ficha ou oferta comercial | Qual variante é anunciada, com quais propriedades e condições de compra? | Validação experimental da formulação do Studio. |

É possível usar esses níveis de forma complementar. A dificuldade aparece quando são misturados como se todos fossem observações equivalentes do mesmo problema.

### 11.2 Preserve o contexto junto com o número

Para cada observação, devem acompanhar o valor: unidade original, transformação aplicada, fonte e localizador, método, variante, estado, condição e tipo de incerteza. Para resultados de célula, acrescente geometria, meio, temperatura, pH, alimentação, idade, preparação, carga externa e identificação das réplicas.

Em um ensaio de potencial, registre também o eletrodo de referência e seu eletrólito. “Ag/AgCl” incompleto não basta para converter sem ressalvas a outra escala, especialmente quando as soluções internas e temperaturas diferem. Tensão entre terminais e potencial de um único eletrodo permanecem distintos.

Um valor ausente fica ausente. Não é zero. Um resultado “±” sem definição não deve virar automaticamente desvio-padrão. Um limite de leitura de uma imagem não representa variação biológica nem intervalo de previsão.

### 11.3 Normalize unidades sem mudar o significado

| Dado ou conversão | Resultado | Cuidado que permanece |
|---|---|---|
| 1 mg O₂/L | 1 g O₂/m³. | A composição e a biodegradabilidade do substrato continuam necessárias. |
| 1 cm² | $10^{-4}$ m². | Informar que área está sendo usada: uma face, duas faces, abertura ou outra base. |
| 1 mS/cm | 0,1 S/m. | Condutividade depende do estado, meio e temperatura. |
| 80 mΩ·cm | $8\times10^{-4}$ Ω·m. | Preservar direção e método. O valor é um exemplo dimensional. |
| Inverso de $8\times10^{-4}$ Ω·m | 1250 S/m. | A conversão não prova adequação à montagem ou calibração. |
| 10 mΩ·cm² | $10^{-6}$ Ω·m². | Trata-se de ASR, não de resistividade volumétrica. |
| 0,5 mgPt/cm² | 0,005 kgPt/m². | A base é Pt metálico explicitamente; Pt/C é outra massa. |
| 78% de porosidade | 0,78 como fração. | Não inserir 78 em uma relação que espera fração. |

Se a resistividade é menor que um valor positivo, seu inverso é uma condutividade **maior que** o inverso desse valor. A inversão troca o sentido da desigualdade. Não transforma um limite em medida exata.

As 44 normalizações comerciais admitidas significam que a transformação dimensional foi estabelecida. Ainda é necessário verificar correspondência de condições antes de usar uma delas como parâmetro de uma equação.

### 11.4 Vá além do resumo do artigo

Os métodos permitem reconstruir a montagem e o protocolo. Os suplementos podem revelar réplicas, dados tabulados, curvas e contradições que não aparecem no resumo. As legendas ajudam a identificar bases de área e tipos de erro, mas também podem conter erros de unidade; precisam ser cruzadas com os métodos e com a coerência dimensional.

Na coleta atual, os documentos licenciados são preservados com autores, DOI, licença e hashes. O hash é uma impressão digital dos bytes: permite verificar qual arquivo foi usado. Não atesta a veracidade de um resultado científico.

Documentos comerciais foram usados para extrair fatos, condições e proveniência. Quando a redistribuição integral não foi liberada, o arquivo completo não foi publicado no repositório. A existência de um link também não significa que o documento foi integralmente recuperado ou inspecionado.

### 11.5 Evite multiplicar a mesma evidência

Uma curva com cem pontos continua sendo uma curva de um ensaio ou conjunto de ensaios. Três alimentações no mesmo reator não equivalem a três reatores independentes. Dois artigos podem reutilizar a mesma montagem, as mesmas séries ou fases sucessivas de operação.

A base registra essa proveniência para agrupar os dados relacionados. O agrupamento precisa acontecer antes de separar ajuste e avaliação, antes de normalizar variáveis com estatísticas aprendidas e antes de escolher parâmetros com base no desempenho.

O termo “big data” só será útil aqui se vier acompanhado de diversidade experimental, qualidade e relações identificáveis. Aumentar a quantidade de linhas copiadas da mesma família não resolve a falta de comparações independentes entre materiais.

<a id="estudos"></a>
## 12. O que os estudos já reunidos permitem aprender

### 12.1 O papel de cada família

| Fonte | Conteúdo relevante | Uso e limite para o Studio |
|---|---|---|
| S02 | Experimento de arquitetura monocâmara com cátodo a ar. | Precedente de arquitetura; dados de glicose não calibram automaticamente cinética de acetato. |
| S08 | Modelo integrado de processos bioeletroquímicos e populações. | Ajuda a estudar competição e balanços. Suas hipóteses e parâmetros não foram copiados como se descrevessem a família atual. |
| S09 | Previsão temporal de energia de MFC com aprendizado a partir de séries. | Ilustra outra tarefa de previsão; não demonstra relação entre uma nova configuração de materiais e sua resposta. |
| S17 | Cátodos carbonáceos, caracterização, ensaios de componente e MFCs com urina e membrana. | Mostra a importância de camada, ligante, método e rota ORR. Difere do domínio acetato/sem membrana. |
| S18 | Comparação de cátodos a ar em MFCs de 30 mL, com acetato. | Família candidata relativamente bem documentada, mas com conflitos de área e outros dados pendentes. |
| S19 | Remoção de nitrato e alteração de arquitetura em reatores relacionados. | Ajuda a compreender competição por matéria e elétrons. O domínio com nitrato não é o caso acetato/O₂ sem esses competidores. |
| S20–S28 | Fichas e ofertas de fabricantes/fornecedores. | Caracterização e comparação comercial; não são novos ensaios independentes de MFC. |
| S29 | Resposta de três reatores a meios sintético e real, com tabelas de picos e tempos. | Acrescenta dados por reator, preservando relação conservadora com S18; não é holdout independente de materiais. |

Os demais itens do índice ajudam a localizar caracterização de superfícies, modelos de biofilme, estudos de membranas e conjuntos de dados. O estado de acesso de cada um precisa ser considerado. O índice completo está na seção 16.

### 12.2 O que uma comparação de cátodos realmente compara em S18

S18 descreve uma montagem de 30 mL, ânodo de feltro, cátodo a ar e resistência de 1 kΩ durante os ciclos. O ensaio é reportado a 21 ± 2 °C e pH de 7,2 ± 0,2 nos métodos. Esses valores já diferem do caso inicial do núcleo, de 28 mL, 25 °C e pH 7.

No braço CC, o cátodo combina tecido W1S1011 com uma camada de Pt/Vulcan-C de fração nominal de Pt de 60%. No braço CP, o suporte é H23C6 e os autores preparam uma camada com Pt de 10% em carbono ativado e Nafion. Portanto, mudam suporte, suporte do catalisador, formulação e preparação da camada. Não se pode atribuir toda a diferença de desempenho apenas a “tecido versus papel”.

A mesma carga de metal também não implica a mesma massa total de camada. Como conta didática, se a carga fosse 0,5 mgPt/cm² e as frações de 60% e 10% estivessem na mesma base seca, seriam necessários aproximadamente 0,833 e 5 mgPt/C por cm², respectivamente, antes de acrescentar o ligante. Essa conta explica o cuidado com a base de massa; não mede espessura ou porosidade nem resolve o estado de fornecimento do pó.

As espessuras de camada catalítica de cerca de 3 e 96 µm aparecem em caracterização por microscopia após preparação e desidratação. Não devem ser usadas como espessuras hidratadas em operação. A igualdade entre um produto comercial atual e o lote dos artigos continua apenas uma correspondência nominal quando o SKU/lote final não foi declarado.

### 12.3 O problema de área que impede uma conversão simples

O ânodo de 2 × 3 cm tem 6 cm² de uma face. Alguns pares corrente/densidade publicados em S18 implicam aproximadamente 12 cm². Duas faces molhadas são uma hipótese possível, mas a expressão usada para a área no texto não resolve inequivocamente a questão. S29 também não fornece a declaração numérica que encerre essa ambiguidade.

Como $I=jA$, uma mudança por fator dois na base de área muda a corrente absoluta reconstruída pelo mesmo fator. O problema não deve ser “resolvido” escolhendo o denominador que faz uma curva ajustar melhor.

Os treze pontos digitalizados de S18 permanecem em densidade, com área numérica pendente e limites de leitura de aproximadamente ±15,7 mV e ±1,75 mA/m². Esses limites dizem respeito à digitalização da imagem. A variabilidade entre reatores é outra informação.

### 12.4 Os dados adicionais de S29

O artigo e seu suplemento descrevem três reatores biológicos e um controle estéril. As tabelas apresentam 21 linhas de alimentação com meio sintético, SWW, e 18 com meio real, RWW. As 39 linhas, combinadas com os três reatores, formam 117 registros reator–alimentação. Há 115 pares medidos de corrente máxima e tempo até esse máximo; dois pares estão ausentes por falha de equipamento.

| Meio | Pares medidos | DQO tabulada, mg/L | Corrente máxima tabulada, mA/m² | Tempo até o pico, h |
|---|---:|---:|---:|---:|
| Sintético, SWW | 62 | 108–1071 | 44–261 | 1,1–26,8 |
| Real, RWW | 53 | 238–732 | 1–115 | 1,9–7,2 |

São faixas descritivas do conjunto, sem ajuste de modelo. As condições e faixas de concentração diferem; a tabela não demonstra que um meio tenha determinado efeito isolado sobre o outro. A coluna de DBO foi calculada pelos autores a partir da relação com DQO e não é uma medição independente repetida em cada linha.

Os mesmos reatores foram usados sucessivamente. O histórico mostra formação do biofilme, fase com acetato e posterior mudança para SWW e RWW, com substituição de cátodos nas transições. Meio, idade e manutenção estão associados. A ordem das linhas publicadas não permite inventar datas de cada alimentação.

S18 e S29 foram agrupados conservadoramente porque compartilham laboratório, construção, origem do enriquecimento e histórico compatível. A identidade dos reatores individuais entre os artigos permanece sem comprovação. A temperatura operacional não foi explicitada em S29 e não foi herdada silenciosamente de S18.

Esses dados ajudam a estudar resposta e repetibilidade de uma família. Não contêm variação controlada de materiais comerciais e não fornecem séries individuais completas de corrente/DQO no tempo. Por isso, ainda não calibram diretamente o núcleo atual.

### 12.5 Outras pendências que devem acompanhar a interpretação

- **S18:** há conflito entre texto e figuras de eficiência coulômbica e entre unidades de concentração em legendas e métodos. A CE conflitante não foi admitida como alvo de ajuste. A replicação das curvas de polarização não deve ser inferida da replicação de outros ensaios do artigo.
- **S17:** os mesmos reatores receberam tratamentos em sequência. O efeito de tratamento pode estar associado à ordem e à idade. O tempo de residência reportado também difere do quociente simples volume/vazão. Uma equação publicada de resistividade tem problema dimensional a revisar e não foi copiada para o núcleo.
- **S19:** a divisão do reator não cria dois volumes iguais ao volume total original; o total permanece 30 mL. A descrição da carga de Pt/C não encerra a distinção entre massa de Pt e de Pt/C. Nitrato compete por recursos e modifica a interpretação da eficiência.

Preservar uma contradição não inutiliza automaticamente o estudo. Indica que certas relações podem ser usadas como contexto e que determinados números ainda não devem sustentar uma conversão ou calibração.

<a id="validacao"></a>
## 13. Calibração, validação e confiança na previsão

### 13.1 O que significa calibrar

Calibrar é usar dados apropriados para estimar os parâmetros de uma formulação dentro de um domínio definido. A comparação precisa usar a mesma grandeza, unidade, geometria e condição representada. Antes de ajustar cinética, convém conhecer as perdas e dimensões que podem ser medidas separadamente.

Uma dificuldade central é a **identificabilidade**: parâmetros diferentes podem compensar uns aos outros e produzir curvas parecidas. Se aumentar uma perda e reduzir outra gera quase a mesma curva, a qualidade visual do ajuste não permite concluir que ambos os mecanismos foram identificados.

Por isso, uma única curva ou um único pico de potência raramente sustenta a determinação simultânea de todos os parâmetros de ânodo, cátodo, transporte e competição. Medidas de componente e de célula, geometrias conhecidas, réplicas e séries pareadas ajudam a restringir essas compensações.

### 13.2 O que significa verificar o cálculo

Verificação pergunta se as equações escolhidas estão sendo resolvidas de forma coerente: unidades, conservação, sinais, casos-limite e estabilidade numérica. É possível verificar perfeitamente um modelo que ainda representa mal uma célula real.

No núcleo, a corrente é buscada respeitando o limite mais restritivo e conferindo o fechamento de tensão. A batelada usa passos adaptativos para limitar a perda de inventário por passo. Reduzir o teto de tempo permite verificar convergência: o resultado deve se aproximar de um valor estável conforme a discretização é refinada.

Na evolução registrada em outubro, houve verificações de massa, carga, consumo catódico de O₂ e energia. Os resíduos muito pequenos são evidência de consistência das contas implementadas, não uma medida de erro preditivo diante de um experimento.

### 13.3 O que significa validar

Validar exige comparar previsões com dados que não foram usados para escolher ou ajustar a relação avaliada. Para investigar novos materiais ou configurações, é especialmente importante reservar estudos, reatores e famílias experimentais inteiros.

Se pontos vizinhos de uma curva forem divididos entre ajuste e teste, o teste continuará muito próximo da informação já vista. Se dois artigos usam o mesmo reator ou um histórico contínuo, dividir pelos títulos dos artigos pode produzir o mesmo problema. O agrupamento por proveniência busca impedir esse vazamento de informação.

Na base atual, a conexão entre S18 e S29 é um exemplo concreto. O programa de avaliação preserva grupos relacionados antes de particionar. Isso não prova, por si só, que todas as ligações entre estudos tenham sido recuperadas ou que os domínios sejam comparáveis; a revisão científica continua necessária.

### 13.4 Como expressar erro e incerteza

O **erro absoluto médio**, MAE, informa o tamanho médio do erro absoluto na unidade da variável. O **RMSE**, raiz do erro quadrático médio, dá peso maior a erros grandes. O **viés** informa uma tendência média de superestimar ou subestimar. Corrente, tensão, energia e remoção devem ter suas próprias avaliações.

Um intervalo preditivo também precisa de avaliação. Para um intervalo nominal de 90%, por exemplo, verifica-se que fração das observações externas caiu dentro dele e qual sua largura. Uma faixa enorme pode cobrir quase tudo e ser pouco útil para decidir.

A incerteza pode vir de medição, diferenças entre reatores, identificação incompleta de parâmetros e estrutura do modelo. Ela não deve ser reduzida automaticamente só porque há muitos pontos correlacionados. O domínio de aplicabilidade informa em quais materiais, geometrias e condições há sustentação para interpretar o erro medido.

Os erros experimentais do Studio continuam **não determinados**. O valor ausente, registrado como `null`, significa que a avaliação ainda não existe; não significa erro zero. O núcleo não possui intervalos calibrados.

### 13.5 O que os testes já demonstraram

O registro mais recente da rodada científica de outubro informa 74 testes aprovados: 32 relacionados ao código JavaScript e 42 em Python, incluindo os testes anteriores, integridade de dados e conversões. A conferência de tipos e a montagem da aplicação também passaram. Contagens menores presentes em registros antigos correspondem a etapas anteriores do trabalho.

Foram verificados casos como ausência de substrato/O₂, circuito aberto/curto, seções eletrônicas independentes, efeitos de condutividade, balanços e separação por proveniência. A curadoria comercial acrescentou verificações de ASR versus resistividade, bases de massa, preços por pack e manutenção de faltantes. Nada disso substitui a avaliação experimental descrita acima.

<a id="aprendizado"></a>
## 14. Roteiro de aprendizado e exercícios

A proposta é aprender por relações e contas pequenas, começando pelo que se conecta à engenharia de materiais. Cada etapa abaixo pode produzir uma página de anotações ou uma planilha simples. Não é necessário implementar o programa para acompanhar o raciocínio.

| Etapa de estudo | Atividade | O que você deve conseguir explicar ao final |
|---|---|---|
| 1. Desenhar o sistema | Desenhar uma monocâmara a ar e uma célula com dois meios. Marcar volumes e fronteiras. | Quantos inventários existem e por onde passam matéria e carga. |
| 2. Fechar unidades | Converter volume, área, condutividade e DQO; calcular massa inicial. | Por que uma conversão pode alterar um resultado por fator 10, 100 ou 1000. |
| 3. Estudar condução | Calcular separadamente resistência do líquido, do eletrodo e dos contatos. | Que caminho domina nas condições escolhidas. |
| 4. Relacionar material e montagem | Escolher uma ficha de feltro/papel e identificar direção, tratamento e compressão. | Por que uma propriedade da ficha pode não corresponder ao eletrodo instalado. |
| 5. Entender metabolismo mínimo | Identificar doador, receptor de elétrons, rotas concorrentes e papel do inóculo em um artigo. | Como DQO pode diminuir sem a carga elétrica equivalente ser coletada. |
| 6. Ler uma curva | Identificar eixos, base de área, protocolo, corrente, tensão e potência. | Por que pico, ponto de operação e energia acumulada são coisas diferentes. |
| 7. Examinar saturação | Calcular $S/(K_S+S)$ para três concentrações. | Por que mais alimento pode ter efeito progressivamente menor. |
| 8. Estudar um ensaio completo | Reconstruir S18 e comparar com o caso inicial do núcleo. | Quais condições coincidem e quais impedem chamar o cálculo de reprodução do artigo. |
| 9. Comparar dados relacionados | Acompanhar os mesmos reatores em S29, mantendo as fases agrupadas. | Por que quantidade de linhas não é quantidade de experimentos independentes. |
| 10. Formular uma hipótese verificável | Escolher uma alteração de material e escrever propriedades, relação física, dados e critério de avaliação. | O que seria necessário para aceitar ou rejeitar a hipótese. |

### Exercício A — inventário e capacidade

Para 28 mL e 1000 mg O₂/L, obtenha 28 mg de DQO inicial. Depois considere $K_S=100$ mg O₂/L e calcule o fator de saturação para $S=10$, 100 e 1000 mg O₂/L.

Os resultados são aproximadamente **0,091; 0,500; 0,909**. A constante não é uma concentração abaixo da qual a reação obrigatoriamente para. Ela define a forma da relação de saturação escolhida.

### Exercício B — qual área está sendo usada?

Um feltro tem uma face de 2 × 3 cm. Calcule a densidade de corrente de 120 µA usando 6 cm²; depois use 12 cm².

Você encontrará **200 e 100 mA/m²**, respectivamente. A corrente física do exemplo é a mesma; mudou a base de normalização. Isso explica por que a questão de área S18/S29 precisa ser resolvida antes de reconstruir corrente absoluta ou comparar parâmetros.

### Exercício C — qual melhoria merece ser medida?

No exemplo da seção 9, compare os 85,71 Ω do líquido com cerca de 0,0143 Ω do ânodo. Antes de procurar um material de condutividade ainda maior, pergunte qual parte do orçamento de perdas poderia ser reduzida e como comprovar essa redução.

O exercício não determina uma compra. Ele orienta a pergunta experimental: condutividade, geometria do percurso, contato ou cinética? Uma montagem diferente pode mudar essa prioridade.

### Exercício D — a mesma carga de metal

Partindo de uma carga de 0,5 mgPt/cm², calcule a massa de catalisador seco necessária se o pó tem 10% de Pt. O resultado ideal é **5 mgPt/C por cm²**, sem ligante. Agora liste o que falta para transformar essa massa em espessura de camada: densidade aparente, porosidade, formulação, deposição e estado de secagem/hidratação.

Esse passo é uma boa ligação entre conhecimento de processamento e interpretação eletroquímica. A formulação e a montagem passam a ser variáveis observáveis, em vez de serem escondidas no nome do material.

### Exercício E — elaborar uma ficha de hipótese

Escreva: “A mudança de ______ pode alterar ______ porque ______. Vou procurar/medir ______ mantendo ______ comparável. Aceitarei a explicação se ______, e registrarei como limitação ______”.

Por exemplo, a posição de um coletor pode alterar o percurso eletrônico. Para sustentar a explicação, seriam necessários geometria, direção da condução e resistência da montagem, além de uma comparação de célula com condições controladas. Uma curva melhor sem esses dados pode revelar uma diferença real, mas não identifica automaticamente sua causa.

<a id="continuidade"></a>
## 15. Próximas decisões científicas

O foco permanece na base necessária à seleção de materiais comerciais. Uma sequência coerente para aprofundar o trabalho é:

1. **Conseguir comparações de produtos e montagens equivalentes.** Priorizar estudos em que variante, preparação, geometria e condições estejam descritas junto com curvas e réplicas. Registrar quando vários fatores mudam simultaneamente.
2. **Fechar as bases que bloqueiam contas.** Resolver área S18/S29, bases de massa e unidades ambíguas; manter o texto original e a justificativa de qualquer correção.
3. **Relacionar caracterização às condições reais.** Procurar condução direcional, compressão, hidratação, contato, preparação e transporte do componente final. A coleta deve continuar conectada às onze etapas.
4. **Separar o que pode ser identificado.** Medir ou obter na literatura as parcelas independentes antes de ajustar parâmetros efetivos da célula inteira. Verificar compensações e sensibilidade.
5. **Reservar uma família externa comparável.** Somente então avaliar erro, conservação, incerteza e domínio para configurações que não participaram do ajuste.
6. **Completar a comparação econômica.** Confirmar variante, quantidade, entrega, custo total e aproveitamento para a montagem, além do preço da folha.

Esse é um roteiro de investigação. As relações ainda não sustentadas continuam hipóteses ou registros. Não é uma declaração de que novos módulos, modelos de membrana ou transportes espaciais tenham sido implementados.

<a id="referencias"></a>
## 16. Referências e localização dos materiais de apoio

### 16.1 Como usar as referências

As fontes S01–S29 mantêm os identificadores usados no projeto. A tabela abaixo indica o papel de cada uma, sem promover uma referência de plataforma ou uma oferta comercial à condição de evidência experimental. O estado detalhado de recuperação fica nos manifestos e no inventário preservado nos anexos.

Para começar a estudar as relações, use S08 como exemplo de estrutura de modelo; S18 e S29 para reconstrução de métodos; S17 para distinguir caracterização, componente e célula; e S06 para transporte de íons e pH. Leia sempre as condições antes de aproveitar um número.

### 16.2 Fontes do projeto

| ID | Referência ou fornecedor | Papel na base |
|---|---|---|
| S01 | [Impact of Surface Properties of Porous SiOC-Based Materials on the Performance of Geobacter Biofilm Anodes](https://chemistry-europe.onlinelibrary.wiley.com/doi/full/10.1002/celc.202001568) | Superfície de materiais e bioânodo; recuperação integral atual pendente. |
| S02 | [Electricity Generation Using an Air-Cathode Single Chamber Microbial Fuel Cell in the Presence and Absence of a Proton Exchange Membrane](https://pure.psu.edu/en/publications/electricity-generation-using-an-air-cathode-single-chamber-microb/) | Arquitetura monocâmara a ar; substrato diferente do núcleo. |
| S03 | [Evaluation of Electrode and Solution Area-Based Resistances Enables Quantitative Comparisons of Factors Impacting Microbial Fuel Cell Performance](https://pure.psu.edu/en/publications/evaluation-of-electrode-and-solution-area-based-resistances-enabl/) | Comparação de resistências; recuperação integral pendente. |
| S04 | [Conduction-based modeling of the biofilm anode of a microbial fuel cell](https://pubmed.ncbi.nlm.nih.gov/17570714/) | Modelo de condução em biofilme. |
| S05 | [A computational model for biofilm-based microbial fuel cells](https://pubmed.ncbi.nlm.nih.gov/17537478/) | Modelo computacional de biofilme. |
| S06 | [Effects of membrane cation transport on pH and microbial fuel cell performance](https://research.wur.nl/en/publications/effects-of-membrane-cation-transport-on-ph-and-microbial-fuel-cel/) | Transporte de cátions e pH; estudo experimental. |
| S07 | [Enhanced activated carbon cathode performance for microbial fuel cell by blending carbon black](https://pure.psu.edu/en/publications/enhanced-activated-carbon-cathode-performance-for-microbial-fuel-/) | Cátodo de carbono ativado e negro de carbono. |
| S08 | [An Integrated Mathematical Model of Microbial Fuel Cell Processes: Bioelectrochemical and Microbiologic Aspects](https://www.mdpi.com/2227-9717/5/4/73) | Modelo integrado; documento completo recuperado. |
| S09 | [Time-series forecasting of microbial fuel cell energy generation using deep learning](https://www.frontiersin.org/journals/computer-science/articles/10.3389/fcomp.2024.1447745/full) | Previsão temporal; documento completo recuperado. |
| S10 | [Microbial fuel cell data set](https://data.mendeley.com/datasets/gydpxvj8gp/1) | Conjunto de dados; arquivos brutos sem recuperação concluída. |
| S11 | [[DATASET 8] - MICROBIAL FUEL CELLS (MFCS), GrowBot](https://zenodo.org/records/8096219) | Conjunto de dados indexado; verificar conteúdo e licença para cada uso. |
| S12 | [Artificial neural network simulating microbial fuel cells with different membrane materials and electrode configurations](https://uwe-repository.worktribe.com/output/1491788/artificial-neural-network-simulating-microbial-fuel-cells-with-different-membrane-materials-and-electrode-configurations) | Rede neural em outras configurações; não é calibração do núcleo. |
| S13 | [Architectural design of hierarchically meso-macroporous carbon for microbial fuel cell anodes](https://pubs.rsc.org/en/content/articlehtml/2016/ra/c5ra26420k) | Arquitetura porosa de ânodo; verificar condições e acesso. |
| S14 | [Electrochemical modeling of microbial fuel cells performance at different operating and structural conditions](https://pubmed.ncbi.nlm.nih.gov/31677000/) | Modelo eletroquímico de outras condições. |
| S15 | [Sites: Data and connections](https://learn.chatgpt.com/docs/sites/data-and-connections) | Referência histórica de plataforma; não é evidência científica. |
| S16 | [A two-population bio-electrochemical model of a microbial fuel cell](https://publications.polymtl.ca/17762/) | Modelo bioeletroquímico de duas populações. |
| S17 | [Carbon-Based Air-Breathing Cathodes for Microbial Fuel Cells](https://www.mdpi.com/2073-4344/6/9/127) | Cátodos carbonáceos; completo recuperado. |
| S18 | [Impact of Air-Cathodes on Operational Stability of Single-Chamber Microbial Fuel Cell Biosensors for Wastewater Monitoring](https://www.mdpi.com/1996-1073/17/14/3574) | Cátodos a ar e estabilidade; artigo e suplemento completos. |
| S19 | [Insight into a single-chamber air-cathode microbial fuel cell for nitrate removal and ecological roles](https://www.frontiersin.org/journals/bioengineering-and-biotechnology/articles/10.3389/fbioe.2024.1397294/full) | Nitrato e alterações de arquitetura; artigo completo. |
| S20 | [CeTech W1S1011 manufacturer product data](https://www.ce-tech.com.tw/data/W1S1011) | Fabricante de suporte W1S1011; propriedades comerciais. |
| S21 | [Fuel Cells Etc — GDE W1S1011, Pt/Vulcan, carga nominal de 0,5 mg/cm²](https://fuelcellsetc.com/products/carbon-cloth-05-ptc-gas-diffusion-electrode-w1s1011) | Fabricante de GDE completo; base de massa comercial ainda a confirmar. |
| S22 | [Fuel Cell Store Freudenberg H23C6 GDL listing](https://www.fuelcellstore.com/freudenberg-h2315-i2-c6) | Oferta/ficha H23C6; unidade de resistência ambígua. |
| S23 | [Torayca TGP-H carbon paper manufacturer data](https://www.cf-composites.toray/products/electrode/pdf/carbon_paper.pdf) | Fabricante Toray; dados direcionais representativos. |
| S24 | [Fuel Cell Store Toray 060 PTFE value pack](https://www.fuelcellstore.com/toray-carbon-paper-060-pack) | Oferta de pack Toray tratado; preço e quantidade. |
| S25 | [SIGRACET gas diffusion layer white paper](https://www.sglcarbon.com/pdf/SIGRACET-Whitepaper.pdf) | Fabricante SGL; GDL e condições de compressão. |
| S26 | [SIGRACELL battery felts TDS BF.01 04/2019](https://www.sglcarbon.com/pdf/SGL-Datasheet-SIGRACELL-Battery-Felts-EN.pdf) | Fabricante SGL; feltros virgens da ficha de 2019. |
| S27 | [Redox Flow SGL felt offer variants](https://redox-flow.com/product/sgl-carbon-felt-electrodes/) | Fornecedor; variantes de feltro e ofertas datadas. |
| S28 | [CXM-200S / CMI-7000S manufacturer technical specifications](https://ionexchangemembranes.com/cmi-7000-cation-exchange-membranes-technical-specifications/) | Fabricante CMI/CXM; condição de medição e pré-hidratação. |
| S29 | [Resilience of anodic biofilm in microbial fuel cell biosensor for BOD monitoring of urban wastewater](https://www.nature.com/articles/s41545-024-00350-5) | Resposta SWW/RWW; artigo e suplemento completos; relacionado a S18. |

### 16.3 Apoio conceitual desta revisão

- [Logan et al. — Microbial Fuel Cells: Methodology and Technology (2006)](https://doi.org/10.1021/es0605016): referência metodológica para organizar a leitura de ensaios de MFC. Nesta revisão foram conferidos identificação e resumo; não se afirma uma nova leitura integral desse artigo.
- [IUPAC — potencial de eletrodo de equilíbrio](https://goldbook.iupac.org/terms/view/09064), [equação de Nernst](https://goldbook.iupac.org/terms/view/09068) e [sobrepotencial](https://goldbook.iupac.org/terms/view/O04358): apoio terminológico. A consulta recuperou enunciados indexados; as tentativas de abertura direta de Nernst/sobrepotencial retornaram acesso negado. Não foi recuperado o compêndio completo.

Essas referências de apoio foram usadas para a explicação. Não foram incorporadas como novos dados de calibração ao corpus 0.3.0.

### 16.4 Onde ficam os dados que sustentam o guia

| Local no repositório | O que procurar |
|---|---|
| [Base científica original](../science/legacy-v0.1/) | Catálogo de 110 propriedades, fontes e contratos iniciais. |
| [Interfaces e arquivos originais](../research/legacy-ui/) | HTMLs, SVGs, previews e ZIP inicial preservados. |
| [Corpus v0.2](../research/corpus-v0.2/) | Cinco artigos, suplemento S18, manifestos, observações e curva digitalizada. |
| [Corpus v0.3](../research/corpus-v0.3/) | Artigo e suplemento S29, dados por reator e relatório de admissão. |
| [Materiais comerciais](../research/materials-v0.1/) | Variantes, propriedades, ofertas, vínculos experimentais e limites de recuperação. |
| [Núcleo de cálculo](../science/mfc-engine.mjs) | Relações e hipóteses do modelo 0.2.0. A leitura de código é opcional para acompanhar este guia. |
| [Avaliação por proveniência](../science/validation.mjs) | Regras de agrupamento e cálculo de métricas quando houver pares experimentais admissíveis. |
| [Curadoria dimensional](../science/material_data.py) | Conversões e restrições que impedem transferência automática de propriedades inadequadas. |

A [aplicação publicada](https://mfc-studio.igorbolognani768385.chatgpt.site) mantém acesso privado. Os registros anexos documentam a publicação e as verificações realizadas em outubro, sem afirmar uma nova conferência de disponibilidade nesta revisão editorial.

<a id="historico"></a>
## 17. História do projeto, preservação e limites de acesso

### 17.1 De onde veio o trabalho

A recuperação inicial encontrou nove arquivos na pasta “Intelligent UI - GPT”: dois HTMLs de interface v0.5, dois SVGs, quatro previews e o ZIP `MFC_Studio_Base_Cientifica_v0.1.zip`. Os HTMLs eram cópias idênticas entre si, assim como os SVGs. O ZIP, identificado originalmente como `libfile_d95e340b73a08191b725993f7c5acf99`, tinha 32.115 bytes e oito membros, todos extraídos.

O pacote inicial continha 110 propriedades propostas, dezesseis fontes de tipos diferentes, sete registros candidatos e dezenove testes de contratos. Esses números descrevem o ponto de partida. Não eram uma base aprovada de treinamento nem evidência de validação preditiva.

A interface antiga contemplava MFC/MEC e cenários em memória. As decisões posteriores estabeleceram MFC independente, montagem guiada, persistência e acesso ChatGPT. Elas prevalecem sobre propostas antigas de integração com METREV completo ou MCP. O preview antigo de METREV não foi alterado.

Também foram encontrados dois documentos de proposta de junho e uma captura textual de um preview antigo. Seus textos foram analisados na recuperação anterior. O documento longo tinha muitas repetições de parágrafos; não foi tratado como um relatório experimental completo de quarenta páginas. Esses materiais históricos permanecem preservados e não substituem resultados experimentais.

### 17.2 Por que havia contagens diferentes nos documentos

| Momento registrado | O que havia sido verificado |
|---|---|
| Base v0.1 | 110 propriedades propostas, 16 fontes, 7 candidatos e 19 testes de contratos. |
| Primeira implementação v0.2 | Núcleo exploratório e corpus com 19 fontes, 5 artigos e 1 suplemento. Relatórios iniciais mencionam 28 ou 29 testes conforme a etapa de desenvolvimento. |
| Conferência de documentos completos | 30 testes JavaScript, 19 legados e 8 de integridade científica, totalizando 57. |
| Limpeza da configuração de origem | Quatro testes adicionais de higienização, totalizando 61. |
| Curadoria do corpus 0.3.0 | 29 fontes, 6 artigos, 2 suplementos e 74 testes na rodada científica de outubro. |

O banco local da primeira auditoria tinha seis documentos e 35 trechos. A auditoria posterior de produção tinha oito documentos e 49 trechos. Esses registros não são retratos simultâneos. O histórico e os hashes permitem identificar a que versão cada resultado se refere.

### 17.3 O episódio da chave de API copiada de uma editora

Uma configuração de Google Maps do site da Frontiers foi copiada junto com os HTMLs de S09 e S19. Ela não era usada pela aplicação MFC Studio. Foram removidos scripts e configurações executáveis das cópias armazenadas, preservando PDFs, texto científico e observações. A versão 0.2.1 do corpus registrou essa higienização sem mudar suas contagens científicas.

Também foi reescrito o histórico alcançável da `main` para retirar aquelas cópias. A auditoria de então examinou 225 objetos de conteúdo em um clone novo e não encontrou o padrão de chave procurado. Nenhuma chave foi chamada, revogada ou rotacionada, conforme a decisão do usuário. A checagem foi incorporada à aquisição e às verificações automáticas.

Esse resultado não certificou ausência em caches, clones externos ou versões históricas guardadas pela hospedagem. As ferramentas disponíveis não permitiram eliminar versões históricas do Sites ou confirmar/encerrar o estado administrativo do alerta de segurança do GitHub. Não foi afirmado que ninguém tivesse copiado a sequência.

O aprendizado para a base científica é preservar o conteúdo e a proveniência necessários à pesquisa sem carregar configurações executáveis de terceiros. Não se deve reproduzir uma credencial no guia para documentar sua remoção.

### 17.4 O que foi acessível e o que não foi

**Conversas:** a recuperação retornou trechos herdados e resumos, não todos os textos integrais das sessões de origem. Este guia não afirma uma leitura integral de conversas que não foram fornecidas. As decisões explícitas posteriores foram preservadas.

**Artigos:** seis arquivos completos e dois suplementos foram recuperados. A inspeção científica anterior se concentrou em corpo principal, métodos, resultados, tabelas ou figuras específicas conforme a fonte. Recuperar o arquivo completo não significa ter revisado manualmente toda imagem ou referência. Nesta revisão editorial foram lidos integralmente os onze arquivos de `docs`, além dos arquivos de apoio identificados no inventário de consolidação.

**Falhas de recuperação:** S01 teve bloqueio de download; S03 devolveu um arquivo de desafio inválido como PDF e não foi contado como documento completo; os dados brutos de S10 continuavam sem recuperação. Licenças específicas de conjuntos externos ligados a S09 não estavam esclarecidas e os ZIPs correspondentes não foram redistribuídos. Isso não demonstra inexistência dos dados.

**Fichas e complementos:** os downloads brutos dos PDFs SGL falharam, mas texto e páginas renderizadas estavam acessíveis. Um link curto de Nafion redirecionou a uma categoria e foi rejeitado como ficha específica. Suplemento S19, preços atuais de Pt/AC e catálogo atual Phychemi não foram recuperados na rodada de curadoria. Não foram inventadas disponibilidade ou caracterização para preencher essas ausências.

**Auditoria do banco publicado:** hashes e metadados dos oito documentos conferiam com a base, e os ativos informados estavam presentes. O leitor do banco truncou um trecho de 10.000 caracteres para 2035 caracteres; por essa ferramenta não foi possível reconstruir independentemente o texto integral armazenado. Essa limitação não deve ser confundida com ausência dos PDFs completos recuperados. Os registros originais detalham a extensão da verificação.

**Interface e acesso:** houve inspeção de desenvolvimento da página inicial, do Studio, da seleção de componentes e do bloqueio de topologias não suportadas. Não foi declarada nova verificação visual mobile ou do fluxo completo de login e cenário por visitante na última rodada científica. O acesso de serviço a cenários privados retornou 401 e a página de teste de desenvolvimento retornou 404 em produção.

### 17.5 Como esta consolidação preserva a memória

Os cinco textos anteriores foram reconciliados nesta explicação, com distinção entre etapas históricas. Os seis arquivos JSON foram incorporados integralmente aos anexos recolhíveis. O inventário adicional registra nome, tamanho e hash dos onze originais e a revisão de origem. O histórico do Git permite recuperar os arquivos anteriores à reorganização.

Os documentos científicos, dados e cenários não foram alterados por esta revisão. Os pequenos utilitários que produzem relatórios foram adaptados para atualizar seu anexo no guia, preservando o texto de leitura. Assim, uma execução posterior não precisa recriar arquivos avulsos em `docs`.

<a id="glossario"></a>
## 18. Glossário de consulta

| Termo | Significado neste guia |
|---|---|
| Ânodo | Eletrodo onde ocorre a oxidação; recebe elétrons da atividade anódica e os conduz ao circuito. |
| Cátodo | Eletrodo onde ocorre a redução; na família estudada, recebe elétrons para reduzir O₂. |
| Anólito / católito | Meios líquidos anódico e catódico, que podem ser compartilhados conforme a arquitetura. |
| Biofilme | Comunidade aderida e sua matriz, com atividade e transporte dependentes das condições e da história. |
| Consórcio misto | Conjunto de microrganismos, sem a hipótese de uma única espécie responsável por toda a resposta. |
| Transferência extracelular de elétrons | Transferência entre a atividade celular e um receptor fora da célula, como o eletrodo. |
| DQO / COD | Demanda química de oxigênio; base de equivalentes de O₂ para a oxidação da amostra. COD é a sigla em inglês. |
| DBO / BOD | Demanda bioquímica de oxigênio em protocolo definido. BOD é a sigla em inglês. |
| Eletrólito | Meio que conduz carga por movimento de íons. |
| Tampão | Sistema químico que resiste à variação de pH dentro de uma capacidade e faixa. |
| Atividade química | Grandeza efetiva usada em relações termodinâmicas; pode diferir da concentração nominal. |
| Potencial de eletrodo | Potencial referido a uma referência definida. Não é a tensão terminal da célula inteira. |
| Circuito aberto / OCV | Condição sem corrente externa; OCV é a tensão de circuito aberto. |
| Sobrepotencial | Desvio de potencial associado à reação sob corrente em relação ao equilíbrio; no núcleo, as perdas efetivas têm convenções próprias. |
| Perda ôhmica | Queda de tensão associada à condução elétrica e representada por corrente vezes resistência. |
| Corrente de troca efetiva | Parâmetro de uma relação de ativação; sua identificação depende da formulação e das condições. |
| ORR | Reação de redução de oxigênio. A rota adotada pelo núcleo é de quatro elétrons. |
| MPL | Camada microporosa de um suporte de eletrodo; composição e fabricação afetam interfaces e transporte. |
| GDL / GDE | GDL é uma camada de difusão de gás; GDE é um eletrodo de difusão de gás, que inclui organização reativa adicional. A ficha deve esclarecer o acabamento. |
| PTFE | Polímero usado, entre outras funções, em tratamentos hidrofóbicos e ligantes. |
| Ionômero | Polímero com grupos iônicos, usado em algumas camadas para contato iônico e ligação; não equivale automaticamente a uma membrana separadora. |
| ASR | Resistência específica por área, em Ω·m² ou unidade equivalente. |
| BET / ECSA | Área específica por adsorção / área eletroquimicamente ativa segundo método. Não são automaticamente a área geométrica. |
| In-plane / through-plane | Medição ao longo do plano / através da espessura. |
| Gurley | Ensaio de passagem de gás sob protocolo definido, frequentemente informado como tempo. |
| Crossover | Passagem de uma espécie para uma região indesejada; no núcleo, há uma perda efetiva de DQO associada ao ingresso de O₂. |
| Eficiência coulômbica / CE | Fração dos equivalentes de elétrons removidos que foi coletada no circuito, segundo a base adotada. |
| Parâmetro efetivo | Número que reúne a resposta de fenômenos na escala de representação escolhida. |
| Relação constitutiva | Regra quantitativa que liga propriedades e condições a um comportamento. |
| Proveniência | Origem e história de um dado, incluindo relações entre estudo, reator, amostra e tratamento. |
| Réplica biológica | Unidade experimental biológica distinta; repetição de leitura da mesma unidade não cria outra réplica. |
| Identificabilidade | Possibilidade de distinguir os valores e efeitos dos parâmetros a partir dos dados disponíveis. |
| Calibração | Estimativa de parâmetros usando dados apropriados e um domínio definido. |
| Verificação / validação | Conferência da resolução e consistência das equações / avaliação de previsões diante de dados externos adequados. |
| Holdout | Conjunto reservado para avaliação; aqui, precisa preservar grupos experimentais relacionados. |
| Domínio de aplicabilidade | Materiais, montagens e condições para os quais há sustentação da interpretação preditiva. |
| Corpus | Conjunto organizado de documentos, fontes e dados. |
| Hash | Impressão digital de bytes para conferir identidade de um arquivo ou conteúdo. |
| D1 / R2 | Serviços usados para guardar registros/textos e arquivos da aplicação, respectivamente. |
| Idempotência | Repetir a aplicação da mesma versão de dados não cria duplicatas nem outra versão disfarçada. |

<a id="anexos"></a>
## 19. Anexos de parâmetros e rastreabilidade

Os anexos abaixo permitem conferir números, arquivos e execução sem interromper a leitura científica. Valores iniciais são assumidos; registros históricos mantêm as datas e versões originais. Os blocos JSON são dados de auditoria, não instruções para o leitor.

### 19.1 Entradas numéricas do núcleo

<details>
<summary>Mostrar os 39 campos, unidades e valores iniciais assumidos</summary>

Todos os números desta tabela são hipóteses do caso inicial, com origem experimental não atribuída. A função da entrada não demonstra sua calibração.

| Grandeza / símbolo | Unidade | Valor inicial | Papel no caso atual |
|---|---|---:|---|
| Volume líquido anódico — Vₐ | m³ | 2,8 × 10^-5 | Entrada de cálculo da relação correspondente; valor assumido. |
| Volume de católito independente — V𝚌 | m³ | 0 | Registrado; volume independente não aplicável ao caso a ar. |
| Volume de gás controlado — Vg | m³ | 0 | Registrado; volume fechado não aplicável à fronteira de ar ambiente. |
| DQO inicial biodegradável na base de acetato — S₀ | g O₂/m³ | 1000 | Entrada de cálculo da relação correspondente; valor assumido. |
| Condutividade iônica hidratada — κ | S/m | 0,5 | Entrada de cálculo da relação correspondente; valor assumido. |
| Percurso iônico efetivo — Lᵢ | m | 0,03 | Entrada de cálculo da relação correspondente; valor assumido. |
| Seção de condução iônica — Aᵢ | m² | 0,0007 | Entrada de cálculo da relação correspondente; valor assumido. |
| Área geométrica anódica — Aₐ | m² | 0,0007 | Entrada de cálculo da relação correspondente; valor assumido. |
| Área geométrica catódica — A𝚌 | m² | 0,0007 | Entrada de cálculo da relação correspondente; valor assumido. |
| Condutividade eletrônica anódica direcional — σₐ | S/m | 3000 | Entrada de cálculo da relação correspondente; valor assumido. |
| Percurso eletrônico anódico — Lₑ,ₐ | m | 0,003 | Entrada de cálculo da relação correspondente; valor assumido. |
| Seção eletrônica anódica — Aₑ,ₐ | m² | 7 × 10^-5 | Entrada de cálculo da relação correspondente; valor assumido. |
| Condutividade eletrônica catódica direcional — σ𝚌 | S/m | 1500 | Entrada de cálculo da relação correspondente; valor assumido. |
| Percurso eletrônico catódico — Lₑ,𝚌 | m | 0,003 | Entrada de cálculo da relação correspondente; valor assumido. |
| Seção eletrônica catódica — Aₑ,𝚌 | m² | 7 × 10^-5 | Entrada de cálculo da relação correspondente; valor assumido. |
| Resistência de contatos — Rcont | Ω | 5 | Entrada de cálculo da relação correspondente; valor assumido. |
| Resistência de carga — Rext | Ω | 1000 | Entrada de cálculo da relação correspondente; valor assumido. |
| Tensão de circuito aberto efetiva — Eoc | V de célula | 0,7 | Entrada de cálculo da relação correspondente; valor assumido. |
| Capacidade de corrente anódica em substrato saturante — jmax,ₐ | A/m² geométrico | 5 | Entrada de cálculo da relação correspondente; valor assumido. |
| Constante de meia saturação de DQO — Kₛ | g O₂/m³ | 100 | Entrada de cálculo da relação correspondente; valor assumido. |
| Densidade de troca anódica efetiva — j₀,ₐ | A/m² geométrico | 0,1 | Entrada de cálculo da relação correspondente; valor assumido. |
| Escala de ativação anódica efetiva — bₐ | V | 0,05 | Entrada de cálculo da relação correspondente; valor assumido. |
| Escala de perda por capacidade de substrato — bₛ | V | 0,025 | Entrada de cálculo da relação correspondente; valor assumido. |
| Densidade de troca catódica efetiva — j₀,𝚌 | A/m² geométrico | 0,1 | Entrada de cálculo da relação correspondente; valor assumido. |
| Escala de ativação ORR efetiva — b𝚌 | V | 0,05 | Entrada de cálculo da relação correspondente; valor assumido. |
| Transferência efetiva de O₂ referida ao gás ambiente — kO₂,g | m/s | 1 × 10^-6 | Entrada de cálculo da relação correspondente; valor assumido. |
| Fração molar de O₂ no ambiente — yO₂ | mol/mol | 0,2095 | Entrada de cálculo da relação correspondente; valor assumido. |
| Pressão do ar ambiente — p | Pa | 101325 | Entrada de cálculo da relação correspondente; valor assumido. |
| Temperatura mantida — T | K | 298,15 | Condição fixa: 298,15 K; dependência com temperatura não validada. |
| Taxa efetiva de consumo não eletrogênico — kcomp | s⁻¹ | 3 × 10^-6 | Entrada de cálculo da relação correspondente; valor assumido. |
| Taxa efetiva de perda de DQO por ingresso de O₂ — kcross | s⁻¹ | 1 × 10^-6 | Entrada de cálculo da relação correspondente; valor assumido. |
| Duração da batelada — Δt | s | 86400 | Duração solicitada da batelada. |
| Passo de saída e teto de integração — Δtmax | s | 300 | Controle numérico: teto do passo e intervalo de saída. |
| pH tamponado informado — pH | 1 | 7 | Registrado e condicionado a pH 7; dinâmica não resolvida. |
| Espessura hidratada do biofilme — δbf | m | 0,00012 | Registrado; não determina crescimento/capacidade no núcleo. |
| Carga de catalisador catódico informada — mcat/A | kg/m² | 0,01 | Registrado; não determina automaticamente a cinética. |
| Área de membrana informada — Am | m² | 0,0007 | Registrado; membrana presente fica fora da família calculada. |
| ASR hidratada informada — ASRm | Ω m² | 0,001 | Registrado; transporte membranar não resolvido. |
| Tensão externa aplicada — Vbias | V | 0 | Deve ser zero para o caso MFC; valor diferente é rejeitado. |

</details>

### 19.2 Notas para manutenção e reprodução

O arquivo de equações oferece cálculo do ponto de operação, curva de polarização, batelada e sensibilidade. As funções principais se chamam `solve`, `polarizationCurve`, `simulateBatch` e `sensitivity`. `PARAMETER_SPECS`, `OUTPUT_SPECS`, `EQUATIONS` e `MODEL_DECLARATION` registram nomes, unidades, papéis e hipóteses. Esses nomes são uma localização para quem mantiver o programa; não são pré-requisito para estudar o guia.

A solução elétrica usa uma mudança de variável próxima ao limite de corrente para manter o fechamento numérico verificável. A batelada usa Euler explícito adaptativo com perda máxima de 2% do inventário por passo. Se restar menos de $10^{-14}$ do inventário inicial, esse residual pode ser mantido explicitamente até o término, sem virar carga elétrica.

As proteções de cálculo incluem duração máxima de sete dias, até 5000 intervalos de saída, até 100000 passos internos e verificações de magnitude. A tensão efetiva é limitada a 2 V como proteção computacional. Esses limites não são um domínio experimental validado. O passo de saída/teto de integração deve estar entre 1 e 3600 s.

O banco guarda cenários e versões por identidade ChatGPT. Execuções recebem versão e hash. PDFs e documentos seguem listas de arquivos conhecidos e verificação de identidade; apenas documentos com redistribuição permitida são publicados integralmente. A página de teste `/qa` é de desenvolvimento. Esses mecanismos preservam o trabalho e o acesso, sem demonstrar precisão científica.

Para manutenção, os comandos existentes incluem `pnpm run check`, `pnpm test` e `pnpm run build`; as rotinas de curadoria estão em `scripts/build-materials.py`, `scripts/audit-s29.py` e `scripts/build-corpus.py`. Os testes Python ficam em `tests`, `scripts`, `science/legacy-v0.1` e `research/corpus-v0.2`. A atualização de relatórios de auditoria passa a substituir somente o bloco correspondente neste guia.

Quando uma auditoria futura for atualizada, sua versão precisa ser comparada à data e ao escopo declarados no texto principal. A rotina preserva a explicação; ela não reescreve automaticamente a interpretação científica ou as contagens do corpo do guia.

Na conferência desta reorganização, a checagem automática também detectou uma diferença de formato dos arquivos compactados entre ambientes Python. A geração passou a explicitar o nível de compactação e o marcador do cabeçalho usados no corpus publicado. Os seis arquivos comprimidos e seus hashes foram preservados integralmente; a correção não altera observações, equações ou parâmetros. Há testes específicos de reprodução e preservação de conteúdo para esse caso. As mudanças de comportamento entre versões estão descritas na [documentação de gzip do Python](https://docs.python.org/3/library/gzip.html#gzip.compress).

### 19.3 Mapa dos onze documentos consolidados

| Arquivo anterior | Onde seu conteúdo foi integrado |
|---|---|
| `CONTEXT_RECONCILIATION.md` | Seções 1–2 e 17; inventário original abaixo. |
| `DATA_CURATION_2026-10-26.md` | Seções 6, 11–13 e 15–17. |
| `EXECUTION_STATUS.md` | Seções 2, 13 e 17; registros de execução abaixo. |
| `MODEL_V02.md` | Seções 4–10, 13 e anexo de parâmetros/limites numéricos. |
| `SOURCE_SANITIZATION.md` | Seção 17.3; auditoria de histórico abaixo. |
| `context-inventory.json` | Inventário integral no anexo e síntese na seção 17. |
| `database-local-verification.json` | Registro local integral; data/versão distinguidas na seção 17. |
| `github-clean-history-verification.json` | Registro integral; limites da limpeza na seção 17.3. |
| `hosted-verification.json` | Registro de produção integral; síntese nas seções 2 e 17. |
| `production-v03-audit.json` | Registro de auditoria integral e seus limites na seção 17. |
| `verification.json` | Registro numérico integral; exemplo explicado na seção 9. |

### 19.4 Registros originais e inventários

Os seis primeiros registros mantêm integralmente os dados JSON dos arquivos anteriores. Assim, um número histórico pode ser conferido sem ser confundido com a situação mais recente. O inventário de consolidação identifica os arquivos lidos e seus hashes antes da reorganização.

<details>
<summary>Inventário original dos materiais e limites da recuperação</summary>

<!-- audit:context-inventory.json:start -->
```json
{
  "date": "2026-10-25",
  "project": "Intelligent UI - GPT",
  "folder_listing_complete": true,
  "next_cursor": null,
  "original_files": [
    {
      "name": "METREV_Cell_Studio_UX_v0.5(1).html",
      "size_bytes": 69571,
      "sha256": "20bfe1d89fb8e3f25e9df6db7c20bf7a33040e1b1e6a70150bbc2a508692e87f",
      "status": "complete_text_read; duplicate_confirmed_by_sha256"
    },
    {
      "name": "METREV_Cell_Studio_UX_v0.5.html",
      "size_bytes": 69571,
      "sha256": "20bfe1d89fb8e3f25e9df6db7c20bf7a33040e1b1e6a70150bbc2a508692e87f",
      "status": "complete_text_read"
    },
    {
      "name": "METREV_Cell_Studio_v05_browser_overview.png",
      "size_bytes": 175663,
      "sha256": "3ea9608db463e77d31ef7e07aee4a4b9e9223bcd29caaa21f24087f49f333953",
      "status": "visually_inspected"
    },
    {
      "name": "METREV_MiniLab_SVG_v0.5(1).svg",
      "size_bytes": 7260,
      "sha256": "190de64c33050a25d438ebceba5372adf5553e4a533c8f09ff6eac4faf95b176",
      "status": "complete_text_read; duplicate_confirmed_by_sha256"
    },
    {
      "name": "METREV_MiniLab_SVG_v0.5.svg",
      "size_bytes": 7260,
      "sha256": "190de64c33050a25d438ebceba5372adf5553e4a533c8f09ff6eac4faf95b176",
      "status": "complete_text_read"
    },
    {
      "name": "METREV_MiniLab_SVG_v0.5_preview.png",
      "size_bytes": 62215,
      "sha256": "1da362ef111fff52026c715cab44f48fd2c181ba144a9845df5e0353da38150a",
      "status": "visually_inspected"
    },
    {
      "name": "METREV_v05_desktop_preview.png",
      "size_bytes": 303711,
      "sha256": "003c5f5348cf250ee1e5335183829ce8eaf3cddeaefb99a3c59c800264cb8279",
      "status": "visually_inspected"
    },
    {
      "name": "METREV_v05_mobile_preview.png",
      "size_bytes": 249859,
      "sha256": "a3d5c2d0af44175f4bb7ede397852978491eeb25b41c19c6bfd2231c45da5113",
      "status": "visually_inspected"
    },
    {
      "name": "MFC_Studio_Base_Cientifica_v0.1.zip",
      "size_bytes": 32115,
      "sha256": "f6beda61f2456e695ae9ede583ec213e86be13f4853cda49a2a11d08f14e1d89",
      "status": "archive_extracted_all_members"
    }
  ],
  "zip_members": [
    {
      "path": "MFC_STUDIO_BASE_CIENTIFICA.md",
      "size_bytes": 24345,
      "sha256": "04740a01f053741a9069291a966325edf17a46b28be218a1995b36ef447ebbcf",
      "status": "text_and_data_reviewed"
    },
    {
      "path": "build_registry.py",
      "size_bytes": 20560,
      "sha256": "39ce2a5fd6626294c5fe43b659be6423d4236a989eab64ce5387121405390fbc",
      "status": "text_and_data_reviewed"
    },
    {
      "path": "evidence.py",
      "size_bytes": 8391,
      "sha256": "b7a57f416b8b16db4bbe89420df99d7938e1c5b35ec9680f7ead1e6b646caf97",
      "status": "text_and_data_reviewed"
    },
    {
      "path": "evidence_seed.jsonl",
      "size_bytes": 8930,
      "sha256": "f978dc1d1316ac079c3020bf20afef9cdf0b9253ff51c1c56118267ef1ab8a29",
      "status": "text_and_data_reviewed"
    },
    {
      "path": "parameter_catalog.json",
      "size_bytes": 36050,
      "sha256": "9d85d7f5690f399b5bc4b25588e9035c764b6af8eb12c3f6578bc7fabe1cc8d7",
      "status": "text_and_data_reviewed"
    },
    {
      "path": "sources.json",
      "size_bytes": 8462,
      "sha256": "ee44b981dd723e24fa0a8f7399b3d12d1a7eae401f2812cd128a2a4c229e63c8",
      "status": "text_and_data_reviewed"
    },
    {
      "path": "test_evidence.py",
      "size_bytes": 5314,
      "sha256": "38159b074721d14f9389b06f76ac515e725d095c9154d7f6ba551dcc1241ec5b",
      "status": "text_and_data_reviewed"
    },
    {
      "path": "validation.json",
      "size_bytes": 1668,
      "sha256": "e214ddb38a224134f03e062ed9a38273ecb75f7e10c86abd71a0285e092d5ff1",
      "status": "text_and_data_reviewed"
    }
  ],
  "conversation_access": "Inherited excerpts and personal-context summaries only. Full source and linked session transcripts were not returned. No claim of complete transcript reading.",
  "version_discovery": "Recursive project folder listing plus exact/prefix filename searches. No later matching version returned; non-indexed material cannot be ruled out.",
  "additional_historical_documents": [
    {
      "name": "Expanded_Research_Proposal_MFC_MEC_Digital_Twin_40Page_Draft.docx",
      "sha256": "82d39f4e13f261ea06a7a7ded3d0c6247afc99b17fb707d8135a579f170877ea",
      "paragraphs": 171,
      "unique_paragraphs": 56,
      "images": 0,
      "status": "all paragraphs and tables extracted; all unique text reviewed; repeated identical paragraphs counted",
      "priority": "historical proposal, superseded by current MFC-only scope"
    },
    {
      "name": "Research_Brief_MFC_MEC_AI_Digital_Twin_SciSpace.docx",
      "sha256": "02c859a56115c266799aed25a0bdb7d7d674422a16c0c68f682eb0d667d2fee3",
      "paragraphs": 32,
      "unique_paragraphs": 32,
      "images": 0,
      "status": "all paragraphs and tables extracted; all unique text reviewed; repeated identical paragraphs counted",
      "priority": "historical proposal, superseded by current MFC-only scope"
    }
  ],
  "increment_2026_10_26": {
    "user_decisions": [
      "select commercial materials",
      "literature and datasheets",
      "cost and availability"
    ],
    "files": [
      {
        "path": "research/materials-v0.1/EXPERIMENTAL_LINK_REVIEW.md",
        "size_bytes": 8374,
        "sha256": "5a2abf51a90c20079cad00ae2a5d1b21956ae78701a06dc2bb73187d378728df"
      },
      {
        "path": "research/materials-v0.1/catalog.json",
        "size_bytes": 90028,
        "sha256": "afd907705b3a4cbea0a4f33256ad46ac2fbbb472e665f81cdfceff021b55a7c0"
      },
      {
        "path": "research/materials-v0.1/curation-report.json",
        "size_bytes": 413,
        "sha256": "1a2dc6576c66a2e63391b33670bec0dbf4edf366d5e80a84c4aff02dd874d404"
      },
      {
        "path": "research/materials-v0.1/retrievals.json",
        "size_bytes": 4119,
        "sha256": "f66385a1279c830de4a416d5ec26fe87b62d5f63271a8ccf3e1756ee372f211f"
      },
      {
        "path": "research/corpus-v0.3/S29_feeds.json",
        "size_bytes": 42618,
        "sha256": "90d81cb16b77505ffb9504d7bf5d668d02af334b0c01bb711d4330d2a02baa6e"
      },
      {
        "path": "research/corpus-v0.3/S29_observations.json",
        "size_bytes": 261783,
        "sha256": "ae06e2859bf782628978eda7f5e292b65cbd24882ae492675fff849556def597"
      },
      {
        "path": "research/corpus-v0.3/S29_source.json",
        "size_bytes": 5531,
        "sha256": "c5fa7660fa55c756d3fc37a5ebbfa3c29dbde0b28edc190fbe184a314d4b4368"
      },
      {
        "path": "research/corpus-v0.3/S29_table1_table2.csv",
        "size_bytes": 21207,
        "sha256": "3d222eaa898b4c165bb2d20ca0c51fa974763babb30734cdf568cd3da6c963f0"
      },
      {
        "path": "research/corpus-v0.3/curation-report.json",
        "size_bytes": 2415,
        "sha256": "5d6c38e4df1ea2d0087b4426e26dfe7598b2e38bb5154e3001acb68ccb083ede"
      },
      {
        "path": "research/corpus-v0.3/documents/NPJ2024.html",
        "size_bytes": 504690,
        "sha256": "1b3344e048ad93284bb5a7676540c0cbb41aed23c6b65d9bae3ab66ff42c7e80"
      },
      {
        "path": "research/corpus-v0.3/documents/NPJ2024.pdf",
        "size_bytes": 1654760,
        "sha256": "b2f2703391497238a512c1d24dd24384a248a55b418ed03ed356e545b8b43587"
      },
      {
        "path": "research/corpus-v0.3/documents/NPJ2024.txt",
        "size_bytes": 88227,
        "sha256": "0c9e6bc22c53eee3193bc791552d369a05126a0aaed8b2f73cce75f254165ae0"
      },
      {
        "path": "research/corpus-v0.3/documents/NPJ2024_pdf.txt",
        "size_bytes": 96568,
        "sha256": "123fa5f0f1b9fe9c4fc847ddd22668b6412b7199944594b2bda8b2e0ca8d3239"
      },
      {
        "path": "research/corpus-v0.3/documents/NPJ2024_supplement.pdf",
        "size_bytes": 1284902,
        "sha256": "2354f24b61bca58ffccd26b34316054b0af24148d66b4c50479fd8654fba06a0"
      },
      {
        "path": "research/corpus-v0.3/documents/NPJ2024_supplement.txt",
        "size_bytes": 33523,
        "sha256": "7785348263bfbd3fd478ba3cab70585f346423a2d22924ec5c5f905df6c2377b"
      },
      {
        "path": "research/corpus-v0.3/documents/NPJ2024_supplement_p5.png",
        "size_bytes": 376510,
        "sha256": "b8f6ace5856b65027e42b63aec3e7cc6cbc13b45cc93c1de26b6018d0faa0a16"
      },
      {
        "path": "research/corpus-v0.3/documents_manifest.json",
        "size_bytes": 6995,
        "sha256": "b2caed0628c913fdd275e516417fa53b830aa760573eb33d4114c622bb8ea1fa"
      },
      {
        "path": "research/corpus-v0.3/extract_s29.py",
        "size_bytes": 9309,
        "sha256": "36955dc8a7b44e0227c5b0416d2c04d066ac16ba8fd4182bd6cccf7272a0f70f"
      },
      {
        "path": "research/corpus-v0.3/fulltext/S29_main.txt",
        "size_bytes": 96724,
        "sha256": "771a55351beb45ca0ae8def30b040ffb92bca733f272ba0d32541308ed72160d"
      },
      {
        "path": "research/corpus-v0.3/fulltext/S29_main.txt.gz",
        "size_bytes": 30981,
        "sha256": "91a2b68430a3168b4bfcfd7eacd31064be8412945884662230d13e297cd98e8f"
      },
      {
        "path": "research/corpus-v0.3/fulltext/S29_supplement.txt",
        "size_bytes": 33679,
        "sha256": "81bf21edd7f0f534b0678293566b5063796bd41153e6e17b5bad37aedbab2f9e"
      },
      {
        "path": "research/corpus-v0.3/fulltext/S29_supplement.txt.gz",
        "size_bytes": 8522,
        "sha256": "f07673cae9af69dc5ba109592fb3909fb3ccef6a124ae7d108b0249b3d1656e5"
      }
    ],
    "inspection_scope": "All structured tables processed; S29Methods and supplementTables1/2 inspected, with all table cells cross-checked; selected scientific figures inspected. Manufacturer numerical tables/footnotes and all31offer options inspected. No claim of manual reading of every figure/reference or microbiome table.",
    "access_limits": [
      "SGL raw PDFsHTTP504; web text/rendered pages available",
      "Nature web open blocked redirect; downloaded full licensed files available",
      "Nafion short listing redirected to category and rejected",
      "S19supplement, currentPt/ACprices and currentPhychemi products not recovered",
      "Prior full conversation transcripts remain unavailable; inherited excerpts/summaries only"
    ],
    "public_documents_policy": "OnlyS29CCBY4fullfiles added; manufacturer full files not redistributed."
  }
}
```
<!-- audit:context-inventory.json:end -->

</details>

<details>
<summary>Verificação numérica inicial do modelo, de 25/10/2026</summary>

<!-- audit:verification.json:start -->
```json
{
  "date": "2026-10-25",
  "model_version": "mfc-kernel/0.2.0",
  "scope": "software_physical_verification_only",
  "tests_passed": 28,
  "predictor_trained": false,
  "experimental_validation": false,
  "experimental_mae": null,
  "experimental_rmse": null,
  "defaults_kind": "assumed_not_calibrated",
  "default_point": {
    "I_A": 0.000461839525154772,
    "V_V": 0.461839525154772,
    "P_W": 0.00021329574699518528,
    "R_ohm": 90.75714285714285,
    "residual_V": 0
  },
  "batch_balances": {
    "initial_COD_g": 0.028,
    "final_COD_g": 0.017015954380520587,
    "removed_COD_g": 0.010984045619479414,
    "electrogenic_COD_g": 0.0033079115326646222,
    "competing_COD_g": 0.005757100565111072,
    "crossover_COD_g": 0.0019190335217036906,
    "charge_C": 39.89561785659057,
    "energy_J": 18.42199475117296,
    "cathode_O2_mol": 0.00010337223539576944,
    "coulombic_efficiency": 0.30115602640963923,
    "mass_residual_g": 2.8406096919120216e-17,
    "charge_residual_C": 2.842170943040401e-14,
    "oxygen_charge_residual_C": 2.842170943040401e-14,
    "max_voltage_residual_V": 1.6653345369377348e-16
  },
  "convergence": {
    "steps_s": [
      300,
      150,
      75
    ],
    "final_COD_g": [
      0.017015954380520587,
      0.0170187152181724,
      0.01702009491570749
    ],
    "energy_J": [
      18.42199475117296,
      18.421984066884807,
      18.421978726040873
    ]
  }
}
```
<!-- audit:verification.json:end -->

</details>

<details>
<summary>Auditoria histórica do banco local, anterior ao corpus 0.3.0</summary>

<!-- audit:database-local-verification.json:start -->
```json
{
  "audit": "local_D1_real_database",
  "counts": {
    "stages": 11,
    "properties": 110,
    "sources": 19,
    "source_stages": 62,
    "documents": 6,
    "document_chunks": 35,
    "experiments": 6,
    "evidence_records": 32,
    "observations": 86,
    "curves": 1,
    "curve_points": 13
  },
  "foreign_key_violations": 0,
  "complete_text_reconstruction_verified": 6,
  "training_eligible_records": 0,
  "seed_sha256": "0fae773d265f9457c56601512d7aa7b282e88d3b44039a9293f5c586d12db845",
  "experimental_predictive_validation": false
}
```
<!-- audit:database-local-verification.json:end -->

</details>

<details>
<summary>Auditoria da limpeza do histórico em 26/10/2026</summary>

<!-- audit:github-clean-history-verification.json:start -->
```json
{
  "scope": "all blobs reachable from all refs in fresh public GitHub clone",
  "blobs_scanned": 225,
  "matches": [],
  "clean": true,
  "commit_count": 4,
  "verified_head": "91f22d7bb71c9a6e657dc56a5a6bc6f4fe6183c2",
  "verified_at": "2026-10-26",
  "ci_run_url": "https://github.com/igorbolognani/MFCStudio---Intelligent-UI/actions/runs/40380732068",
  "ci_conclusion": "success",
  "excludes": "Unreachable GitHub objects, caches, third-party clones and historical Sites versions."
}
```
<!-- audit:github-clean-history-verification.json:end -->

</details>

<details>
<summary>Aplicação do corpus 0.3.0 e presença dos documentos na produção</summary>

<!-- audit:hosted-verification.json:start -->
```json
{
  "url": "https://mfc-studio.igorbolognani768385.chatgpt.site",
  "publication_audit": "shared_corpus_and_access_boundary",
  "seed": {
    "alreadyApplied": false,
    "version": "mfc-corpus/0.3.0",
    "report": {
      "properties_proposed": 110,
      "sources": 29,
      "complete_main_articles": 6,
      "supplements": 2,
      "records": 198,
      "observations": 397,
      "numeric_observations": 393,
      "missing_observation_cells": 4,
      "digitized_curve_points": 13,
      "material_variants": 16,
      "commercial_offer_snapshots": 31,
      "S29_reactor_feed_records": 117,
      "S29_measured_response_pairs": 115,
      "S29_missing_response_pairs": 2,
      "training_eligible_records": 0,
      "predictor_trained": false,
      "experimental_error_metrics": null,
      "all_11_stages_mapped": true,
      "independent_validation_pending": true
    }
  },
  "pdf_uploads": [
    {
      "id": "S08-pdf",
      "alreadyStored": true
    },
    {
      "id": "S09-pdf",
      "alreadyStored": true
    },
    {
      "id": "S17-pdf",
      "alreadyStored": true
    },
    {
      "id": "S18-pdf",
      "alreadyStored": true
    },
    {
      "id": "S19-pdf",
      "alreadyStored": true
    },
    {
      "id": "S18-supplement-pdf",
      "alreadyStored": true
    },
    {
      "id": "S29-pdf",
      "sha256": "b2f2703391497238a512c1d24dd24384a248a55b418ed03ed356e545b8b43587",
      "stored": true
    },
    {
      "id": "S29-supplement-pdf",
      "sha256": "2354f24b61bca58ffccd26b34316054b0af24148d66b4c50479fd8654fba06a0",
      "stored": true
    }
  ],
  "database": {
    "version": "mfc-corpus/0.3.0",
    "counts": {
      "stages": 11,
      "properties": 110,
      "sources": 29,
      "source_stages": 86,
      "documents": 8,
      "document_chunks": 49,
      "experiments": 15,
      "evidence_records": 198,
      "observations": 397,
      "curves": 1,
      "curve_points": 13
    },
    "training_eligible_records": 0,
    "seed_applied": true,
    "pdf_assets": [
      {
        "id": "S08-pdf",
        "present": true
      },
      {
        "id": "S09-pdf",
        "present": true
      },
      {
        "id": "S17-pdf",
        "present": true
      },
      {
        "id": "S18-pdf",
        "present": true
      },
      {
        "id": "S19-pdf",
        "present": true
      },
      {
        "id": "S18-supplement-pdf",
        "present": true
      },
      {
        "id": "S29-pdf",
        "present": true
      },
      {
        "id": "S29-supplement-pdf",
        "present": true
      }
    ],
    "embedded_assets": [
      {
        "id": "S08-html",
        "present": true,
        "sha256_matches": true
      },
      {
        "id": "S09-html",
        "present": true,
        "sha256_matches": true
      },
      {
        "id": "S17-html",
        "present": true,
        "sha256_matches": true
      },
      {
        "id": "S18-html",
        "present": true,
        "sha256_matches": true
      },
      {
        "id": "S19-html",
        "present": true,
        "sha256_matches": true
      },
      {
        "id": "S29-html",
        "present": true,
        "sha256_matches": true
      }
    ],
    "content_sha256": "a0a246631a0d64887c432ed09e8cb94f3e620cdc52b0471b48aa4e40d548c100"
  },
  "service_cannot_impersonate_visitor": true,
  "development_QA_not_public": true,
  "landing_available": true,
  "idempotency_recheck": {
    "alreadyApplied": true,
    "version": "mfc-corpus/0.3.0"
  }
}
```
<!-- audit:hosted-verification.json:end -->

</details>

<details>
<summary>Conferência de metadados e limite de leitura do banco publicado</summary>

<!-- audit:production-v03-audit.json:start -->
```json
{
  "document_count": 8,
  "document_metadata_hashes_match_seed": true,
  "document_metadata_truncated": false,
  "fulltext_database_reconstruction_performed": false,
  "fulltext_database_reconstruction_limit": "Sites database row reader truncated the first10000-character chunk to2035characters; full database text was not independently reconstructed.",
  "local_original_files_and_generated_text_hashes_verified": true,
  "project_id": "appgprj_6ade38dd6f4481919a62ea9e66ab76c8",
  "verified_runtime_version_id": "appgprj_6ade38dd6f4481919a62ea9e66ab76c8~appgver_42daf4f9ea04819195a9d51f1a45877a",
  "github_implementation_commit": "5dde96ec44ff31db43026d92e0e08b3e93b9d5ac",
  "ci": {
    "status": "completed",
    "conclusion": "success",
    "url": "https://github.com/igorbolognani/MFCStudio---Intelligent-UI/actions/runs/40419765285"
  },
  "scope": "Corpus0.3.0 data/backend verification; no new visual QA or predictive accuracy claim"
}
```
<!-- audit:production-v03-audit.json:end -->

</details>

<details>
<summary>Inventário desta consolidação: onze arquivos lidos e conferidos</summary>

<!-- audit:consolidation-inventory.json:start -->
```json
{
  "revision_date": "2026-11-02",
  "source_commit": "b6a75fed55fa5c22cabbc12e2e2514de199d126d",
  "original_documents": [
    {
      "path": "docs/CONTEXT_RECONCILIATION.md",
      "bytes": 5164,
      "sha256": "ac4e714e1a517bdd7cc1728d90b10be5974a2e3301c6e06a23ec5e6826e72a5c",
      "reading_scope": "complete_file_received_and_read"
    },
    {
      "path": "docs/DATA_CURATION_2026-10-26.md",
      "bytes": 7388,
      "sha256": "ded5df9fad47992337368ccaddb209a597d42731b3f74d1b970e4e663d41d307",
      "reading_scope": "complete_file_received_and_read"
    },
    {
      "path": "docs/EXECUTION_STATUS.md",
      "bytes": 5756,
      "sha256": "d1623156881001996b455e0643f5d4ad7b95373d07a09fc31e4ca343e8325351",
      "reading_scope": "complete_file_received_and_read"
    },
    {
      "path": "docs/MODEL_V02.md",
      "bytes": 7187,
      "sha256": "d488945f43223c6d614167ea10d24a4bcc36203f4db745ee3bdf4294c7c8ddbd",
      "reading_scope": "complete_file_received_and_read"
    },
    {
      "path": "docs/SOURCE_SANITIZATION.md",
      "bytes": 3155,
      "sha256": "faf7475fb9fbd5895314f0fcaa0cb77f035a18e6c69c9c3afdf4ddfea2e46e45",
      "reading_scope": "complete_file_received_and_read"
    },
    {
      "path": "docs/context-inventory.json",
      "bytes": 10381,
      "sha256": "cc24b834f46ed8ef7807d64d8692562ccb3079199c2b46474ead64b2e3e5b34a",
      "reading_scope": "complete_file_received_and_read"
    },
    {
      "path": "docs/database-local-verification.json",
      "bytes": 548,
      "sha256": "38b035d6caff8032434aa96eea67a9cc05b90aaa2b603ec37ce21f4dd551214e",
      "reading_scope": "complete_file_received_and_read"
    },
    {
      "path": "docs/github-clean-history-verification.json",
      "bytes": 490,
      "sha256": "c49eb55168d564d624b19b8d2c12964fcc963fd5aefb346c7a4e8775c44eb940",
      "reading_scope": "complete_file_received_and_read"
    },
    {
      "path": "docs/hosted-verification.json",
      "bytes": 3507,
      "sha256": "697f2d958525ff8e1e369adb3d78c15150de3847ff876a1125e0496eba1e4605",
      "reading_scope": "complete_file_received_and_read"
    },
    {
      "path": "docs/production-v03-audit.json",
      "bytes": 947,
      "sha256": "ff81157b479553373f16d2724d6c36254e044b4f2f8442868ced713fad30221c",
      "reading_scope": "complete_file_received_and_read"
    },
    {
      "path": "docs/verification.json",
      "bytes": 1415,
      "sha256": "4b13ebff34790991f9bcaefd5381c983633105e35bd496d559e6c7e496d5e0c6",
      "reading_scope": "complete_file_received_and_read"
    }
  ],
  "supporting_files_reviewed": [
    "README.md",
    "science/mfc-engine.mjs",
    "science/validation.mjs",
    "science/material_data.py",
    "scripts/build-materials.py",
    "scripts/seed-hosted-corpus.py",
    "scripts/verify-database.py",
    "research/corpus-v0.2/RESEARCH_STATUS.md",
    "research/corpus-v0.3/curation-report.json",
    "research/materials-v0.1/curation-report.json"
  ],
  "scope_limits": [
    "All11docsreadcompletely; existing conversation excerpts and prior inventories used. No claim to retrieve missing full past transcripts.",
    "Scientific PDFs and images retain the previous per-source inspection limits; this editorial revision does not claim new complete visual inspection of all figures.",
    "Current code reviewed on2026-11-02; production audits in the originals describe2026-10-25/26, not a new live verification on2026-11-02.",
    "IUPACdirectpagesNernst/overpotentialHTTP403; indexeddefinitionsavailable. Logan2006bibliographicrecord/abstractconsulted, notfulltext."
  ]
}
```
<!-- audit:consolidation-inventory.json:end -->

</details>
