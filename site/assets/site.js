/* Navegação do site "Tênis em números" (lida por assets/comum.js). Carregar ANTES de comum.js.
   idiomas: true liga o seletor PT/EN; cada texto é "igual nos dois" ou ["português", "English"]. */
window.SITE = {
  idiomas: true,
  marca: ["Tênis em números", "Tennis by numbers"],
  paginas: [
    ["index.html", ["Início", "Home"], ["Achados", "Findings"]],
    ["epocas.html", ["Elo · auge", "Elo · peak"], ["Épocas", "Eras"]],
    ["jogadores.html", ["Vestiário", "Locker room"], ["Jogadores", "Players"]],
    ["torneios.html", ["Quadra central", "Centre court"], ["Torneios", "Tournaments"]],
    ["jogo.html", "Tie-break", ["O jogo", "The game"]],
    ["sobre.html", ["Bastidores", "Behind the scenes"], ["Sobre os dados", "About the data"]],
  ],
  extras: null,
  autor: { nome: "Gabriel Isoton De David", linkedin: ["https://www.linkedin.com/in/gabriel-isoton-de-david/", "https://www.linkedin.com/in/gabriel-isoton-de-david/?locale=en-US"], github: "https://github.com/gabrielisoton/tenis-atp" },
  rodape: ["Projeto pessoal de analytics de tênis", "Personal tennis analytics project"],
};
