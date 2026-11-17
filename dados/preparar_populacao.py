"""Passo 2 — monta a POPULAÇÃO a partir dos CSVs brutos da TML-Database.

População de interesse: todas as partidas de simples do circuito principal
da ATP entre 1991 e 2025 (Grand Slams, ATP Finals, Masters 1000, ATP 500 e
ATP 250) que foram concluídas em quadra.

Ficam fora:
- Copa Davis (D), Jogos Olímpicos (O) e eventos por equipes ou de exibição
  (nível A: World Team Cup, Grand Slam Cup, ATP Cup, United Cup, Laver Cup, Next Gen Finals);
- partidas não concluídas: W/O (walkover), RET (abandono) e DEF (desclassificação).

Unidade de análise: a partida. Data do torneio, ids e ordem da partida ficam na base para análises de
carreira (Elo, janelas de 52 semanas, jogadores homônimos).
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent  # pasta dados/
RAW = BASE / "base" / "raw"
SAIDA = BASE / "base" / "populacao.parquet"
RESUMO = BASE / "base" / "resumo_populacao.json"

NIVEIS = {
    "G": "Grand Slam",
    "F": "ATP Finals",
    "M": "Masters 1000",
    "500": "ATP 500",
    "250": "ATP 250",
}
SUPERFICIES = {"Hard": "Dura", "Clay": "Saibro", "Grass": "Grama", "Carpet": "Carpete"}
RODADAS = {
    "R128": "1ª rodada (R128)", "R64": "R64", "R32": "R32", "R16": "Oitavas (R16)",
    "QF": "Quartas", "SF": "Semifinal", "F": "Final", "RR": "Fase de grupos",
}
MAOS = {"R": "Destro", "L": "Canhoto"}
SET_RE = re.compile(r"\d+-\d+")
ANOS = (1991, 2025)  # temporadas completas; a atual entra pela atualização automática


def carregar_brutos() -> pd.DataFrame:
    arquivos = sorted(RAW.glob("*.csv"))
    if not arquivos:
        raise SystemExit("Sem CSVs em dados/base/raw — rode dados/baixar.py antes.")
    return pd.concat([pd.read_csv(f, low_memory=False) for f in arquivos], ignore_index=True)


def pontos_e_consistencia(pop: pd.DataFrame) -> None:
    """Pontos ganhos por cada lado e checagem de que as estatísticas da partida são possíveis.

    Pontos do vencedor = ganhos no próprio saque + ganhos devolvendo o saque do perdedor. Cada game
    vencido exige pelo menos 4 pontos, então um lado com menos de 4 × (games que venceu) pontos tem
    estatísticas impossíveis (ex.: 6-1 6-3 com 32 pontos). Essas partidas (~0,15% da base, espalhadas
    pelos anos) ficam com `stats_ok = False` e saem de todos os critérios de saque, devolução e pontos.
    """
    games = pop["placar"].astype(str).map(lambda s: [tuple(map(int, x.split("-"))) for x in SET_RE.findall(s)])
    pop["games_vencedor"] = games.map(lambda g: sum(a for a, _ in g))
    pop["games_perdedor"] = games.map(lambda g: sum(b for _, b in g))
    pv = pop["v_1won"] + pop["v_2won"] + (pop["p_svpt"] - pop["p_1won"] - pop["p_2won"])
    pp = pop["v_svpt"] + pop["p_svpt"] - pv
    completas = pop[["v_svpt", "p_svpt", "v_1in", "v_svgms", "v_1won", "v_2won", "p_1won", "p_2won"]].notna().all(axis=1)         & (pop["v_svpt"] > 0) & (pop["p_svpt"] > 0)
    pop["stats_ok"] = completas & (pv >= 4 * pop["games_vencedor"]) & (pp >= 4 * pop["games_perdedor"])
    pop["pontos_vencedor"] = pv.where(pop["stats_ok"])
    pop["pontos_perdedor"] = pp.where(pop["stats_ok"])


def nomes_por_id(pop: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Um nome por jogador (id), e um id por nome exibido.

    - Erro de digitação na fonte: o mesmo id com nomes diferentes fica com o nome mais frequente
      (ex.: uma partida de John Millman, id MH30, registrada como "Marc-Andrea Huesler").
    - Homônimos: nomes iguais com ids diferentes ganham o país no nome, menos o de mais partidas
      (ex.: Martin Damm, tcheco dos anos 90, e "Martin Damm (USA)", americano a partir de 2024).
    """
    lados = [("vencedor", "id_vencedor", "pais_vencedor"), ("perdedor", "id_perdedor", "pais_perdedor")]
    todos = pd.concat([pop[list(c)].set_axis(["nome", "id", "pais"], axis=1) for c in lados])
    mais_frequente = lambda s: s.value_counts(dropna=False).index[0]  # noqa: E731
    nome = todos.groupby("id")["nome"].agg(mais_frequente)
    pais = todos.groupby("id")["pais"].agg(mais_frequente)
    partidas = todos["id"].value_counts()
    correcoes = []
    for n, ids in nome.groupby(nome).groups.items():
        if len(ids) > 1:
            principal = max(ids, key=lambda i: partidas[i])
            for i in ids:
                if i != principal:
                    nome[i] = f"{n} ({pais[i]})"
                    correcoes.append(f"homônimo: {i} {n} → {nome[i]}")
    for n_col, id_col, _ in lados:
        novo = pop[id_col].map(nome)
        trocas = pop.loc[pop[n_col] != novo, [id_col, n_col]].drop_duplicates()
        correcoes += [f"nome: {i} {antigo} → {nome[i]}" for i, antigo in trocas.itertuples(index=False)
                      if not antigo == nome[i].split(" (")[0]]
        pop[n_col] = novo
    return pop, sorted(set(correcoes))


