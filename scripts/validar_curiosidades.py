"""Valida as curiosidades (tenis/curiosidades.py) contra fatos conhecidos do tênis. Termina com "TUDO OK"."""
import json
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from tenis import curiosidades as cu  # noqa: E402

pop = pd.read_parquet(RAIZ / "dados" / "base" / "populacao.parquet")
D = RAIZ / "site" / "data"
C = cu.exportar(pop, json.loads((D / "venceu_perdendo.json").read_text(encoding="utf-8")), json.loads((D / "extras.json").read_text(encoding="utf-8")))
falhas = []


def checar(cond, msg):
    print(("ok   " if cond else "FALHA") + " " + msg)
    if not cond:
        falhas.append(msg)


L = C["longos"][0]
checar((L["vencedor"], L["perdedor"], L["ano"], L["minutos"]) == ("John Isner", "Nicolas Mahut", 2010, 665), f"jogo mais longo: {L['vencedor']} × {L['perdedor']} {L['ano']}, {L['minutos']} min (11h05)")
A = C["aces"][0]
checar((A["jogador"], A["aces"]) == ("John Isner", 113), f"mais aces numa partida: {A['jogador']} {A['aces']}")
fin = {(f["ano"], f["vencedor"]) for f in C["viradas"]["finais_gs"]}
checar({(2020, "Dominic Thiem"), (2021, "Novak Djokovic"), (2022, "Rafael Nadal")} <= fin, f"viradas de 0–2 em finais de Slam: {sorted(fin)}")
Z = C["zebras"]["slams"]
checar(any(z["vencedor"] == "Denis Istomin" and z["perdedor"] == "Novak Djokovic" for z in Z[:3]), "zebra em Slam: Istomin × Djokovic (Australian Open 2017) entre as 3 maiores")
checar(all(z["chance"] < 0.1 for z in Z), "toda zebra da lista tinha menos de 10% de chance")
S = {s["jogador"]: s["n"] for s in C["sequencias"]}
checar(S.get("Roger Federer", 0) >= 35 and S.get("Novak Djokovic", 0) >= 35, f"sequências: Federer {S.get('Roger Federer')} (2006–07), Djokovic {S.get('Novak Djokovic')} (2011)")
checar(C["pneus"]["triplo"] and C["pneus"]["triplo"][0]["vencedor"] == "Sergi Bruguera", "o único 6-0 6-0 6-0: Bruguera, Roland Garros 1993")
print("\nTUDO OK" if not falhas else f"\n{len(falhas)} FALHA(S): " + " | ".join(falhas))
sys.exit(1 if falhas else 0)
