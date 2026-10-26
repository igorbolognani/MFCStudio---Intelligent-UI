# Incremento v0.2 do MFC Studio

Implementação concluída: aplicação MFC independente, landing e Studio separados, onze etapas em ordem, diagrama selecionável, painel científico agrupado/minimizável, autenticação ChatGPT, cenários versionados em D1, registros de execução com hashes, corpus rastreável D1 e documentos CC BY em R2.

O catálogo completo pode receber valores e métodos como propriedades registradas. O núcleo possui 39 campos numéricos, com papéis explícitos; eles não cobrem todas as 110 propriedades propostas. Relações resolvidas: fechamento elétrico, caminhos ôhmicos, ativação efetiva, limitação por substrato e O2, consumo de DQO e integração de carga/energia.

Verificação executada: 29 testes do núcleo, 19 testes originais e oito testes do corpus; TypeScript e build de produção aprovados. Banco local real auditado: 15 tabelas de esquema, 11 etapas, 110 propriedades, 19 fontes, 62 relações fonte-etapa, seis documentos/35 trechos, seis grupos de proveniência, 32 registros, 86 observações, uma curva/13 pontos; zero violação de referências e reconstrução íntegra dos textos por hash. A versão do corpus é imutável e seeding é idempotente.

Browser QA de desenvolvimento: landing e Studio renderizados, seleção de etapas/SVG e bloqueio de previsões para membrana pendente inspecionados. Login e dados por usuário dependem do despacho de identidade do Sites; a rota /qa só existe em desenvolvimento e retorna 404 em produção. Não foi alegada verificação visual específica em viewport mobile quando a ferramenta não ofereceu mudança de viewport.

Pendente científico: calibração experimental, réplicas, resolução da base de área S18, dataset externo comparável e intervalos calibrados. MAE/RMSE externos permanecem null. O modelo não resolve outras topologias, transporte membranar, dinâmica do pH, crescimento do biofilme, gás finito nem relação aprendida entre descritores e cinética.

## Fechamento da publicação em 26 de outubro de 2026

A versão 2 do Site foi publicada com sucesso em `https://mfc-studio.igorbolognani768385.chatgpt.site`, mantendo acesso privado. O seeding de produção foi conferido como já aplicado e idempotente: 11 etapas, 110 propriedades, 19 fontes, seis documentos em 35 trechos, 32 registros, 86 observações e uma curva de 13 pontos. Os cinco PDFs principais e o PDF do suplemento estão presentes no R2 com SHA-256 conferido no upload.

Foi corrigida a ausência do suplemento na allowlist de download. Um teste adicional verifica que cada documento completo aponta para um PDF original existente, de tamanho e hash corretos. Total: 30 testes Node, 19 testes legados e oito testes de integridade do corpus, todos aprovados; TypeScript e build de produção aprovados. Acesso de serviço a cenários privados retorna 401 e /qa retorna 404 na produção. Login interativo e fluxo completo de cenário por visitante permanecem fora da verificação automatizada desta entrega.

## Curadoria de materiais e dados — 26 de outubro de 2026

Decisões confirmadas: seleção de materiais comerciais, acesso a literatura/fichas técnicas e prioridade para custo/disponibilidade. Corpus 0.3.0 preparado com 29 fontes, oito documentos completos licenciados (seis artigos e dois suplementos), 198 registros e 397 células de observação (393 numéricas e quatro faltantes). Inclui 16 variantes de materiais, 46 propriedades, 31 ofertas datadas e 115 pares experimentais de pico/tempo de resposta publicados em S29. O artigo e o suplemento S29 foram recuperados integralmente. Dados comerciais não são amostras experimentais; réplicas/feeds ligados permanecem agrupados.

Foram acrescentados normalização dimensional, guardas para transferência ao solver, tratamento de preços por pack/área e auditoria de admissão. Duas propriedades continuam sem conversão admitida. Nenhum preço entregue, vínculo automático de parâmetro, treinamento ou erro externo foi declarado. Sem novas telas ou equações. Os 32 registros científicos anteriores e a curva original foram preservados sem alteração. A base numérica de área S18/S29 continua pendente.

Verificações locais desta rodada: 32 testes Node e 42 Python aprovados (74 no total), TypeScript e build de produção aprovados. Hashes de todos os novos artefatos licenciados e a rastreabilidade das tabelas foram conferidos. Não houve nova QA visual de interface, pois este incremento não alterou as telas. `DATA_CURATION_2026-10-26.md` descreve fatos, inferências e lacunas; o recibo de produção é registrado separadamente após o deploy.

Publicação verificada: corpus 0.3.0 aplicado em D1; 29 fontes, 86 relações fonte-etapa, oito documentos em 49 trechos, 15 grupos de proveniência (não 15 experimentos independentes), 198 registros e 397 células de observação. Os oito PDFs estão presentes; os dois novos PDFs S29 foram conferidos por SHA-256 no upload; os seis HTMLs comprimidos armazenados correspondem aos hashes do seed. Metadados, hash e contagem de caracteres dos oito documentos conferem com o seed. Acesso de serviço a cenários retorna 401 e /qa retorna 404. A CI do commit 5dde96ec44ff31db43026d92e0e08b3e93b9d5ac passou. Recibos em `hosted-verification.json` e `production-v03-audit.json`.

Limite da auditoria direta: a ferramenta de leitura do D1 truncou uma célula de texto de 10.000 caracteres; não foi possível reconstruir independentemente o texto integral do banco por essa ferramenta. Isso não afetou a inspeção dos arquivos completos de origem, o seeding com hashes nem a verificação dos metadados dos documentos e ativos armazenados. Não se declara nova verificação visual ou de login interativo nesta rodada.
