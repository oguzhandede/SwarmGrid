# SwarmGrid Core Backend

The Core Backend is the central API and risk engine for SwarmGrid. Built with .NET 8, it ingests telemetry from Edge Agents, calculates risk scores, persists events, and broadcasts real-time updates to dashboards.

## Features

- ✅ REST API for telemetry ingestion and risk queries
- ✅ Real-time risk scoring with configurable thresholds
- ✅ SignalR hub for live dashboard updates
- ✅ Time-series storage with TimescaleDB
- ✅ State caching and trend analysis with Redis
- ✅ Multi-tenant architecture

## Requirements

- .NET 8 SDK
- PostgreSQL 16+ with TimescaleDB extension
- Redis 7+

## Quick Start

### Using Docker (Recommended)

```bash
# From repository root
docker-compose up -d core-backend postgres redis
```

### Local Development

```bash
cd core-backend

# Restore dependencies
dotnet restore

# Run the API
dotnet run --project src/SwarmGrid.Api
```

## Configuration

### Environment Variables

| Variable                        | Description                  | Default          |
| ------------------------------- | ---------------------------- | ---------------- |
| `ConnectionStrings__PostgreSQL` | PostgreSQL connection string | -                |
| `ConnectionStrings__Redis`      | Redis connection string      | `localhost:6379` |
| `ASPNETCORE_ENVIRONMENT`        | Runtime environment          | `Development`    |

### appsettings.json

```json
{
  "ConnectionStrings": {
    "PostgreSQL": "Host=localhost;Database=swarmgrid;Username=swarmgrid;Password=swarmgrid",
    "Redis": "localhost:6379"
  }
}
```

## API Endpoints

| Endpoint                     | Method    | Description                       |
| ---------------------------- | --------- | --------------------------------- |
| `/health`                    | GET       | Health check                      |
| `/api/telemetry/ingest`      | POST      | Ingest telemetry from Edge Agents |
| `/api/risk/current/{zoneId}` | GET       | Current risk for a zone           |
| `/api/risk/events/{siteId}`  | GET       | Recent risk events                |
| `/hubs/risk`                 | WebSocket | SignalR hub for real-time updates |

See [API Documentation](../docs/API.md) for full reference.

## Project Structure

```
src/
├── SwarmGrid.Api/           # REST API and SignalR hub
├── SwarmGrid.Application/   # Business logic and risk engine
├── SwarmGrid.Domain/        # Entities and enums
└── SwarmGrid.Infrastructure/# Data access and caching
```

## Testing

```bash
cd core-backend
dotnet test
```

## Health Check

The API exposes a health endpoint:

```bash
curl http://localhost:5000/health
```
