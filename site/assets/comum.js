/* Funções comuns às páginas do site. Os números vêm de data/*.json, gerados por scripts/exportar_site.py;
   o site só desenha e filtra (os cálculos de jogadores são conferidos com o Python em jogadores.js → conferir()).
   A barra de navegação é declarada em assets/site.js (window.SITE). */

const CORES = {
  pop: "#6250d6", amostra: "#c98500", top: "#d55181", demais: "#898781",
  neutra: "#898781", erro: "#d03b3b", ok: "#0ca30c",
  sup: { "Dura": "#2a78d6", "Saibro": "#eb6834", "Grama": "#1baf7a", "Carpete": "#898781",
         "Hard": "#2a78d6", "Clay": "#eb6834", "Grass": "#1baf7a", "Carpet": "#898781" },
};

// navegação: cada site define window.SITE em assets/site.js
//   { marca, paginas: [[href, sobretítulo, nome]], extras: { rotulo, dica, itens: [[href, sobretítulo, nome]] }, rodape,
//     idiomas }  — com idiomas: true, cada texto pode ser [pt, en] e aparece o seletor PT/EN na barra
const SITE = window.SITE || { marca: "Estatística no Tênis", paginas: [], extras: null, rodape: "" };

/* ---------------- idioma ----------------
   Só um site que declara SITE.idiomas troca de idioma: outros sites no mesmo domínio github.io que não declaram
   continuam em português, mesmo que o visitante tenha escolhido inglês aqui (a escolha fica no localStorage).
   - texto fixo no HTML: <span data-l="pt">…</span><span data-l="en">…</span> (o CSS esconde o outro idioma);
     atributos: data-en-title, data-en-placeholder, data-en-aria-label; <title data-en="…">
   - texto montado no JS: T("português", "English")
   - rótulos que vêm dos dados (superfícies, critérios…): tr(rótulo), com o dicionário data/en.json
     (gerado de tenis/idiomas.py) */
const IDIOMA = (() => {
  if (!SITE.idiomas) return "pt";
  const q = new URLSearchParams(location.search).get("lang");
  try {
    if (q === "en" || q === "pt") localStorage.setItem("lingua", q);
    return (q || localStorage.getItem("lingua")) === "en" ? "en" : "pt";
  } catch (e) { return q === "en" ? "en" : "pt"; }
})();
const EM_INGLES = IDIOMA === "en";
document.documentElement.dataset.lang = IDIOMA;
if (EM_INGLES) document.documentElement.lang = "en";
const T = (pt, en) => EM_INGLES ? en : pt;
const L = x => Array.isArray(x) ? T(x[0], x[1]) : x;          // texto do site.js: "pt" ou ["pt", "en"]
let _EN = {};
const tr = s => EM_INGLES && typeof s === "string" ? (_EN[s] ?? s) : s;
const ordinal = n => !EM_INGLES ? `${n}º`
  : n + ((n % 100 >= 11 && n % 100 <= 13) ? "th" : ({ 1: "st", 2: "nd", 3: "rd" }[n % 10] || "th"));
function trocarIdioma(l) {
  try { localStorage.setItem("lingua", l); } catch (e) { /* sem armazenamento: vale só a URL */ }
  const u = new URL(location.href);
  u.searchParams.set("lang", l);
  location.replace(u);
}
function aplicarIdiomaFixo() {
  if (!EM_INGLES) return;
  const t = document.querySelector("title[data-en]"); if (t) document.title = t.dataset.en;
  for (const a of ["title", "placeholder", "aria-label"])
    document.querySelectorAll(`[data-en-${a}]`).forEach(el => el.setAttribute(a, el.getAttribute(`data-en-${a}`)));
}

/* ---------------- dados ---------------- */
const _cache = {};
const _json = nome => fetch(`data/${nome}.json`).then(r => {
  if (!r.ok) throw new Error(`Falha ao carregar ${nome}.json`);
  return r.json();
});
// em inglês, o dicionário dos rótulos chega antes de qualquer dado (tr() já funciona quando a página desenha)
const _dicionario = EM_INGLES ? _json("en").then(d => { _EN = d; }).catch(() => {}) : Promise.resolve();
async function carregar(nome) {
  if (!_cache[nome]) _cache[nome] = _dicionario.then(() => _json(nome));
  return _cache[nome];
}

