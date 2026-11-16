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
  ],
  extras: { rotulo: ["Origem", "Origin"],
            dica: ["O projeto nasceu deste trabalho de disciplina", "The project grew out of this course assignment"],
            itens: [["https://gabrielisoton.github.io/ia003-tenis-estatistica/", "IA003 · UFRGS", ["Trabalho da disciplina", "Course assignment (in Portuguese)"]]] },
  rodape: ["Projeto pessoal de analytics de tênis · nasceu do trabalho final da IA003 (Especialização em IA, UFRGS)",
           "Personal tennis analytics project · grew out of the IA003 final assignment (AI specialization, UFRGS, Brazil)"],
};
