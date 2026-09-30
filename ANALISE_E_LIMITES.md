# Análise, hipóteses e limites

## Pergunta de negócio

Como uma transportadora pode reduzir atrasos quando seus registros de entrega e de ocorrência não permitem explicar, viagem a viagem, o que antecedeu cada atraso?

## O que é fato, hipótese e teste

| Nível | Afirmação | Evidência ou desenho |
|---|---|---|
| Confirmado | 352 de 2.637 viagens atrasaram (13,35%). | Tabela diária de desempenho, janeiro–junho de 2024. |
| Confirmado | Não é possível ligar as 330 ocorrências às 352 entregas atrasadas. | As tabelas não compartilham identificador de viagem; totais e séries mensais não se conciliam. |
| Confirmado | 44 de 130 dias tiveram mais de 15% de atraso e concentraram 213 atrasos (60,5%). | Agregação dos registros diários de pontualidade. |
| Hipótese prioritária | Rota, equipe e diária são um cluster de prontidão pré-partida a testar. | 237 de 330 registros (71,8%); as três categorias aparecem nos seis meses. |
| Solução proposta | Gate de Prontidão com identificador de viagem, sinais, dono, decisão e desfecho. | Especificação em PRODUTO_E_PILOTO.md. |
| Teste | Implantação escalonada por rota, turno ou unidade comparável. | Piloto de 30 dias com métricas antecedentes, resultado e guardrails. |

O ponto analítico central é deliberado: os três sinais mais frequentes são uma prioridade de investigação, não uma causa raiz comprovada de cada atraso. A falha de rastreabilidade é a raiz sistêmica que a base atual permite confirmar.

## Resultado executivo

Em vez de recomendar três iniciativas isoladas, o projeto propõe um único produto operacional: o **Gate de Prontidão da Viagem**. Antes da saída, rota, equipe e diária passam por uma regra comum. Uma pendência abre uma exceção com responsável, prazo e decisão. A mesma viagem recebe, depois, seu resultado de entrega.

Isso cria dois ganhos ao mesmo tempo:

1. A equipe age antes que uma pendência se transforme em atraso.
2. A empresa passa a saber, por viagem, quais sinais antecederam o resultado e consegue medir o efeito das ações.

| Indicador | Resultado | Como usar |
|---|---:|---|
| Viagens na tabela de desempenho | 2.637 | Linha de base, janeiro–junho de 2024 |
| Entregas atrasadas | 352 (13,35%) | Resultado principal do piloto |
| Entregas no prazo | 2.285 (86,65%) | Linha de base de pontualidade |
| Ocorrências na tabela de causas | 330 | Não equivalem automaticamente a entregas atrasadas |
| Rota + equipe + diária | 237 (71,8%) | Primeira fila do gate |
| Sem causa identificada | 43 (13,0%) | Prioridade de qualidade de dados |
| Dias acima de 15% de atraso | 44 de 130 | Operar por exceção nesses dias |
| Entregas sem erro | 94,20% | Guardrail de qualidade |
| Entregas completas | 90,71% | Guardrail de qualidade |

## Intervenções propostas

| Sinal de entrada | Controle moderno e plausível | Dono da exceção | Indicador antecedente |
|---|---|---|---|
| Rota sem versão ou ETA validado | Contrato de rota com versão planejada, ETA e corredor geográfico. Alertar apenas desvios acima da tolerância e registrar um motivo estruturado. | Planejamento logístico | Percentual de viagens com rota validada antes da saída |
| Equipe sem confirmação em T−2h | Confirmação em T−24h e T−2h, com banco de cobertura acionável e tempo de substituição registrado. | Escala operacional | Percentual de equipes confirmadas até T−2h |
| Diária sem comprovação de liberação | Pré-validação financeira, pagamento digital rastreável e fila de exceção com SLA. “Solicitado” não equivale a “pago”. | Financeiro e operações | Percentual de diárias comprovadas até T−2h |
| Causa ausente ou livre | Catálogo de motivos, obrigatório no fechamento da exceção, com horário e responsável. | Central operacional | Percentual de ocorrências com motivo padronizado |

