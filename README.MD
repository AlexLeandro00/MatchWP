# MatCh.wp

Assistente de estratégia para a **rota de topo** de League of Legends, no estilo OP.GG. O usuário escolhe o seu campeão e o campeão inimigo, e a página mostra a chance de vitória, runas, feitiços e itens dos vencedores, dicas de como jogar contra o campeão e uma análise do começo de jogo.

Projeto da matéria de Inteligência Artificial (ADS, FICR). A IA pega dados de uma base, aprende com eles e toma decisões.

## Como funciona

1. **Dados:** 12.719 partidas ranqueadas da API da Riot (região EUW, patches 13.6 a 14.24), de um conjunto público do Hugging Face ([AngryBacteria/league_of_legends](https://huggingface.co/datasets/AngryBacteria/league_of_legends)).
2. **Extração (`extrair.py`):** separa os confrontos de topo (8.125 partidas, 16.250 linhas, uma de cada ponto de vista) e salva em `confrontos_topo.csv`.
3. **Modelo 1 (`treinar.py`):** regressão logística que prevê a chance de vitória usando só os dois campeões, que são as informações que o usuário digita.
4. **Modelo 2 (`treinar_lane.py`):** regressão logística que usa a diferença de CS aos 10 minutos e os marcadores de vantagem na lane.
5. **Página (`app.py`):** feita com Streamlit. Os nomes de itens, runas e feitiços vêm do Data Dragon, o serviço oficial de dados estáticos da Riot.
6. **Dicas (`dicas_matchup.json`):** textos de como jogar contra cada campeão, escritos a partir de guias públicos e das dicas do autor.

## Resultados

| Modelo | Entrada | Acerto no teste | Chute |
|---|---|---|---|
| 1. Chance de vitória | os dois campeões | 50,8% | 50% |
| 2. Começo de jogo | CS e vantagem na lane | 57,1% | 50% |

O teste usa 20% das partidas, separadas por partida para que as duas linhas de um mesmo confronto fiquem juntas.

**Leitura:** só saber os dois campeões quase não prevê o vencedor. O que acontece na lane pesa muito mais. O site mostra, junto de cada percentual, quantas partidas o sustentam e a margem de erro.

## Limitações

- Poucas partidas por confronto (a maioria dos pares tem menos de 30).
- Dados de 2023 e 2024: o jogo muda a cada patch (drift).
- O modelo 2 usa informação de dentro da partida. Ele serve para orientar o jogo, e não para prever antes dele.
- Correlação não é causa: quem está ganhando a lane naturalmente farma mais.
- Dicas de meio e fim de jogo ficaram de fora, porque exigem a timeline da Riot (14,5 GB).

## Próximos passos

- Coletar partidas do patch atual pela API da Riot e retreinar, para reduzir o problema dos dados antigos.
- Usar a timeline da Riot para gerar dicas de meio e fim de jogo.

## Como rodar

```powershell
python -m venv venv
venv\Scripts\activate
pip install pandas scikit-learn ijson streamlit
streamlit run app.py
```

O repositório já traz `confrontos_topo.csv` e os modelos treinados. Para refazer tudo do zero, baixe o `match_v5.json` (1,3 GB) do Hugging Face para a pasta e rode `extrair.py`, `treinar.py` e `treinar_lane.py`, nessa ordem.

## Aviso

Projeto acadêmico. MatCh.wp não é endossado pela Riot Games e não reflete as opiniões da Riot Games nem de quem trabalha com as propriedades da Riot Games. League of Legends e Riot Games são marcas registradas da Riot Games, Inc.