# 🎾 Tênis em números · Tennis by numbers

Projeto pessoal de analytics de tênis: todas as **96.165 partidas** do circuito principal da ATP entre 1991 e 2025,
com saque, devolução, break points, tie-breaks e títulos de cada jogador. Site estático em **português e inglês**.

- **Site:** https://gabrielisoton.github.io/tenis-atp/ (em inglês: `?lang=en`)
- **Roadmap e backlog:** [ROADMAP.md](ROADMAP.md) e as [issues](https://github.com/gabrielisoton/tenis-atp/issues) · [quadro](https://github.com/users/gabrielisoton/projects/1)

> *Personal tennis analytics project: every main-tour ATP match from 1991 to 2025, with serve, return, break
> points, tie-breaks and titles per player. Static site in Portuguese and English.*

## Páginas
| Página | O que mostra |
|---|---|
| Início | A base, a população (o que entra e o que fica de fora), o que tem em cada partida, termos de uso |
| O circuito | Descritiva da população inteira com filtros: superfícies, duração, aces, ranking |
| Explorar | Top N × demais, ranking × zebras (chance de o favorito vencer), linha do tempo, "venceu perdendo nos pontos" |
| Jogadores | Líderes de todos os critérios (pódio e quadro de medalhas), ranking por critério com IC 95% de Wilson e perfil completo de cada jogador |
| Elo | Elo geral e por superfície partida a partida: carreira de cada jogador, maiores picos, o auge (pico e melhor média de 12 meses, com a idade e a idade no auge por época), nº 1 por temporada, Elo atual e a validação (acerto e calibração contra o ranking) |

## Como funciona
O Python é o motor: baixa a base, monta a população e exporta JSON. O site só desenha e filtra no navegador.
```
dados/      baixar.py (CSVs da TML, 1991+) → preparar_populacao.py (base/populacao.parquet, com data, ids e ordem)
tenis/      estatistica.py, analises.py (critérios, líderes, perfis), elo.py, exportacao.py, idiomas.py (rótulos em inglês)
scripts/    exportar_site.py (gera site/data/*.json) · validar_estatistica.py (confere contra o scipy)
site/       index, circuito, explorar, jogadores + assets/ + data/  → publicado no GitHub Pages pelo Actions
```
Os cálculos da página Jogadores são refeitos em JavaScript e **conferidos com o Python** a cada carga
(`conferir()` em `site/assets/jogadores.js`, resultado no console).

## Como rodar
```bash
pip install -r requirements.txt
python dados/baixar.py
python dados/preparar_populacao.py
python scripts/exportar_site.py
python scripts/validar_estatistica.py
python scripts/validar_elo.py              # Elo: previsão, calibração e picos coerentes
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
