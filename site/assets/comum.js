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
function plot(el, dados, layout = {}) {
  // com responsive: true o Plotly não estica a caixa do gráfico até a altura pedida: ela fica no min-height do CSS e
  // o fim do gráfico (eixo x) vazava por baixo do texto seguinte. A caixa passa a ter a altura do próprio gráfico.
  if (layout.height) (typeof el === "string" ? document.getElementById(el) : el).style.minHeight = layout.height + "px";
  return Plotly.react(el, dados, layoutBase(layout), PLOTLY_CONFIG);
}


function rodape() {
  const f = document.createElement("footer");
  f.innerHTML = `${SITE.rodape ? L(SITE.rodape) + "<br>" : ""}
    ${T("Dados", "Data")}: <a href="https://github.com/Tennismylife/TML-Database">TML-Database (Tennismylife)</a>, ATP <span data-meta="periodo"></span>, ${T("uso educacional", "educational use")}.`;
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
    el.textContent = typeof v === "number" && v > 9999 ? br(v, 0) : v;
  }));
}

document.addEventListener("DOMContentLoaded", () => { aplicarIdiomaFixo(); montarNav(); rodape(); preencherMeta(); });
