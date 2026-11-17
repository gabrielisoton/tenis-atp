"""Pressão acima do esperado: break points, tie-breaks e sets decisivos comparados com o que os pontos do próprio
jogador NA MESMA PARTIDA preveem.

- **Break points salvos:** esperado = BPs enfrentados × % de pontos ganhos no saque nos pontos que NÃO foram break
  point, na mesma partida. Os BPs saem da conta do esperado para não medir o ponto com ele mesmo.
- **Break points convertidos:** o espelho: BPs que o adversário enfrentou × (1 − % do saque dele fora dos BPs).
- O break point não é um ponto como os outros: no circuito inteiro, quem saca ganha cerca de 1,3 p.p. A MAIS nos
  break points do que nos outros pontos de saque. Essa diferença do circuito (`lg.attrs["ajuste_bp"]`) entra no
  esperado, então 0 = "como o circuito" e os dois critérios são simétricos (o que um salva acima do esperado, o
  outro deixa de converter).
- **Tie-breaks e sets decisivos:** esperado = chance de vencer um tie-break (ou um set) dada a % de pontos que cada
  um ganhou sacando na partida, pelo modelo ponto → game → tie-break → set (pontos independentes, saque alternado).
  Quem ganhou mais pontos na partida "deveria" ganhar mais tie-breaks; acima disso é frieza nos momentos que decidem.

Os pontos da própria partida incluem os do tie-break e do set decisivo, o que puxa o esperado na direção do que
aconteceu: a medida fica conservadora (mais perto de 0), nunca exagerada.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _game(p: np.ndarray) -> np.ndarray:
    """Chance de quem saca vencer o game, ganhando cada ponto com chance p (com vantagem)."""
    q = 1 - p
    return p**4 * (1 + 4 * q + 10 * q**2) + 20 * p**3 * q**3 * p**2 / (1 - 2 * p * q)


def tie_break(pa: np.ndarray, pb: np.ndarray) -> np.ndarray:
    """Chance de A vencer um tie-break até 7 (com 2 de diferença); pa, pb = chance de cada um vencer o ponto no
    próprio saque. Média de A sacar primeiro e B sacar primeiro."""
    def um(primeiro_a: bool):
        # P[i, j] = chance de chegar a i pontos de A e j de B
        P = {(0, 0): np.ones_like(pa)}
        ganha = np.zeros_like(pa)
        for t in range(12):                       # até 6-6
            for i in range(0, min(t, 6) + 1):
                j = t - i
                if j > 6 or (i, j) not in P:
                    continue
                saca_a = ((t + 1) // 2) % 2 == 0 if primeiro_a else ((t + 1) // 2) % 2 == 1
                pw = pa if saca_a else 1 - pb      # chance de A ganhar este ponto
                for (ni, nj, pr) in ((i + 1, j, pw), (i, j + 1, 1 - pw)):
                    if ni == 7:
                        ganha = ganha + P[(i, j)] * pr
                    elif nj == 7:
                        pass
                    else:
                        P[(ni, nj)] = P.get((ni, nj), 0) + P[(i, j)] * pr
        # 6-6: a cada dois pontos cada um saca um; A vence a "dupla" com pa(1-pb), perde com (1-pa)pb
        aa, bb = pa * (1 - pb), (1 - pa) * pb
        return ganha + P[(6, 6)] * aa / (aa + bb)
    return (um(True) + um(False)) / 2


def set_(pa: np.ndarray, pb: np.ndarray) -> np.ndarray:
    """Chance de A vencer um set (até 6, tie-break em 6-6) com pa, pb no próprio saque; média de quem saca primeiro."""
    ga, gb = _game(pa), _game(pb)                 # A segura o saque; B segura o saque
    tb = tie_break(pa, pb)

    def um(primeiro_a: bool):
        P = {(0, 0): np.ones_like(pa)}
        ganha = np.zeros_like(pa)
        for t in range(12):
            for i in range(0, min(t, 6) + 1):
                j = t - i
                if (i, j) not in P:
                    continue
                if (i == 6 and j < 5) or (j == 6 and i < 5) or i > 6 or j > 6:
                    continue
                saca_a = (t % 2 == 0) == primeiro_a
                pw = ga if saca_a else 1 - gb
                for (ni, nj, pr) in ((i + 1, j, pw), (i, j + 1, 1 - pw)):
                    if (ni == 6 and nj <= 4) or (ni == 7):
                        ganha = ganha + P[(i, j)] * pr
                    elif (nj == 6 and ni <= 4) or nj == 7:
                        pass
                    else:
                        P[(ni, nj)] = P.get((ni, nj), 0) + P[(i, j)] * pr
        return ganha + P.get((6, 6), 0) * tb
    return (um(True) + um(False)) / 2


def esperados(lg: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta ao formato longo (um jogador por partida) os esperados de pressão: bp_sav_esp, bp_conv_esp,
    tb_esp e dec_esp. Só onde a partida tem estatísticas consistentes (as outras ficam NaN)."""
    ok = lg["sv_pts"].notna()                     # partida com estatísticas consistentes (ver analises._componentes)
    o_sv_won = lg["ret_pts"] - lg["ret_won"]
    o_bp_sav = lg["bp_opp"] - lg["bp_conv"]
    # meu saque e o dele fora dos BPs (se todos os pontos de saque foram BP, o que não acontece, o saque inteiro)
    sv_fora = ((lg["sv_won"] - lg["bp_sav"]) / (lg["sv_pts"] - lg["bp_fac"])).where(lg["sv_pts"] > lg["bp_fac"], lg["sv_won"] / lg["sv_pts"])
    o_sv_fora = ((o_sv_won - o_bp_sav) / (lg["ret_pts"] - lg["bp_opp"])).where(lg["ret_pts"] > lg["bp_opp"], o_sv_won / lg["ret_pts"])
    m = ok & (lg["bp_fac"] > 0)
    ajuste = float((lg.loc[m, "bp_sav"].sum() - (lg.loc[m, "bp_fac"] * sv_fora[m]).sum()) / lg.loc[m, "bp_fac"].sum())
    # esperados arredondados por partida em 0,01: as somas do site (em centésimos inteiros) batem com as do Python
    lg["bp_sav_esp"] = (lg["bp_fac"] * (sv_fora + ajuste).clip(0, 1)).where(ok).round(2)
    lg["bp_conv_esp"] = (lg["bp_opp"] * (1 - (o_sv_fora + ajuste).clip(0, 1))).where(ok).round(2)
    pa = (lg["sv_won"] / lg["sv_pts"]).clip(0.01, 0.99).to_numpy()
    pb = (o_sv_won / lg["ret_pts"]).clip(0.01, 0.99).to_numpy()
    com = ok.to_numpy()
    tb, st = np.full(len(lg), np.nan), np.full(len(lg), np.nan)
    tb[com], st[com] = tie_break(pa[com], pb[com]), set_(pa[com], pb[com])
    lg["tb_esp"] = (lg["tb_jogados"] * tb).round(2)
    lg["dec_esp"] = (lg["decisivo_jogado"] * st).round(2)
    # tie-breaks e sets decisivos só das partidas com estatísticas (o esperado precisa dos pontos)
    for c, novo in (("tb_jogados", "tb_j_s"), ("tb_vencidos", "tb_v_s"), ("decisivo_jogado", "dec_j_s"), ("decisivo_vencido", "dec_v_s")):
        lg[novo] = lg[c].where(ok)
    lg.attrs["ajuste_bp"] = ajuste
    return lg


