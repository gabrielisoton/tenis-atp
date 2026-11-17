# Roadmap · Tênis em números

> **EN summary:**
> - Next steps: move the data to **1991 onwards**, the first season with full serve and return stats.
> - Add **total points won**, tournament pages and a 52-week view.
> - Build **Elo ratings** to measure each player's **peak** and the age at which they reached it. That enables fair
>   cross-era comparisons by age, plus a playful "peak vs peak" simulator.
> - Then: rivalries (head-to-head), playing styles, court speed and match prediction.
> - **What makes a player win:** rank the aspects of the game that matter most in a single match, and turn them into
>   training priorities for club players, with the limits stated clearly.
> - **The world No. 1s:** follow each No. 1's indicators **from low rankings to the top**:
>   - by ranking phase and by season, with milestones and the "breakthrough year";
>   - against everyone and only against the Top 10;
>   - side-by-side comparisons by age;
>   - what all No. 1s have in common, and what fades first after the peak.
> - Each item below is a GitHub issue.

## Princípios
- **Dados de 1991 em diante.** É a primeira temporada com estatísticas de saque, devolução e duração em
  praticamente todas as partidas.

  | Temporadas | Resultado, placar, idade | Ranking | Saque e pontos | Duração |
  |---|---|---|---|---|
  | 1968–1972 | ✅ | ❌ | ❌ | ❌ |
  | 1973–1990 | ✅ | ✅ | ❌ | ❌ |
  | **1991–hoje** | ✅ | ✅ | ✅ (~91% das partidas) | ✅ |

- **Temporada em andamento entra parcial** (Action mensal, item 3): conta em Elo, títulos, confrontos e perfis; as
  contas por temporada usam só temporadas completas. Em nov/2026 a TML de 2026 ia só até 17/01/2026 (Adelaide e
  Auckland), e o selo "dados até" deixa isso claro.
- **Sem ponto a ponto:** a base tem o total de cada partida, não o que aconteceu em cada game.
- **Python calcula, o site desenha.** Toda métrica nova nasce em `tenis/analises.py` e, quando o site refaz a conta
  no navegador, tem checagem Python × JS.
- **PT e EN sempre:** texto novo com `T()`/`data-l` e rótulos de dados no dicionário de `tenis/idiomas.py`.
- **Comparar épocas com honestidade.** Elo mede domínio sobre os **contemporâneos**, não nível absoluto: raquetes,
  cordas, preparo físico e velocidade das quadras mudaram. Toda página que compara épocas traz esse aviso.

## Leitura crítica das ideias
**% de pontos ganhos (TPW%)**
- É a melhor métrica-resumo de domínio no tênis: 50% é o jogador médio e ~55% é nível de nº 1. E é barata, porque os
  componentes já existem.
- **"Por game"** não dá (não há ponto a ponto). **Por partida** dá, e rende a curiosidade "venceu ganhando menos
  pontos que o adversário" (Federer × Djokovic, Wimbledon 2019, é o exemplo famoso).
- **Por torneio:** funciona melhor como página do torneio ("Nadal em Roland Garros").
- **Por período:** pede janela móvel de 52 semanas.

**Auge e "quem ganharia"**
- Medir o auge com **Elo** (geral e por superfície), não com o ranking ATP, que muda de regra ao longo do tempo.
- **Idade do auge:** sai da idade em cada partida.
- **"Quem ganharia" não tem resposta factual entre épocas.** Vira um simulador **Pico × Pico** assumidamente lúdico
  (probabilidade Elo de um contra o outro), com o aviso.
- A comparação **justa** é **por idade**: corrida de títulos e Slams por idade e curva de envelhecimento.
- Começando em 1991, quem estava no meio da carreira (Lendl, Becker, Edberg) entra sem o histórico anterior: o Elo
  deles no início dos anos 90 aparece subestimado.

**O que faz ganhar (para quem treina)**
- Dá para **ranquear os aspectos** que mais pesam na vitória. Na prévia com 2000–2025 (66.202 partidas com
  estatísticas), quem foi melhor em cada aspecto venceu:

  | Aspecto | Vencedor foi melhor |
  |---|---|
  | Pontos ganhos com o 1º saque | 83% |
  | Pontos ganhos com o 2º saque | 78% |
  | Break points salvos | 69% |
  | Aces por game | 60% |
  | Duplas faltas por game (menos) | 57% |
  | 1º saque dentro | 57% |

- **Cuidado com o desenho do modelo.** A devolução de um jogador é o espelho do saque do adversário. Pôr as duas
  coisas juntas faz a devolução "explicar tudo" (+6,7 contra ~0 dos componentes de saque).
