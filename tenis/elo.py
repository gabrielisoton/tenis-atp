"""Elo dos jogadores (geral e por superfície), partida a partida.

Método (o mesmo do Tennis Abstract, documentado aqui para ser reproduzível):
- todo jogador começa com 1500;
- chance de A vencer B antes da partida: 1 / (1 + 10^((Rb − Ra) / 400));
- depois da partida: R += K · (resultado − chance), com K = 250 / (partidas já jogadas + 5)^0,4.
  Quem tem poucas partidas muda rápido; veteranos mudam devagar;
- Elo por superfície: o mesmo cálculo só com as partidas daquela superfície (carpete conta como dura,
  as duas são quadras rápidas e o carpete some do circuito em 2009).

Ordem das partidas: data do torneio → torneio → rodada (R128 antes de R64 … antes da final). A base
começa em 1991 com todos em 1500: 1991–1992 servem de aquecimento e não entram em picos.
Só partidas concluídas do circuito principal (a população): sem Challengers, qualifying nem Copa Davis,
por isso os valores absolutos ficam abaixo dos de quem usa essas partidas.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from tenis import analises as an

INICIAL = 1500.0
# Elo puro sai confiante demais nos extremos (só circuito principal). As PROBABILIDADES usam a diferença
# multiplicada por ESCALA_PROB, ajustada em 1993–2015 e conferida em 2016–2025 (scripts/validar_elo.py).
ESCALA_PROB = 0.84
# Simulador "Pico × Pico": escala ajustada só em partidas melhor de 3; o melhor de 5 sai convertendo a chance
# por set (validado em scripts/validar_elo.py: prevê os jogos de Slam melhor que usar a mesma chance).
ESCALA_MD3 = 0.75
AQUECIMENTO = (1991, 1992)  # anos calculados mas fora de picos e rankings históricos
SUPERFICIE_ELO = {"Dura": "Dura", "Carpete": "Dura", "Saibro": "Saibro", "Grama": "Grama"}
ORDEM_RODADA = {"1ª rodada (R128)": 0, "R64": 1, "R32": 2, "Oitavas (R16)": 3, "Fase de grupos": 3.5,
                "Quartas": 4, "Semifinal": 5, "Final": 6}


def k_fator(n: np.ndarray | float) -> np.ndarray | float:
    return 250.0 / (np.asarray(n, dtype=float) + 5.0) ** 0.4


def chance(ra, rb, escala: float = 1.0):
    """Probabilidade de A vencer B pelo Elo (escala < 1 = calibrada, ver ESCALA_PROB)."""
    return 1.0 / (1.0 + 10.0 ** (escala * (np.asarray(rb) - np.asarray(ra)) / 400.0))


def ordenar(pop: pd.DataFrame) -> pd.DataFrame:
    rod = pop["rodada"].map(ORDEM_RODADA).fillna(2.5)
    return pop.assign(_rod=rod).sort_values(["data", "id_torneio", "_rod", "ordem"], kind="stable").drop(columns="_rod")


def calcular(pop: pd.DataFrame) -> pd.DataFrame:
    """Elo de cada jogador antes e depois de cada partida (geral e na superfície) e a chance prevista.

    Devolve as partidas em ordem cronológica com, para vencedor (v) e perdedor (p):
    elo_v/elo_p e elo_sup_v/elo_sup_p (antes), elo_v_dep/elo_p_dep e elo_sup_v_dep/elo_sup_p_dep (depois),
    n_v/n_p (partidas anteriores), p_elo (chance do vencedor pelo Elo geral) e p_elo_sup (pela média
    do Elo geral com o da superfície, como no Tennis Abstract).
    """
    d = ordenar(pop).reset_index(drop=True)
    sup = d["superficie"].map(SUPERFICIE_ELO).to_numpy()
    v_ids, p_ids = d["id_vencedor"].to_numpy(), d["id_perdedor"].to_numpy()
    nota, jogos, nota_s, jogos_s = {}, {}, {}, {}
    out = np.empty((len(d), 12))
    for i in range(len(d)):
        a, b, s_ = v_ids[i], p_ids[i], sup[i]
        ra, rb = nota.get(a, INICIAL), nota.get(b, INICIAL)
        na, nb = jogos.get(a, 0), jogos.get(b, 0)
        sa, sb = nota_s.get((a, s_), INICIAL), nota_s.get((b, s_), INICIAL)
        nsa, nsb = jogos_s.get((a, s_), 0), jogos_s.get((b, s_), 0)
        e = 1.0 / (1.0 + 10.0 ** ((rb - ra) / 400.0))
        es = 1.0 / (1.0 + 10.0 ** ((sb - sa) / 400.0))
        ra2, rb2 = ra + k_fator(na) * (1 - e), rb - k_fator(nb) * (1 - e)
        sa2, sb2 = sa + k_fator(nsa) * (1 - es), sb - k_fator(nsb) * (1 - es)
        out[i] = (ra, rb, sa, sb, na, nb, e, es, ra2, rb2, sa2, sb2)
        nota[a], nota[b], nota_s[(a, s_)], nota_s[(b, s_)] = ra2, rb2, sa2, sb2
        jogos[a], jogos[b] = na + 1, nb + 1
        jogos_s[(a, s_)], jogos_s[(b, s_)] = nsa + 1, nsb + 1
    cols = ["elo_v", "elo_p", "elo_sup_v", "elo_sup_p", "n_v", "n_p", "p_elo", "p_elo_sup_puro",
            "elo_v_dep", "elo_p_dep", "elo_sup_v_dep", "elo_sup_p_dep"]
    d[cols] = out
    d["sup_elo"] = sup
    mv, mp = (d["elo_v"] + d["elo_sup_v"]) / 2, (d["elo_p"] + d["elo_sup_p"]) / 2
    d["p_elo_sup"] = chance(mv, mp)
    return d


def depois(d: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por jogador-partida com o Elo DEPOIS da partida (para linhas do tempo e picos)."""
    lados = []
    for x, nome in (("v", "vencedor"), ("p", "perdedor")):
        lados.append(pd.DataFrame({
            "i": d.index, "data": d["data"], "ano": d["ano"], "id": d[f"id_{nome}"], "jogador": d[nome],
            "idade": d[f"idade_{nome}"], "superficie": d["sup_elo"],
            "elo": d[f"elo_{x}_dep"], "elo_sup": d[f"elo_sup_{x}_dep"], "partidas": d[f"n_{x}"] + 1}))
    return pd.concat(lados).sort_values(["i"], kind="stable").reset_index(drop=True)


