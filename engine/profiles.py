"""Prediction profiles — segment forecasts by usage without mixing sources.

The engine ingests every Osiris feed once (shared intake), but each *profile*
only ever sees the events of its allowed domains, predicts separately, and keeps
an isolated history (ledger + calibration). Hard guarantee: a policy signal can
never influence a finance forecast, because the two never share a brief.

Three domains group the raw feed sources/categories:
  - finance : markets, crypto, futures, prediction markets, economics
  - presse  : geopolitics, conflict, news, risk, health, unrest, ...
  - météo   : earthquakes, weather, fires, storms, floods, space weather, ...

`domain_for(source, category)` resolves any WorldEvent to exactly one domain.
`PROFILES` lists the active profiles; météo is deliberately in no profile, so
weather events are ingested (for context) but never predicted — a wanted
refocus. (politique/affaires-publiques arrives in sprint 2 via the MANTU
adapter, once there is a non-empty source for it.)
"""
from __future__ import annotations

# Maps each Osiris `source` (from FEEDS) AND each `category` to a domain.
# Keyed on BOTH because `_to_event` may override an event's category from the
# upstream payload; `domain_for` checks `source` first (always reliable, fixed
# by FEEDS) then falls back to `category`, then to the "presse" default.
SOURCE_DOMAIN: dict[str, str] = {
    # ── finance ──────────────────────────────────────────────────────────
    # market / prediction-market / futures sources
    "markets": "finance",
    "crypto": "finance",
    "futures": "finance",
    "polymarket": "finance",
    "manifold": "finance",
    # FMP paid finance feeds
    "fmp-econ": "finance",
    "fmp-earnings": "finance",
    "fmp-news": "finance",
    # economics (World Bank family)
    "worldbank": "finance",
    "wb-gdp": "finance",
    "wb-unemployment": "finance",
    "wb-poverty": "finance",
    # finance-flavoured categories
    "market-odds": "finance",
    "economy": "finance",

    # ── presse (geopolitics / news / society) ────────────────────────────
    "gdelt": "presse",
    "conflicts": "presse",
    "news": "presse",
    "risk": "presse",              # country-risk
    "frontlines": "presse",
    "wikipedia": "presse",         # wiki-attention
    "unhcr": "presse",             # displacement
    "unrest": "presse",
    "ooni": "presse",              # censorship
    "cyber": "presse",
    "infra": "presse",             # infrastructure
    "ioda": "presse",              # internet outages
    "who": "presse",               # health-outbreaks
    "hungermap": "presse",         # food-security
    "brief-matinal": "presse",     # local-news lab scraper
    "enriched-news": "presse",     # full-text enrichment
    # presse-flavoured categories
    "geopolitical": "presse",
    "conflict": "presse",
    "instability": "presse",
    "infrastructure": "presse",
    "attention": "presse",
    "outage": "presse",
    "displacement": "presse",
    "censorship": "presse",
    "health": "presse",
    "food": "presse",

    # ── météo (natural hazards / physical earth) ─────────────────────────
    "usgs": "météo",               # earthquakes
    "eonet": "météo",              # weather
    "firms": "météo",              # fires
    "openaq": "météo",             # air-quality
    "gdacs": "météo",              # disaster alerts
    "nhc": "météo",                # hurricanes
    "glofas": "météo",             # flood-outlook
    "swpc": "météo",               # space-weather
    # météo-flavoured categories
    "seismic": "météo",
    "weather": "météo",
    "wildfire": "météo",
    "air-quality": "météo",
    "disaster": "météo",
    "hurricane": "météo",
    "flood-outlook": "météo",
    "space-weather": "météo",
}

DEFAULT_DOMAIN = "presse"


def domain_for(source: str, category: str = "") -> str:
    """Resolve a (source, category) pair to its domain.

    `source` wins (it is fixed by FEEDS and never rewritten), `category` is a
    fallback for events whose source isn't explicitly mapped. Anything unknown
    is treated as "presse" — the safest bucket for an unclassified news-like
    signal, and it can never leak into a finance forecast.
    """
    if source in SOURCE_DOMAIN:
        return SOURCE_DOMAIN[source]
    if category in SOURCE_DOMAIN:
        return SOURCE_DOMAIN[category]
    return DEFAULT_DOMAIN


# Active prediction profiles. Each profile only ever sees events whose domain is
# in its `domains` set. météo is in NO profile on purpose (weather stays as
# context, not as a forecast target). No affaires-publiques profile yet — it
# would be empty without the MANTU adapter (sprint 2).
PROFILES: list[dict] = [
    {"name": "finance", "domains": {"finance"}},
    {"name": "newsletter", "domains": {"presse"}},
]
