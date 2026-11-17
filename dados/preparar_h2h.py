"""Passo 4 — partidas para os CONFRONTOS DIRETOS (H2H), com a mesma regra do H2H oficial da ATP.

Diferente da população (que serve às estatísticas), aqui entra tudo que conta num confronto direto:
- circuito principal (Grand Slams, ATP Finals, Masters 1000, ATP 500/250), Copa Davis, Olimpíadas e as
  competições por equipes da ATP (World Team Cup, ATP Cup, United Cup); fora a Laver Cup e a Grand Slam Cup
  (exibições);
- partidas com abandono (RET) ou desclassificação (DEF) contam; W/O não conta.
Conferido com os H2H oficiais: Djokovic × Nadal 31–29, Federer × Nadal 16–24, Federer × Djokovic 23–27,
Murray × Djokovic 11–25, Alcaraz × Sinner 10–6 (até 2025). Partidas antes de 1991 não estão na base.

Saída: dados/base/h2h.parquet (pontos de cada lado só quando as estatísticas são consistentes, como na
população: pontos ≥ 4 × games vencidos).
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
RAW = BASE / "base" / "raw"
SAIDA = BASE / "base" / "h2h.parquet"
NIVEIS = {"G": "Grand Slam", "F": "ATP Finals", "M": "Masters 1000", "500": "ATP 500", "250": "ATP 250",
          "D": "Copa Davis", "O": "Olimpíadas", "A": "Equipes ATP"}
EXCLUIR_A = r"Laver|Grand Slam Cup"
SUPERFICIES = {"Hard": "Dura", "Clay": "Saibro", "Grass": "Grama", "Carpet": "Carpete"}
RODADAS = {"R128": "1ª rodada (R128)", "R64": "R64", "R32": "R32", "R16": "Oitavas (R16)", "QF": "Quartas",
           "SF": "Semifinal", "F": "Final", "RR": "Fase de grupos"}
SET_RE = re.compile(r"(\d+)-(\d+)")
ANO_FIM = 2025


def main() -> None:
    d = pd.concat([pd.read_csv(f, low_memory=False) for f in sorted(RAW.glob("*.csv"))], ignore_index=True)
    d["lv"] = d["tourney_level"].astype(str)
    ano = d["tourney_date"].astype(str).str[:4].astype(int)
    placar = d["score"].astype(str)
    ok = (d["lv"].isin(NIVEIS) & ~((d["lv"] == "A") & d["tourney_name"].str.contains(EXCLUIR_A, case=False, na=False))
          & ~placar.str.contains("W/O|Walkover", case=False) & (ano <= ANO_FIM))
    d = d[ok].copy()
    data = pd.to_datetime(d["tourney_date"].astype(str), format="%Y%m%d")
    games = d["score"].astype(str).map(lambda s: [tuple(map(int, x)) for x in SET_RE.findall(s)])
    gv, gp = games.map(lambda g: sum(a for a, _ in g)), games.map(lambda g: sum(b for _, b in g))
    v_sv, p_sv = d["w_1stWon"] + d["w_2ndWon"], d["l_1stWon"] + d["l_2ndWon"]
    pv = v_sv + (d["l_svpt"] - p_sv)
    pp = d["w_svpt"] + d["l_svpt"] - pv
    stats_ok = (d[["w_svpt", "l_svpt", "w_1stWon", "w_2ndWon", "l_1stWon", "l_2ndWon"]].notna().all(axis=1)
                & (d["w_svpt"] > 0) & (d["l_svpt"] > 0) & (pv >= 4 * gv) & (pp >= 4 * gp))
    h = pd.DataFrame({
        "data": data.dt.strftime("%Y-%m-%d"), "ano": data.dt.year, "id_torneio": d["tourney_id"].astype(str),
        "torneio": d["tourney_name"], "nivel": d["lv"].map(NIVEIS), "superficie": d["surface"].map(SUPERFICIES),
        "rodada": d["round"].map(RODADAS).fillna(d["round"]), "ordem": d["match_num"],
        "id_vencedor": d["winner_id"].astype(str), "vencedor": d["winner_name"],
        "id_perdedor": d["loser_id"].astype(str), "perdedor": d["loser_name"], "placar": d["score"].astype(str),
        "abandono": placar[d.index].str.contains("RET|DEF", regex=True),
        "v_sv_pts": d["w_svpt"].where(stats_ok), "v_sv_won": v_sv.where(stats_ok),
        "p_sv_pts": d["l_svpt"].where(stats_ok), "p_sv_won": p_sv.where(stats_ok),
    })
    # um nome por id, igual à população (homônimos já separados lá)
    pop = pd.read_parquet(BASE / "base" / "populacao.parquet")
    nomes = pd.concat([pop[["id_vencedor", "vencedor"]].set_axis(["id", "nome"], axis=1),
                       pop[["id_perdedor", "perdedor"]].set_axis(["id", "nome"], axis=1)]).drop_duplicates("id").set_index("id")["nome"]
    for lado in ("vencedor", "perdedor"):
        h[lado] = h[f"id_{lado}"].map(nomes).fillna(h[lado])
    h = h.sort_values(["data", "id_torneio", "ordem"], kind="stable").reset_index(drop=True)
    h.to_parquet(SAIDA, index=False)
    print(f"{len(h)} partidas ({h['abandono'].sum()} com abandono, {h['v_sv_pts'].notna().mean():.1%} com estatísticas) → {SAIDA.name}")
    print(h["nivel"].value_counts().to_dict())


if __name__ == "__main__":
    main()
