"""Passo 3 — tabela de TÍTULOS (finais vencidas) para a corrida de títulos e Slams por idade.

Diferente da população, aqui contam as finais não concluídas: um título ganho porque o adversário
abandonou ou não entrou em quadra continua sendo título.

- 1991 em diante: todas as finais do circuito principal (Grand Slams, ATP Finals, Masters 1000, ATP 500,
  ATP 250), dos CSVs de dados/base/raw.
- Antes de 1991: só as finais de Grand Slam. A fonte codifica os outros torneios de outro jeito antes de
  1991 (a maioria fica como "A", junto com eventos por equipes e exibições), então só os Slams são
  confiáveis. Assim, quem já estava no circuito em 1991 (Sampras, Becker, Edberg, Lendl…) entra na corrida
  de Slams com a contagem certa; os demais títulos deles antes de 1991 ficam de fora (avisado no site).

Saída: dados/base/titulos.parquet
"""
import urllib.request
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent
RAW = BASE / "base" / "raw"
RAW_ANTIGO = BASE / "base" / "raw_antigo"       # 1968–1990, só para as finais de Slam (ignorado no git)
SAIDA = BASE / "base" / "titulos.parquet"
URL = "https://raw.githubusercontent.com/Tennismylife/TML-Database/master/{ano}.csv"
NIVEIS = {"G": "Grand Slam", "F": "ATP Finals", "M": "Masters 1000", "500": "ATP 500", "250": "ATP 250"}
ANOS_ANTIGOS = range(1968, 1991)


def baixar_antigos() -> None:
    RAW_ANTIGO.mkdir(parents=True, exist_ok=True)
    for ano in ANOS_ANTIGOS:
        destino = RAW_ANTIGO / f"{ano}.csv"
        if not destino.exists():
            urllib.request.urlretrieve(URL.format(ano=ano), destino)


def finais(arquivos, niveis) -> pd.DataFrame:
    d = pd.concat([pd.read_csv(f, low_memory=False) for f in arquivos], ignore_index=True)
    d = d[(d["round"] == "F") & d["tourney_level"].astype(str).isin(niveis)]
    data = pd.to_datetime(d["tourney_date"].astype(str), format="%Y%m%d")
    return pd.DataFrame({
        "data": data.dt.strftime("%Y-%m-%d"), "ano": data.dt.year, "torneio": d["tourney_name"],
        "nivel": d["tourney_level"].astype(str).map(NIVEIS), "id_vencedor": d["winner_id"].astype(str),
        "vencedor": d["winner_name"], "perdedor": d["loser_name"], "idade": d["winner_age"].round(2),
        "placar": d["score"].astype(str),
        "concluida": ~d["score"].astype(str).str.contains(r"W/O|RET|DEF", regex=True),
    })


def main() -> None:
    baixar_antigos()
    novos = finais(sorted(RAW.glob("*.csv")), NIVEIS)
    novos["fonte"] = "1991+"
    antigos = finais(sorted(RAW_ANTIGO.glob("*.csv")), ["G"])
    antigos["fonte"] = "slam_antes_1991"
    t = pd.concat([antigos, novos], ignore_index=True).sort_values(["data", "torneio"]).reset_index(drop=True)
    # um nome por id, igual à população (o mais frequente; homônimos já separados lá)
    pop = pd.read_parquet(BASE / "base" / "populacao.parquet")
    nomes = pd.concat([pop[["id_vencedor", "vencedor"]].set_axis(["id", "nome"], axis=1),
                       pop[["id_perdedor", "perdedor"]].set_axis(["id", "nome"], axis=1)]).drop_duplicates("id").set_index("id")["nome"]
    t["vencedor"] = t["id_vencedor"].map(nomes).fillna(t["vencedor"])
    t.to_parquet(SAIDA, index=False)
    print(f"{len(t)} títulos ({(t['fonte'] == 'slam_antes_1991').sum()} Slams antes de 1991, "
          f"{(~t['concluida']).sum()} finais não concluídas) → {SAIDA.name}")


if __name__ == "__main__":
    main()
