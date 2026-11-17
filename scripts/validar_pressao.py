"""Valida a pressão acima do esperado (tenis/pressao.py): os modelos de game, tie-break e set, o equilíbrio do
circuito, que a medida se descola do saque e o que ela diz dos nº 1. Termina com "TUDO OK"."""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from tenis import analises as an  # noqa: E402
from tenis import pressao as pr  # noqa: E402

pop = pd.read_parquet(RAIZ / "dados" / "base" / "populacao.parquet")
falhas = []


def checar(cond, msg):
    print(("ok   " if cond else "FALHA") + " " + msg)
    if not cond:
        falhas.append(msg)


# 1. modelos: valor conhecido do game, simetria e amplificação (set > tie-break > ponto)
p, q = np.array([.6, .65, .7, .5]), np.array([.6, .6, .6, .5])
checar(abs(pr._game(np.array([.6]))[0] - 0.73573) < 1e-4, f"game com 60% dos pontos no saque: {pr._game(np.array([.6]))[0]:.4f} (conhecido: 0,7357)")
checar(np.allclose(pr.tie_break(p, q) + pr.tie_break(q, p), 1) and np.allclose(pr.set_(p, q) + pr.set_(q, p), 1),
       "tie-break e set simétricos: P(A) + P(B) = 1")
checar(np.all(pr.set_(p[1:3], q[1:3]) > pr.tie_break(p[1:3], q[1:3])), "o set amplifica mais a vantagem por ponto que o tie-break")

# 2. no circuito inteiro, observado = esperado
lg = an.longo(pop)
for o, e, d in [("bp_sav", "bp_sav_esp", "bp_fac"), ("bp_conv", "bp_conv_esp", "bp_opp"), ("tb_v_s", "tb_esp", "tb_j_s"), ("dec_v_s", "dec_esp", "dec_j_s")]:
    dif = (lg[o].sum() - lg[e].sum()) / lg[d].sum()
    checar(abs(dif) < 0.001, f"circuito: {o} observado − esperado = {100 * dif:+.3f} p.p.")
aj = lg.attrs["ajuste_bp"]
checar(-0.05 < aj < 0.05, f"no break point quem saca ganha {100 * aj:+.1f} p.p. em relação aos outros pontos de saque")

# 3. a medida se descola do saque (a % crua de BP salvos é quase só saque)
tab = an.tabela_jogadores(lg)
r_cru, r_ae = tab["bp_salvos"].corr(tab["saque_ganhos"]), tab["bp_salvos_ae"].corr(tab["saque_ganhos"])
checar(r_cru > 0.7 and abs(r_ae) < 0.3, f"correlação com o saque: BP salvos crus {r_cru:.2f} → acima do esperado {r_ae:.2f}")

# 4. estabilidade (anos pares × ímpares, jogadores com 50+ partidas em cada metade)
cols = ["partida", "bp_sav", "bp_sav_esp", "bp_fac", "tb_v_s", "tb_esp", "tb_j_s", "dec_v_s", "dec_esp", "dec_j_s"]
h = lg.assign(par=lg["ano"] % 2 == 0).groupby(["jogador", "par"])[cols].sum().unstack()
ok = (h["partida"][True] >= 50) & (h["partida"][False] >= 50)
conf = {}
for nome, (o, e, d) in {"BP salvos": ("bp_sav", "bp_sav_esp", "bp_fac"), "tie-breaks": ("tb_v_s", "tb_esp", "tb_j_s"),
                        "sets decisivos": ("dec_v_s", "dec_esp", "dec_j_s")}.items():
    a, b = [(h[o][k] - h[e][k]) / h[d][k] for k in (True, False)]
    r = a[ok].corr(b[ok])
    conf[nome] = 2 * r / (1 + r)                               # Spearman-Brown: confiabilidade da carreira inteira
print("     confiabilidade (pares × ímpares, Spearman-Brown): " + ", ".join(f"{k} {v:.2f}" for k, v in conf.items()))
checar(conf["sets decisivos"] > 0.3 and conf["sets decisivos"] > max(conf["BP salvos"], conf["tie-breaks"]),
       "sets decisivos acima do esperado se repetem mais que BP e tie-breaks (traço do jogador, não só sorte)")

# 5. os nº 1: sets decisivos acima do esperado, e bem mais do que nos outros sets (não é viés do modelo)
n1 = list(json.loads((RAIZ / "site" / "data" / "numero1.json").read_text(encoding="utf-8"))["jogadores"])
x = tab.reindex(n1).dropna(subset=["dec_ae"])
checar((x["dec_ae"] > 0).sum() >= len(x) - 2, f"sets decisivos acima do esperado: {(x['dec_ae'] > 0).sum()} de {len(x)} nº 1 (média {100 * x['dec_ae'].mean():+.1f} p.p.)")
pp = pop.set_index("id_partida")["placar"].astype(str).map(lambda s: [tuple(map(int, t)) for t in re.findall(r"(\d+)-(\d+)", s)])
sv, sp = pp.map(lambda L: sum(a > b for a, b in L)), pp.map(lambda L: sum(a < b for a, b in L))
m = lg[lg["dec_esp"].notna()].copy()
m["sets_v"] = np.where(m["venceu"] == 1, m["id_partida"].map(sv), m["id_partida"].map(sp))
m["sets_j"] = m["id_partida"].map(sv) + m["id_partida"].map(sp)
pa = (m["sv_won"] / m["sv_pts"]).clip(.01, .99).to_numpy()
pb = ((m["ret_pts"] - m["ret_won"]) / m["ret_pts"]).clip(.01, .99).to_numpy()
m["nd_j"], m["nd_v"] = m["sets_j"] - m["dec_j_s"], m["sets_v"] - m["dec_v_s"]
m["nd_esp"] = m["nd_j"] * pr.set_(pa, pb)
g = m[m["jogador"].isin(n1)][["nd_v", "nd_esp", "nd_j", "dec_v_s", "dec_esp", "dec_j_s"]].sum()
nd, dec = (g["nd_v"] - g["nd_esp"]) / g["nd_j"], (g["dec_v_s"] - g["dec_esp"]) / g["dec_j_s"]
checar(dec > 3 * nd, f"nº 1 nos outros sets {100 * nd:+.1f} p.p. × nos sets decisivos {100 * dec:+.1f} p.p.")

# 6. um caso conhecido: Nishikori, famoso pelo aproveitamento em sets decisivos
top = tab[tab["dec_ae_n"] >= 60]["dec_ae"].sort_values(ascending=False)
checar("Kei Nishikori" in top.head(5).index, f"Nishikori entre os 5 maiores em sets decisivos acima do esperado ({list(top.head(5).index)})")

print("\nTUDO OK" if not falhas else f"\n{len(falhas)} FALHA(S): " + " | ".join(falhas))
sys.exit(1 if falhas else 0)