- **Feito** (aba "O que faz ganhar" da página O jogo, `tenis/ganhar.py`, conferido por `scripts/validar_ganhar.py`), com a
  base 1991+ (95.462 partidas com estatísticas consistentes):
  - **leitura simples:** quem ganhou mais pontos com o 1º saque venceu 83%; com o 2º, 79%; break points salvos 71%;
    aces 63%; menos duplas faltas 63%; 1º saque dentro 57% (sem empates);
  - **modelo** (por desvio-padrão): 1º saque +4,1 · 2º saque +3,1 · 1º saque dentro +1,1 · aces e duplas faltas
    +0,1; acerta o vencedor em 92%; a mesma ordem em toda superfície, nível e época;
  - **um ponto é um ponto:** convertido em pontos, os três valem quase o mesmo: +1 ponto de saque a cada 100 vale
    ≈ +11 p.p. de chance de vencer numa partida parelha (1º saque 10,9 · 2º 10,7 · 1º dentro 11,6).
- **O modelo correto** usa os componentes do saque de cada jogador; o lado do adversário é a devolução.
  - Na prévia (2000–2025, outra padronização) pesavam ≈ +2,7, +1,9 e +0,75: a mesma ordem do resultado final acima.
    Simetricamente, a devolução contra cada um desses.
  - Aces e duplas faltas ficam ≈ 0 depois disso: valem pelo ponto que dão ou tiram, não por si.
- **Ganhar partida ≠ ser campeão.** Campeão é bom em muitos aspectos, constante e decide sob pressão. Isso é uma
  análise no nível do jogador, não da partida. Ela virou a página **"Os nº 1"** (abaixo).

**Os nº 1: a jornada até o topo**
- **Por que é a análise mais forte:** uma carreira tem história (começo, ano da virada, auge, declínio), e é isso que
  prende o fã. O grupo é o dos **nº 1 do mundo**: critério objetivo, fácil de explicar.
- **Feito** (aba "Os nº 1" da página Épocas, `tenis/numero1.py`, conferido por `scripts/validar_numero1.py`).
- **O que todos têm em comum** (21 nº 1 desde 1991 contra 508 jogadores com ≥ 100 partidas, em desvios-padrão):
  - **sets decisivos:** +1,8 (19 dos 21 acima de +1);
  - **2º saque:** +1,6 (14 dos 21);
  - **tie-breaks:** +1,5;
  - **break points salvos:** +1,3; **devolução:** +1,2 (14 dos 21);
  - aces (+0,3) e 1º saque dentro (+0,0) estão quase na média. **Saque grande não faz um nº 1.**
- **Anos da virada** (maior salto de vitórias contra o Top 10): Federer 2004, Nadal 2008, Djokovic 2011,
  Murray 2015, Alcaraz 2022, Sinner 2023.
- **Depois do topo** (17 nº 1 que já pararam, do auge às duas últimas temporadas): cai primeiro a **devolução**
  (−1,9 p.p., em 15 dos 17) e os pontos com o 1º saque (−1,9, em 15 dos 17); o 1º saque dentro não muda.
- **Idade ao chegar a nº 1:** Alcaraz 19,4 · Nadal 22,2 · Federer 22,5 · Djokovic 24,2.
- **A jornada (Djokovic):** da fase de ranking > 50 ao nº 1:

  | Indicador | > 50 | Nº 1 |
  |---|---|---|
  | Pontos com o 1º saque | 68% | 74,5% |
  | Com o 2º saque | 50% | 56,5% |
  | Devolução | 38% | 43% |

  Contra o Top 10, as vitórias saltam de 27% em 2010 para **86% em 2011**, o "ano da virada" que aparece sozinho nos
  dados.
- **Desenho:**
  - **eixo principal:** fase de ranking (> 50, 11–50, 4–10, 2–3, nº 1), que lida com as poucas partidas do começo de
    carreira; temporada como linha do tempo complementar;
  - **duas réguas:** contra todos e só contra Top 10, porque no topo os adversários são mais fortes;
  - **seções:** a jornada, comparar jornadas (por idade), o que todos têm em comum e depois do topo.
