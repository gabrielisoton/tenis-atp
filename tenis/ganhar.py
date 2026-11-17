"""O que faz ganhar uma partida: o peso de cada aspecto do jogo na vitória, partida a partida.

Dois jeitos complementares, para cada recorte de superfície × nível × época:

- **Leitura simples:** em quantas partidas o vencedor foi melhor que o perdedor em cada aspecto (sem contar
  empates), com IC de Wilson. Pontos totais e pontos no saque entram como referência.
- **Modelo:** regressão logística da vitória nas DIFERENÇAS entre os dois jogadores, padronizadas (efeito de
  +1 desvio-padrão), com IC 95% pela matriz de informação. Cada partida entra num sentido sorteado (A × B),
  então o modelo é simétrico e não tem intercepto.

Armadilha de desenho: numa partida, a devolução de um jogador é o espelho do saque do outro (pontos que A
ganha devolvendo o 1º saque de B = pontos que B perde com o 1º saque). Pôr devolução e saque juntos no modelo
faz a devolução "explicar tudo". Por isso o modelo usa só os componentes do saque de cada um, e cada diferença
mede ao mesmo tempo o saque de A e a devolução de A contra aquele saque de B.

Tradução para quem treina: efeito de +1 ponto percentual numa partida parelha (β/4 por unidade) e, dividindo
pela fração de pontos de saque que o componente move, o valor de +1 ponto a cada 100 pontos de saque.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from tenis import estatistica as est

MODELO = ["ganhos_1", "ganhos_2", "primeiro_dentro", "aces_game", "df_game"]
LEITURA = ["tpw", "saque", "ganhos_1", "ganhos_2", "bp_salvos", "aces_game", "df_game", "primeiro_dentro"]
MENOR_MELHOR = {"df_game"}
SUPERFICIES = ["Todas", "Dura", "Saibro", "Grama"]
NIVEIS = ["Todos", "Grand Slam", "Masters 1000", "ATP 500", "ATP 250"]
EPOCAS = {"Todas": (1991, 9999), "1991–2002": (1991, 2002), "2003–2012": (2003, 2012), "2013+": (2013, 9999)}
MIN_PARTIDAS = 400


def _lado(x: pd.DataFrame, s: str) -> pd.DataFrame:
    seg = x[f"{s}_svpt"] - x[f"{s}_1in"]
    return pd.DataFrame({
        "primeiro_dentro": x[f"{s}_1in"] / x[f"{s}_svpt"],
        "ganhos_1": x[f"{s}_1won"] / x[f"{s}_1in"],
        "ganhos_2": x[f"{s}_2won"] / seg,
        "aces_game": x[f"{s}_ace"] / x[f"{s}_svgms"],
        "df_game": x[f"{s}_df"] / x[f"{s}_svgms"],
        "bp_salvos": x[f"{s}_bpsav"] / x[f"{s}_bpfac"].where(x[f"{s}_bpfac"] > 0),
        "saque": (x[f"{s}_1won"] + x[f"{s}_2won"]) / x[f"{s}_svpt"],
    }, index=x.index)


def base(pop: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Partidas com estatísticas consistentes e os dois lados medidos; aspectos do vencedor (V) e do perdedor (P)."""
    ok = pop["stats_ok"].copy()
    for s in ("v", "p"):
        ok &= (pop[f"{s}_svgms"] > 0) & (pop[f"{s}_1in"] > 0) & (pop[f"{s}_svpt"] > pop[f"{s}_1in"])
    x = pop[ok]
    V, P = _lado(x, "v"), _lado(x, "p")
    V["tpw"], P["tpw"] = x["pontos_vencedor"], x["pontos_perdedor"]
    return x, V, P


def logit(X: np.ndarray, y: np.ndarray, iteracoes: int = 25) -> tuple[np.ndarray, np.ndarray]:
    """Regressão logística sem intercepto por Newton-Raphson; devolve coeficientes e erros-padrão."""
    b = np.zeros(X.shape[1])
    for _ in range(iteracoes):
        p = 1 / (1 + np.exp(-X @ b))
        H = X.T @ (X * (p * (1 - p))[:, None])
        passo = np.linalg.solve(H, X.T @ (y - p))
        b += passo
        if np.abs(passo).max() < 1e-10:
            break
    return b, np.sqrt(np.diag(np.linalg.inv(H)))