# ------------------------------------------------------------------ resultados para o site
SUPS = ["Dura", "Saibro", "Grama"]


def validacao(d: pd.DataFrame) -> dict:
    """Acerto e calibração do Elo antes de cada partida, comparado ao ranking (fora do aquecimento)."""
    x = d[~d["ano"].between(*AQUECIMENTO) & d["ranking_vencedor"].notna() & d["ranking_perdedor"].notna()
          & (d["ranking_vencedor"] != d["ranking_perdedor"])]
    dif = ((x["elo_v"] + x["elo_sup_v"]) - (x["elo_p"] + x["elo_sup_p"])) / 2
    p = pd.Series(chance(dif, 0, ESCALA_PROB), index=x.index)
    acerto = lambda m: float(((p[m] > .5) if m is not None else (p > .5)).mean())  # noqa: E731
    rk = (x["ranking_vencedor"] < x["ranking_perdedor"])
    rng = np.random.default_rng(0)
    vira = rng.random(len(x)) < .5                      # perspectiva aleatória para ter as duas pontas
    pp, y = np.where(vira, 1 - p.to_numpy(), p.to_numpy()), np.where(vira, 0, 1)
    faixas = pd.cut(pp, np.arange(0, 1.0001, .1))
    cal = pd.DataFrame({"p": pp, "y": y, "f": faixas}).groupby("f", observed=True).agg(previsto=("p", "mean"), real=("y", "mean"), n=("y", "size"))
    return {
        "n": int(len(x)), "acerto_elo": acerto(None), "acerto_ranking": float(rk.mean()),
        "brier_elo": float(((1 - p) ** 2).mean()), "logloss_elo": float(-np.log(p).mean()),
        "por_decada": {dec: {"elo": float((p[g.index] > .5).mean()), "ranking": float(rk[g.index].mean()), "n": int(len(g))}
                       for dec, g in x.groupby("decada")},
        "calibracao": cal.reset_index(drop=True).round(4).to_dict("list"),
        "escala": ESCALA_PROB,
    }


