from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import threading

from ..config import load_config
from ..pipeline import PipelineManager

app = FastAPI(title="Silhouette Booth API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton pipeline
_cfg = load_config('interactive_video_booth/app/config.yaml')
_pipeline = PipelineManager(_cfg)

_jobs = {}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/capture")
async def capture(body: dict):
    duration = int(body.get("duration", _cfg.app.record_duration_s))
    # Fire countdown + record in a thread so API returns quickly
    def run():
        res = _pipeline.countdown_and_record(duration_s=duration)
        _jobs[res.get("job_id")] = res
    t = threading.Thread(target=run, daemon=True)
    t.start()
    return {"status": "started"}


@app.get("/status/{job_id}")
async def status(job_id: str):
    res = _jobs.get(job_id)
    if not res:
        raise HTTPException(status_code=404, detail="job_id not found")
    return JSONResponse(content=res)


@app.get("/list-outputs")
async def list_outputs():
    import os, json, glob
    out_dir = _cfg.app.watched_folder
    files = []
    for meta in glob.glob(os.path.join(out_dir, '*.json')):
        try:
            with open(meta, 'r', encoding='utf-8') as f:
                data = json.load(f)
            files.append(data)
        except Exception:
            continue
    return {"files": sorted(files, key=lambda x: x.get('timestamp_utc', ''), reverse=True)}