- **Cuidados:**
  - **Cobertura:** com a base 1991+, 15 dos 21 têm a jornada completa; Sampras, Agassi e Courier já estavam no
    topo em 1991 e Becker, Edberg e Muster tinham carreira antes (a página avisa em cada caso).
  - **Começo da carreira:** sem Challengers nem qualifying na TML, o começo tem poucas partidas.
  - **Clutch:** momentos decisivos só viram "clutch" comparados ao esperado (#19, feito: ver "Pressão acima do esperado").
  - **Não é causa:** "o que mudou" na subida não é receita.
- **Limites para o amador:**
  - **Não é causa:** é correlação em profissionais.
  - **Sem erros e winners:** a base não tem erros não forçados, winners, troca de bola nem subida à rede. No nível
    amador os erros dominam.
  - **Hipóteses:** o guia traduz os números em prioridades de treino, deixando isso claro.
- **Feito** (aba "Para quem treina" da página O jogo): seis prioridades, cada uma com **o dado** e **na quadra
  (hipótese)** separados, filtro de quadra e o quadro "o que os dados não dizem" no topo.
  1. Todo ponto conta igual (+1 ponto de saque em 100 ≈ +11 p.p. de chance).
  2. 2º saque: o ponto mais disputado (o devolvedor ganha ~50% no 2º saque, ~29% no 1º, em toda quadra).
  3. Devolução: atacar o 2º saque (14 dos 21 nº 1 bem acima do circuito).
  4. 1º saque: vale o ponto, não o ace (só 4 dos 21 nº 1 se destacam em aces ou 1º saque dentro).
  5. Momentos de pressão (sets decisivos e tie-breaks; "acima do esperado" fica para o item 18).
  6. Com os anos, cuidar das pernas (a devolução cai primeiro em 15 dos 17 nº 1 que pararam).
  - **Por quadra:** o saibro devolve mais (32% contra o 1º saque × 26% na grama) e tem metade dos aces, mas a ordem
    do que pesa é a mesma.

**Pressão acima do esperado** (feito: `tenis/pressao.py`, 4 critérios novos no ranking e no perfil, conferido por
`scripts/validar_pressao.py`)
- **Método:** cada momento de pressão comparado com o que os pontos do próprio jogador **na mesma partida** previam.
  Break points: o saque (ou a devolução) nos outros pontos. Tie-breaks e sets decisivos: a chance dada pela % de pontos
  que cada um ganhou sacando (modelo ponto → game → tie-break → set). 0 = como o circuito.
- **Descola do saque:** a % crua de BP salvos tem correlação 0,89 com o saque; acima do esperado, 0,15.
- **No break point, quem saca ganha 1,3 p.p. a mais** que nos outros pontos de saque (no circuito inteiro).
- **Frieza é quase sorte, menos no set decisivo:** comparando anos pares e ímpares, o "acima do esperado" se repete
  pouco em break points (0,23) e tie-breaks (0,19) e bem mais em sets decisivos (0,51).
- **Os nº 1:** acima do esperado em sets decisivos 21 de 21 (+7,7 p.p.; nos outros sets, só +1,8), tie-breaks +3,5,
  break points quase 0. Maiores em sets decisivos: Nishikori, Sampras, Alcaraz, Del Potro, Djokovic.
- **Limite:** o dado não separa frieza de preparo físico (o set decisivo é o fim da partida).

**Desde 1968:** descartado. Ganharíamos Borg, McEnroe e Connors, mas com buracos grandes nos dados. 1991+ cobre
Sampras, Agassi, Big 3 e a nova geração com tudo medido.

## Estrutura do site
Para não virar um site longo demais, tudo cabe em **6 páginas**, uma por tipo de pergunta. Os itens novos entram como
abas dessas páginas, não como páginas novas:

| Página | Itens do backlog que entram nela |
|---|---|
| Achados (início) | um card novo para cada achado forte de qualquer item |
| Jogadores | 6 perfil × torneio · 8 janela de 52 semanas · 18 pressão acima do esperado (feito) |
| Épocas | 21 Os nº 1 (feito) |
| Torneios (nova, quando o item 7 for feito) | 7 páginas de torneio · 16 velocidade da quadra |
| O jogo | 15 sacador × devolvedor · 17 histórias · 20 o que faz ganhar (feito) · 22 guia para quem treina (feito) |
| Sobre os dados | 3 atualização automática (selo "dados até", feito: o selo fica no rodapé de todas as páginas) · 19 previsão de partidas e calibração |

## Fases
| Fase | Tema | Entrega visível |
|---|---|---|
| 0 | Fundação | Base 1991+ com datas e ids, atualização automática, carregamento sob demanda |
| 1 | Pontos e torneios | TPW%, "venceu perdendo", perfil × torneio, páginas de torneio, janela de 52 semanas |
| 2 | Auge e épocas | Elo geral e por superfície, pico e idade do auge, corrida por idade, curva de envelhecimento, Pico × Pico, **Os nº 1: a jornada até o topo** |
| 3 | Rivalidades e histórias | H2H, sacador × devolvedor, velocidade da quadra, viradas e sequências, pressão acima do esperado |
| 4 | Modelos e o que faz ganhar | O que faz ganhar uma partida, guia para quem treina, previsão de partidas e calibração (Elo × ranking × ML) |

## Backlog
Esforço: **P** = um dia ou menos · **M** = alguns dias · **G** = uma semana ou mais.
**Começar por:** 1 → 4/5 → 9 → 10/11.

| # | Item | Fase | Esforço | Depende de |
|---|---|---|---|---|
| [1](https://github.com/gabrielisoton/tenis-atp/issues/2) | Base 1991+ com data do torneio, ids dos jogadores e níveis; o site passa a mostrar 1991–hoje | 0 | M | — |
| [2](https://github.com/gabrielisoton/tenis-atp/issues/3) | Página Jogadores mais rápida: cada aba desenhada ao abrir, checagem Python × JS adiada (arquivos por jogador/torneio ficam para os itens que tiverem detalhe próprio) | 0 | P | 1 |
| [3](https://github.com/gabrielisoton/tenis-atp/issues/4) | Atualização automática da TML (Action mensal) + selo "dados até" | 0 | P | 1 |
| [4](https://github.com/gabrielisoton/tenis-atp/issues/5) | TPW% (pontos ganhos totais) como critério, com IC de Wilson | 1 | P | — |
| [5](https://github.com/gabrielisoton/tenis-atp/issues/6) | "Venceu perdendo nos pontos": lista e por jogador | 1 | P | — |
| [6](https://github.com/gabrielisoton/tenis-atp/issues/7) | Perfil × torneio (V–D, títulos, TPW em cada torneio) | 1 | M | 1, 2 |
| [7](https://github.com/gabrielisoton/tenis-atp/issues/8) | Páginas de torneio (campeões, donos, recordes) | 1 | M | 1, 2 |
| [8](https://github.com/gabrielisoton/tenis-atp/issues/9) | Janela móvel de 52 semanas no perfil | 1 | P | 1 |
| [9](https://github.com/gabrielisoton/tenis-atp/issues/10) | Elo geral e por superfície + validação contra picos conhecidos | 2 | G | 1 |
| [10](https://github.com/gabrielisoton/tenis-atp/issues/11) | Pico e idade do auge (ranking de picos) | 2 | M | 9 |
| [11](https://github.com/gabrielisoton/tenis-atp/issues/12) | Corrida de títulos e Slams por idade | 2 | P | 1 |
| [12](https://github.com/gabrielisoton/tenis-atp/issues/13) | Curva de envelhecimento do circuito por época | 2 | P | 1 |
| [13](https://github.com/gabrielisoton/tenis-atp/issues/14) | Simulador "Pico × Pico" (probabilidade Elo por superfície, MD3/MD5, com aviso) | 2 | M | 9, 10 |
| [14](https://github.com/gabrielisoton/tenis-atp/issues/15) | Confrontos diretos (H2H) | 3 | M | 1, 2 |
| [15](https://github.com/gabrielisoton/tenis-atp/issues/16) | Mapa sacador × devolvedor por época | 3 | P | — |
| [16](https://github.com/gabrielisoton/tenis-atp/issues/17) | Velocidade da quadra (aces por torneio e ano, ajustado pelos jogadores) | 3 | M | 1 |
| [17](https://github.com/gabrielisoton/tenis-atp/issues/18) | Histórias: viradas de 0–2, quinto set, pneus, sequências, matadores de gigantes | 3 | M | 1 |
| [18](https://github.com/gabrielisoton/tenis-atp/issues/19) | Pressão acima do esperado (break points e tie-break) | 3 | M | — |
| [19](https://github.com/gabrielisoton/tenis-atp/issues/20) | Previsão de partidas e calibração (Elo × ranking × ML) | 4 | G | 9 |
| [20](https://github.com/gabrielisoton/tenis-atp/issues/21) | O que faz ganhar uma partida: ranking dos aspectos (leitura simples + modelo por superfície e nível) | 4 | M | — (melhor com 1) |
| [21](https://github.com/gabrielisoton/tenis-atp/issues/22) | **Os nº 1:** a jornada até o topo (fase de ranking + temporada, ano da virada, régua contra Top 10), comparar jornadas, o que têm em comum, depois do topo | 2 | G | 1, 2 (18 ajuda) |
| [22](https://github.com/gabrielisoton/tenis-atp/issues/23) | Guia para quem treina: prioridades a partir dos dados, com os limites | 4 | P | 20, 21 |

Cada linha é uma issue no GitHub (o número leva até ela), com labels `fase-N` e `esforco-P/M/G`.
Acompanhamento no quadro [Tênis em números](https://github.com/users/gabrielisoton/projects/1) (campo **Fase** e **Status**).
