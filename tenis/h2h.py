"""Confrontos diretos (H2H) a partir de dados/base/h2h.parquet.

O site carrega um índice pequeno (nomes e as maiores rivalidades) e, quando o visitante escolhe um jogador,
só o arquivo daquele jogador (data/h2h/<id>.json), com todas as partidas dele. O confronto com qualquer
adversário sai desse arquivo.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

NIVEIS = ["Grand Slam", "ATP Finals", "Masters 1000", "ATP 500", "ATP 250", "Copa Davis", "Olimpíadas", "Equipes ATP"]
SUPS = ["Dura", "Saibro", "Grama", "Carpete"]
RODADAS = ["1ª rodada (R128)", "R64", "R32", "Oitavas (R16)", "Fase de grupos", "Quartas", "Semifinal", "Final"]


def _idx(serie: pd.Series, ordem: list) -> list:
    m = {v: i for i, v in enumerate(ordem)}
    return [m.get(v, -1) for v in serie]


def exportar(h: pd.DataFrame, saida: Path, min_partidas: int = 20, n_rivalidades: int = 40) -> dict:
    """Grava data/h2h/<id>.json para quem tem ≥ min_partidas e devolve o índice (data/h2h/indice.json)."""
    pasta = saida / "h2h"
    pasta.mkdir(parents=True, exist_ok=True)
    for f in pasta.glob("*.json"):
        f.unlink()
    lados = []
    for eu, ele, venceu in (("vencedor", "perdedor", 1), ("perdedor", "vencedor", 0)):
        x = pd.DataFrame({"i": h.index, "id": h[f"id_{eu}"], "nome": h[eu], "o": h[f"id_{ele}"], "v": venceu,
                          "sv_pts": h["v_sv_pts" if venceu else "p_sv_pts"], "sv_won": h["v_sv_won" if venceu else "p_sv_won"],
                          "ret_pts": h["p_sv_pts" if venceu else "v_sv_pts"],
                          "ret_won": (h["p_sv_pts"] - h["p_sv_won"]) if venceu else (h["v_sv_pts"] - h["v_sv_won"])})
        lados.append(x)
    longo = pd.concat(lados).sort_values("i", kind="stable")
    contagem = longo["id"].value_counts()
    nomes = longo.drop_duplicates("id").set_index("id")["nome"]
    torneios = sorted(h["torneio"].unique())                 # nome do torneio vira número (lista no índice)
    base = {"d": h["data"].str.replace("-", "").astype(int).tolist(), "t": _idx(h["torneio"], torneios), "n": _idx(h["nivel"], NIVEIS),
            "s": _idx(h["superficie"], SUPS), "r": _idx(h["rodada"], RODADAS), "p": h["placar"].tolist(),
            "a": h["abandono"].astype(int).tolist()}
    escritos = 0
    for jid, g in longo[longo["id"].isin(contagem[contagem >= min_partidas].index)].groupby("id"):
        ii = g["i"].to_numpy()
        st = [None if pd.isna(a) else [int(a), int(b), int(c), int(e)]
              for a, b, c, e in zip(g["sv_pts"], g["sv_won"], g["ret_pts"], g["ret_won"])]
        doc = {"id": jid, "nome": nomes[jid], **{k: [v[i] for i in ii] for k, v in base.items()},
               "o": g["o"].tolist(), "v": g["v"].astype(int).tolist(), "st": st}
        (pasta / f"{jid}.json").write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        escritos += 1
    # maiores rivalidades (pares com mais partidas)
    par = pd.DataFrame({"a": h[["id_vencedor", "id_perdedor"]].min(axis=1), "b": h[["id_vencedor", "id_perdedor"]].max(axis=1),
                        "va": (h["id_vencedor"] == h[["id_vencedor", "id_perdedor"]].min(axis=1)).astype(int)})
    riv = par.groupby(["a", "b"]).agg(n=("va", "size"), va=("va", "sum")).reset_index().sort_values("n", ascending=False).head(n_rivalidades)
    return {
        "jogadores": [[jid, nomes[jid], int(n)] for jid, n in contagem.items()],
        "com_arquivo": int(escritos), "min_partidas": min_partidas,
        "rivalidades": [[r.a, r.b, int(r.n), int(r.va), int(r.n - r.va)] for r in riv.itertuples()],
        "niveis": NIVEIS, "sups": SUPS, "rodadas": RODADAS, "torneios": torneios,
        "anos": [int(h["ano"].min()), int(h["ano"].max())],
    }
