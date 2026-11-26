"""Passo 1 — baixa os CSVs anuais da TML-Database (ATP, de 1991 até a temporada atual).

1991 é a primeira temporada com estatísticas de saque e duração em quase todas as partidas; antes disso a
base só tem resultado, placar e (desde 1973) ranking.

Todas as temporadas são baixadas de novo a cada execução (~25 MB), porque a TML acrescenta partidas da temporada
em andamento e corrige também as antigas. No fim grava `base/fonte.json`, a impressão digital (sha256) de cada CSV:
a atualização automática (.github/workflows/atualizar.yml) só refaz a base quando esse arquivo muda.

Fonte: https://stats.tennismylife.org/tennis-match-database (a TML-Database saiu do GitHub em janeiro de 2026;
o repositório https://github.com/Tennismylife/TML-Database ficou só como referência histórica). Mesmo esquema
de colunas da antiga base JeffSackmann/tennis_atp.
"""
import hashlib
import json
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent  # pasta dados/
RAW = BASE / "base" / "raw"
FONTE = BASE / "base" / "fonte.json"
URL = "https://stats.tennismylife.org/data/{ano}.csv"
ANO_INI = 1991


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    ano_fim = date.today().year
    for ano in range(ANO_INI, ano_fim + 1):
        destino = RAW / f"{ano}.csv"
        try:
            urllib.request.urlretrieve(URL.format(ano=ano), destino)
            print(f"baixado {destino.name} ({destino.stat().st_size / 1024:.0f} KB)")
        except urllib.error.HTTPError as erro:  # temporada que a TML ainda não publicou
            print(f"{destino.name}: não disponível ({erro.code})")
    arquivos = sorted(RAW.glob("*.csv"))
    FONTE.write_text(json.dumps({f.stem: hashlib.sha256(f.read_bytes()).hexdigest()[:16] for f in arquivos}, indent=1),
                     encoding="utf-8")
    print(f"{len(arquivos)} arquivos em {RAW}")


if __name__ == "__main__":
    main()
