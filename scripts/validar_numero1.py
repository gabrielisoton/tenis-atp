"""Valida a análise dos nº 1 (tenis/numero1.py) contra o que a história do tênis conhece. Termina com "TUDO OK"."""
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from tenis import numero1  # noqa: E402

pop = pd.read_parquet(RAIZ / "dados" / "base" / "populacao.parquet")
N = numero1.exportar(pop, pd.read_parquet(RAIZ / "dados" / "base" / "titulos.parquet"))
J, falhas = N["jogadores"], []


def checar(cond, msg):
    print(("ok   " if cond else "FALHA") + " " + msg)
    if not cond:
        falhas.append(msg)


checar(len(J) >= 20 and {"Roger Federer", "Pete Sampras", "Carlos Alcaraz", "Marcelo Rios"} <= set(J), f"{len(J)} nº 1 na base, incluindo os dos anos 90")
for nome, ano in {"Novak Djokovic": 2011, "Roger Federer": 2004, "Rafael Nadal": 2008, "Jannik Sinner": 2023}.items():
    checar((J[nome]["virada"] or {}).get("ano") == ano, f"ano da virada de {nome}: {(J[nome]['virada'] or {}).get('ano')} (esperado {ano})")
checar(J["Pete Sampras"]["cobertura"] == "ja_no_topo" and J["Boris Becker"]["cobertura"] == "antes_1991" and J["Novak Djokovic"]["cobertura"] == "completa",
       "cobertura: Sampras já no topo em 1991, Becker com carreira antes de 1991, Djokovic com a jornada completa")
checar(J["Novak Djokovic"]["marcos"]["slams"] == 24 and J["Roger Federer"]["marcos"]["titulos"] == 103, "marcos: Djokovic 24 Slams, Federer 103 títulos")
c = {r["crit"]: r["z"] for r in N["em_comum"]}
checar(min(c["ganhos_2"], c["devolucao"]) > max(c["aces_game"], c["primeiro_dentro"]),
       f"em comum: 2º saque ({c['ganhos_2']}) e devolução ({c['devolucao']}) acima de aces ({c['aces_game']}) e 1º saque dentro ({c['primeiro_dentro']})")
d = {r["ind"]: r for r in N["depois_do_topo"]["media"]}
checar(d["devolucao"]["media"] < 0 and d["devolucao"]["caiu_em"] >= 2 * N["depois_do_topo"]["n"] / 3,
       f"depois do topo: devolução cai em {d['devolucao']['caiu_em']} de {N['depois_do_topo']['n']}")
fases = J["Novak Djokovic"]["fases"]
checar(fases["nº 1"]["todos"]["vitorias"] > fases["> 50"]["todos"]["vitorias"], "jornada: Djokovic vence mais como nº 1 do que com ranking > 50")
print("\nTUDO OK" if not falhas else f"\n{len(falhas)} FALHA(S): " + " | ".join(falhas))
sys.exit(1 if falhas else 0)
