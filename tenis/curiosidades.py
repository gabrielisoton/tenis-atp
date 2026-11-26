"""Curiosidades do circuito: as histórias que fazem um fã querer explorar.

- Maiores zebras: o vencedor tinha a menor chance antes do jogo, pelo Elo (média do geral com o da superfície,
  calibrada como no resto do site). Só entre jogadores com 30+ partidas (Elo já assentado) e fora do aquecimento.
- Viradas de 0–2 em sets (melhor de 5), jogos mais longos, mais aces numa partida, pneus (sets 6-0),
  maiores sequências de vitórias e quem mais venceu o nº 1 do mundo.
- Vencer perdendo nos pontos e o favorito × a zebra vêm de análises que já existem (sem conta nova).
Tudo só com partidas concluídas do circuito principal (a população).
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from tenis import elo

SET_RE = re.compile(r"(\d+)-(\d+)")


def _sets(placar: pd.Series) -> pd.Series:
    return placar.astype(str).map(lambda s: [tuple(map(int, x)) for x in SET_RE.findall(s)])


def _partida(r) -> dict:
    return {"ano": int(r.ano), "torneio": r.torneio, "nivel": r.nivel, "rodada": r.rodada, "vencedor": r.vencedor,
            "perdedor": r.perdedor, "placar": r.placar}


def zebras(pop: pd.DataFrame, n: int = 10) -> dict:
    d = elo.calcular(pop)
    mv, mp = (d["elo_v"] + d["elo_sup_v"]) / 2, (d["elo_p"] + d["elo_sup_p"]) / 2
    d["chance"] = elo.chance(mv, mp, elo.ESCALA_PROB)
    ok = d[~d["ano"].between(*elo.AQUECIMENTO) & (d["n_v"] >= 30) & (d["n_p"] >= 30)]

    def lista(x):
        return [{**_partida(r), "chance": round(float(r.chance), 4),
                 "rank_v": None if pd.isna(r.ranking_vencedor) else int(r.ranking_vencedor),
                 "rank_p": None if pd.isna(r.ranking_perdedor) else int(r.ranking_perdedor)}
                for r in x.nsmallest(n, "chance").itertuples()]
    return {"geral": lista(ok), "slams": lista(ok[ok["nivel"] == "Grand Slam"]),
            "contra_n1": lista(ok[ok["ranking_perdedor"] == 1])}


def viradas(pop: pd.DataFrame) -> dict:
    st = _sets(pop["placar"])
    v = st.map(lambda L: len(L) == 5 and L[0][0] < L[0][1] and L[1][0] < L[1][1])
    x = pop[v]
    fin = x[(x["rodada"] == "Final") & (x["nivel"] == "Grand Slam")].sort_values("data")
    quem = x["vencedor"].value_counts().head(8)
    return {"n": int(v.sum()), "n_melhor_de_5": int((st.map(len) == 5).sum()),
            "finais_gs": [_partida(r) for r in fin.itertuples()],
            "jogadores": [[k, int(c)] for k, c in quem.items()]}


def longos(pop: pd.DataFrame, n: int = 8) -> list[dict]:
    x = pop.dropna(subset=["minutos"]).nlargest(n, "minutos")
    return [{**_partida(r), "minutos": int(r.minutos)} for r in x.itertuples()]


def aces(pop: pd.DataFrame, n: int = 8) -> list[dict]:
    lados = []
    for eu, ele, venceu in (("v", "p", True), ("p", "v", False)):
        lados.append(pd.DataFrame({"jogador": pop["vencedor" if venceu else "perdedor"], "adversario": pop["perdedor" if venceu else "vencedor"],
                                   "aces": pop[f"{eu}_ace"], "venceu": venceu, "ano": pop["ano"], "torneio": pop["torneio"],
                                   "rodada": pop["rodada"], "placar": pop["placar"], "minutos": pop["minutos"]}))
    x = pd.concat(lados).dropna(subset=["aces"]).nlargest(n, "aces")
    return [{"ano": int(r.ano), "torneio": r.torneio, "rodada": r.rodada, "jogador": r.jogador, "adversario": r.adversario,
             "aces": int(r.aces), "venceu": bool(r.venceu), "placar": r.placar} for r in x.itertuples()]


def pneus(pop: pd.DataFrame) -> dict:
    st = _sets(pop["placar"])
    triplo = pop[st.map(lambda L: len(L) == 3 and all(a == 6 and b == 0 for a, b in L))]
    dados = pd.concat([pd.Series(st.map(lambda L: sum(a == 6 and b == 0 for a, b in L)).values, index=pop["vencedor"].values),
                       pd.Series(st.map(lambda L: sum(a == 0 and b == 6 for a, b in L)).values, index=pop["perdedor"].values)])
    quem = dados.groupby(level=0).sum().sort_values(ascending=False).head(8)
    total = int(st.map(lambda L: sum((a, b) in ((6, 0), (0, 6)) for a, b in L)).sum())
    return {"triplo": [_partida(r) for r in triplo.itertuples()], "total_sets": total,
            "jogadores": [[k, int(c)] for k, c in quem.items()]}


def sequencias(pop: pd.DataFrame, n: int = 8) -> list[dict]:
    o = elo.ordenar(pop).reset_index(drop=True)
    lados = pd.concat([pd.DataFrame({"i": o.index, "jogador": o["vencedor"], "v": 1, "data": o["data"], "adv": o["perdedor"], "torneio": o["torneio"]}),
                       pd.DataFrame({"i": o.index, "jogador": o["perdedor"], "v": 0, "data": o["data"], "adv": o["vencedor"], "torneio": o["torneio"]})])
    lados = lados.sort_values(["jogador", "i"], kind="stable")
    melhores = []
    for nome, g in lados.groupby("jogador", sort=False):
        v = g["v"].to_numpy()
        if v.sum() < 40:
            continue
        # tamanho de cada sequência de vitórias; a melhor de cada jogador
        grupos = (v == 0).cumsum()
        tam = pd.Series(v).groupby(grupos).sum()
        k = int(tam.idxmax())
        idx = np.flatnonzero((grupos == k) & (v == 1))
        datas, fim = g["data"].to_numpy(), idx[-1] + 1
        melhores.append({"jogador": nome, "n": int(tam.max()), "inicio": str(datas[idx[0]])[:7], "fim": str(datas[idx[-1]])[:7],
                         "parou_em": None if fim >= len(g) else {"adversario": g["adv"].iloc[fim], "torneio": g["torneio"].iloc[fim],
                                                                 "ano": int(str(g["data"].iloc[fim])[:4])}})
    return sorted(melhores, key=lambda r: -r["n"])[:n]


def matadores_n1(pop: pd.DataFrame, n: int = 8) -> list[list]:
    v = pop[pop["ranking_perdedor"] == 1]["vencedor"].value_counts()
    jogos = pd.concat([pop[pop["ranking_perdedor"] == 1]["vencedor"], pop[pop["ranking_vencedor"] == 1]["perdedor"]]).value_counts()
    return [[k, int(c), int(jogos[k])] for k, c in v.head(n).items()]


def exportar(pop: pd.DataFrame, vp: dict, extras: dict) -> dict:
    fx = extras["faixas_ranking"]
    jg = vp["jogadores"]
    perdeu = sorted(zip(jg["jogador"], jg["perdeu_mais"]), key=lambda x: -x[1])[:6]
    return {
        "zebras": zebras(pop), "viradas": viradas(pop), "longos": longos(pop), "aces": aces(pop), "pneus": pneus(pop),
        "sequencias": sequencias(pop), "matadores_n1": matadores_n1(pop),
        # % entre as partidas sem empate em pontos (a mesma base do "ganhar mais pontos garante a vitória?")
        "venceu_perdendo": {"pct": round(vp["resumo"]["menos"] / (vp["resumo"]["n"] - vp["resumo"]["empates"]), 6), "finais_gs": vp["finais_gs"],
                            "jogadores": [[k, int(c)] for k, c in perdeu]},
        "favorito": {"perto": {"faixa": fx[0]["faixa"], "pct": fx[0]["pop_taxa"]}, "longe": {"faixa": fx[-1]["faixa"], "pct": fx[-1]["pop_taxa"]}},
    }
