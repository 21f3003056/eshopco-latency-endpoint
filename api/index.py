from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import os
import json

app = FastAPI()

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Load the dataset once when the app starts
# For Vercel, use absolute path or environment-aware path
def load_data():
    try:
        # Try multiple possible paths for the JSON file
        possible_paths = [
            "q-vercel-latency.json",  # Root directory
            "/var/task/q-vercel-latency.json",  # Vercel runtime path
            "./q-vercel-latency.json",  # Current directory
            "api/q-vercel-latency.json"  # Inside api folder
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                return pd.DataFrame(data)
        
        # If file not found, return empty DataFrame
        return pd.DataFrame()
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()

@app.get("/")
async def root():
    return {"message": "Vercel Latency Analytics API is running."}

@app.get("/api/")
async def get_latency_stats_get(regions: str = "", threshold_ms: int = 200):
    """GET endpoint for latency stats"""
    try:
        if df.empty:
            raise HTTPException(status_code=500, detail="Data not loaded")
        
        # Parse regions from query parameter
        regions_to_process = []
        if regions:
            regions_to_process = [r.strip() for r in regions.split(",")]
        
        results = []
        
        for region in regions_to_process:
            region_df = df[df["region"] == region]
            
            if not region_df.empty:
                avg_latency = round(region_df["latency_ms"].mean(), 2)
                p95_latency = round(np.percentile(region_df["latency_ms"], 95), 2)
                avg_uptime = round(region_df["uptime_pct"].mean(), 3)
                breaches = int(region_df[region_df["latency_ms"] > threshold_ms].shape[0])
                
                results.append({
                    "region": region,
                    "avg_latency": avg_latency,
                    "p95_latency": p95_latency,
                    "avg_uptime": avg_uptime,
                    "breaches": breaches,
                })
        
        return {"regions": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/api/")
async def get_latency_stats_post(request: Request):
    """POST endpoint for latency stats (original functionality)"""
    try:
        if df.empty:
            raise HTTPException(status_code=500, detail="Data not loaded")
            
        payload = await request.json()
        regions_to_process = payload.get("regions", [])
        threshold = payload.get("threshold_ms", 200)

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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "data_loaded": not df.empty,
        "total_records": len(df) if not df.empty else 0
    }