CRITERIOS_AE = {"bp_salvos": ("bp_sav", "bp_sav_esp", "bp_fac"), "bp_convertidos": ("bp_conv", "bp_conv_esp", "bp_opp"),
                "tie_breaks": ("tb_v_s", "tb_esp", "tb_j_s"), "decisivos": ("dec_v_s", "dec_esp", "dec_j_s")}


def confiabilidade(lg: pd.DataFrame, minimo: int = 50) -> dict:
    """Quanto o "acima do esperado" de cada jogador se repete: correlação entre anos pares e ímpares (jogadores com
    `minimo`+ partidas em cada metade), levada à carreira inteira por Spearman-Brown (2r / (1 + r)).
    Perto de 0 = é sorte (muda de um período para outro); perto de 1 = é um traço do jogador."""
    cols = ["partida"] + [c for t in CRITERIOS_AE.values() for c in t]
    h = lg.assign(par=lg["ano"] % 2 == 0).groupby(["jogador", "par"])[cols].sum().unstack()
    ok = (h["partida"][True] >= minimo) & (h["partida"][False] >= minimo)
    saida = {}
    for k, (o, e, d) in CRITERIOS_AE.items():
        a, b = [(h[o][x] - h[e][x]) / h[d][x] for x in (True, False)]
        r = float(a[ok].corr(b[ok]))
        saida[k] = {"r": round(r, 3), "confiabilidade": round(2 * r / (1 + r), 3)}
    return {"criterios": saida, "jogadores": int(ok.sum())}
