/* Navegação do site "Tênis em números" (lida por assets/comum.js). Carregar ANTES de comum.js.
   idiomas: true liga o seletor PT/EN; cada texto é "igual nos dois" ou ["português", "English"]. */
window.SITE = {
  idiomas: true,
  marca: ["Tênis em números", "Tennis by numbers"],
  paginas: [
    ["index.html", ["Início", "Home"], ["Base e população", "Data and population"]],
    ["circuito.html", ["Visão geral", "Overview"], ["O circuito", "The tour"]],
    ["explorar.html", "Tie-break", ["Explorar", "Explore"]],
    ["jogadores.html", ["Vestiário", "Locker room"], ["Jogadores", "Players"]],
    ["elo.html", ["Épocas", "Eras"], "Elo"],
    ["rivalidades.html", ["Duelos", "Head to head"], ["Rivalidades", "Rivalries"]],
  ],
  extras: null,
  rodape: ["Projeto pessoal de analytics de tênis · <a href=\"https://github.com/gabrielisoton/tenis-atp\">código no GitHub</a>",
           "Personal tennis analytics project · <a href=\"https://github.com/gabrielisoton/tenis-atp\">code on GitHub</a>"],
};
