# eShopCo Latency API

Serverless endpoint for monitoring deployment latency metrics.

## API Usage

**Endpoint:** `POST /api/latency`

**Request:**
```json
{
  "regions": ["apac", "emea"],
  "latency_ms": 180
}
