"""Corrida de títulos e Slams por idade (dados/base/titulos.parquet).

Comparar épocas por idade é justo e factual: "quantos Slams cada um tinha aos 22 anos" não depende de Elo
nem de raquete. Para quem jogou antes de 1991 só os Slams estão completos (ver dados/preparar_titulos.py).
"""
from __future__ import annotations

import pandas as pd

NIVEL_COD = {"Grand Slam": "G", "ATP Finals": "F", "Masters 1000": "M", "ATP 500": "5", "ATP 250": "2"}


def exportar(titulos: pd.DataFrame, pop: pd.DataFrame, min_titulos: int = 10) -> dict:
    """Uma lista de títulos (idade, nível, torneio, ano) por jogador que ganhou ≥ 1 Slam ou ≥ min_titulos títulos.

    Marcas por jogador:
    - "so_slams": todos os títulos são de antes de 1991 → só a corrida de Slams vale;
    - "antes_1991": jogou antes de 1991 (Slam antes de 1991 ou estreou na base em 1991 com 21+ anos) → na
      corrida de títulos faltam os títulos não-Slam de antes de 1991.
    """
    t = titulos.dropna(subset=["idade"]).copy()
    slams = t[t["nivel"] == "Grand Slam"].groupby("vencedor").size()
    total = t[t["fonte"] == "1991+"].groupby("vencedor").size()
    nomes = sorted(set(slams.index) | set(total[total >= min_titulos].index))
    estreia = pd.concat([pop[["vencedor", "ano", "idade_vencedor"]].set_axis(["nome", "ano", "idade"], axis=1),
                         pop[["perdedor", "ano", "idade_perdedor"]].set_axis(["nome", "ano", "idade"], axis=1)])
    estreia = estreia.sort_values("ano").groupby("nome").first()
    jogadores = {}
    for nome in nomes:
        g = t[t["vencedor"] == nome].sort_values("data")
        antes = bool((g["fonte"] == "slam_antes_1991").any() or
                     (nome in estreia.index and estreia.loc[nome, "ano"] <= 1991 and (estreia.loc[nome, "idade"] or 0) >= 21))
        jogadores[nome] = {
            "t": [[round(float(r.idade), 2), NIVEL_COD[r.nivel], r.torneio, int(r.ano)] for r in g.itertuples()],
            "so_slams": bool((g["fonte"] == "slam_antes_1991").all()),
            "antes_1991": antes,
        }
    return {"jogadores": jogadores, "niveis": {v: k for k, v in NIVEL_COD.items()},
            "ano_fim": int(t["ano"].max()), "slams_desde": int(t[t["fonte"] == "slam_antes_1991"]["ano"].min())}
