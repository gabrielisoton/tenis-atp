"""Página Torneios: um índice e um arquivo por torneio (carregado só quando a pessoa escolhe o torneio).

Entram só os torneios principais (Grand Slams, ATP Finals, Masters 1000 e ATP 500, pelo nível atual); o índice traz
também um resumo de cada nível (quem mais venceu, recordes, quem venceu mais torneios diferentes), calculado pelo nível
que o torneio tinha em cada ano.

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
NIVEIS_SITE = ["Grand Slam", "Masters 1000", "ATP 500", "ATP Finals"]


def _limpo(v):
    return None if pd.isna(v) else v


def _recordes(fin: pd.DataFrame) -> dict:
    """Recordes de uma lista de finais (uma linha por final)."""
    def um(r):
        return {"ano": int(r.ano), "campeao": r.vencedor, "vice": r.perdedor, "placar": r.placar, "torneio": r.torneio, "cod": r.cod,
                "idade": _limpo(r.idade_v), "rank": None if pd.isna(r.rank_v) else int(r.rank_v), "minutos": None if pd.isna(r.minutos) else int(r.minutos)}
    def ext(col, maior):
        f = fin.dropna(subset=[col])
        if f.empty:
            return None
        return um(f.loc[f[col].idxmax() if maior else f[col].idxmin()])
    return {"mais_jovem": ext("idade_v", False), "mais_velho": ext("idade_v", True), "pior_ranking": ext("rank_v", True), "final_mais_longa": ext("minutos", True)}


def _niveis(t: pd.DataFrame, indice: list) -> dict:
    """Resumo de cada nível pelas finais disputadas naquele nível (o nível do ano, não o atual)."""
    fin = t[t["rodada"] == "F"].reset_index(drop=True)
    out = {}
    for niv in NIVEIS_SITE:
        f = fin[fin["nivel"] == niv]
        if f.empty:
            continue
        donos = f["vencedor"].value_counts()
        dif = f.groupby("vencedor")["cod"].nunique().sort_values(ascending=False, kind="stable")
        dif = dif[dif >= 2].head(8)
        out[niv] = {"desde": int(f["ano"].min()), "finais": int(len(f)), "torneios": sum(1 for r in indice if r["nivel"] == niv),
                    "donos": [[k, int(v)] for k, v in donos.head(10).items()],
                    "diferentes": [[k, int(v), int(donos[k])] for k, v in dif.items()],
                    "recordes": _recordes(f)}
    return out


def exportar(t: pd.DataFrame, saida: Path) -> dict:
    saida.mkdir(parents=True, exist_ok=True)
    t = t[~t["torneio"].str.contains("Next Gen", case=False, na=False)]  # o Next Gen não é o ATP Finals
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
        if ult["nivel"] not in NIVEIS_SITE:
            continue
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
        vm = [v["aces"] for v in vel]; vc = [v["circuito"] for v in vel if v["circuito"]]
        indice.append({"cod": cod, "nome": ult["torneio"], "nivel": ult["nivel"], "superficie": ult["superficie"],
                       "anos": [int(anos[0]), int(anos[-1])], "edicoes": len(anos),
                       "dono": [donos.index[0], int(donos.iloc[0])] if len(donos) else None,
                       "ultimo": [campeoes[-1]["campeao"], campeoes[-1]["ano"]] if campeoes else None,
                       "vel": round(float((sum(vm) / len(vm)) / (sum(vc) / len(vc)) - 1), 3) if vm and vc else None})
    indice.sort(key=lambda r: (ORDEM_GS.get(r["cod"], 9), ORDEM_NIVEL.get(r["nivel"], 9), r["nome"]))
    # arquivos de torneios que saíram do site (ATP 250)
    ficam = {f"{r['cod']}.json" for r in indice} | {"indice.json"}
    for f in saida.glob("*.json"):
        if f.name not in ficam:
            f.unlink()
    return {"torneios": indice, "min_edicoes": MIN_EDICOES, "niveis": _niveis(t, indice)}