def exportar(pop: pd.DataFrame, min_pico_serie: float = 2050.0) -> dict:
    """Tudo o que a página Elo mostra: validação, picos, nº 1 por temporada, Elo atual e séries mensais."""
    d = calcular(pop)
    dep = depois(d)
    valido = ~dep["ano"].between(*AQUECIMENTO)
    ult = dep["data"].max()

    def picos(col, df, n):
        t = df[valido.loc[df.index]].sort_values(col, ascending=False).drop_duplicates("id").head(n)
        return [{"jogador": r.jogador, "elo": round(float(getattr(r, col)), 1), "data": r.data,
                 "idade": None if pd.isna(r.idade) else round(float(r.idade), 1), "partidas": int(r.partidas)}
                for r in t.itertuples()]

    # nº 1 por Elo no fim de cada temporada, entre quem jogou nos últimos 12 meses
    n1 = []
    datas = pd.to_datetime(dep["data"])
    completa = an.ultima_temporada_completa(pop)
    for ano in sorted(dep.loc[valido & (dep["ano"] <= completa), "ano"].unique()):
        fim = pd.Timestamp(f"{ano}-12-31")
        ate = dep[datas <= fim]
        ativo = ate[pd.to_datetime(ate["data"]) > fim - pd.Timedelta(days=365)].groupby("id").tail(1)
        r = ativo.sort_values("elo", ascending=False).iloc[0]
        n1.append({"ano": int(ano), "jogador": r.jogador, "elo": round(float(r.elo), 1)})
    # Elo atual (jogou nos últimos 12 meses da base)
    rec = dep[pd.to_datetime(dep["data"]) > pd.Timestamp(ult) - pd.Timedelta(days=365)]
    ativos = set(rec["id"])
    ultimo = dep[dep["id"].isin(ativos)].groupby("id").tail(1).sort_values("elo", ascending=False).head(20)
    sup_atual = {}
    for s_ in SUPS:
        u = dep[(dep["superficie"] == s_) & dep["id"].isin(ativos)].groupby("id").tail(1)
        sup_atual[s_] = [{"jogador": r.jogador, "elo": round(float(r.elo_sup), 1)} for r in
                         u.sort_values("elo_sup", ascending=False).head(10).itertuples()]
    # séries mensais (último Elo de cada mês) de quem passou de min_pico_serie fora do aquecimento
    pico_id = dep[valido].groupby("id")["elo"].max()
    ids = pico_id[pico_id >= min_pico_serie].index
    m = dep[dep["id"].isin(ids)].assign(mes=lambda x: x["data"].str[:7])
    series = {}
    for jid, g in m.groupby("id"):
        geral = g.groupby("mes").tail(1)
        item = {"meses": geral["mes"].tolist(), "elo": geral["elo"].round(1).tolist()}
        for s_ in SUPS:
            gs = g[g["superficie"] == s_].groupby("mes").tail(1)
            item[s_] = {"meses": gs["mes"].tolist(), "elo": gs["elo_sup"].round(1).tolist()}
        series[g["jogador"].iloc[0]] = item
    return {
        "metodo": {"inicial": INICIAL, "k": "250 / (partidas + 5)^0,4", "escala_prob": ESCALA_PROB,
                   "aquecimento": list(AQUECIMENTO), "superficies": SUPS, "ultima_data": ult},
        "validacao": validacao(d),
        "picos": {"geral": picos("elo", dep, 30),
                  **{s_: picos("elo_sup", dep[dep["superficie"] == s_], 15) for s_ in SUPS}},
        "n1_por_ano": n1,
        "atual": {"geral": [{"jogador": r.jogador, "elo": round(float(r.elo), 1)} for r in ultimo.itertuples()], **sup_atual},
        "series": series,
        "auges": (lista := auges(dep, min_pico_serie)),
        "idade_auge_por_epoca": idade_auge_por_epoca(lista),
        "envelhecimento": curva_idade(dep),
        "simulador": simulador(dep, [r["jogador"] for r in lista]),
    }


