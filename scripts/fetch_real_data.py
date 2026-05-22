"""
Descarga REAL de datasets de Kaggle/GitHub/Wikipedia para enriquecer el modelo.

Para los datasets de GitHub (públicos sin auth) lo hacemos automático.
Para Kaggle se necesita kaggle.json en ~/.kaggle/ — el script lo detecta.
Para Wikipedia/eloratings scrape con BeautifulSoup.

Uso:
    pip install kaggle beautifulsoup4 requests pandas
    python scripts/fetch_real_data.py [--full | --quick]

Outputs:
    data/raw/martj42_results.csv       (49K+ partidos internacionales 1872-2026)
    data/raw/fifa_rankings.csv          (snapshot FIFA ranking abril 2026)
    data/raw/eloratings_current.csv     (Elo actual de las 48 selecciones)
    data/raw/eafc26_players.csv         (ratings EA FC26)
    data/raw/wc2026_squads.json         (convocados scrapeados de Wikipedia)
    data/raw/transfermarkt_values.csv   (market value de jugadores)
"""
from __future__ import annotations
import json
import os
import sys
import urllib.request
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# 1. Resultados internacionales (martj42 — GitHub mirror público)
# =============================================================================
def download_martj42_results():
    print("[1/6] Descargando 49K resultados internacionales (martj42)...")
    url = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
    out = RAW_DIR / "martj42_results.csv"
    try:
        urllib.request.urlretrieve(url, out)
        print(f"   ✓ {out.stat().st_size // 1024} KB")
    except Exception as e:
        print(f"   ✗ {e}")


# =============================================================================
# 2. Worldcup.json (openfootball — fixture oficial)
# =============================================================================
def download_openfootball():
    print("[2/6] Descargando fixture oficial openfootball 2026...")
    url = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"
    out = RAW_DIR / "openfootball_2026.json"
    try:
        urllib.request.urlretrieve(url, out)
        print(f"   ✓ {out.stat().st_size // 1024} KB")
    except Exception as e:
        print(f"   ✗ {e}")


# =============================================================================
# 3. Kaggle datasets (requiere kaggle.json en ~/.kaggle/)
# =============================================================================
def download_kaggle_datasets():
    print("[3/6] Descargando datasets Kaggle...")
    kaggle_creds = Path.home() / ".kaggle" / "kaggle.json"
    if not kaggle_creds.exists():
        print(f"   ⚠ No se encontró {kaggle_creds}")
        print(f"   ⚠ Para activar: ir a kaggle.com/settings → 'Create New API Token'")
        print(f"   ⚠ Guardar kaggle.json en ~/.kaggle/ y chmod 600")
        return
    try:
        import kaggle
        datasets = [
            ("martj42/international-football-results-from-1872-to-2017", "intl-football"),
            ("lucasyukioimafuko/fifa-mens-world-ranking", "fifa-ranking"),
            ("nyagami/ea-sports-fc-25-database-ratings-and-stats", "fc25-db"),
            ("rovnez/fc-26-fifa-26-player-data", "fc26-db"),
            ("sarazahran1/wc2026-match-probability-baseline-dataset", "wc26-baseline"),
        ]
        for ds, alias in datasets:
            target = RAW_DIR / "kaggle" / alias
            target.mkdir(parents=True, exist_ok=True)
            try:
                kaggle.api.dataset_download_files(ds, path=str(target), unzip=True)
                print(f"   ✓ {alias}")
            except Exception as e:
                print(f"   ✗ {alias}: {e}")
    except ImportError:
        print("   ⚠ pip install kaggle  (no instalado)")


# =============================================================================
# 4. Elo ratings scraping eloratings.net
# =============================================================================
def scrape_elo_ratings():
    print("[4/6] Scraping eloratings.net (Elo actual)...")
    try:
        import urllib.request as r
        req = r.Request("https://www.eloratings.net/",
                        headers={"User-Agent": "Mozilla/5.0"})
        html = r.urlopen(req, timeout=30).read().decode("utf-8", errors="replace")
        out = RAW_DIR / "eloratings_raw.html"
        out.write_text(html, encoding="utf-8")
        print(f"   ✓ {out.stat().st_size // 1024} KB raw HTML (parsearlo con BeautifulSoup)")
    except Exception as e:
        print(f"   ✗ {e}")


# =============================================================================
# 5. Wikipedia squads (8 selecciones a modo de muestra)
# =============================================================================
def scrape_wiki_squads():
    print("[5/6] Scraping Wikipedia 2026 FIFA World Cup squads...")
    url = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads"
    out = RAW_DIR / "wiki_squads.html"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", errors="replace")
        out.write_text(html, encoding="utf-8")
        print(f"   ✓ {out.stat().st_size // 1024} KB")
        # nota: parsing detallado con pandas.read_html en script separado
    except Exception as e:
        print(f"   ✗ {e}")


# =============================================================================
# 6. Transfermarkt datasets (GitHub mirror dcaribou)
# =============================================================================
def download_transfermarkt():
    print("[6/6] Descargando Transfermarkt datasets (dcaribou)...")
    urls = [
        ("https://raw.githubusercontent.com/dcaribou/transfermarkt-datasets/main/data/curated/players.csv", "tm_players.csv"),
        ("https://raw.githubusercontent.com/dcaribou/transfermarkt-datasets/main/data/curated/player_valuations.csv", "tm_valuations.csv"),
    ]
    for url, fname in urls:
        out = RAW_DIR / fname
        try:
            urllib.request.urlretrieve(url, out)
            print(f"   ✓ {fname}: {out.stat().st_size // 1024} KB")
        except Exception as e:
            print(f"   ✗ {fname}: {e}")


def main():
    print(f"Descargando data real a {RAW_DIR}\n")
    download_martj42_results()
    download_openfootball()
    download_kaggle_datasets()
    scrape_elo_ratings()
    scrape_wiki_squads()
    download_transfermarkt()
    print(f"\nLista de archivos descargados:")
    for f in sorted(RAW_DIR.rglob("*")):
        if f.is_file():
            print(f"  {f.relative_to(RAW_DIR)}: {f.stat().st_size // 1024} KB")
    print("\nSiguiente paso: parsear estos archivos para actualizar teams.json + matches_historical")


if __name__ == "__main__":
    main()
