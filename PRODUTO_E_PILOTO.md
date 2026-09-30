# Gate de Prontidão da Viagem

## Proposta de produto

O Gate de Prontidão é uma fila de exceções antes da saída. Ele não tenta adivinhar um atraso com “IA” antes de possuir dados confiáveis. Primeiro, reúne em uma mesma viagem o que hoje fica fragmentado: plano de rota, equipe, diária, decisão operacional e entrega.

O objetivo é simples: impedir que uma viagem com pendência relevante saia sem uma decisão explícita e criar rastreabilidade para aprender se aquele sinal antecede atraso.

## Estado da viagem

| Estado | Regra | Decisão permitida |
|---|---|---|
| Verde | Rota, equipe e diária estão validadas no horário de corte. | Liberar. |
| Amarelo | Há pendência com dono, SLA e alternativa viável. | Resolver antes da saída ou reprogramar. |
| Vermelho | Falta informação crítica, não há cobertura ou o SLA expirou. | Não liberar sem contingência ou justificativa de responsável. |

O estado não substitui o julgamento do despacho. Ele torna a decisão visível, consistente e auditável.

## Passaporte digital da viagem

O mínimo para ligar sinal, decisão e resultado:

| Campo | Exemplo | Por que existe |
|---|---|---|
| trip_id | TRP-2048 | Conecta todos os eventos à mesma viagem. |
| planned_departure_at | 2026-09-29 14:00 | Define os horários de corte T−24h, T−12h e T−2h. |
| route_version e planned_eta | R3 / 2026-09-30 09:30 | Permite validar plano e alterações de rota. |
| crew_confirmed_at | 2026-09-29 12:05 | Mede confirmação e cobertura no momento certo. |
| per_diem_paid_at | 2026-09-29 11:40 | Diferencia solicitação de pagamento de pagamento comprovado. |
| readiness_state | verde, amarelo ou vermelho | Dá uma regra compartilhada à liberação. |
| exception_code | rota, equipe, diária, outro | Cria um catálogo de motivos analisável. |
| exception_owner e due_at | escala / 13:30 | Mostra quem decide e qual é o SLA. |
| resolution_action | substituir, replanejar, liberar com exceção | Fecha o loop de decisão. |
| actual_departure_at, delivered_at, promised_at | timestamps | Permite calcular atraso e efeito operacional. |

Eventos precisam ser imutáveis ou ter trilha de alteração. Uma correção posterior não deve apagar o estado observado antes da saída.

## Fluxo por área

| Momento | Planejamento | Escala | Financeiro | Central operacional |
|---|---|---|---|---|
| T−24h | Publica rota e ETA planejados. | Inicia confirmação da equipe. | Pré-valida diária. | Cria a viagem e abre o passaporte. |
| T−12h | Revisa rota inviável ou restrição conhecida. | Identifica ausência e cobertura. | Sinaliza pendência de liberação. | Abre exceção e atribui dono. |
| T−2h | Confirma versão final de rota. | Confirma equipe ou substituição. | Confirma pagamento. | Libera, replaneja ou exige justificativa. |
| Saída e rota | Registra mudança de rota e motivo. | Registra troca de equipe. | Registra exceção financeira. | Fecha decisão e acompanha entrega. |

## Como medir o piloto

### Implementação

- Cobertura: percentual de viagens com passaporte criado antes da saída.
- Qualidade de dados: percentual de exceções com código, horário, dono e decisão.
- SLA: percentual de equipe e diária confirmadas até T−2h.
- Operação: tempo entre exceção e resolução; alertas que viraram verde antes da saída.

### Resultado

- Atrasos por 100 viagens.
- Saídas após o horário planejado.
- Taxa de entrega no prazo.

### Guardrails

- Entregas sem erro.
- Entregas completas.
- Exceções justificadas por segurança, cliente ou legislação.

Uma queda de atraso só é uma melhoria válida se não vier acompanhada de piora nos guardrails.

## Desenho de avaliação

O piloto não deve comparar apenas “antes e depois”, porque demanda, clima, rotas e calendário podem mudar. A proposta é usar implantação escalonada:

1. Selecionar rotas, turnos ou unidades com volume suficiente e características parecidas.
2. Começar com uma parte delas em modo observação.
3. Ativar o gate gradualmente e manter algumas unidades ainda não expostas como referência temporária.
4. Comparar atrasos por 100 viagens, aderência aos SLAs e guardrails, sempre descrevendo as diferenças entre os grupos.

Se a comparação for pequena ou os grupos forem muito diferentes, o resultado deve ser relatado como evidência operacional inicial, não como causalidade definitiva.

## Evolução de dados para ciência de dados

Depois que o passaporte produzir registros por viagem, um modelo de risco pode ser considerado. Antes disso, o problema é de instrumentação, não de algoritmo.

Um modelo futuro deve:

- usar somente atributos disponíveis antes da saída;
- ser validado em períodos futuros, não em amostras aleatórias;
- medir calibração e desempenho por rota, turno e tipo de operação;
- priorizar revisão humana e capacidade limitada;
- ter motivo de alerta interpretável e processo de contestação;
- ser reavaliado quando rotas, regras ou dados mudarem.

## Uso responsável

O gate deve facilitar a resolução de pendências, não criar um mecanismo de punição individual. Dados de equipe e GPS precisam de finalidade definida, acesso por necessidade, retenção proporcional e comunicação clara. Para produção, a empresa deve revisar a implementação com as áreas de privacidade, segurança e relações de trabalho.
