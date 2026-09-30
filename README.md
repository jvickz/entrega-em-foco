# Entrega em Foco

> Um produto de dados para identificar riscos operacionais e agir antes que uma viagem atrasada vire um problema para o cliente.

**Projeto de João Vitor Marinho · Ciência de dados aplicada à logística**

[Abrir o dashboard](./portfolio_joao_vitor_marinho.html) · [Entender o produto](./PRODUTO_E_PILOTO.md) · [Revisar análise e limitações](./ANALISE_E_LIMITES.md)

[Ver versão publicada](https://jvickz.github.io/entrega-em-foco/) · [Código no GitHub](https://github.com/jvickz/entrega-em-foco) · [Post no LinkedIn](https://www.linkedin.com/feed/update/urn:li:activity:7511033135023820802/)

## O projeto em 30 segundos

Uma transportadora registrou **2.637 viagens** no primeiro semestre de 2024. Dessas, **352 chegaram atrasadas — 13,35% do total**.

O problema mais relevante apareceu antes do modelo: as ocorrências não possuem um identificador que permita ligá-las à viagem correspondente. A operação sabe que o atraso aconteceu, mas não consegue demonstrar qual pendência o antecedeu nem se a ação tomada resolveu o problema.

Minha resposta foi desenhar o **Gate de Prontidão da Viagem**, uma fila de exceções que reúne rota, equipe e diária antes da saída. Cada pendência recebe responsável, prazo e decisão registrada.

| Evidência | Leitura para o negócio |
| --- | --- |
| 352 viagens atrasadas | O problema afeta 13,35% da operação analisada. |
| 237 de 330 registros em rota, equipe e diária | 71,8% dos sinais registrados podem ser investigados antes da partida. |
| 43 registros sem causa identificada | A qualidade do dado impede aprendizado operacional em 13% das ocorrências. |
| 44 de 130 dias acima de 15% de atraso | Dias críticos concentraram 60,5% dos atrasos e justificam gestão por exceção. |

## A decisão proposta

O gate transforma mensagens, planilhas e pendências dispersas em uma rotina operacional compartilhada:

1. **T−24h:** cria o passaporte digital da viagem e registra rota, escala e diária.
2. **T−12h:** identifica exceções e atribui responsável e prazo.
3. **T−2h:** resolve, substitui, replaneja ou exige justificativa para liberação.
4. **Saída e entrega:** fecha o ciclo com decisão, horário e resultado observado.

Uma viagem vermelha não sai sem contingência, replanejamento ou justificativa registrada. Esse histórico cria a base necessária para um futuro modelo de risco por viagem.

## O que torna este case relevante

- **Parte da decisão de negócio:** o painel mostra o que fazer, quem deve agir e como medir.
- **Separa fato de hipótese:** os 237 registros prioritários orientam o piloto, mas não são tratados como causas comprovadas dos atrasos.
- **Evita IA prematura:** primeiro instrumenta o processo; depois avalia se um modelo preditivo acrescenta valor.
- **Inclui validação:** o piloto de 30 dias mede adoção, SLA, atrasos por 100 viagens e guardrails de qualidade.
- **Expõe limitações:** divergências entre tabelas e ausência de `trip_id` aparecem no produto e na documentação.

## Entregáveis

| Arquivo | Finalidade |
| --- | --- |
| [`index.html`](./index.html) | Página principal pronta para GitHub Pages. |
| [`portfolio_joao_vitor_marinho.html`](./portfolio_joao_vitor_marinho.html) | Versão local com nome exclusivo para evitar abrir cópias antigas. |
| [`dashboard.html`](./dashboard.html) | Dashboard executivo independente de servidor. |
| [`PRODUTO_E_PILOTO.md`](./PRODUTO_E_PILOTO.md) | Fluxo operacional, contrato de dados e experimento de 30 dias. |
| [`ANALISE_E_LIMITES.md`](./ANALISE_E_LIMITES.md) | Método, fatos, hipóteses e limitações. |
| [`POST_LINKEDIN.md`](./POST_LINKEDIN.md) | Texto preparado para apresentação pública do projeto. |
| [`src/build_dashboard.py`](./src/build_dashboard.py) | Consolidação dos dados e geração do painel. |
| [`src/download_data.py`](./src/download_data.py) | Download reproduzível da fonte publicada. |

## Tecnologias e competências demonstradas

**Python, pandas, openpyxl, HTML, CSS e JavaScript**, com foco em análise exploratória, qualidade de dados, previsão temporal simples, desenho de produto analítico, experimentação e comunicação executiva.

O dashboard não depende de bibliotecas externas nem de servidor. Os dados agregados ficam incorporados ao HTML final.

## Como executar

Requer Python 3.10 ou superior.

```powershell
python -m pip install -r requirements.txt
python src/download_data.py
python src/build_dashboard.py
```

Depois, abra `index.html` no navegador.

## Previsão e uso responsável

A média móvel de cinco registros estima **1,4 atraso no próximo dia histórico**, com MAE de **1,05 atraso/dia** no holdout cronológico, ante **1,38** do baseline ingênuo. Ela demonstra planejamento de capacidade; não prevê qual viagem atrasará.

Um modelo individual só deve ser criado depois que o passaporte digital produzir atributos disponíveis antes da saída e desfechos ligados pelo mesmo `trip_id`. Informações de equipe e localização precisam de finalidade clara, acesso restrito e revisão de privacidade.

## Fonte

Luiz Eduardo Simao e Amauri Pedro Cordeiro Junior, *Data Set Perfect Trip*, Mendeley Data, publicado em 2026, DOI [10.17632/jn2dcs2m77.1](https://doi.org/10.17632/jn2dcs2m77.1), licença CC BY 4.0.

O recorte analítico usa dados de janeiro a junho de 2024. Consulte [`ANALISE_E_LIMITES.md`](./ANALISE_E_LIMITES.md) para as divergências identificadas na fonte.

## Autor

**João Vitor Marinho**  
Projeto de portfólio em ciência de dados, analytics e inteligência operacional.
