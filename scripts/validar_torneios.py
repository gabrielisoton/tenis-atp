"""Valida a página Torneios (dados/preparar_torneios.py + tenis/torneios.py) contra fatos conhecidos. Termina com "TUDO OK"."""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
D = RAIZ / "site" / "data" / "torneios"
falhas = []


def checar(cond, msg):
    print(("ok   " if cond else "FALHA") + " " + msg)
    if not cond:
        falhas.append(msg)


def t(cod):
    return json.loads((D / f"{cod}.json").read_text(encoding="utf-8"))


I = json.loads((D / "indice.json").read_text(encoding="utf-8"))["torneios"]
checar([x["nome"] for x in I[:4]] == ["Australian Open", "Roland Garros", "Wimbledon", "US Open"], "os 4 Slams abrem a lista, na ordem do calendário")
for cod, nome, n in (("520", "Rafael Nadal", 14), ("540", "Roger Federer", 8), ("580", "Novak Djokovic", 10)):
    dono = dict(t(cod)["donos"])
    checar(dono.get(nome) == n, f"{t(cod)['nome']}: {nome} com {dono.get(nome)} títulos (esperado {n})")
W = t("540")
ix = W["jogadores"]
fin19 = [m for m in W["chaves"]["2019"] if m[0] == 6][0]
checar((ix[fin19[1]], ix[fin19[2]]) == ("Novak Djokovic", "Roger Federer"), "final de Wimbledon 2019: Djokovic × Federer")
checar(len(W["chaves"]["2019"]) == 127, f"chave completa de Wimbledon 2019: {len(W['chaves']['2019'])} partidas (127)")
checar(any(c["ano"] == 1968 for c in W["campeoes"]), "campeões dos Slams desde 1968")
print("\nTUDO OK" if not falhas else f"\n{len(falhas)} FALHA(S): " + " | ".join(falhas))
sys.exit(1 if falhas else 0)
