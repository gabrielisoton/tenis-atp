/* Navegação do site "Tênis em números" (lida por assets/comum.js). Carregar ANTES de comum.js.
   idiomas: true liga o seletor PT/EN; cada texto é "igual nos dois" ou ["português", "English"]. */
window.SITE = {
  idiomas: true,
  marca: ["Tênis em números", "Tennis by numbers"],
  paginas: [
    ["index.html", ["Início", "Home"], ["Achados", "Findings"]],
    ["epocas.html", ["Elo · auge", "Elo · peak"], ["Épocas", "Eras"]],
    ["jogadores.html", ["Vestiário", "Locker room"], ["Jogadores", "Players"]],
    ["jogo.html", "Tie-break", ["O jogo", "The game"]],
    ["sobre.html", ["Bastidores", "Behind the scenes"], ["Sobre os dados", "About the data"]],
  ],
  extras: null,
  rodape: ["Projeto pessoal de analytics de tênis · <a href=\"https://github.com/gabrielisoton/tenis-atp\">código no GitHub</a>",
           "Personal tennis analytics project · <a href=\"https://github.com/gabrielisoton/tenis-atp\">code on GitHub</a>"],
};