Os controles são propostas de implementação. Nenhum deles deve ser apresentado como economia ou redução de atraso já observada.

## Desenho do piloto de 30 dias

| Fase | Dias | Objetivo | Evidência a registrar |
|---|---|---|---|
| Linha de base | 1–5 | Criar identificador único e observar o fluxo sem bloquear a saída. | Pendência, horário, dono, decisão e entrega por viagem. |
| Ajuste | 6–10 | Ativar alertas em poucas rotas ou turnos e remover falsos positivos. | Taxa de alerta, tempo de resolução e motivos de exceção. |
| Escalonamento | 11–24 | Expandir gradualmente, preservando uma unidade ainda não exposta como referência temporária. | Cobertura do gate, SLAs e atrasos por 100 viagens. |
| Decisão | 25–30 | Definir se o fluxo deve ser ampliado, alterado ou interrompido. | Pontualidade, qualidade e comparação entre grupos. |

Métricas de implementação sugeridas: pelo menos 95% das viagens com estado de prontidão registrado antes da saída, pelo menos 95% das equipes confirmadas até T−2h e pelo menos 98% das diárias comprovadas até T−2h. Essas metas devem ser calibradas após os cinco dias de linha de base.

## Previsão de capacidade

Uma média móvel dos cinco últimos registros estima 1,4 atraso para o próximo registro após 28/06/2024. No backtest cronológico dos últimos 26 registros, o erro médio absoluto foi 1,05 atraso/dia, contra 1,38 ao repetir o resultado do dia anterior.

Essa previsão é mantida como demonstração de capacidade analítica e apoio ao dimensionamento diário. Não identifica a viagem em risco, não explica as causas e não deve ser usada como previsão da operação atual: a série histórica termina em junho de 2024.

## Método

1. Ler as abas diárias de pontualidade, entrega sem erro e entrega completa.
2. Consolidar contagens por mês, preservando os denominadores de cada aba.
3. Agregar a frequência de cada categoria de causa no primeiro semestre.
4. Medir concentração de categorias e dias com taxa diária de atraso acima de 15%.
5. Separar os últimos 20% dos registros diários para validar uma média móvel de cinco registros contra a referência de repetir o dia anterior.
6. Incorporar os resultados ao painel e explicitar os limites antes das recomendações.

## Limites e validações necessárias

- **Sem vínculo ocorrência–viagem:** não há identificador comum para associar cada atraso a uma ocorrência, descartar duplicidade ou medir a efetividade de uma ação por viagem.
- **Contagens mensais divergentes:** a tabela de desempenho e a de ocorrências seguem padrões mensais diferentes. Isso reforça que uma não pode ser usada como explicação direta da outra.
- **Denominador semestral ambíguo:** a página da fonte informa 2.637 viagens em 2024, mas cada planilha semestral de viagens também soma 2.637. O painel restringe a análise ao primeiro semestre, que tem a tabela de causas correspondente.
- **Previsão histórica e agregada:** a série acaba em junho de 2024 e não há atributos antes da entrega para treinar um modelo individual honesto.
- **Sem inferência causal:** frequência de uma categoria não prova que uma ação reduzirá atraso. O piloto escalonado é a etapa que pode produzir evidência mais forte.
- **Uso responsável dos dados:** confirmação de equipe e GPS devem apoiar a operação, não vigilância ou punição automática. A produção deve aplicar minimização de dados, acesso por necessidade e políticas compatíveis com LGPD.

## Fonte

Luiz Eduardo Simao e Amauri Pedro Cordeiro Junior. *Data Set Perfect Trip*. Mendeley Data, publicado em 2026; dados operacionais de janeiro a dezembro de 2024. DOI: [10.17632/jn2dcs2m77.1](https://doi.org/10.17632/jn2dcs2m77.1). Licença da fonte: CC BY 4.0. A análise deste painel usa as tabelas de desempenho de janeiro–junho e a tabela semestral de causas.
