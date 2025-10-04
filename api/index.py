from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import os
import json

app = FastAPI()

# Enable CORS for POST requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST"],
    allow_headers=["*"],
)

def load_data():
    possible_paths = [
        "q-vercel-latency.json",
        "/var/task/q-vercel-latency.json",
        "./q-vercel-latency.json",
        "api/q-vercel-latency.json"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
            return pd.DataFrame(data)
    return pd.DataFrame()

df = load_data()

@app.post("/api/")
async def get_latency_stats(request: Request):
    if df.empty:
        raise HTTPException(status_code=500, detail="Data not loaded")
    payload = await request.json()
    regions_to_process = payload.get("regions", [])
    threshold = payload.get("threshold_ms", 180)
    results = []
    for region in regions_to_process:
        region_df = df[df["region"] == region]
        if not region_df.empty:
            avg_latency = round(region_df["latency_ms"].mean(), 2)
            p95_latency = round(np.percentile(region_df["latency_ms"], 95), 2)
            avg_uptime = round(region_df["uptime_pct"].mean(), 3)
            breaches = int(region_df[region_df["latency_ms"] > threshold].shape[0])
            results.append({
                "region": region,
                "avg_latency": avg_latency,
                "p95_latency": p95_latency,
                "avg_uptime": avg_uptime,
                "breaches": breaches,
            })
    return {"regions": results}
