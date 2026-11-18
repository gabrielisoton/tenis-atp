# 🎾 Tênis em números · Tennis by numbers

Projeto pessoal de analytics de tênis: todas as partidas do circuito principal da ATP **desde 1991** (mais de 96 mil),
com saque, devolução, break points, tie-breaks e títulos de cada jogador. Site estático em **português e inglês**,
atualizado todo mês; o rodapé de cada página mostra até quando vão os dados.

- **Site:** https://gabrielisoton.github.io/tenis-atp/ (em inglês: `?lang=en`)
- **Roadmap e backlog:** [ROADMAP.md](ROADMAP.md) e as [issues](https://github.com/gabrielisoton/tenis-atp/issues) · [quadro](https://github.com/users/gabrielisoton/projects/1)

> *Personal tennis analytics project: every main-tour ATP match since 1991, with serve, return, break points,
> tie-breaks and titles per player. Static site in Portuguese and English, updated monthly.*

## Páginas
Cinco páginas, cada uma respondendo a um tipo de pergunta. Cada aba tem endereço próprio (`pagina.html#aba`), para
links diretos e compartilhamento.

| Página | Pergunta | Abas |
|---|---|---|
| **Início** (`index.html`) | O que há de mais legal? | 6 curiosidades em linguagem de fã, a chamada "Joga tênis? Veja o que treinar" e os atalhos para cada página (números de `data/achados.json`) |
| **Épocas** | Quem foi o melhor de cada época? | Elo (o que é, a carreira em Elo, maiores picos, o mais forte hoje, nº 1 por temporada e, na mesma aba, a idade do auge) · Corrida por idade · Pico × Pico · Os nº 1 |
| **Jogadores** | Quão bom é o meu jogador? | Rivalidades (H2H com a regra oficial) · Perfil do jogador · Os melhores em cada fundamento (pódio e medalhas) · Ranking completo (22 critérios com margem de erro, inclusive a pressão acima do esperado) |
| **O jogo** | O que decide uma partida? | Vencer perdendo · Favoritos e zebras · Como o jogo mudou · A elite × o resto · Para quem treina (com o modelo "o que faz ganhar" recolhido no fim) |
| **Sobre os dados** | Dá para confiar? | A base e a população · Métodos e validação (checagens, Elo × ranking, regras de cada contagem) |

Endereços antigos (`explorar.html`, `circuito.html`, `elo.html`, `rivalidades.html`) redirecionam para o lugar novo.

**Como o site fala** (depois de um teste com dois usuários simulados, um fã no celular e um tenista amador):
- cada aba começa com **a resposta em uma frase**, citando jogadores;
- o **"📖 Como ler"** tem uma ou duas linhas, com exemplo e sem fórmula;
- tudo que é técnico (margem de erro, desvio-padrão, fórmulas, métodos) fica recolhido em **"🔎 Para quem quer aprofundar"**;
- nada de jargão na parte visível: "pontos em cada 100" em vez de p.p., "margem de erro" em vez de IC.
Uma sexta página, **Torneios**, entra quando o item de páginas de torneio for feito.

## Como funciona
O Python é o motor: baixa a base, monta a população e exporta JSON. O site só desenha e filtra no navegador.
```
dados/      baixar.py (CSVs da TML, 1991+) → preparar_populacao.py (base/populacao.parquet, com data, ids e ordem)
tenis/      estatistica.py, analises.py (critérios, líderes, perfis), elo.py, exportacao.py, idiomas.py (rótulos em inglês)
scripts/    exportar_site.py (gera site/data/*.json) · validar_estatistica.py (confere contra o scipy)
tenis/      … achados.py (números da página inicial), corrida.py, h2h.py, numero1.py (os nº 1), ganhar.py (o que faz ganhar), pressao.py (acima do esperado)
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
python scripts/validar_ganhar.py           # o que faz ganhar: logística × scipy, ordem estável, um ponto é um ponto
python scripts/validar_pressao.py          # pressão: modelos de game/tie-break/set, circuito = 0, estabilidade, nº 1
python -m http.server 8600 -d site     # http://localhost:8600
```

## Atualização automática
A Action [`atualizar.yml`](.github/workflows/atualizar.yml) roda no dia 3 de cada mês (ou à mão, em *Actions*):
1. `dados/baixar.py` baixa de novo as duas últimas temporadas e grava `dados/base/fonte.json`, o sha256 de cada CSV;
2. se esse arquivo não mudou, a TML não tem partidas novas e a Action para aí;
3. se mudou, refaz a base, exporta o site e roda as cinco validações; passando, faz o commit e publica.

**Temporada em andamento:** entra parcial. Elo, títulos, confrontos e perfis usam todas as partidas; as contas
**por temporada** (linha do tempo, nº 1 de cada ano, temporadas dos nº 1) usam só temporadas completas, e a
temporada termina com o ATP Finals (sem partidas desde 1º/nov, ela ainda está em andamento). "Jogador ativo" é
quem jogou nos 12 meses antes da última data da base. O selo "dados até" sai de `resumo_populacao.json`.

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
