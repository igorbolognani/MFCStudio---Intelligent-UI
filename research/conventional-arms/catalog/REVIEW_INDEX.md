# Índice de revisão e dados do catálogo MFC

Este índice responde a três perguntas separadas: **qual artigo foi lido**, **qual decisão recebeu para as seis famílias convencionais F1–F6** e **quais braços/resultados numéricos estão de fato registrados**. O denominador continua congelado em 7.599 publicações.

## Estado atual após B18

| Medida | Registros | O que conta |
|---|---:|---|
| Corpo recuperado | 1.599 / 7.599 (21,04%) | Corpo de artigo, não somente resumo ou página de acesso |
| Identidade documental confirmada | 1.467 / 7.599 (19,31%) | Texto integral ligado à identidade da publicação |
| Triagem individual | 487 / 7.599 (6,41%) | Artigos com uma decisão de revisão documentada |
| Métodos completos lidos | 218 / 7.599 (2,87%) | Métodos em escopo integral, não apenas sinal automático |
| Artigos com controle admitido em F1–F6 | 47 / 7.599 (0,62%) | Artigo com ao menos um braço correspondente a uma das seis famílias |
| Revisões excluídas de F1–F6 | 144 | Decisão de escopo, não avaliação da qualidade do artigo |
| Revisões pendentes | 18 | Falta localizar ou confirmar evidência para uma decisão |
| Confirmações de controles existentes | 11 | Reconferências dentro dos 47 artigos admitidos; não aumentam o total |

Para superar 50% em cada etapa, são necessários 3.800 registros. A checagem atualizada fica em [coverage.json](coverage.json); o detalhamento de cada publicação fica nas tabelas abaixo.

## Listas por artigo

| Arquivo | Linhas de artigos | Como ler |
|---|---:|---|
| [Aprovados F1–F6](approved-F1-F6.psv) | 47 | Família, estado do texto, leituras e quantidade de braços/dados numéricos vinculados por registro |
| [Excluídos de F1–F6](excluded-F1-F6.psv) | 144 | Família examinada, localizador de método/resultado e motivo específico da exclusão |
| [Pendentes](pending-F1-F6.psv) | 18 | Evidência que falta para resolver a compatibilidade ou atribuição do resultado |

“Excluído” significa apenas que nenhum controle do artigo foi admitido nas seis montagens iniciais. As listas conservam estudos MFC com outra alimentação, outras geometrias, eletrodos, membranas ou aceitadores; também incluem MEC/MES, revisões e casos em que o braço e o resultado não puderam ser ligados com segurança. O motivo e o localizador permanecem por artigo. “Pendente” significa que a decisão ainda não foi fechada.

## Braços registrados e medições encontradas

| Registro | Contagem atual | Conteúdo |
|---|---:|---|
| Linhas de braços experimentais | 98 | Configurações de braços nas tabelas de levantamento, métodos, expansão externa e catálogo; uma linha é um braço, não um artigo |
| Observações numéricas registradas | 65 | Medições publicadas com unidade, fase, condição, carga, localizador, estado e nota |
| Observações ligadas a artigos admitidos F1–F6 | 64 | Incluem resultados de braços convencionais e de braços alternativos dentro do mesmo artigo |
| Braços na expansão de stacks alternativas | 17 em 13 artigos | Os 13 artigos já pertencem aos 47 admitidos; esta expansão não acrescenta aprovações |
| Valores contextuais do artigo B18 fora de F1–F6 | 18 | Resultados de respiração anódica/incrustação, preservados em uma tabela separada |

* Os 65 registros de [observações vinculadas](registered-observations.psv) vêm das tabelas de métodos, expansão externa e catálogo. As 64 observações associadas a artigos admitidos não são automaticamente dados de calibração: os estados atuais são `context_only` ou `quality_hold`.
* [Braços da expansão externa](external-expansion-arms-index.psv) preserva a montagem completa por braço e os IDs dos resultados associados. Alguns braços são comparadores; a tabela registra também modificações de stack. Use os campos de câmara, aceitador, alimentação, eletrodos, separador e circuito para distinguir o que mudou.
* [Valores contextuais de B18](context-observations.psv) registra 18 números do artigo `10.3389/fmicb.2018.03284`, incluindo condição e localizador. A unidade de produção de H₂ aparece como `rnmol` no XML e permanece em `quality_hold`; a curva de incrustação na Fig. 2 ainda não foi digitalizada.

Uma aprovação do artigo e a prontidão de um número são estados diferentes. A aprovação informa que existe um controle elegível em alguma família F1–F6. A observação informa qual braço produziu o valor e sob que condições; o estado `context_only`/`quality_hold` impede que seja usado como dado de calibração sem nova análise.

## Como conferir proveniência

- [Catálogo das 7.599 publicações](publications.psv.gz) — identidade, família, estado de documento e sinais de triagem.
- [Decisões atuais](reviews.psv) e [histórico de revisões](review-history.psv) — decisão, escopo, localizador e justificativa.
- [Tentativas de acesso](acquisition.psv) — rota, estado, bytes e hash. Uma tentativa com erro fica preservada quando outra rota recupera o documento.
- [Braços e observações originais do catálogo](arms.psv) e [observations.psv](observations.psv).
- [Auditoria dos lotes e commits](BATCH_HISTORY.md) — número de artigos revisados por commit, revisões de registro e falhas históricas do CI.

## Padrão dos próximos commits

O assunto do commit informa a **quantidade de artigos**, usando `Review N articles; A admitted, E excluded, P pending (Bxx)`. O corpo registra artigos novos e revisões de decisões anteriores separadamente. Quantidade de arquivos, braços e observações fica em campos próprios; nenhum desses números será apresentado como se fosse a quantidade de artigos. Os commits já publicados permanecem na ordem original e são explicados no histórico de lotes.

## Verificação

```sh
python3 scripts/build-conventional-catalog.py --check --require-over-half
```

A verificação compara as listas geradas com o catálogo de origem, confere seus hashes e mantém o denominador de 7.599. Retorna código 2 enquanto alguma das cinco etapas ainda não supera 50%.