# ------------------------------------------------------------------ auge: quando e com que idade
EPOCAS_AUGE = [(1993, 2002), (2003, 2012), (2013, 2100)]


def auges(dep: pd.DataFrame, min_pico: float = 2050.0) -> list[dict]:
    """Pico instantâneo e auge sustentado (melhor média de 12 meses do Elo de fim de mês) de cada jogador.

    - idade: a partir do nascimento estimado (data da partida − idade registrada, mediana);
    - "no_auge": o melhor período de 12 meses termina no último ano da base, então o auge pode não ter
      chegado ainda (ex.: quem está subindo agora) — fica fora das contas de idade;
    - "carreira_antes_1991": estreou na base em 1991–1992 já com 22 anos ou mais; o auge pode ter sido
      antes de 1991 — também fica fora das contas de idade.
    """
    dep = dep.assign(dt=pd.to_datetime(dep["data"]))
    nasc = (dep["dt"] - pd.to_timedelta(dep["idade"] * 365.25, unit="D")).groupby(dep["id"]).median()
    ult = dep["dt"].max()
    valido = ~dep["ano"].between(*AQUECIMENTO)
    pico = dep[valido].groupby("id")["elo"].max()
    idade = lambda jid, t: None if pd.isna(nasc[jid]) else round((t - nasc[jid]).days / 365.25, 1)  # noqa: E731
    saida = []
    for jid in pico[pico >= min_pico].index:
        g = dep[dep["id"] == jid].set_index("dt")
        mes = g["elo"].resample("ME").last().ffill()
        rol = mes.rolling(12).mean()
        rol = rol[rol.index.year > AQUECIMENTO[1]].dropna()
        if rol.empty:
            continue
        fim = rol.idxmax()
        ini = fim - pd.DateOffset(months=11)
        gi = g[g["ano"] > AQUECIMENTO[1]]
        t_pico = gi["elo"].idxmax()
        estreia = g.index.min()
        saida.append({
            "jogador": g["jogador"].iloc[0],
            "pico": round(float(gi["elo"].max()), 1), "pico_data": t_pico.strftime("%Y-%m"), "pico_idade": idade(jid, t_pico),
            "auge": round(float(rol.max()), 1), "auge_ini": ini.strftime("%Y-%m"), "auge_fim": fim.strftime("%Y-%m"),
            "auge_idade": idade(jid, ini + (fim - ini) / 2),
            "no_auge": bool(fim > ult - pd.Timedelta(days=365)),
            "carreira_antes_1991": bool(estreia.year <= AQUECIMENTO[1] and (idade(jid, estreia) or 0) >= 22),
        })
    return sorted(saida, key=lambda r: -r["auge"])


