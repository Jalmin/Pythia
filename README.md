# PYTHIA

**A world-watching prediction oracle.** PYTHIA reads the live globe through [Osiris](https://github.com/simplifaisoul/osiris)'s real-time feeds, hands a digest to a **local LLM**, and forecasts what happens next — across the next **24 hours, week, month, and year**. No markets, no cloud, no API keys, no cost. It runs entirely on your machine.

```
OSIRIS :3000 ──live world feeds──▶ PYTHIA ENGINE :8088 ──world brief──▶ LOCAL LLM (Ollama :11434)
 (the eyes)   news · conflict · weather · seismic · cyber ·               (the oracle)
              infrastructure · Polymarket crowd odds
 UI ◀───── predictions (24h / week / month / year) · chat · windows ─────◀
```

> Built on the shoulders of [Osiris](https://github.com/simplifaisoul/osiris) (live globe + feeds), [MiroFish](https://github.com/666ghj/MiroFish) (the prediction-engine idea + model config), and [Ollama](https://ollama.com) (local LLM). MIT licensed.

## What it does
- **Senses** the world — pulls every Osiris feed (news, GDELT, conflict, **NWS storm/flood polygon zones**, EONET weather, wildfire, seismic, cyber, infrastructure, country-risk) plus **Polymarket** crowd probabilities, into one brief.
- **Thinks** — a local model (whatever Ollama has; switchable in the UI) forecasts concrete future events per time-horizon, each with a probability, reasoning, and location.
- **Shows** — a predictions deck grouped by horizon; **click a prediction to fly the globe to it**.
- **Chat** — ask the oracle anything; it sees *every* live source + its own forecasts.
- **Windows** — open news feeds (and chat) as **movable, resizable, borderless windows**; keep the globe in the middle and watch the world go on.
- **Globe spin** — manual rotate (adjustable speed) or *smart-spin* that snaps to live events.

## Repo layout
- `engine/` — the PYTHIA oracle (Python / FastAPI). The core, 100% original.
  - `osiris_intake.py` (feeds → events), `world_state.py` (the brief), `oracle.py` (local-LLM forecaster + chat), `pipeline.py`, `loop.py`, `server.py`.
- `integrations/osiris/` — the overlay applied to an Osiris checkout (components, API routes, and `INSTALL.md`).
- `run-all.sh`, `PYTHIA.app`, `PYTHIA.command` — one-tap launchers.

## Requirements
- [Ollama](https://ollama.com) running with a chat model pulled (e.g. `ollama pull llama3.1`).
- An [Osiris](https://github.com/simplifaisoul/osiris) checkout with the overlay applied (see `integrations/osiris/INSTALL.md`).
- Python 3.11+ with [uv](https://docs.astral.sh/uv/).

## Run
```bash
cp .env.example .env          # defaults work out of the box
./run-all.sh                  # starts Osiris (:3000) + the engine (:8088), opens the dashboard
```
…or double-click **`PYTHIA.app`** (macOS). Then hit the **Eye** icon for the oracle deck and press **PREDICT**.

Run just the engine: `uv run python -m engine.run`.

## Config (`.env`)
Horizons, predictions-per-horizon, refresh cadence, and the model are all configurable. Leave the `LLM_*` lines blank to reuse whatever model MiroFish/Ollama is set to, or set `LLM_MODEL=llama3.1`.

## API (engine, :8088)
`/predict` · `/predictions` · `/chat` · `/world` · `/state` (+`/state/stream` SSE) · `/models` · `/model` · `/loop` · `/links` · `/health`

## Notes
- **No secrets in this repo.** It needs no API keys — the oracle is a local model.
- Osiris is upstream and not bundled here; clone it and apply the overlay. PYTHIA does not redistribute Osiris's or MiroFish's code.

## License
MIT — see [LICENSE](LICENSE).
