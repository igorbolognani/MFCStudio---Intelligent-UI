# Histórico dos lotes e auditoria dos commits

As quantidades abaixo contam **artigos com decisão de revisão acrescentada ou atualizada**. “Arquivos” é uma contagem diferente. Um mesmo arquivo `reviews.psv` pode conter decisões para muitos artigos. Com exceção da referência `ca0ccfa`, os commits foram verificados quanto ao conteúdo e ao CI histórico; os limites de acesso estão anotados na tabela.

| Commit | Arquivos alterados | Artigos revisados neste commit | CI naquele SHA | Diagnóstico |
|---|---:|---|---|---|
| [b57a457](https://github.com/igorbolognani/MFCStudio---Intelligent-UI/commit/b57a45722c56abf5a341fb69056cbe1cf7bc3a3f) · lxml e integridade | 1 | 0; alteração de CI | Falhou | `setup-node` tentou configurar cache do pnpm antes de o executável estar disponível. A versão atual desativa esse cache e instala pnpm em etapa própria. |
| [a9c6360](https://github.com/igorbolognani/MFCStudio---Intelligent-UI/commit/a9c63608f9f9bb5a92da4d141275176067272212) · B04 | 6 | 5 novos; 1 decisão revista | Falhou | Descoberta dos testes parou com `ModuleNotFoundError: lxml`; o job não chegou às etapas posteriores. |
| [e21838a](https://github.com/igorbolognani/MFCStudio---Intelligent-UI/commit/e21838a746ce5a51acd60eac3a05d508988f3103) · B03 | 10 | 4 novos; também registrou um braço F4 | Falhou | Mesma ausência de `lxml` na descoberta de testes. |
| [88a31ad](https://github.com/igorbolognani/MFCStudio---Intelligent-UI/commit/88a31adb860302a8fb3d860f3e2e7daca1b65c9a) · originais convencionais | 6 | 9 novos | Falhou | Mesma ausência de `lxml` na descoberta de testes. |
| [2369824](https://github.com/igorbolognani/MFCStudio---Intelligent-UI/commit/2369824c3a0bd44233bcd26b548ad4f36a7f8306) · B02 | 8 | 6 novos | Falhou | Mesma ausência de `lxml` na descoberta de testes. |
| [ce44f7e](https://github.com/igorbolognani/MFCStudio---Intelligent-UI/commit/ce44f7e39cd19ca3299f6ad136d2535aa9c6f287) · referências F1/F4/F5 | 6 | 7 novos; 1 decisão revista | Falhou | Mesma ausência de `lxml` na descoberta de testes. |
| [ca0ccfa](https://github.com/igorbolognani/MFCStudio---Intelligent-UI/commit/ca0ccfaaa77deccfc4061206addf1f975870d53) · referência F4 acetato | não recuperado | Não verificável | Não verificável | A pesquisa pelo SHA/título encontrou a referência, mas a API atual não forneceu commit, arquivos ou execução de CI. Não infiro se está em `main` nem a quantidade de artigos. |
| [c851e05](https://github.com/igorbolognani/MFCStudio---Intelligent-UI/commit/c851e05b840e2393de1878e8fbdc3d492c173644) · B01 | 6 | 6 novos | Falhou | Mesma ausência de `lxml` na descoberta de testes. |
| [64262c3](https://github.com/igorbolognani/MFCStudio---Intelligent-UI/commit/64262c3d1d52e57ca8cec405df3b0d82b5d0e398) · métodos F1/F5/F6 | 6 | 15 novos; 1 decisão revista | Falhou | Mesma ausência de `lxml` na descoberta de testes. |
| [ffd7f0e](https://github.com/igorbolognani/MFCStudio---Intelligent-UI/commit/ffd7f0e517981214990a17b6db9e4576c7f8fd97) · meta e corpos | 10 | 19 novos | Falhou | Mesma ausência de `lxml` na descoberta de testes. |
| [B17 · 4ee8f29](https://github.com/igorbolognani/MFCStudio---Intelligent-UI/commit/4ee8f29de0fa085117d654c52e8ea89f4b8b65f9) · métodos completos | 5 | 10 novos; 0 admitidos; 10 excluídos | Passou | CI `Verify MFC Studio` concluído com sucesso. Os dez artigos têm corpo, identidade, localizadores e motivo de exclusão registrados. |

## O que a falha antiga significa

Os nove SHAs recuperáveis acima tiveram CI vermelho. Em oito commits de catálogo, a execução falhou antes de concluir a descoberta dos testes porque o workflow não instalava `lxml`. No commit de workflow `b57a457`, a falha veio da ordem/cache de instalação do pnpm. Esses erros não demonstram que os dados do artigo estejam errados; demonstram que a revisão automatizada daquele SHA não terminou com sucesso.

As alterações acessíveis estão incorporadas na linha atual de `main`. O [workflow atual](../../../.github/workflows/verify.yml) instala `lxml==6.1.1`, prepara pnpm sem depender do cache antecipado do `setup-node` e passou no B17. Isso verifica o estado atual de `main`; não reescreve nem transforma retroativamente os resultados históricos dos SHAs anteriores. A referência `ca0ccfa` continua sem evidência suficiente para concluir status, conteúdo ou CI.

## Convenção daqui em diante

Um commit por lote de artigos, com a contagem no assunto. Exemplo deste próximo lote: `Review 1 article; 0 admitted, 1 excluded (B18)`. Revisão de decisão, arquivo alterado, braço adicionado e observação numérica recebem contagens separadas no corpo do commit e no índice. A lista de evidências mostra uma linha por artigo; tabelas de braço/resultado mantêm linhas por dado.
