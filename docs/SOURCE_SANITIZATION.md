# Sanitização dos documentos de origem

Em 26 de outubro de 2026, o alerta do GitHub foi rastreado ao campo de configuração Google Maps do site da Frontiers, incluído no HTML dos artigos S09 e S19. A mesma sequência aparecia nos arquivos HTML e nas cópias comprimidas incorporadas ao seed. A aplicação MFC Studio não usa Google Maps nem essa chave. Nenhuma chave foi chamada, revogada ou rotacionada.

Foram removidos scripts executáveis e configurações da editora das cópias dos dois artigos. Os textos científicos extraídos, PDFs, suplemento, observações e cenários não foram alterados. O manifesto distingue o hash de bytes recebidos do hash da cópia sanitizada; a proveniência científica e os identificadores são preservados. O corpus passa de 0.2.0 para 0.2.1, com as mesmas contagens científicas.

O seeding 0.2.1 substitui os HTMLs comprimidos em R2 e atualiza apenas os metadados de origem dos documentos cujo texto científico continua idêntico. As linhas históricas de seeding não contêm a chave. O status de produção confere os bytes armazenados por SHA-256.

A aquisição agora tem uma checagem que examina fontes, arquivos comprimidos e conteúdo base64 incorporado. O build recusa HTML com um padrão de chave Google. Quatro testes cobrem remoção de configuração, preservação do conteúdo científico e fórmulas, detecção dentro de gzip/base64 e ausência do padrão nos arquivos atuais. A CI executa essa checagem.

A limpeza do histórico publicado do GitHub reconstrói os commits de implementação mantendo sua sequência e removendo os objetos contaminados dos ancestrais de main. Uma reescrita não certifica eliminação de caches por SHA, clones externos ou versões históricas guardadas pelo provedor de hospedagem; essas cópias não são controladas pela atualização da branch. As ferramentas de Sites disponíveis não oferecem exclusão de versões históricas.
