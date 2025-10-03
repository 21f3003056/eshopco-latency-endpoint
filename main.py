from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json, numpy as np

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

with open("latency_data.json") as f:
    data = [json.loads("{" + rec.replace(", ", ", \"").replace(": ", "\": ") + "}") for rec in f.read().strip().split('\n')]

@app.post("/latency")
async def latency_metrics(request: Request):
    req = await request.json()
    target_regions = req["regions"]
    latency_threshold = req["latency_ms"]
    results = {}

    for region in target_regions:
        region_records = [r for r in data if r["region"] == region]
        latency_list = [r["latencyms"] for r in region_records]
        uptime_list = [r["uptimepct"] for r in region_records]
        breaches = sum(l > latency_threshold for l in latency_list)
        results[region] = {
            "avg_latency": float(np.mean(latency_list)) if latency_list else None,
            "p95_latency": float(np.percentile(latency_list, 95)) if latency_list else None,
            "avg_uptime": float(np.mean(uptime_list)) if uptime_list else None,
            "breaches": breaches
        }
    return results
