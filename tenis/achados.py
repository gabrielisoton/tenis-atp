"""Os achados da página inicial: os fatos mais marcantes de cada análise, com os números tirados dos
resultados já calculados (nada digitado à mão — a página acompanha a base quando ela é atualizada).

Cada achado tem: tema, número de destaque, os dados de um mini gráfico e o link para a aba que explica.
O texto (PT/EN) fica no site, montado a partir destes números.
"""
from __future__ import annotations

import numpy as np

from tenis import analises as an


# aspectos do jogo comparados no card "a maior vantagem do Top N" (proporções; fora os totais e o resultado)
ASPECTOS = ["primeiro_dentro", "ganhos_1", "ganhos_2", "devolucao", "bp_salvos", "bp_convertidos"]


def _melhores(tab) -> dict:
    """O jogador mais completo: o 1º do quadro de medalhas e em quantos aspectos ele fica no top 10."""
    podio, med = an.lideres(tab)
    return {"jogador": med.index[0], "top": int(med.iloc[0]["top10"]), "ouro": int(med.iloc[0]["ouro"]), "n": int(len(podio))}


def _perfil(tab, nome: str) -> dict | None:
    """O aspecto do jogo em que `nome` mais se destaca (percentil entre os jogadores com 100+ partidas)."""
    melhor = None
    for k in ("ganhos_1", "ganhos_2", "devolucao", "bp_salvos", "bp_convertidos", "tie_breaks", "decisivos", "primeiro_dentro", "aces_game"):
        rk = an.ranking_criterio(tab, k)
        if nome in rk.index and (melhor is None or rk.loc[nome, "percentil"] > melhor["percentil"]):
            melhor = {"jogador": nome, "chave": k, "aspecto": an.CRIT[k].nome, "percentil": round(float(rk.loc[nome, "percentil"]), 1),
                      "posicao": int(rk.loc[nome, "posicao"]), "total": int(len(rk))}
    return melhor


def montar(resumo: dict, extras: dict, vp: dict, E: dict, corrida: dict, h2h: dict, n1: dict, ganhar: dict, conf: dict,
           tab=None, curios: dict | None = None, torneios: dict | None = None) -> dict:
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
        # o jogo está mais rápido? aces e duração (melhor de 3) por temporada completa
        "tempo": {"anos": [r["ano"] for r in lt], "aces": [round(r["aces_media"], 2) for r in lt],
                  "minutos": [round(r["minutos_bo3_media"], 1) for r in lt]},
        # a maior vantagem do Top 5 e do Top 10 sobre os demais, entre os aspectos do jogo (em pontos percentuais)
        "vantagem": {n: sorted([{"chave": k, "top": round(extras["top_n"]["por_n"][n]["Todas"]["top"][k], 4),
                                 "demais": round(extras["top_n"]["por_n"][n]["Todas"]["demais"][k], 4),
                                 "dif": round(extras["top_n"]["por_n"][n]["Todas"]["top"][k] - extras["top_n"]["por_n"][n]["Todas"]["demais"][k], 4)}
                                for k in ASPECTOS], key=lambda r: -r["dif"]) for n in ("5", "10")},
        "numero1": {"n": nn, "acima": acima,
                    "mais_jovem": min(({"jogador": k, "idade": v["marcos"]["n1_idade"]} for k, v in n1["jogadores"].items() if v["marcos"]["n1_idade"]),
                                      key=lambda r: r["idade"])},
        # para os cards de cada aba
        "atual": E["atual"]["geral"][0],
        "perfil": None if tab is None else _perfil(tab, "Roger Federer"),
        "melhores": None if tab is None else _melhores(tab),
        "zebra": None if curios is None else curios["zebras"]["slams"][0],
        "dono_torneio": None if torneios is None else (lambda t: {"jogador": t["dono"][0], "n": t["dono"][1], "torneio": t["nome"], "cod": t["cod"]})(
            max((t for t in torneios["torneios"] if t["dono"]), key=lambda t: t["dono"][1])),
        # 10. o que faz ganhar: quanto vale +1 ponto de saque a cada 100 numa partida parelha, e o peso (z) de cada aspecto
        "ganhar": (lambda c: {"por_ponto": round(sum(x["por_ponto"] for x in c if x["por_ponto"]) / 3, 4),
                              "z": {x["crit"]: x["z"] for x in c}})(ganhar["recortes"]["Todas|Todos|Todas"]["modelo"]["coef"]),
        # 11. frieza existe? quanto o "acima do esperado" se repete, e os nº 1 nos sets decisivos
        "pressao": {"conf": {k: v["confiabilidade"] for k, v in conf["criterios"].items()},
                    "n1_dec_acima": sum(1 for j in n1["jogadores"].values() if (j["pressao"]["dec_ae"] or 0) > 0),
                    "n1": len(n1["jogadores"]),
                    "n1_dec_media": round(float(np.mean([j["pressao"]["dec_ae"] for j in n1["jogadores"].values() if j["pressao"]["dec_ae"] is not None])), 4)},
    }
