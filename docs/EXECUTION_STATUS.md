# Incremento v0.2 do MFC Studio

Implementação concluída: aplicação MFC independente, landing e Studio separados, onze etapas em ordem, diagrama selecionável, painel científico agrupado/minimizável, autenticação ChatGPT, cenários versionados em D1, registros de execução com hashes, corpus rastreável D1 e documentos CC BY em R2.

O catálogo completo pode receber valores e métodos como propriedades registradas. O núcleo possui 39 campos numéricos, com papéis explícitos; eles não cobrem todas as 110 propriedades propostas. Relações resolvidas: fechamento elétrico, caminhos ôhmicos, ativação efetiva, limitação por substrato e O2, consumo de DQO e integração de carga/energia.

Verificação executada: 29 testes do núcleo, 19 testes originais e oito testes do corpus; TypeScript e build de produção aprovados. Banco local real auditado: 15 tabelas de esquema, 11 etapas, 110 propriedades, 19 fontes, 62 relações fonte-etapa, seis documentos/35 trechos, seis grupos de proveniência, 32 registros, 86 observações, uma curva/13 pontos; zero violação de referências e reconstrução íntegra dos textos por hash. A versão do corpus é imutável e seeding é idempotente.

Browser QA de desenvolvimento: landing e Studio renderizados, seleção de etapas/SVG e bloqueio de previsões para membrana pendente inspecionados. Login e dados por usuário dependem do despacho de identidade do Sites; a rota /qa só existe em desenvolvimento e retorna 404 em produção. Não foi alegada verificação visual específica em viewport mobile quando a ferramenta não ofereceu mudança de viewport.

Pendente científico: calibração experimental, réplicas, resolução da base de área S18, dataset externo comparável e intervalos calibrados. MAE/RMSE externos permanecem null. O modelo não resolve outras topologias, transporte membranar, dinâmica do pH, crescimento do biofilme, gás finito nem relação aprendida entre descritores e cinética.

## Fechamento da publicação em 26 de outubro de 2026

A versão 2 do Site foi publicada com sucesso em `https://mfc-studio.igorbolognani768385.chatgpt.site`, mantendo acesso privado. O seeding de produção foi conferido como já aplicado e idempotente: 11 etapas, 110 propriedades, 19 fontes, seis documentos em 35 trechos, 32 registros, 86 observações e uma curva de 13 pontos. Os cinco PDFs principais e o PDF do suplemento estão presentes no R2 com SHA-256 conferido no upload.

Foi corrigida a ausência do suplemento na allowlist de download. Um teste adicional verifica que cada documento completo aponta para um PDF original existente, de tamanho e hash corretos. Total: 30 testes Node, 19 testes legados e oito testes de integridade do corpus, todos aprovados; TypeScript e build de produção aprovados. Acesso de serviço a cenários privados retorna 401 e /qa retorna 404 na produção. Login interativo e fluxo completo de cenário por visitante permanecem fora da verificação automatizada desta entrega.
