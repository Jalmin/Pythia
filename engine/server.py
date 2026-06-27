"""PYTHIA oracle API — Osiris world data in, future predictions out."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .config import CONFIG
from .state import STATE

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("pythia.server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from .loop import LOOP
    from .pipeline import run_prediction
    LOOP.start()
    log.info("PYTHIA oracle up | %s", CONFIG.summary())

    async def _boot():
        from .runtime import intake
        # wait for Osiris to be reachable, then give its routes a moment to compile
        for _ in range(20):
            if await intake.health():
                break
            await asyncio.sleep(2)
        await asyncio.sleep(4)
        await run_prediction(trigger="boot")

    asyncio.create_task(_boot())
    yield


app = FastAPI(title="PYTHIA Oracle", version="0.2.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "pythia-oracle", "config": CONFIG.summary()}


@app.get("/config")
async def config():
    return CONFIG.summary()


_links_cache: dict = {"ts": 0.0, "data": None}


@app.get("/links")
async def links():
    import time as _t
    now = _t.monotonic()
    if _links_cache["data"] and now - _links_cache["ts"] < 8:
        data = dict(_links_cache["data"])
    else:
        from .runtime import intake, oracle
        osiris_up, oracle_up = await asyncio.gather(intake.health(), oracle.health())
        data = {"engine": True, "osiris": bool(osiris_up), "oracle": bool(oracle_up)}
        _links_cache.update(ts=now, data=dict(data))
    from .runtime import oracle as _oracle
    data.update(model=_oracle.model, generating=STATE.generating,
                loop=STATE.loop_enabled, last_run_ms=STATE.last_run_ms,
                prediction_count=len(STATE.predictions))
    return data


@app.get("/models")
async def models():
    """Installed local models + the one currently in use."""
    from .runtime import oracle
    return {"models": await oracle.list_models(), "current": oracle.model}


@app.post("/model")
async def set_model(payload: dict = Body(...)):
    """Switch the oracle's model at runtime."""
    from .runtime import oracle
    name = (payload or {}).get("model", "").strip()
    if not name:
        raise HTTPException(400, "provide `model`")
    oracle.model = name
    STATE.publish("model", {"model": name})
    log.info("oracle model switched -> %s", name)
    return {"model": oracle.model}


@app.get("/predictions")
async def predictions():
    return {"predictions": [p.model_dump() for p in STATE.predictions],
            "world": STATE.world.model_dump() if STATE.world else None}


@app.post("/predict")
async def predict():
    """Run an oracle pass now (sense the world -> forecast)."""
    from .pipeline import run_prediction
    if STATE.generating:
        return {"status": "already running"}
    asyncio.create_task(run_prediction(trigger="manual"))
    return {"status": "started"}


@app.get("/world")
async def world():
    if not STATE.world:
        raise HTTPException(404, "no world brief yet — run /predict")
    return STATE.world.model_dump()


@app.get("/runs")
async def runs():
    return {"runs": [r.model_dump() for r in list(STATE.runs.values())[-20:]]}


@app.get("/state")
async def state():
    return STATE.snapshot()


@app.get("/state/stream")
async def stream():
    async def gen():
        q = STATE.subscribe()
        try:
            yield STATE.sse({"kind": "snapshot", "payload": STATE.snapshot()})
            while True:
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=15)
                    yield STATE.sse(msg)
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            STATE.unsubscribe(q)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/chat")
async def chat(payload: dict = Body(...)):
    """Ask the oracle anything — it sees every live source + current predictions."""
    from .runtime import intake, oracle
    from .world_state import build_brief
    msg = (payload or {}).get("message", "").strip()
    if not msg:
        raise HTTPException(400, "provide `message`")
    brief = STATE.world
    if brief is None:
        try:
            brief = build_brief(await intake.fetch(limit=150))
            STATE.set_world(brief)
        except Exception:  # noqa: BLE001
            brief = None
    answer = await oracle.chat(msg, brief, STATE.predictions, payload.get("history", []))
    return {"answer": answer}


@app.post("/loop")
async def loop(payload: dict = Body(default={})):
    STATE.set_loop(bool(payload.get("enabled", not STATE.loop_enabled)))
    return {"loop_enabled": STATE.loop_enabled}
