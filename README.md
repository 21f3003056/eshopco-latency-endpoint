# eShopCo Latency API

Serverless endpoint for monitoring deployment latency metrics.

## API Usage

**Endpoint:** `POST /app/index`

**Request:**
```json
{
  "regions": ["apac", "emea"],
  "latency_ms": 180
}