def leitura(V: pd.DataFrame, P: pd.DataFrame) -> list[dict]:
    saida = []
    for k in LEITURA:
        d = (V[k] - P[k]).dropna()
        if k in MENOR_MELHOR:
            d = -d
        melhor, n = int((d > 0).sum()), int((d != 0).sum())
        _, lo, hi = est.ic_wilson(melhor, n)
        saida.append({"crit": k, "pct": round(melhor / n, 4), "ic": [round(float(lo), 4), round(float(hi), 4)], "n": n,
                      "empates": round(float((d == 0).mean()), 4)})
    return saida


def modelo(V: pd.DataFrame, P: pd.DataFrame, sorteio: np.ndarray, frac: dict) -> dict:
    D = (V[MODELO] - P[MODELO]).to_numpy()
    D[sorteio] *= -1                                  # metade das partidas vista do lado de quem perdeu
    y = (~sorteio).astype(float)
    sd = D.std(axis=0)
    b, ep = logit(D / sd, y)
    acerto = float((((D / sd) @ b > 0) == (y == 1)).mean())
    linhas = []
    for k, bb, ee, s in zip(MODELO, b, ep, sd):
        por_pp = bb / s * 0.01 / 4                    # +1 p.p. numa partida parelha (inclinação máxima da logística)
        linhas.append({"crit": k, "z": round(float(bb), 3), "ic": round(float(1.96 * ee), 3), "dp": round(float(s), 4),
                       "por_pp": round(float(por_pp), 4) if k in frac else None,
                       "por_ponto": round(float(por_pp / frac[k]), 4) if k in frac else None})
    return {"coef": sorted(linhas, key=lambda r: -r["z"]), "acerto": round(acerto, 4)}


def exportar(pop: pd.DataFrame) -> dict:
    x, V, P = base(pop)
    sorteio = np.random.default_rng(0).random(len(x)) < .5
    sup = x["superficie"].replace({"Carpete": "Dura"})   # carpete conta como quadra rápida coberta
    recortes = {}
    for s in SUPERFICIES:
        for nv in NIVEIS:
            for ep, (a0, a1) in EPOCAS.items():
                m = (x["ano"].between(a0, a1) & ((sup == s) if s != "Todas" else True) & ((x["nivel"] == nv) if nv != "Todos" else True)).to_numpy()
                if m.sum() < MIN_PARTIDAS:
                    continue
                v, p = V[m], P[m]
                # fração dos pontos de saque que cada componente move: 1º saque = pontos de 1º saque; 2º = de 2º;
                # 1º dentro: cada p.p. a mais troca um ponto de 2º saque por um de 1º (vale a diferença entre eles)
                pd_ = pd.concat([v, p])
                frac = {"ganhos_1": float(pd_["primeiro_dentro"].mean()), "ganhos_2": float(1 - pd_["primeiro_dentro"].mean()),
                        "primeiro_dentro": float((pd_["ganhos_1"] - pd_["ganhos_2"]).mean())}
                recortes[f"{s}|{nv}|{ep}"] = {"n": int(m.sum()), "leitura": leitura(v, p), "modelo": modelo(v, p, sorteio[m], frac)}
    # o circuito em cada superfície (somas de pontos dos dois jogadores), para o guia de quem treina
    circuito = {}
    for s in SUPERFICIES:
        g = x if s == "Todas" else x[sup == s]
        S = lambda c: float(g[f"v_{c}"].sum() + g[f"p_{c}"].sum())  # noqa: E731
        circuito[s] = {"n": int(len(g)), "dev_1": round(1 - S("1won") / S("1in"), 4), "dev_2": round(1 - S("2won") / (S("svpt") - S("1in")), 4),
                       "primeiro_dentro": round(S("1in") / S("svpt"), 4), "aces_game": round(S("ace") / S("svgms"), 3),
                       "df_game": round(S("df") / S("svgms"), 3), "saque": round((S("1won") + S("2won")) / S("svpt"), 4)}
    return {"recortes": recortes, "circuito": circuito, "superficies": SUPERFICIES, "niveis": NIVEIS, "epocas": list(EPOCAS),
            "min_partidas": MIN_PARTIDAS, "n_total": int(len(x))}