/* ---------------- formatação (pt-BR, ou en-US no site em inglês) ---------------- */
function br(x, casas = 2) {
  if (x === null || x === undefined || Number.isNaN(x)) return "—";
  return Number(x).toLocaleString(EM_INGLES ? "en-US" : "pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas });
}
const dataCurta = d => d ? new Date(d + "T12:00:00").toLocaleDateString(EM_INGLES ? "en-GB" : "pt-BR") : "—";
const pct = (x, casas = 1) => (x === null || x === undefined) ? "—" : br(100 * x, casas) + "%";

/* ---------------- navegação ---------------- */
function montarNav() {
  const atual = location.pathname.split("/").pop() || "index.html";
  const nav = document.createElement("nav");
  nav.className = "nav";
  nav.innerHTML = `<div class="nav-dentro">
    <a class="marca" href="index.html"><span class="bola"></span> ${L(SITE.marca)}</a>
    ${SITE.paginas.map(([href, set, nome]) =>
      `<a class="item ${href === atual ? "ativo" : ""}" href="${href}"><small>${L(set)}</small>${L(nome)}</a>`).join("")}
    ${SITE.extras ? `<span class="nav-sep" title="${L(SITE.extras.dica) || ""}">${L(SITE.extras.rotulo)}</span>` +
      SITE.extras.itens.map(([href, set, nome]) =>
        `<a class="item extra ${href === atual ? "ativo" : ""}" href="${href}"><small>${L(set)}</small>${L(nome)}</a>`).join("") : ""}
    ${SITE.idiomas ? `<span class="idioma" role="group" aria-label="Idioma · Language">${[["pt", "Português"], ["en", "English"]]
      .map(([l, n]) => `<button type="button" data-idioma="${l}" class="${l === IDIOMA ? "on" : ""}" title="${n}" lang="${l}"
        aria-pressed="${l === IDIOMA}">${l.toUpperCase()}</button>`).join("")}</span>` : ""}
  </div>`;
  nav.querySelectorAll("[data-idioma]").forEach(b => b.addEventListener("click", () => {
    if (b.dataset.idioma !== IDIOMA) trocarIdioma(b.dataset.idioma); }));
  document.body.prepend(nav);
}

/* ---------------- quadra em SVG (fundo do hero) ---------------- */
function svgQuadra() {
  // proporções reais: 23,77 m × 10,97 m (duplas); simples 8,23 m; linha de saque a 6,40 m da rede
  return `<svg class="quadra" viewBox="0 0 1188 549" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
    <g fill="none" stroke="#fff" stroke-width="5">
      <rect x="20" y="20" width="1148" height="509"/>
      <line x1="20" y1="83" x2="1168" y2="83"/><line x1="20" y1="466" x2="1168" y2="466"/>
      <line x1="285" y1="83" x2="285" y2="466"/><line x1="903" y1="83" x2="903" y2="466"/>
      <line x1="285" y1="274.5" x2="903" y2="274.5"/>
      <line x1="594" y1="10" x2="594" y2="539" stroke-dasharray="4 6" stroke-width="7"/>
      <line x1="20" y1="274.5" x2="40" y2="274.5"/><line x1="1148" y1="274.5" x2="1168" y2="274.5"/>
    </g></svg>`;
}

/* ---------------- componentes ---------------- */
function placar(el, itens) {
  el.classList.add("placar");
  el.innerHTML = itens.map(i => `<div class="cel"><div class="rot">${i.rot}</div>
    <div class="num">${i.num}</div>${i.sub ? `<div class="sub">${i.sub}</div>` : ""}</div>`).join("");
}

function comoLer(texto) {
  return `<details class="como-ler"><summary>📖 ${T("Como ler", "How to read")}</summary><div>${texto}</div></details>`;
}

function katexEm(el, tex, display = true) {
  if (window.katex) katex.render(tex, el, { displayMode: display, throwOnError: false });
  else el.textContent = tex;
}

/* ---------------- Plotly: tema ---------------- */
const PLOTLY_CONFIG = { displayModeBar: false, responsive: true, locale: EM_INGLES ? "en" : "pt-BR" };
function layoutBase(extra = {}) {
  return Object.assign({
    font: { family: "Barlow, system-ui, sans-serif", size: 14, color: "#14211b" },
    paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
    separators: EM_INGLES ? ".," : ",.", margin: { l: 56, r: 18, t: 46, b: 52 },
    hoverlabel: { font: { family: "Barlow", size: 13 } },
    legend: { orientation: "h", y: 1.02, yanchor: "bottom", x: 0 },
    xaxis: { showgrid: false, zeroline: false, linecolor: "#c3c2b7", automargin: true },
    yaxis: { gridcolor: "rgba(137,135,129,.22)", zeroline: false, automargin: true },
    bargap: 0.25, barcornerradius: 4,
  }, extra);
}
/* no celular (tela estreita) os gráficos ficavam compridos e espremidos: margens fixas de até 220 px para os rótulos
   sobravam pouco espaço para as barras. Aqui, um ajuste só para todos: margens menores, rótulos longos abreviados,
   fonte e título menores, legenda embaixo e altura um pouco menor. */
const CELULAR = () => window.innerWidth < 600;
const abreviar = (t, n = 18) => typeof t === "string" && t.length > n ? t.slice(0, n - 1).trimEnd() + "…" : t;
function paraCelular(L, dados) {
  const m = L.margin || {};
  L.margin = { ...m, l: Math.min(m.l ?? 56, 96), r: Math.min(m.r ?? 18, 14), t: Math.min(m.t ?? 46, 64), b: Math.min(m.b ?? 52, 96) };
  L.font = { ...(L.font || {}), size: 12 };
  if (L.height) L.height = Math.max(280, Math.round(L.height * 0.85));
  if (L.title) L.title = { ...(typeof L.title === "string" ? { text: L.title } : L.title), font: { size: 14, family: "Barlow Condensed" } };
  if (L.legend) L.legend = { ...L.legend, font: { size: 11 } };
  // rótulos de categoria compridos (barras horizontais): abrevia só o texto do eixo, o dado e o hover continuam inteiros
  const cats = [...new Set(dados.filter(t => t.orientation === "h" && Array.isArray(t.y)).flatMap(t => t.y))];
  if (cats.some(c => typeof c === "string" && c.length > 18))
    L.yaxis = { ...(L.yaxis || {}), tickmode: "array", tickvals: cats, ticktext: cats.map(c => abreviar(c)), tickfont: { size: 11 } };
  return L;
}
function plot(el, dados, layout = {}) {
  let L = layoutBase(layout);
  if (CELULAR()) L = paraCelular(L, dados);
  // com responsive: true o Plotly não estica a caixa do gráfico até a altura pedida: ela fica no min-height do CSS e
  // o fim do gráfico (eixo x) vazava por baixo do texto seguinte. A caixa passa a ter a altura do próprio gráfico.
  if (L.height) (typeof el === "string" ? document.getElementById(el) : el).style.minHeight = L.height + "px";
  return Plotly.react(el, dados, L, PLOTLY_CONFIG);
}
/* a resposta da pergunta da aba em uma frase, logo abaixo do título */
function resposta(el, frase, sub = "") {
  (typeof el === "string" ? document.getElementById(el) : el).innerHTML = `<div class="resposta">${frase}${sub ? `<small>${sub}</small>` : ""}</div>`;
}
/* como ler em uma ou duas frases, sempre visível */
const lerCurto = texto => `<p class="ler">📖 ${texto}</p>`;


function rodape() {
  const f = document.createElement("footer");
  const A = SITE.autor;
  f.innerHTML = `${A ? `<span class="autor">${T("Desenvolvido por", "Built by")} <b>${A.nome}</b>${A.linkedin ? ` · <a href="${T(...A.linkedin)}" target="_blank" rel="noopener">LinkedIn</a>` : ""} · <a href="${A.github}">GitHub</a></span><br>` : ""}
    ${SITE.rodape ? L(SITE.rodape) + "<br>" : ""}
    ${T("Dados", "Data")}: <a href="https://github.com/Tennismylife/TML-Database">TML-Database (Tennismylife)</a>, ATP <span data-meta="periodo"></span>, ${T("uso educacional", "educational use")}.
    <span class="selo-dados">${T("Dados até", "Data up to")} <b data-meta="data_corte"></b> (<span data-meta="ultimos_torneios"></span>)</span>`;
  document.body.append(f);
}

/* abre a aba indicada no endereço (pagina.html#aba): procura o botão pelo id ou pelo data-a.
   Chamar DEPOIS de ligar os eventos das abas (algumas desenham o conteúdo no primeiro clique). */
function abrirAbaDoHash(sel) {
  const h = decodeURIComponent(location.hash.slice(1));
  if (!h) return;
  const b = document.querySelector(`${sel} button[data-a="${h}"], ${sel} button#${CSS.escape(h)}`);
  if (b && !b.classList.contains("on")) b.click();
}

/* números da base no texto fixo: <span data-meta="N|periodo|ano_min|ano_max|n_temporadas"></span>
   (vêm de data/meta.json, então o texto acompanha a base quando ela é atualizada) */
function preencherMeta() {
  const alvos = document.querySelectorAll("[data-meta]");
  if (!alvos.length) return;
  carregar("meta").then(m => alvos.forEach(el => {
    const v = m.resumo[el.dataset.meta];
    el.textContent = el.dataset.meta === "data_corte" ? dataCurta(v) : Array.isArray(v) ? v.join(T(" e ", " and "))
      : typeof v === "number" && v > 9999 ? br(v, 0) : v;
  }));
}

document.addEventListener("DOMContentLoaded", () => { aplicarIdiomaFixo(); montarNav(); rodape(); preencherMeta(); });
