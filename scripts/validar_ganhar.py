"""Valida "o que faz ganhar" (tenis/ganhar.py): a conta do modelo contra o scipy e os resultados contra o que se
espera do tênis. Termina com "TUDO OK"."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from tenis import ganhar  # noqa: E402

pop = pd.read_parquet(RAIZ / "dados" / "base" / "populacao.parquet")
G = ganhar.exportar(pop)
falhas = []


def checar(cond, msg):
    print(("ok   " if cond else "FALHA") + " " + msg)
    if not cond:
        falhas.append(msg)


# 1. a regressão logística (Newton-Raphson) bate com a máxima verossimilhança do scipy
rng = np.random.default_rng(1)
X = rng.normal(size=(4000, 3))
y = (rng.random(4000) < 1 / (1 + np.exp(-X @ np.array([1.5, -0.7, 0.2])))).astype(float)
b, _ = ganhar.logit(X, y)
nll = lambda w: np.sum(np.logaddexp(0, X @ w) - y * (X @ w))  # noqa: E731
ref = minimize(nll, np.zeros(3), method="BFGS").x
checar(np.abs(b - ref).max() < 1e-3, f"logística confere com o scipy: {np.round(b, 3)} × {np.round(ref, 3)}")

# 2. ordem dos aspectos na base inteira
g = G["recortes"]["Todas|Todos|Todas"]
z = {c["crit"]: c["z"] for c in g["modelo"]["coef"]}
checar(z["ganhos_1"] > z["ganhos_2"] > z["primeiro_dentro"] > max(z["aces_game"], z["df_game"]),
       f"ordem: 1º saque {z['ganhos_1']} > 2º saque {z['ganhos_2']} > 1º dentro {z['primeiro_dentro']} > aces/duplas faltas")
checar(max(abs(z["aces_game"]), abs(z["df_game"])) < 0.5, f"aces ({z['aces_game']}) e duplas faltas ({z['df_game']}) quase somem depois dos pontos")
checar(g["modelo"]["acerto"] >= 0.9, f"o modelo acerta o vencedor em {g['modelo']['acerto']:.1%}")

# 3. a mesma ordem em cada superfície, nível e época
um_corte = [k for k in G["recortes"] if sum(p not in ("Todas", "Todos") for p in k.split("|")) == 1]
fora = [k for k in um_corte if not (lambda zz: zz["ganhos_1"] > zz["ganhos_2"] > zz["primeiro_dentro"])(
    {c["crit"]: c["z"] for c in G["recortes"][k]["modelo"]["coef"]})]
checar(not fora, f"mesma ordem em {len(um_corte)} recortes de superfície, nível e época" + (f" (fora: {fora})" if fora else ""))

# 4. "um ponto é um ponto": convertido em pontos, os três componentes valem parecido
pp = [c["por_ponto"] for c in g["modelo"]["coef"] if c["por_ponto"] is not None]
checar(max(pp) / min(pp) < 1.25, f"valor de +1 ponto a cada 100: {[round(100 * x, 1) for x in pp]} p.p. (diferença < 25%)")

# 5. leitura simples coerente com "venceu perdendo nos pontos"
L = {r["crit"]: r for r in g["leitura"]}
vp = json.loads((RAIZ / "site" / "data" / "venceu_perdendo.json").read_text(encoding="utf-8"))["resumo"]["pct"]
checar(abs((1 - L["tpw"]["pct"]) * (1 - L["tpw"]["empates"]) - vp) < 0.01,
       f"quem ganha mais pontos vence {L['tpw']['pct']:.1%}; vence perdendo nos pontos {vp:.1%}")
checar(L["ganhos_1"]["pct"] > L["ganhos_2"]["pct"] > L["primeiro_dentro"]["pct"] > 0.5,
       f"leitura simples: 1º saque {L['ganhos_1']['pct']:.0%} > 2º saque {L['ganhos_2']['pct']:.0%} > 1º dentro {L['primeiro_dentro']['pct']:.0%} > 50%")

print("\nTUDO OK" if not falhas else f"\n{len(falhas)} FALHA(S): " + " | ".join(falhas))
sys.exit(1 if falhas else 0)
