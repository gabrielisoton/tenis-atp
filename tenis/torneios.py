"""Página Torneios: um índice e um arquivo por torneio (carregado só quando a pessoa escolhe o torneio).

Cada arquivo traz os campeões de cada ano, os maiores campeões, os recordes, a "velocidade" da quadra (aces por game de
saque comparados com o circuito na mesma superfície e no mesmo ano) e a chave completa de cada edição. Os nomes dos
jogadores vão numa lista e as partidas guardam só o índice, para o arquivo ficar pequeno.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ORDEM_GS = {"580": 0, "520": 1, "540": 2, "560": 3}
ORDEM_NIVEL = {"Grand Slam": 0, "ATP Finals": 1, "Masters 1000": 2, "ATP 500": 3, "ATP 250": 4}
RODADAS = ["R128", "R64", "R32", "R16", "QF", "SF", "F", "RR"]
MIN_EDICOES = 3


def _limpo(v):
    return None if pd.isna(v) else v


def exportar(t: pd.DataFrame, saida: Path) -> dict:
    saida.mkdir(parents=True, exist_ok=True)
    novos = t[~t["antigo"]]
    # circuito: aces por game de saque por ano e superfície (referência da "velocidade")
    ok = novos.dropna(subset=["aces", "games_saque"])
    ok = ok[ok["games_saque"] > 0]
    circ = ok.groupby(["ano", "superficie"])[["aces", "games_saque"]].sum()
    circ = (circ["aces"] / circ["games_saque"]).to_dict()
    indice = []
    for cod, g in novos.groupby("cod"):
        anos = sorted(g["ano"].unique())
        if len(anos) < MIN_EDICOES:
            continue
        ult = g[g["ano"] == anos[-1]].iloc[0]
        todas = t[t["cod"] == cod]
        fin = todas[todas["rodada"] == "F"].sort_values("ano")
        nomes = sorted(set(g["vencedor"]) | set(g["perdedor"]) | set(fin["vencedor"]) | set(fin["perdedor"]))
        ix = {n: i for i, n in enumerate(nomes)}
        campeoes = [{"ano": int(r.ano), "campeao": r.vencedor, "vice": r.perdedor, "placar": r.placar,
                     "idade": _limpo(r.idade_v), "rank": None if pd.isna(r.rank_v) else int(r.rank_v), "minutos": None if pd.isna(r.minutos) else int(r.minutos)}
                    for r in fin.itertuples()]
        donos = fin["vencedor"].value_counts()
        com_idade = [c for c in campeoes if c["idade"] is not None]
        com_rank = [c for c in campeoes if c["rank"] is not None]
        com_min = [c for c in campeoes if c["minutos"] is not None]
        recordes = {
            "mais_jovem": min(com_idade, key=lambda c: c["idade"]) if com_idade else None,
            "mais_velho": max(com_idade, key=lambda c: c["idade"]) if com_idade else None,
            "pior_ranking": max(com_rank, key=lambda c: c["rank"]) if com_rank else None,
            "final_mais_longa": max(com_min, key=lambda c: c["minutos"]) if com_min else None,
        }
        # velocidade: aces por game de saque do torneio × circuito (mesma superfície, mesmo ano)
        vel = []
        for ano, ga in g.dropna(subset=["aces", "games_saque"]).groupby("ano"):
            gs = ga["games_saque"].sum()
            if gs >= 150:
                ref = circ.get((ano, ga["superficie"].iloc[0]))
                vel.append({"ano": int(ano), "aces": round(float(ga["aces"].sum() / gs), 3), "circuito": None if ref is None else round(float(ref), 3)})
        # chaves: [rodada, vencedor, perdedor, seed_v, seed_p, entrada_v, entrada_p, placar]
        chaves = {}
        for ano, ga in g.groupby("ano"):
            ga = ga.assign(r=ga["rodada"].map({r: i for i, r in enumerate(RODADAS)})).sort_values(["r", "ordem"])
            chaves[str(int(ano))] = [[int(r.r), ix[r.vencedor], ix[r.perdedor], _limpo(r.seed_v), _limpo(r.seed_p), r.entrada_v, r.entrada_p, r.placar]
                                     for r in ga.itertuples()]
        arq = {"cod": cod, "nome": ult["torneio"], "nomes_antigos": sorted(set(g["torneio"]) - {ult["torneio"]}), "nivel": ult["nivel"],
               "superficie": ult["superficie"], "anos": [int(a) for a in anos], "jogadores": nomes, "campeoes": campeoes,
               "donos": [[k, int(v)] for k, v in donos.head(10).items()], "recordes": recordes, "velocidade": vel,
               "rodadas": RODADAS, "chaves": chaves}
        (saida / f"{cod}.json").write_text(json.dumps(arq, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        indice.append({"cod": cod, "nome": ult["torneio"], "nivel": ult["nivel"], "superficie": ult["superficie"],
                       "anos": [int(anos[0]), int(anos[-1])], "edicoes": len(anos),
                       "dono": [donos.index[0], int(donos.iloc[0])] if len(donos) else None})
    indice.sort(key=lambda r: (ORDEM_GS.get(r["cod"], 9), ORDEM_NIVEL.get(r["nivel"], 9), r["nome"]))
    return {"torneios": indice, "min_edicoes": MIN_EDICOES}
