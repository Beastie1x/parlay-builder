import requests, pandas as pd
from io import BytesIO

NFLVERSE_PBP_URL = "https://github.com/nflverse/nflverse-data/releases/latest/download/pbp_{season}.csv.gz"

def fetch_pbp(season:int)->pd.DataFrame:
    url = NFLVERSE_PBP_URL.format(season=season)
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return pd.read_csv(BytesIO(r.content), compression="gzip", low_memory=False)
