# API Reference

SwarmGrid exposes a REST API for data ingestion and queries, plus a SignalR hub for real-time updates.

**Base URL:** `http://localhost:5000`

## Authentication

> **Note:** Authentication is not yet implemented. This is planned for a future release.

## REST Endpoints

### Health Check

#### `GET /health`

Returns the health status of the API.

**Response:** `200 OK`

```json
{
  "status": "Healthy"
}
```

---

### Telemetry

#### `POST /api/telemetry/ingest`

Ingests telemetry data from Edge Agents. Accepts an array of telemetry objects.

**Request Body:**

```json
[
  {
    "tenantId": "demo",
    "siteId": "site-01",
    "cameraId": "cam-01",
    "zoneId": "zone-01",
    "timestamp": "2024-01-30T10:00:00Z",
    "density": 0.5,
    "avgSpeed": 0.12,
    "speedVariance": 0.03,
    "flowEntropy": 0.8,
    "alignment": 0.6,
    "bottleneckIndex": 0.2
  }
]
```

**Response:** `200 OK`

```json
{
  "processed": 1,
  "riskEvents": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "tenantId": "demo",
      "siteId": "site-01",
      "cameraId": "cam-01",
      "zoneId": "zone-01",
      "createdAt": "2024-01-30T10:00:00Z",
      "riskScore": 0.42,
      "riskLevel": "Green",
      "suggestedActions": [],
      "acknowledged": false
    }
  ]
}
```

**Telemetry Fields:**

| Field             | Type        | Description              |
| ----------------- | ----------- | ------------------------ |
| `tenantId`        | string      | Organization identifier  |
| `siteId`          | string      | Site/location identifier |
| `cameraId`        | string      | Camera identifier        |
| `zoneId`          | string      | Zone identifier          |
| `timestamp`       | ISO 8601    | Time of measurement      |
| `density`         | float (0-1) | Crowd density ratio      |
| `avgSpeed`        | float       | Average movement speed   |
| `speedVariance`   | float       | Speed variance           |
| `flowEntropy`     | float (0-1) | Movement disorder        |
| `alignment`       | float (0-1) | Movement alignment       |
| `bottleneckIndex` | float (0-1) | Congestion indicator     |

---

### Risk

#### `GET /api/risk/current/{zoneId}`

Returns the current risk status of a specific zone.

**Parameters:**

| Parameter | Type   | Description     |
| --------- | ------ | --------------- |
| `zoneId`  | string | Zone identifier |

**Response:** `200 OK`

```json
{
  "zoneId": "zone-01",
  "riskScore": 0.42,
  "riskLevel": "Green",
  "density": 0.35,
  "trend": "stable",
  "lastUpdate": "2024-01-30T10:00:00Z"
}
```

**Risk Levels:**

| Level    | Score Range | Description       |
| -------- | ----------- | ----------------- |
| `Green`  | 0.0 - 0.39  | Normal conditions |
| `Yellow` | 0.4 - 0.69  | Elevated risk     |
| `Orange` | 0.7 - 0.89  | High risk         |
| `Red`    | 0.9 - 1.0   | Critical risk     |

---

#### `GET /api/risk/events/{siteId}`

Returns recent risk events for a site.

**Parameters:**

| Parameter | Type        | Description               |
| --------- | ----------- | ------------------------- |
| `siteId`  | string      | Site identifier           |
| `limit`   | int (query) | Max results (default: 50) |

**Response:** `200 OK`

```json
{
  "events": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "zoneId": "zone-01",
      "riskScore": 0.75,
      "riskLevel": "Orange",
      "createdAt": "2024-01-30T10:00:00Z",
      "acknowledged": false,
      "suggestedActions": ["Consider crowd management", "Monitor zone closely"]
    }
  ],
  "total": 1
}
```

---

#### `POST /api/risk/events/{eventId}/acknowledge`

Acknowledges a risk event.

**Parameters:**

| Parameter | Type | Description      |
| --------- | ---- | ---------------- |
| `eventId` | GUID | Event identifier |

**Request Body:**

```json
{
  "userId": "operator-01",
  "note": "Investigated on site - situation resolved"
}
```

**Response:** `200 OK`

```json
{
  "success": true,
  "acknowledgedAt": "2024-01-30T10:05:00Z"
}
```

---

## SignalR Hub

### Connection

**URL:** `/hubs/risk`

**Protocol:** SignalR (WebSocket with fallbacks)

### Client Events (Server → Client)

#### `RiskUpdate`

Sent when risk status changes for a subscribed zone.

```json
{
  "zoneId": "zone-01",
  "riskScore": 0.65,
  "riskLevel": "Yellow",
  "density": 0.45,
  "timestamp": "2024-01-30T10:00:00Z"
}
```

#### `Alert`

Sent when a new alert is generated.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "zoneId": "zone-01",
  "riskLevel": "Orange",
  "message": "Risk level elevated",
  "suggestedActions": ["Consider crowd management"],
  "timestamp": "2024-01-30T10:00:00Z"
}
```

### Server Methods (Client → Server)

#### `SubscribeToZone(zoneId: string)`

Subscribe to real-time updates for a specific zone.

#### `UnsubscribeFromZone(zoneId: string)`

Unsubscribe from updates for a specific zone.

### JavaScript Example

```javascript
import * as signalR from "@microsoft/signalr";

const connection = new signalR.HubConnectionBuilder()
  .withUrl("http://localhost:5000/hubs/risk")
  .withAutomaticReconnect()
  .build();

connection.on("RiskUpdate", (data) => {
  console.log("Risk update:", data);
});

connection.on("Alert", (data) => {
  console.log("New alert:", data);
});

await connection.start();
await connection.invoke("SubscribeToZone", "zone-01");
```

---

## Error Responses

All endpoints return standard error responses:

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {}
}
```

**Common Status Codes:**

| Code  | Description                        |
| ----- | ---------------------------------- |
| `400` | Bad Request - Invalid input        |
| `404` | Not Found - Resource doesn't exist |
| `500` | Internal Server Error              |
