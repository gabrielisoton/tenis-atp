# 🎾 Tênis em números · Tennis by numbers

Projeto pessoal de analytics de tênis: todas as **96.165 partidas** do circuito principal da ATP entre 1991 e 2025,
com saque, devolução, break points, tie-breaks e títulos de cada jogador. Site estático em **português e inglês**.

- **Site:** https://gabrielisoton.github.io/tenis-atp/ (em inglês: `?lang=en`)
- **Roadmap e backlog:** [ROADMAP.md](ROADMAP.md) e as [issues](https://github.com/gabrielisoton/tenis-atp/issues) · [quadro](https://github.com/users/gabrielisoton/projects/1)

> *Personal tennis analytics project: every main-tour ATP match from 1991 to 2025, with serve, return, break
> points, tie-breaks and titles per player. Static site in Portuguese and English.*

## Páginas
Cinco páginas, cada uma respondendo a um tipo de pergunta. Cada aba tem endereço próprio (`pagina.html#aba`), para
links diretos e compartilhamento.

| Página | Pergunta | Abas |
|---|---|---|
| **Achados** (`index.html`) | O que há de mais interessante? | 9 achados com o número, um mini gráfico e o link para a análise (números tirados de `data/achados.json`) |
| **Jogadores** | Quão bom é o meu jogador? | Líderes de cada critério (pódio e quadro de medalhas) · Ranking por critério com IC de Wilson · Perfil do jogador · Rivalidades (H2H com a regra oficial) |
| **Épocas** | Quem foi o melhor de cada época? | Elo (carreiras, picos, Elo atual, nº 1 por temporada) · O auge (pico, melhor média de 12 meses, idade, curva de envelhecimento pelo método delta) · Corrida por idade (títulos e Slams, Slams desde 1968) · Pico × Pico · Os nº 1 (a jornada por fase de ranking, ano da virada, comparar jornadas, o que todos têm em comum, depois do topo) |
| **O jogo** | O que faz ganhar no tênis? | Top N × demais · Ranking e zebras · Linha do tempo · Venceu perdendo nos pontos |
| **Sobre os dados** | Dá para confiar? | A base e a população · O circuito (descritiva com filtros) · Métodos e validação (checagens, Elo × ranking, regras de cada contagem) |

Endereços antigos (`explorar.html`, `circuito.html`, `elo.html`, `rivalidades.html`) redirecionam para o lugar novo.
Uma sexta página, **Torneios**, entra quando o item de páginas de torneio for feito.

## Como funciona
O Python é o motor: baixa a base, monta a população e exporta JSON. O site só desenha e filtra no navegador.
```
dados/      baixar.py (CSVs da TML, 1991+) → preparar_populacao.py (base/populacao.parquet, com data, ids e ordem)
tenis/      estatistica.py, analises.py (critérios, líderes, perfis), elo.py, exportacao.py, idiomas.py (rótulos em inglês)
scripts/    exportar_site.py (gera site/data/*.json) · validar_estatistica.py (confere contra o scipy)
tenis/      … achados.py (números da página inicial), corrida.py, h2h.py, numero1.py (os nº 1)
site/       index (achados), jogadores, epocas, jogo, sobre + assets/ + data/  → publicado no GitHub Pages pelo Actions
```
Os cálculos da página Jogadores são refeitos em JavaScript e **conferidos com o Python** a cada carga
(`conferir()` em `site/assets/jogadores.js`, resultado no console).

## Como rodar
```bash
pip install -r requirements.txt
python dados/baixar.py
python dados/preparar_populacao.py
python dados/preparar_titulos.py          # finais vencidas (+ Slams desde 1968) para a corrida por idade
python dados/preparar_h2h.py              # partidas que contam no H2H oficial (inclui abandonos, Davis, Olimpíadas)
python scripts/exportar_site.py
python scripts/validar_estatistica.py
python scripts/validar_elo.py              # Elo: previsão, calibração e picos coerentes
python scripts/validar_numero1.py          # nº 1: anos da virada, cobertura, marcos e o que todos têm em comum
python -m http.server 8600 -d site     # http://localhost:8600
```

## Idiomas
Seletor **PT / EN** na barra (a escolha fica salva e vai na URL, `?lang=en`).
- **Texto fixo no HTML:** `<span data-l="pt">…</span><span data-l="en">…</span>`.
- **Texto montado no JS:** `T("português", "English")`.
- **Rótulos que vêm dos dados:** `tr(rótulo)`, com o dicionário de `tenis/idiomas.py`, exportado para
  `site/data/en.json`.

## Dados
Fonte: [TML-Database (Tennismylife)](https://github.com/Tennismylife/TML-Database). Uso pessoal, educacional e de
pesquisa não comercial, com citação da fonte; uso comercial (inclusive treinar modelos de previsão para serviços
comerciais) exige autorização ([termos](https://stats.tennismylife.org/tennis-match-database#usage-terms)).
