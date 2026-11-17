"""Os achados da página inicial: os fatos mais marcantes de cada análise, com os números tirados dos
resultados já calculados (nada digitado à mão — a página acompanha a base quando ela é atualizada).

Cada achado tem: tema, número de destaque, os dados de um mini gráfico e o link para a aba que explica.
O texto (PT/EN) fica no site, montado a partir destes números.
"""
from __future__ import annotations

import numpy as np


def montar(resumo: dict, extras: dict, vp: dict, E: dict, corrida: dict, h2h: dict, n1: dict, ganhar: dict, conf: dict) -> dict:
    # 1. maior pico de Elo e a carreira de quem o atingiu
    pico = E["picos"]["geral"][0]
    serie = E["series"][pico["jogador"]]
    # 2. idade do auge (curva de envelhecimento pelo método delta) e por época
    env = E["envelhecimento"]
    # 3. Slams até os 22 anos (corrida por idade)
    J = corrida["jogadores"]
    aos22 = sorted(((n, sum(1 for t in v["t"] if t[1] == "G" and t[0] < 23)) for n, v in J.items()), key=lambda x: -x[1])[:6]
    # 4. venceu perdendo nos pontos
    jg = vp["jogadores"]
    fed = jg["jogador"].index("Roger Federer") if "Roger Federer" in jg["jogador"] else None
    # 5. a maior rivalidade
    nomes = {j[0]: j[1] for j in h2h["jogadores"]}
    a, b, n, va, vb = h2h["rivalidades"][0]
    # 6. pontos ganhos: elite × resto
    top10 = extras["top_n"]["por_n"]["10"]["Todas"]
    # 7. o Elo prevê melhor que o ranking
    V = E["validacao"]
    # 8. como o jogo mudou: aces por partida
    lt = extras["linha_tempo"]
    # 9. o que todo nº 1 tem: quantos estão bem acima do circuito (z > 1) em cada critério de jogo
    nn = len(n1["jogadores"])
    acima = {r["crit"]: round(r["pct_acima_1"] * nn) for r in n1["em_comum"]}
    return {
        "resumo": {"N": resumo["N"], "periodo": resumo["periodo"], "n_jogadores": resumo["n_jogadores"]},
        "pico": {"jogador": pico["jogador"], "elo": pico["elo"], "data": pico["data"], "idade": pico["idade"],
                 "serie": {"meses": serie["meses"], "elo": serie["elo"]},
                 "segundo": E["picos"]["geral"][1]},
        "auge": {"idade": env["delta"]["pico"], "por_epoca": {k: v["pico"] for k, v in env["por_epoca"].items()},
                 "curvas": {k: {"idades": v["idades"], "nivel": v["nivel"]} for k, v in env["por_epoca"].items()}},
        "aos22": aos22,
        "venceu_perdendo": {"pct": vp["resumo"]["pct"], "pct_decisivo": vp["por"]["set_decisivo"]["Sim"]["pct"],
                            "finais_gs": len(vp["finais_gs"]),
                            "federer": None if fed is None else {"perdeu_mais": jg["perdeu_mais"][fed], "venceu_menos": jg["venceu_menos"][fed],
                                                                "derrotas": jg["d_com_pontos"][fed]},
                            "wimbledon_2019": next(({"pv": f["pontos_vencedor"], "pp": f["pontos_perdedor"]} for f in vp["finais_gs"]
                                                    if f["ano"] == 2019 and f["torneio"] == "Wimbledon"), None)},
        "rivalidade": {"a": nomes[a], "b": nomes[b], "n": n, "va": va, "vb": vb},
        "elite": {"tpw_top10": top10["top"]["tpw"], "tpw_demais": top10["demais"]["tpw"], "vitorias_top10": top10["duelo"]["vitorias_top"]},
        "elo_acerta": {"elo": V["acerto_elo"], "ranking": V["acerto_ranking"], "n": V["n"]},
        "aces": {"anos": [r["ano"] for r in lt], "media": [round(r["aces_media"], 2) for r in lt]},
        "numero1": {"n": nn, "acima": acima},
        # 10. o que faz ganhar: quanto vale +1 ponto de saque a cada 100 numa partida parelha, e o peso (z) de cada aspecto
        "ganhar": (lambda c: {"por_ponto": round(sum(x["por_ponto"] for x in c if x["por_ponto"]) / 3, 4),
                              "z": {x["crit"]: x["z"] for x in c}})(ganhar["recortes"]["Todas|Todos|Todas"]["modelo"]["coef"]),
        # 11. frieza existe? quanto o "acima do esperado" se repete, e os nº 1 nos sets decisivos
        "pressao": {"conf": {k: v["confiabilidade"] for k, v in conf["criterios"].items()},
                    "n1_dec_acima": sum(1 for j in n1["jogadores"].values() if (j["pressao"]["dec_ae"] or 0) > 0),
                    "n1": len(n1["jogadores"]),
                    "n1_dec_media": round(float(np.mean([j["pressao"]["dec_ae"] for j in n1["jogadores"].values() if j["pressao"]["dec_ae"] is not None])), 4)},
    }
