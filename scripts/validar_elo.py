"""Valida o Elo (tenis/elo.py): previsão melhor que o ranking, calibração e picos coerentes com o que se sabe.

Roda a cada atualização da base. Termina com "TUDO OK" ou com a lista do que falhou.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from tenis import elo  # noqa: E402

pop = pd.read_parquet(RAIZ / "dados" / "base" / "populacao.parquet")
d = elo.calcular(pop)
v = elo.validacao(d)
falhas = []


def checar(cond, msg):
    print(("ok   " if cond else "FALHA") + " " + msg)
    if not cond:
        falhas.append(msg)


# 1. previsão: o Elo antes da partida acerta mais que "o melhor ranqueado vence", no geral e em toda década
checar(v["acerto_elo"] > v["acerto_ranking"], f"Elo acerta {v['acerto_elo']:.1%} × ranking {v['acerto_ranking']:.1%}")
for dec, x in v["por_decada"].items():
    checar(x["elo"] >= x["ranking"] - 0.005, f"{dec}: Elo {x['elo']:.1%} × ranking {x['ranking']:.1%}")
# 2. calibração fora da amostra: ajustada em 1993–2015, conferida em 2016–2025
x = d[d["ano"] > 2015]
dif = ((x["elo_v"] + x["elo_sup_v"]) - (x["elo_p"] + x["elo_sup_p"])) / 2
ll = lambda c: float(-np.log(elo.chance(dif, 0, c)).mean())  # noqa: E731
checar(ll(elo.ESCALA_PROB) < ll(1.0), f"calibração melhora a log-loss em 2016–2025: {ll(1.0):.4f} → {ll(elo.ESCALA_PROB):.4f}")
cal = pd.DataFrame(v["calibracao"])
checar((cal["previsto"] - cal["real"]).abs().max() < 0.06, f"calibração: maior erro por faixa {(cal['previsto'] - cal['real']).abs().max():.3f} < 0,06")
# 3. picos coerentes com a história do esporte (fora do aquecimento 1991–1992)
dep = elo.depois(d)
dep = dep[~dep["ano"].between(*elo.AQUECIMENTO)]
top = dep.sort_values("elo", ascending=False).drop_duplicates("id")
checar(top["jogador"].iloc[0] == "Novak Djokovic", f"maior pico geral: {top['jogador'].iloc[0]} ({top['elo'].iloc[0]:.0f})")
checar({"Roger Federer", "Rafael Nadal", "Andy Murray"} <= set(top["jogador"].head(6)), "Federer, Nadal e Murray entre os 6 maiores picos")
saibro = dep[dep["superficie"] == "Saibro"].sort_values("elo_sup", ascending=False)
grama = dep[dep["superficie"] == "Grama"].sort_values("elo_sup", ascending=False)
checar(saibro["jogador"].iloc[0] == "Rafael Nadal", f"maior pico no saibro: {saibro['jogador'].iloc[0]}")
checar(grama["jogador"].iloc[0] == "Roger Federer", f"maior pico na grama: {grama['jogador'].iloc[0]}")
# 4. contas: soma de Elo se conserva (o que um ganha o outro perde) — com K diferente para cada um, não é
#    exato; checamos só que nenhuma nota é absurda
checar(dep["elo"].between(1000, 2800).all(), f"todas as notas entre 1000 e 2800 (min {dep['elo'].min():.0f}, max {dep['elo'].max():.0f})")

print("\nTUDO OK" if not falhas else f"\n{len(falhas)} FALHA(S): " + " | ".join(falhas))
sys.exit(1 if falhas else 0)
