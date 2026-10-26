# Materiais comerciais ↔ evidência experimental

Consultado em 26/10/2026. Nenhum código, fonte ou dado da aplicação foi alterado. O material abaixo é candidato a integração, sem ajuste ou treinamento.

## Conclusão operacional

O vínculo mais completo disponível é **feltro de carbono comercial + GDE completo Pt/C–W1S1011**, como em S18/S29. Mesmo nesse caso, o artigo identifica grade, fornecedor e formulação, mas não o SKU/lote final do GDE. O SKU atual corresponde à formulação nominal; a equivalência histórica permanece inferência documentada. O GDL W1S1011 nu e o GDE Pt/C comprado são produtos distintos.

## Identidade e estágio

| Artigo / componente | Identificação encontrada | Vínculo comercial verificado | Limite |
|---|---|---|---|
| S18/S29 cátodo completo | W1S1011, FuelCell Store, 0,5 mgPt/cm², 60% Pt/Vulcan-C | [Fuel Cells Etc GDE](https://fuelcellsetc.com/products/carbon-cloth-05-ptc-gas-diffusion-electrode-w1s1011), SKU11060059 para5×5cm; MPL410µm; Nafion postcoat | SKU final/lote não constam dos artigos; correlação por formulação nominal |
| S18 suporte catódico CC | W1S1011, MPL | [CeTech fabricante](https://www.ce-tech.com.tw/data/W1S1011); [distribuidor](https://www.fuelcellstore.com/carbon-cloth-mpl-w1s1011), SKU23070001 | Suporte não inclui Pt/C; suas curvas H₂/ar a60°C não são resultadosMFC |
| S18 suporte CP | FreudenbergH23C6 com MPL, comprado FuelCell Store | [Produto](https://www.fuelcellstore.com/freudenberg-h2315-i2-c6), SKU31070005 | Recebe coating manual adicional; não é um GDE pronto equivalente ao CC |
| S18/S29 ânodo | Alfa Aesar, feltro6,35mm,99,0%,2×3cm | [CoA43200](https://documents.thermofisher.com/TFS-Assets/GC/certificate/Certificate-of-Analysis/043200-R06A009.pdf) corresponde a descrição | SKU43200 é candidato por marca/espessura/pureza; artigo não informaSKU/lote |
| S17 suporte CF | Alfa Aesar, feltro3,18mm,99% | [CoA43199](https://documents.thermofisher.com/TFS-Assets/GC/certificate/Certificate-of-Analysis/043199-G05S049.pdf) corresponde a descrição | Não intercambiável com feltro6,35mm; lote experimental desconhecido |
| S17 AC | NORIT SX Ultra, Sigma-Aldrich | [Sigma53663](https://www.sigmaaldrich.com/NL/en/product/sigald/53663) | Grade coincide; ficha atual não identifica lote2016; preço/disponibilidade regionais |
| S17 CB | Acetileno50%compressed, Alfa Aesar | [Thermo039724](https://www.thermofisher.com/order/catalog/product/039724.A1) corresponde à descrição | SKU inferido por catálogo; “50%compressed” descreve densificação do pó, não50%carbono |
| S17 membrana | CMI-7000, Membranes International | [Fabricante: CXM-200S(CMI-7000S)](https://ionexchangemembranes.com/cmi-7000-cation-exchange-membranes-technical-specifications/) | Alias/linhagem atuais documentados; condições de ensaio e pré-hidratação não são universais |
| S17 CC/SS/ânodo | CC Fuel Cell Earth; SS McMaster-Carr; véu carbono PRF30g/m² | Artigo identifica fornecedor, mas sem códigos suficientes | Não atribuir grade comercial arbitrária ao tecido, aço ou véu |
| S19 ânodo/cátodo | W0S1009/W1S1009, Phychemi; Sylgard184; Pt/C | Identidade nominal está nos métodos | W1S1009 não é W1S1011; lote, Pt wt%, massaPt versusPt/C e receita completa de cura não resolvidos |

**Montagem S18:** etapa10 = tecido/papel, GDL/MPL e tratamento hidrofóbico; etapa11 = camada catalítica Pt/C, ligante/ionômero e processo de deposição. O Nafion postcoat do GDE pertence à composição da camada/interfase e **não deve criar uma membrana separadora na etapa6**. Para o CP, os autores usam por1mgPt/C:0,83µLágua+6,67µLNafion+3,3µLisopropanol. Concentração de sólidos do ionômero/SKU não foi especificada; não calcular fração de ligante apenas desses volumes.

## Preço e disponibilidade observados

O [fabricante do GDE](https://fuelcellsetc.com/products/carbon-cloth-05-ptc-gas-diffusion-electrode-w1s1011) publica variantes específicas:

| Tamanho | SKU | USD/folha | Estado informado |
|---|---|---:|---|
|5×5cm|11060059|51|InStock|
|10×10cm|11060060|111|InStock|
|20×20cm|11060061|354|InStock|
|30×30cm|11060062|720|InStock|
|40×40cm|11060063|1183|InStock|

Captura doHTML e dados estruturados preservados em `GDE_11060059_variants_observed.json`, incluindoURL por variante. Frete, impostos, importação paraEspanha, perdas de corte e custos de montagem não incluídos. O preço da folha5×5éUSD51; não representa custo de um cátodo acabado instalado. Valores/estoque podem mudar.

O GDL nuW1S1011 aparece a partir deUSD24 eH23C6 a partir deUSD19 no distribuidor; tamanho não confirmado para essas chamadas iniciais, portanto não compararUSD/cm². O fabricanteCXM200S publica folha1,2×0,5m porUSD200, com orçamento/frete posteriores. Não foi enviada solicitação ou compra.

## Restrições das fichas

- A [fichaCeTech](https://www.fuelcellstore.com/spec-sheets/w0s1011-w1s1011-spec-sheet.pdf) fornece espessura0,41mm,200g/m²,Gurley<55s e resistência através da espessura<13mΩcm². São valores de ensaio/limites nominais; não são uma curva de transporte deO₂ hidratada nem taxaORR.
- A fichaFreudenberg atualmente vinculada à páginaH23C6 **não contém colunaH23C6**. Não reutilizar dadosH23C9/H23CX653. A tabela comparativa do distribuidor2021 contémH23C6, mas não substitui especificação do lote nem resolve todas as condições de compressão.
- CMI/CXM é enviada na formaNa⁺; resistência<30Ωcm² é medida em0,5MNaCl. Pré-hidratação indicada:12h na solução de aplicação ou5%NaCl. Não converter esse limite em resistência universal no meioMFC.
- NoPt10%/AC do CP, catálogosThermo38325(reduzido) e38326(não reduzido) ambos têm≈50%água. O artigo não distingue ambos; não fecharSKU. Um descontoUSD encontrado terminou em2025 e não foi usado como preço atual.
- S17 usaAC80%/PTFE20% eMPL≈CB83%/PTFE17%, com rotas diferentes. S19 usaPDMS ePt/C. Igualdade do suporte ou da carga nominal não identifica o eletrodo final.

## Comparação adicional S29

[Salvian et al., npj Clean Water7:53(2024)](https://www.nature.com/articles/s41545-024-00350-5),DOI10.1038/s41545-024-00350-5, possui construção compatível comS18:30mL,feltro2×3cm/6,35mm,GDEW1S1011/Pt0,5mgPt/cm² e1kΩ. Os métodos completos e suplemento foram recuperados. Três reatores biológicos mais controle recebem meiosSWW/RWW; suplementoTabela1/2 fornecejmáx e tempo atéjmáx porR1–R3.

Foram extraídos39feeds×3reatores=117registros, incluindo2faltantes de equipamento, totalizando115paresmedidos/230respostasnuméricas. OsIDs de feed preservam a ordem da tabela, sem inventar data cronológica. BOD é a coluna calculada pelos autores a partir deCOD. Todos permanecem candidatos.

A FiguraS7 mostra biofilme0–55d,acetato55–143d,SWW143–207d,RWW207–247d; cátodos são trocados em143/207d. A coincidência comS18 justifica o grupo conservador `Salvian2024-Surrey-30mL`; a sobreposição de reatores individuais não foi comprovada. Portanto não éholdout externo de materiais. Área numérica continua pendente: métodos dizem2×3cm e “área projetada”, sem declaração12cm². Temperatura operacional não foi explicitada. Nada foi ajustado ou treinado.

## Acesso, direitos e arquivos

- S29:PDF12p,HTML,texto principal; suplementoPDF13p e texto;CCBY4verificado emRights&permissions. `S29_documents_manifest.json` guarda hashes, tamanhos,URLs e licenças. `S29_source.json` guarda métodos, limites e família. `S29_feeds.json`, `S29_observations.json`,CSV e `extract_s29.py` preservam extração. Seis testes de integridade/alinhamento passaram.
- PDFs de fornecedores/CoAs eHTMLs foram recuperados para inspeção temporária; direitos de redistribuição integral não foram liberados. Integrar fatos/proveniência; não copiar automaticamente esses documentos aoGitHub público.
- S19PMC devolveu challenge na busca; XML integral viaEuropePMC foi recuperado, mas suplementoDataSheet1.PDF não foi recuperado nesta revisão. OXML referencia o arquivo e licencia o artigoCCBY4. Não afirmar leitura do suplementoS19.
- PáginaThermoPt/AC bloqueou downloadHTTP403; catálogo foi consultado via resultado primário, sem preço atual confirmado. Buscas de página comercial exataPhychemiW0S1009/W1S1009 não resolveram catálogo atual. Isso não prova indisponibilidade.