def idade_auge_por_epoca(lista: list[dict]) -> list[dict]:
    """Idade no auge sustentado por época do auge (sem quem está no auge agora nem carreiras pré-1991)."""
    ok = pd.DataFrame([r for r in lista if not r["no_auge"] and not r["carreira_antes_1991"] and r["auge_idade"]])
    ok["ano"] = ok["auge_fim"].str[:4].astype(int)
    saida = []
    for a, b in EPOCAS_AUGE:
        g = ok[ok["ano"].between(a, b)]["auge_idade"]
        n = len(g)
        ep = float(g.std(ddof=1) / np.sqrt(n)) if n > 1 else None
        saida.append({"epoca": f"{a}–{min(b, int(ok['ano'].max()))}", "n": n, "mediana": float(g.median()), "media": float(g.mean()),
                      "ic_inf": float(g.mean() - 1.96 * ep) if ep else None, "ic_sup": float(g.mean() + 1.96 * ep) if ep else None})
    return saida


# ------------------------------------------------------------------ curva de envelhecimento
def _nivel(d: dict, base: int = 20, idades=range(18, 37)) -> dict:
    """Soma variações médias d[a] (Elo de a → a+1) num nível por idade, com 0 aos `base` anos."""
    nivel = {base: 0.0}
    for a in range(base, max(idades)):
        if a in d and a in nivel:
            nivel[a + 1] = nivel[a] + d[a]
    for a in range(base - 1, min(idades) - 1, -1):
        if a in d and a + 1 in nivel:
            nivel[a] = nivel[a + 1] - d[a]
    return nivel


def curva_idade(dep: pd.DataFrame, min_partidas: int = 10, reamostras: int = 300, semente: int = 0) -> dict:
    """Curva de envelhecimento pelo Elo: ingênua (média por idade) × método delta (mesmo jogador, a → a+1).

    A média ingênua sobe com a idade por sobrevivência: quem continua jogando aos 33 é quem é bom. O método
    delta compara cada jogador com ele mesmo um ano depois (os dois anos com ≥ min_partidas partidas) e soma
    as variações médias. IC 95% por reamostragem de jogadores. Por época: a época é a do ano de idade a.
    """
    x = dep[~dep["ano"].between(*AQUECIMENTO) & dep["idade"].notna()].copy()
    x["a"] = np.floor(x["idade"]).astype(int)
    s = x.groupby(["id", "a"]).agg(elo=("elo", "mean"), n=("elo", "size"), ano=("ano", "median")).reset_index()
    s = s[s["a"].between(17, 38)]
    ing = s[s["n"] >= min_partidas].groupby("a")["elo"].agg(["mean", "size"])
    m = s[s["n"] >= min_partidas]
    p = m.merge(m.assign(a=m["a"] - 1), on=["id", "a"], suffixes=("", "_2"))
    p["d"] = p["elo_2"] - p["elo"]
    p["epoca"] = pd.cut(p["ano"], [1992, 2002, 2012, 2100], labels=["1993–2002", "2003–2012", f"2013–{int(x['ano'].max())}"])
    rng = np.random.default_rng(semente)

    def com_ic(pp):
        # soma de w·d e de w por jogador × idade; cada reamostra de jogadores vira um produto de matrizes
        pp = pp.assign(w=2 / (1 / pp["n"] + 1 / pp["n_2"]))
        pp = pp.assign(wd=pp["w"] * pp["d"])
        wd = pp.pivot_table(index="id", columns="a", values="wd", aggfunc="sum", fill_value=0.0)
        w = pp.pivot_table(index="id", columns="a", values="w", aggfunc="sum", fill_value=0.0)
        idades_a = wd.columns.astype(int).tolist()
        media = lambda c: {a: float(x) for a, x, t in zip(idades_a, c @ wd.to_numpy(), c @ w.to_numpy()) if t > 0 for x in [x / t]}  # noqa: E731
        nivel = _nivel(media(np.ones(len(wd))))
        cont = rng.multinomial(len(wd), np.full(len(wd), 1 / len(wd)), size=reamostras)
        amostras = [_nivel(media(c)) for c in cont]
        idades = sorted(nivel)
        ic = {a: np.percentile([b[a] for b in amostras if a in b], [2.5, 97.5]) for a in idades}
        pico = max(nivel, key=nivel.get)
        return {"idades": idades, "nivel": [round(nivel[a], 1) for a in idades],
                "ic_inf": [round(float(ic[a][0]), 1) for a in idades], "ic_sup": [round(float(ic[a][1]), 1) for a in idades],
                "pico": int(pico), "aos_30": round(nivel.get(30, np.nan) - nivel[pico], 1),
                "pares": int(len(pp)), "jogadores": int(pp["id"].nunique())}

    return {
        "ingenua": {"idades": ing.index.astype(int).tolist(), "elo": ing["mean"].round(1).tolist(), "n": ing["size"].astype(int).tolist()},
        "delta": com_ic(p),
        "por_epoca": {str(e): com_ic(g) for e, g in p.groupby("epoca", observed=True)},
        "pares_por_idade": p.groupby("a").size().astype(int).to_dict(),
        "min_partidas": min_partidas,
    }


