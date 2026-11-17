"""Os achados da página inicial: os fatos mais marcantes de cada análise, com os números tirados dos
resultados já calculados (nada digitado à mão — a página acompanha a base quando ela é atualizada).

Cada achado tem: tema, número de destaque, os dados de um mini gráfico e o link para a aba que explica.
O texto (PT/EN) fica no site, montado a partir destes números.
"""
from __future__ import annotations


def montar(resumo: dict, extras: dict, vp: dict, E: dict, corrida: dict, h2h: dict) -> dict:
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
    }
