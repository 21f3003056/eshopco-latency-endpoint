from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import statistics

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

class LatencyRequest(BaseModel):
    regions: List[str]
    latency_ms: int

# Load telemetry data once at startup
with open('telemetry_data.json', 'r') as f:
    telemetry_data = json.load(f)

def calculate_percentile(data, percentile):
    if not data:
        return 0
    sorted_data = sorted(data)
    index = (len(sorted_data) - 1) * percentile / 100
    lower = int(index)
    upper = min(lower + 1, len(sorted_data) - 1)
    weight = index - lower
    return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight

@app.post("/")
async def get_latency_metrics(request: LatencyRequest):
    response = {}

    for region in request.regions:
        region_data = [item for item in telemetry_data if item.get("region") == region]
        if not region_data:
            response[region] = {
                "avg_latency": 0,
                "p95_latency": 0,
                "avg_uptime": 0,
                "breaches": 0
            }
            continue

        latencies = [item.get("latencyms", 0) for item in region_data]
        uptimes = [item.get("uptimepct", 0) for item in region_data]

        avg_latency = statistics.mean(latencies) if latencies else 0
        p95_latency = calculate_percentile(latencies, 95)
        avg_uptime = statistics.mean(uptimes) if uptimes else 0
        breaches = sum(1 for latency in latencies if latency > request.latency_ms)

        response[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 2),
            "breaches": breaches
        }

    return response

@app.get("/")
async def root():
    return {"message": "eShopCo Latency API"}
