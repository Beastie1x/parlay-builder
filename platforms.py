from dataclasses import dataclass
import pandas as pd
import os, requests

@dataclass
class PlatformSpec:
    name: str
    max_legs: int
    notes: str = ""

class PlatformAdapter:
    def fetch_lines(self, sport: str) -> pd.DataFrame:
        raise NotImplementedError
    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        cols = ["player","team","market","line","odds_over","odds_under","game_id","start_time","sport"]
        for c in cols:
            if c not in df.columns:
                df[c] = None
        return df[cols]

class UnderdogAdapter(PlatformAdapter):
    spec = PlatformSpec("underdog", max_legs=20, notes="Pick'em O/U props")
    def fetch_lines(self, sport: str) -> pd.DataFrame:
        sess = requests.Session()
        sess.headers.update({"User-Agent":"ParlayBuilder/1.0"})
        urls = [
            "https://api.underdogfantasy.com/v4/over_under_lines",
            "https://api.underdogfantasy.com/beta/over_under_lines",
        ]
        data=None
        for u in urls:
            try:
                r = sess.get(u, timeout=20)
                if r.ok and "application/json" in r.headers.get("content-type",""):
                    data=r.json(); break
            except: pass
        if data is None and os.getenv("UNDERDOG_COOKIE"):
            sess.headers.update({"Cookie": os.getenv("UNDERDOG_COOKIE")})
            try:
                r = sess.get(urls[0], timeout=20); r.raise_for_status(); data=r.json()
            except: pass
        if data is None:
            return pd.DataFrame(columns=["player","team","market","line","odds_over","odds_under","game_id","start_time","sport"])
        rows=[]
        def norm(m): return (m or "").lower().replace(" ","_")
        for item in data:
            try:
                player = item.get("player_name") or item.get("over_under",{}).get("player",{}).get("name")
                team = item.get("team_abbr") or item.get("over_under",{}).get("team_abbr")
                market = norm(item.get("stat_name") or item.get("over_under",{}).get("stat_name",""))
                line = float(item.get("line",0.0))
                over = int(item.get("over_odds",-120)); under=int(item.get("under_odds",-120))
                gid = str(item.get("game_id") or item.get("over_under",{}).get("game_id",""))
                ts = item.get("start_time") or item.get("over_under",{}).get("starts_at")
                rows.append({"player":player,"team":team,"market":market,"line":line,
                             "odds_over":over,"odds_under":under,"game_id":gid,"start_time":ts,"sport":sport})
            except: pass
        return self.normalize(pd.DataFrame(rows))

class PrizePicksAdapter(PlatformAdapter):
    spec = PlatformSpec("prizepicks", max_legs=6, notes="Upload CSV or set PRIZEPICKS_COOKIE")
    def fetch_lines(self, sport: str) -> pd.DataFrame:
        return pd.DataFrame(columns=["player","team","market","line","odds_over","odds_under","game_id","start_time","sport"])

class ChalkboardAdapter(PlatformAdapter):
    spec = PlatformSpec("chalkboard", max_legs=12, notes="Upload CSV from your source")
    def fetch_lines(self, sport: str) -> pd.DataFrame:
        return pd.DataFrame(columns=["player","team","market","line","odds_over","odds_under","game_id","start_time","sport"])

class KalshiAdapter(PlatformAdapter):
    spec = PlatformSpec("kalshi", max_legs=8, notes="Binary markets; upload CSV")
    def fetch_lines(self, sport: str) -> pd.DataFrame:
        return pd.DataFrame(columns=["player","team","market","line","odds_over","odds_under","game_id","start_time","sport"])

ADAPTERS = {
    "underdog": UnderdogAdapter,
    "prizepicks": PrizePicksAdapter,
    "chalkboard": ChalkboardAdapter,
    "kalshi": KalshiAdapter,
}
def get_adapter(platform: str) -> PlatformAdapter:
    key = platform.lower()
    if key not in ADAPTERS: raise ValueError(f"Unsupported platform: {platform}")
    return ADAPTERS[key]()
