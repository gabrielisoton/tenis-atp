"""Passo 5 — todas as partidas de cada torneio, para a página Torneios: as chaves completas (com W.O. e abandonos)
e os campeões. Saída: base/torneios.parquet.

Diferente da população, aqui entram TODAS as partidas da chave (inclusive W.O.), porque uma chave com buracos não
serve. Os torneios são agrupados pelo código da TML (o fim do `tourney_id`), que não muda quando o torneio troca
de nome ou de cidade (ex.: Hamburg foi Masters até 2008 e é ATP 500 depois, com o mesmo código).
Os Grand Slams ganham também as finais de 1968–1990 (dos CSVs antigos), para a lista de campeões.
"""
import sys
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent
RAW = BASE / "base" / "raw"
RAW_ANTIGO = BASE / "base" / "raw_antigo"
SAIDA = BASE / "base" / "torneios.parquet"
sys.path.insert(0, str(BASE))
from preparar_populacao import NIVEIS  # noqa: E402

SUP = {"Hard": "Dura", "Clay": "Saibro", "Grass": "Grama", "Carpet": "Carpete"}
RODADAS = ["R128", "R64", "R32", "R16", "QF", "SF", "F", "RR"]


def ler(arquivos) -> pd.DataFrame:
    d = pd.concat([pd.read_csv(f, low_memory=False) for f in arquivos], ignore_index=True)
    d["lv"] = d["tourney_level"].astype(str)
    return d


def montar(d: pd.DataFrame, antigo: bool) -> pd.DataFrame:
    data = pd.to_datetime(d["tourney_date"].astype(str), format="%Y%m%d")
    num = lambda c: pd.to_numeric(d[c], errors="coerce")  # noqa: E731
    return pd.DataFrame({
        "cod": d["tourney_id"].astype(str).str.split("-").str[-1].str.lstrip("0"), "ano": data.dt.year,
        "data": data.dt.strftime("%Y-%m-%d"), "torneio": d["tourney_name"], "nivel": d["lv"].map(NIVEIS),
        "superficie": d["surface"].map(SUP), "rodada": d["round"].astype(str), "ordem": num("match_num"),
        "id_vencedor": d["winner_id"].astype(str), "vencedor": d["winner_name"], "id_perdedor": d["loser_id"].astype(str),
        "perdedor": d["loser_name"], "seed_v": num("winner_seed"), "seed_p": num("loser_seed"),
        "entrada_v": d["winner_entry"].fillna(""), "entrada_p": d["loser_entry"].fillna(""),
        "rank_v": num("winner_rank"), "rank_p": num("loser_rank"), "idade_v": num("winner_age").round(1),
        "placar": d["score"].astype(str), "minutos": num("minutes"),
        "aces": num("w_ace") + num("l_ace"), "games_saque": num("w_SvGms") + num("l_SvGms"), "antigo": antigo,
    })


def main() -> None:
    novos = ler(sorted(RAW.glob("*.csv")))
    novos = novos[novos["lv"].isin(NIVEIS) & novos["round"].isin(RODADAS)]
    t = [montar(novos, False)]
    if RAW_ANTIGO.exists():
        velhos = ler(sorted(RAW_ANTIGO.glob("*.csv")))
        velhos = velhos[(velhos["lv"] == "G") & (velhos["round"] == "F")]
        t.append(montar(velhos, True))
    t = pd.concat(t, ignore_index=True)
    # um nome por id, igual à população (o mais frequente; homônimos já separados lá)
    pop = pd.read_parquet(BASE / "base" / "populacao.parquet")
    nomes = pd.concat([pop[["id_vencedor", "vencedor"]].set_axis(["id", "nome"], axis=1),
                       pop[["id_perdedor", "perdedor"]].set_axis(["id", "nome"], axis=1)]).drop_duplicates("id").set_index("id")["nome"]
    t["vencedor"] = t["id_vencedor"].map(nomes).fillna(t["vencedor"])
    t["perdedor"] = t["id_perdedor"].map(nomes).fillna(t["perdedor"])
    t.to_parquet(SAIDA, index=False)
    print(f"{len(t)} partidas de {t['cod'].nunique()} torneios → {SAIDA.name}")


if __name__ == "__main__":
    main()