# ------------------------------------------------------------------ simulador Pico × Pico
def chance_set(p_md3: float) -> float:
    """Chance de vencer um set que, num melhor de 3, dá chance p_md3 de vencer a partida (p = s²(3 − 2s))."""
    lo, hi = 0.0, 1.0
    for _ in range(60):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if m * m * (3 - 2 * m) < p_md3 else (lo, m)
    return (lo + hi) / 2


def chance_md5(p_md3: float) -> float:
    s = chance_set(p_md3)
    return s ** 3 * (10 - 15 * s + 6 * s * s)


def simulador(dep: pd.DataFrame, nomes: list[str], min_partidas_sup: int = 20) -> dict:
    """Auge sustentado (melhor média de 12 meses) e pico de cada jogador, no geral e em cada superfície.

    A idade usa o mesmo nascimento estimado de `auges` (data da partida − idade registrada, mediana): no auge, a idade
    no meio dos 12 meses; no pico, na data do pico.
    """
    todas = dep.assign(dt=pd.to_datetime(dep["data"]))
    nasc = (todas["dt"] - pd.to_timedelta(todas["idade"] * 365.25, unit="D")).groupby(todas["jogador"]).median()
    idade = lambda nome, t: None if pd.isna(nasc.get(nome)) else round((t - nasc[nome]).days / 365.25, 1)  # noqa: E731
    dep = dep[~dep["ano"].between(*AQUECIMENTO)].assign(dt=lambda x: pd.to_datetime(x["data"]))
    saida = {}
    for nome, g in dep[dep["jogador"].isin(nomes)].groupby("jogador"):
        item = {}
        for chave, h, col in [("geral", g, "elo")] + [(s_, g[g["superficie"] == s_], "elo_sup") for s_ in SUPS]:
            if len(h) < (1 if chave == "geral" else min_partidas_sup):
                continue
            mes = h.set_index("dt")[col].resample("ME").last().ffill()
            rol = mes.rolling(12, min_periods=12).mean().dropna()
            if rol.empty:
                continue
            fim = rol.idxmax()
            ini = fim - pd.DateOffset(months=11)
            k_pico = h[col].idxmax()
            item[chave] = {"auge": round(float(rol.max()), 1), "ini": ini.strftime("%Y-%m"),
                           "fim": fim.strftime("%Y-%m"), "pico": round(float(h[col].max()), 1),
                           "pico_data": h.loc[k_pico, "data"][:7], "partidas": int(len(h)),
                           "idade": idade(nome, ini + (fim - ini) / 2), "pico_idade": idade(nome, h.loc[k_pico, "dt"])}
        saida[nome] = item
    return {"jogadores": saida, "escala_md3": ESCALA_MD3, "min_partidas_sup": min_partidas_sup}