def montar_populacao(bruto: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    ano = bruto["tourney_date"].astype(str).str[:4].astype(int)
    bruto = bruto[ano.between(*ANOS)]
    etapas = {"partidas_brutas": len(bruto)}

    df = bruto[bruto["tourney_level"].astype(str).isin(NIVEIS)].copy()
    etapas["apos_filtro_nivel"] = len(df)

    nao_concluida = df["score"].astype(str).str.contains(r"W/O|RET|DEF", regex=True)
    df = df[~nao_concluida].copy()
    etapas["apos_excluir_nao_concluidas"] = len(df)

    sets = df["score"].astype(str).apply(lambda s: len(SET_RE.findall(s)))
    rank_ok = df["winner_rank"].notna() & df["loser_rank"].notna()
    minutos = df["minutes"].where(df["minutes"].between(20, 720))  # <20 min = erro de registro

    data = pd.to_datetime(df["tourney_date"].astype(str), format="%Y%m%d")
    pop = pd.DataFrame({
        "ano": data.dt.year,
        "data": data.dt.strftime("%Y-%m-%d"),           # início do torneio
        "id_torneio": df["tourney_id"].astype(str),
        "ordem": df["match_num"],                         # ordem da partida dentro do torneio
        "id_vencedor": df["winner_id"].astype(str),
        "id_perdedor": df["loser_id"].astype(str),
        "torneio": df["tourney_name"],
        "nivel": df["tourney_level"].astype(str).map(NIVEIS),
        "superficie": df["surface"].map(SUPERFICIES),
        "ambiente": df["indoor"].map({"O": "Aberto", "I": "Coberto"}),
        "rodada": df["round"].map(RODADAS).fillna(df["round"]),
        "melhor_de": df["best_of"].map({3: "Melhor de 3", 5: "Melhor de 5"}),
        "vencedor": df["winner_name"],
        "perdedor": df["loser_name"],
        "pais_vencedor": df["winner_ioc"],
        "mao_vencedor": df["winner_hand"].map(MAOS),
        "idade_vencedor": df["winner_age"].round(1),
        "altura_vencedor": df["winner_ht"],
        "ranking_vencedor": df["winner_rank"],
        "ranking_perdedor": df["loser_rank"],
        "minutos": minutos,
        "aces_total": df["w_ace"] + df["l_ace"],
        "duplas_faltas_total": df["w_df"] + df["l_df"],
        "sets_jogados": sets,
        "placar": df["score"],
        # perfil do perdedor (para a análise por jogador / top N)
        "pais_perdedor": df["loser_ioc"],
        "mao_perdedor": df["loser_hand"].map(MAOS),
        "idade_perdedor": df["loser_age"].round(1),
        "altura_perdedor": df["loser_ht"],
    })
    # estatísticas de saque de cada lado: v_ = vencedor, p_ = perdedor
    for lado, pref in (("v", "w"), ("p", "l")):
        for novo, orig in (("ace", "ace"), ("df", "df"), ("svpt", "svpt"), ("1in", "1stIn"),
                           ("1won", "1stWon"), ("2won", "2ndWon"), ("svgms", "SvGms"),
                           ("bpsav", "bpSaved"), ("bpfac", "bpFaced")):
            pop[f"{lado}_{novo}"] = df[f"{pref}_{orig}"].to_numpy()
    pop["decada"] = (pop["ano"] // 10 * 10).astype(str) + "s"
    pop["set_decisivo"] = np.where(pop["sets_jogados"] == df["best_of"], "Sim", "Não")
    pop["favorito_venceu"] = np.where(
        rank_ok, np.where(df["winner_rank"] < df["loser_rank"], "Sim", "Não"), None
    )
    pop["dif_ranking"] = (df["winner_rank"] - df["loser_rank"]).abs()
    pontos_e_consistencia(pop)
    pop, correcoes = nomes_por_id(pop)
    pop = pop.sort_values(["data", "id_torneio", "ordem"], kind="stable").reset_index(drop=True)
    pop.insert(0, "id_partida", np.arange(1, len(pop) + 1))

    etapas["N_populacao"] = len(pop)
    resumo = {
        "fonte": "TML-Database (Tennismylife) — https://github.com/Tennismylife/TML-Database",
        "periodo": f"{pop['ano'].min()}–{pop['ano'].max()}",
        "ano_min": int(pop["ano"].min()), "ano_max": int(pop["ano"].max()),
        "n_temporadas": int(pop["ano"].nunique()),
        "pct_com_estatisticas": round(100 * pop["stats_ok"].mean(), 1),
        "n_stats_impossiveis": int((pop["v_svpt"].notna() & ~pop["stats_ok"]).sum()),
        "correcoes_de_nome": correcoes,
        "N": len(pop),
        "n_variaveis": pop.shape[1],
        "n_variaveis_brutas": bruto.shape[1],
        "etapas_filtro": etapas,
        "pct_ausentes": (pop.isna().mean() * 100).round(2).to_dict(),
        "n_torneios": int(pop[["torneio", "ano"]].drop_duplicates().shape[0]),
        "n_jogadores": int(pd.concat([pop["vencedor"], pop["perdedor"]]).nunique()),
    }
    return pop, resumo


def main() -> None:
    pop, resumo = montar_populacao(carregar_brutos())
    pop.to_parquet(SAIDA, index=False)
    RESUMO.write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: resumo[k] for k in ("N", "n_variaveis", "etapas_filtro")}, indent=2))
    print(f"salvo {SAIDA.name} ({SAIDA.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
