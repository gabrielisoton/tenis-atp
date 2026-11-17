"""Os nº 1 do mundo: a jornada até o topo, o que todos têm em comum e o que cai depois do auge.

Grupo: todo jogador que entrou em alguma partida da base (1991+) como nº 1 do ranking.

- Jornada: indicadores por FASE de ranking (o ranking de entrada do próprio jogador em cada partida:
  > 50, 11–50, 4–10, 2–3, nº 1) e por temporada, em duas réguas: contra todos e só contra Top 10 (no
  topo os adversários são mais fortes, então a régua "contra Top 10" é a comparação justa).
- Ano da virada: a temporada com o maior salto na % de vitórias contra o Top 10 em relação à anterior
  (≥ 6 jogos contra Top 10 nas duas, salto ≥ 10 pontos, até o ano do 1º nº 1).
- Em comum: distância (z) de cada nº 1 para os jogadores com ≥ 100 partidas, só em critérios de jogo
  (fora vitórias, títulos e afins, que já definem quem é nº 1).
- Depois do topo: para quem já parou, a variação do auge sustentado (Elo) às duas últimas temporadas.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from tenis import analises as an
from tenis import elo

FASES = [(51, 99999, "> 50"), (11, 50, "11–50"), (4, 10, "4–10"), (2, 3, "2–3"), (1, 1, "nº 1")]
IND = {  # indicador: (numerador, denominador), somas dos componentes de analises.longo
    "vitorias": ("venceu", "partida"), "tpw": ("sv_won+ret_won", "sv_pts+ret_pts"), "saque": ("sv_won", "sv_pts"),
    "devolucao": ("ret_won", "ret_pts"), "primeiro_dentro": ("first_in", "sv_pts"), "ganhos_1": ("first_won", "first_in"),
    "ganhos_2": ("second_won", "second_pts"), "bp_salvos": ("bp_sav", "bp_fac"), "bp_convertidos": ("bp_conv", "bp_opp"),
}
CRIT_JOGO = ["primeiro_dentro", "ganhos_1", "ganhos_2", "aces_game", "df_game", "devolucao", "bp_convertidos",
             "bp_salvos", "tie_breaks", "decisivos"]


def _val(s: pd.Series, num: str, den: str) -> float | None:
    f = lambda e: float(sum(s[c] for c in e.split("+")))  # noqa: E731
    d = f(den)
    return round(f(num) / d, 5) if d else None


def _ind(s: pd.Series) -> dict:
    return {"n": int(s["partida"]), **{k: _val(s, *v) for k, v in IND.items()}}


def _fase(r) -> str | None:
    if pd.isna(r):
        return None
    return next(n for a, b, n in FASES if a <= r <= b)


def exportar(pop: pd.DataFrame, titulos: pd.DataFrame) -> dict:
    lg = an.longo(pop)
    nomes = sorted(set(pop.loc[pop["ranking_vencedor"] == 1, "vencedor"]) | set(pop.loc[pop["ranking_perdedor"] == 1, "perdedor"]))
    dep = elo.depois(elo.calcular(pop)).assign(dt=lambda x: pd.to_datetime(x["data"]))
    auges = {r["jogador"]: r for r in elo.auges(dep, 0)}
    tab = an.tabela_jogadores(lg)                                    # referência: ≥ 100 partidas na base
    ref = tab[CRIT_JOGO].copy()
    ref["df_game"] = -ref["df_game"]                                 # menos duplas faltas = melhor
    z = (ref - ref.mean()) / ref.std()
    corte = pd.Timestamp(pop["data"].max())                         # ativo = jogou nos 12 meses antes do corte
    completa = an.ultima_temporada_completa(pop)                    # temporadas: só as completas
    datas = pd.concat([pop[["vencedor", "data", "ranking_vencedor"]].set_axis(["nome", "data", "rk"], axis=1),
                       pop[["perdedor", "data", "ranking_perdedor"]].set_axis(["nome", "data", "rk"], axis=1)])
    jogadores, queda = {}, []
    for nome in nomes:
        g = lg[lg["jogador"] == nome].copy()
        g["fase"] = g["rank"].map(_fase)
        # cobertura da jornada: começa na base fora do Top 30? já estava no circuito antes de 1991?
        temp = g.groupby("ano")[an.COMPONENTES].sum()
        temp10 = temp[temp["partida"] >= 10]
        rk_ini = float(g[g["ano"] == temp10.index.min()]["rank"].median())
        idade_ini = float(g[g["ano"] == temp10.index.min()]["idade"].median())
        cobertura = "antes_1991" if temp10.index.min() <= 1992 and idade_ini >= 22 else ("ja_no_topo" if rk_ini <= 30 else "completa")
        fases = {}
        for f in [x[2] for x in FASES]:
            gf = g[g["fase"] == f]
            if len(gf):
                fases[f] = {"todos": _ind(gf[an.COMPONENTES].sum()),
                            "top10": _ind(gf[gf["rank_oponente"] <= 10][an.COMPONENTES].sum()) if (gf["rank_oponente"] <= 10).any() else None}
        # temporadas (com o melhor ranking e o Elo de fim de ano)
        d = dep[dep["jogador"] == nome]
        elo_fim = d.groupby("ano")["elo"].last()
        t10 = g[g["rank_oponente"] <= 10].groupby("ano")[["partida", "venceu"]].sum()
        temporadas = []
        for ano, s in temp.iterrows():
            if s["partida"] < 5 or ano > completa:
                continue
            temporadas.append({"ano": int(ano), "melhor_rank": None if g[g["ano"] == ano]["rank"].isna().all() else int(g[g["ano"] == ano]["rank"].min()),
                               **_ind(s), "n_top10": int(t10.loc[ano, "partida"]) if ano in t10.index else 0,
                               "vit_top10": round(float(t10.loc[ano, "venceu"] / t10.loc[ano, "partida"]), 4) if ano in t10.index and t10.loc[ano, "partida"] else None,
                               "elo": round(float(elo_fim[ano]), 1) if ano in elo_fim.index else None})
        # ano da virada: maior salto de vitórias contra Top 10 até o ano do 1º nº 1
        ano_n1 = int(g[g["rank"] == 1]["ano"].min())
        cand = [(t["ano"], t["vit_top10"] - p["vit_top10"], p["vit_top10"], t["vit_top10"]) for p, t in zip(temporadas, temporadas[1:])
                if t["ano"] == p["ano"] + 1 and t["ano"] <= ano_n1 and p["n_top10"] >= 6 and t["n_top10"] >= 6]
        melhor = max(cand, key=lambda c: c[1]) if cand else None
        virada = {"ano": melhor[0], "antes": round(melhor[2], 4), "depois": round(melhor[3], 4)} if melhor and melhor[1] >= 0.10 and cobertura != "antes_1991" else None
        # marcos: 1º título (1991+), 1º Slam (desde 1968), 1º nº 1
        tj = titulos[titulos["vencedor"] == nome].sort_values("data")
        tit91 = tj[tj["fonte"] == "1991+"]
        slams = tj[tj["nivel"] == "Grand Slam"]
        marcos = {"titulo": None if tit91.empty else {"data": tit91["data"].iloc[0], "torneio": tit91["torneio"].iloc[0]},
                  "slam": None if slams.empty else {"data": slams["data"].iloc[0], "torneio": slams["torneio"].iloc[0]},
                  "n1": datas[(datas["nome"] == nome) & (datas["rk"] == 1)]["data"].min(),
                  "titulos": int(len(tj[tj["fonte"] == "1991+"])), "slams": int(len(slams)),
                  "titulos_antes_1991_fora": cobertura == "antes_1991"}
        # Elo por idade (fim de cada mês), para comparar jornadas; idade em cada marco
        nasc = (d["dt"] - pd.to_timedelta(d["idade"] * 365.25, unit="D")).median()
        idade = lambda dt: None if pd.isna(nasc) or dt is None else round((pd.Timestamp(dt) - nasc).days / 365.25, 1)  # noqa: E731
        for k in ("titulo", "slam"):
            if marcos[k]:
                marcos[k]["idade"] = idade(marcos[k]["data"])
        marcos["n1_idade"] = idade(marcos["n1"])
        mes = d.set_index("dt")["elo"].resample("ME").last().dropna()
        idade_elo = {"idade": [round((t - nasc).days / 365.25, 2) for t in mes.index] if pd.notna(nasc) else [],
                     "elo": mes.round(1).tolist()}
        assin = z.loc[nome].sort_values(ascending=False) if nome in z.index else pd.Series(dtype=float)
        jogadores[nome] = {"cobertura": cobertura, "fases": fases, "temporadas": temporadas, "virada": virada, "marcos": marcos,
                           "idade_elo": idade_elo, "z": {k: round(float(v), 2) for k, v in assin.items()},
                           "auge": None if nome not in auges else {k: auges[nome][k] for k in ("auge", "auge_ini", "auge_fim", "auge_idade")},
                           "ativo": bool(d["dt"].max() > corte - pd.Timedelta(days=365))}
        # depois do topo: quem já parou, do ano do auge às duas últimas temporadas com ≥ 15 partidas
        t15 = temp[temp["partida"] >= 15]
        if not jogadores[nome]["ativo"] and nome in auges:
            ano_pico = int(auges[nome]["auge_fim"][:4])
            fim = list(t15.index[-2:])
            if ano_pico in t15.index and ano_pico not in fim:
                p, u = _ind(t15.loc[ano_pico]), _ind(t15.loc[fim].sum())
                queda.append({"jogador": nome, "pico": ano_pico, "fim": [int(fim[0]), int(fim[-1])],
                              **{k: None if p[k] is None or u[k] is None else round(u[k] - p[k], 5) for k in IND}})
    # o que todos têm em comum
    Z = z.loc[[n for n in nomes if n in z.index]]
    comum = [{"crit": c, "z": round(float(Z[c].mean()), 3), "ic": round(float(1.96 * Z[c].std() / np.sqrt(len(Z))), 3),
              "pct_acima_1": round(float((Z[c] > 1).mean()), 3)} for c in CRIT_JOGO]
    comum.sort(key=lambda r: -r["z"])
    Q = pd.DataFrame(queda)
    depois = {"n": int(len(Q)), "jogadores": queda,
              "media": sorted([{"ind": k, "media": round(float(Q[k].mean()), 5), "ep": round(float(Q[k].std() / np.sqrt(len(Q))), 5),
                                "caiu_em": int((Q[k] < 0).sum())} for k in IND], key=lambda r: r["media"])} if len(Q) else None
    return {"jogadores": jogadores, "em_comum": comum, "n_referencia": int(len(tab)), "depois_do_topo": depois,
            "fases": [x[2] for x in FASES], "criterios": CRIT_JOGO}
