/* Seção "A base de dados" + "População" da página inicial.
   Uso: secaoBase(elemento, meta.resumo, { unidade, tituloPop }). O texto segue o idioma escolhido (T de comum.js). */

function secaoBase(el, r, { unidade = "Unidade amostral", tituloPop = "População e unidade amostral" } = {}) {
  const e = r.etapas_filtro;
  el.innerHTML = `
  <div class="grade g2">
    <div class="cartao">
      <h3>${T("Fonte e contexto", "Source and context")}</h3>
      <p><b>${T("Fonte", "Source")}:</b> <a href="https://github.com/Tennismylife/TML-Database">TML-Database (Tennismylife)</a>,
        ${T(`base pública de partidas da ATP desde 1968, com um arquivo por temporada, mantida pelo projeto`,
            `a public database of ATP matches since 1968, one file per season, maintained by the`)}
        <a href="https://stats.tennismylife.org/tennis-match-database">Tennismylife</a>${T("", " project")}.</p>
      <p><b>${T("Esquema", "Schema")}:</b> ${T(`o mesmo dicionário de dados da base <i>tennis_atp</i> de Jeff Sackmann (Tennis Abstract),
        referência em analytics de tênis. Essa base foi retirada do GitHub pelo autor em 2026.`,
        `the same data dictionary as Jeff Sackmann's <i>tennis_atp</i> database (Tennis Abstract), the reference in
        tennis analytics. The author took that database off GitHub in 2026.`)}</p>
      <p><b>${T("Conteúdo", "Contents")}:</b> ${T(`resultado e placar, perfil dos jogadores (idade, altura, mão, país, ranking) e
        estatísticas de saque de cada partida.`, `result and score, player profile (age, height, hand, country, ranking) and
        serve statistics for every match.`)}</p>
    </div>
    <div class="cartao">
      <h3>${tituloPop}</h3>
      <p><b>${T("População", "Population")}:</b> ${T(`todas as partidas de simples do circuito principal da ATP (Grand Slams, ATP Finals,
        Masters 1000, ATP 500 e 250) <b>concluídas</b> entre ${r.ano_min} e ${r.ano_max}.`, `every <b>completed</b> singles match on the main
        ATP tour (Grand Slams, ATP Finals, Masters 1000, ATP 500 and 250) between ${r.ano_min} and ${r.ano_max}.`)}</p>
      <p style="font-size:.9rem;color:var(--tinta-2)">${T(`<b>Por que ${r.ano_min}?</b> É a primeira temporada com estatísticas
        de saque, devolução e duração em quase todas as partidas (${br(r.pct_com_estatisticas, 1)}% da base). Antes disso a fonte só
        tem resultado e placar.`, `<b>Why ${r.ano_min}?</b> It is the first season with serve, return and duration stats for almost
        every match (${br(r.pct_com_estatisticas, 1)}% of the data). Before that the source only has results and scores.`)}</p>
      <p><b>${unidade}:</b> ${T("a partida", "the match")}.</p>
      <div class="funil">${[
        [T(`Partidas brutas ${r.periodo}`, `Raw matches ${r.periodo}`), e.partidas_brutas],
        [T("Só circuito principal", "Main tour only"), e.apos_filtro_nivel],
        [T("Só partidas concluídas = população", "Completed matches only = population"), e.apos_excluir_nao_concluidas],
      ].map(([rot, v], i) => `<div class="passo" style="margin-left:${i * 14}px;margin-right:${i * 14}px">
          <span>${rot}</span><b>${br(v, 0)}</b></div>`).join("")}</div>
      <p style="font-size:.9rem;color:var(--tinta-2)">${T(`Ficaram de fora a Copa Davis, as Olimpíadas, os eventos por
        equipes ou de exibição e as partidas não concluídas (W/O, abandono, desclassificação).`, `Left out: Davis Cup,
        the Olympics, team and exhibition events, and matches that were not completed (walkover, retirement, default).`)}</p>
    </div>
  </div>`;
}

function termosDeUso() {
  return `<p class="nota">${T(`<b>Termos de uso da base:</b> a TML permite uso pessoal, educacional e de pesquisa não
    comercial, com citação da fonte; uso comercial (inclusive treinar modelos de previsão para serviços comerciais)
    exige autorização.`, `<b>Database terms of use:</b> TML allows personal, educational and non-commercial research
    use, with attribution; commercial use (including training prediction models for commercial services) requires
    permission.`)} <a href="https://stats.tennismylife.org/tennis-match-database#usage-terms">${T("Termos atuais", "Current terms")}</a>.</p>`;
}
