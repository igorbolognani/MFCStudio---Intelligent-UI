# MFC Studio — núcleo mecanístico exploratório v0.2

Data: 25 de outubro de 2026. Este núcleo resolve uma hipótese quantitativa acoplada; **não foi calibrado e não tem erro preditivo experimental demonstrado**. Não há modelo estatístico treinado. As saídas com os defaults são verificações de código, não reproduções de um artigo.

## Fatos, proposta, lacunas

Fatos do pacote v0.1 lidos: `MFC_STUDIO_BASE_CIENTIFICA.md`, `evidence.py`, `evidence_seed.jsonl`, `sources.json`. As sete linhas candidatas não contêm curvas ou parâmetros suficientes para identificar este núcleo, nem validação independente. S02 é glicose/efluente e não calibra acetato. S08 é um modelo com mediador e populações; fornece precedente estrutural para balanços e competição, não parâmetros intercambiáveis com esta formulação.

Proposta implementada: primeira família de engenharia monocâmara, acetato expresso em DQO, consórcio misto, sem membrana, cátodo a ar ambiente, ORR de quatro elétrons, batelada, pH tamponado 7 e 25 °C. Escolhida por permitir investigar conjuntamente caminho iônico, carga, capacidade anódica, disponibilidade de substrato e transporte de O₂. A escolha define escopo de implementação; sua suficiência experimental continua pendente.

Lacunas: nenhum ajuste a curvas experimentais, incerteza calibrada, relação aprendida de material→parâmetros, distribuição espacial ou balanço de pH. Biofilme tem capacidade ativa fixa. Nomes de materiais, espessura de biofilme e carga de catalisador são registros; sua alteração nominal não cria coeficientes causais. pH/temperatura fora do caso de referência retornam previsão indisponível.

## Relações resolvidas

- Caminho iônico uniforme efetivo: `Rsol = Li/(κ Ai)`.
- Caminhos eletrônicos: `Re = Le/(σ Ae)`, com seção eletrônica própria, distinta da área geométrica reacional.
- Capacidade anódica limitada por substrato: `Icap,a = jmax,a Aa S/(Ks+S)`.
- Ativação efetiva: `ηa = ba asinh[I/(2 j0,a Aa)]`, correspondente catódica análoga.
- Perda de capacidade: `ηS = −bS ln(1−I/Icap,a)`.
- O₂ no contorno aberto: `C_O₂,g = yO₂ p/(RT)` e `Ilim,O₂ = 4 F Ac kO₂,g C_O₂,g`.
- Perda de transferência: `ηO₂ = −RT/(4F) ln(1−I/Ilim,O₂)`.
- Fechamento: `Eoc = I(Rext+RΩ)+ηa+ηc+ηS+ηO₂`. Eoc é um parâmetro efetivo de célula, não um potencial padrão de semirreação.
- DQO: `d(Va S)/dt = −8 I/F − kcomp Va S − kcross (C_O₂,g/C_O₂,g,ref) Va S`.
- Carga/energia: `Q=∫I dt`; `E=∫IV dt`; `CE=Q/(ΔmCOD F/8)`; `nO₂=Q/(4F)`.

S é `g O₂/m³`, numericamente igual a mg O₂/L. A massa da equação é em gramas; 8 é g DQO por mol de elétrons. O₂ de referência para a escala de ingresso é ar a 20,95%, 101325 Pa, 298,15 K. kO₂,g é efetivo e referido à concentração no gás; **não é kLa aquoso**. Crossover é um sumidouro fenomenológico de DQO, não uma solução do campo de O₂ dissolvido. Sem O₂ ambiente, esse sumidouro e a corrente são zero.

Todos os valores default, incluindo geometria de 28 mL/7 cm², são declarados **assumidos**, sem fonte experimental atribuída. Um laboratório pode substituir entradas por caracterizações, mas isso por si só não calibra a lei constitutiva completa.

## Topologia e indisponibilidade

Contrato preserva as onze etapas em toda configuração. Monocâmara líquida compartilha o meio anódico: não soma volume catódico. Cátodo a ar não recebe católito independente. Gás controlado requer inventário finito. Duas câmaras, membranas, regimes contínuos/fed-batch, outros substratos/culturas ou revestimento anódico ativo retornam `prediction_unavailable` com razões específicas.

Membrana ausente não é implementada como simples resistência zero em um solver universal: só a família explícita sem membrana é resolvida. Uma configuração com membrana conserva seus metadados e não recebe números extrapolados.

## Verificação numérica

Raiz elétrica monótona é resolvida em coordenada de sobrepotencial `z`: `I=Ilim(1−exp(−z))`. Isso evita falso fechamento quando a corrente está mais próxima do limite de transporte do que a precisão de ponto flutuante permite representar diretamente. Residual é conferido antes de retornar números.

Batelada usa Euler explícito adaptativo com perda máxima de 2% de inventário por passo. Integra e registra separadamente as rotas eletrogênica, concorrente e crossover; a soma fecha massa. Carga e O₂ reacional são integrados com a mesma corrente. O teto do passo é configurável, com teste de convergência ao reduzir pela metade. No inventário residual inferior a `10⁻¹⁴` do inicial, a integração pode terminar mantendo esse inventário explicitamente; não o converte em carga. A tolerância e ocorrência aparecem em `numerics`.

Guardas limitam duração a sete dias, 5000 intervalos de saída, 100000 passos internos, magnitudes numéricas e tensão efetiva de MFC até 2 V. Eles são limites computacionais, **não um domínio experimental calibrado**.

28 testes passaram: fechamento elétrico, circuito aberto/curto, ausência de substrato/O₂, SI, seções eletrônicas independentes, efeito de condutividade, limitações anódica/catódica, conservação DQO/carga/O₂/energia, refinamento temporal, entradas inválidas/extremas, topologias fora de cobertura, campos registrados sem causalidade inventada e separação de dados por proveniência. Esses testes não medem precisão experimental.

## Calibração e avaliação preparadas

`validation.mjs` constrói componentes conexos por estudo, reator, família e grupo de origem antes de particionar. Assim, artigos e datasets ligados transitivamente ao mesmo ensaio não caem em treino e teste. Uma família única não produz uma avaliação de generalização.

MAE/RMSE/bias preservam unidade física, exigem pares finitos e pelo menos dois grupos independentes por padrão. Ausência de dados ou origem sintética retorna métricas `null`. Cobertura/largura de intervalos também exigem dados experimentais independentes. Essas funções não certificam automaticamente a revisão de proveniência, a ausência de treino no holdout ou a compatibilidade das bases.

Próximo ajuste deve usar curvas completas com cargas/correntes/tensões e geometria nas mesmas condições, réplicas ou incerteza declarada, DQO/tempo pareados e informações de preparo. Identificar parâmetros simultaneamente, verificar correlações e deixar estudos/reatores/famílias completos de fora. Medir erro de tensão/potência/remoção, conservação, erro temporal e cobertura. Não ajustar todos os coeficientes a um único pico de potência.

## API

`defaultConfig()`, `validateConfig(config)`, `compileTopology(config)`, `solve(config, {cod_g_m3})`, `polarizationCurve(config,n)`, `simulateBatch(config)`, `sensitivity(config,fraction,keys)`.

`PARAMETER_SPECS`, `OUTPUT_SPECS`, `EQUATIONS`, `MODEL_DECLARATION`, `STAGES`, `STAGE_LABELS` dão nome, símbolo, unidade, papel e proveniência. Sensibilidade é OAT determinística; não intervalo de confiança.

Execução: `node --test mfc-engine.test.mjs`.
