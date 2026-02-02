# SwarmGrid Architecture

This document describes the high-level architecture of SwarmGrid, a privacy-first crowd risk early warning platform.

## System Overview

SwarmGrid follows a hybrid edge-cloud architecture designed for privacy and low-latency processing.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SWARMGRID ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────┐    ┌─────────────────────────────────────────────────────┐   │
│   │  Camera  │    │                    EDGE DEVICE                       │   │
│   │  (RTSP)  │───▶│  ┌─────────────────────────────────────────────┐    │   │
│   └──────────┘    │  │              Edge Agent (Python)             │    │   │
│                   │  │  ┌─────────┐  ┌─────────┐  ┌─────────────┐  │    │   │
│                   │  │  │  RTSP   │  │  YOLO   │  │  Feature    │  │    │   │
│                   │  │  │ Decoder │─▶│Detector │─▶│ Extraction  │  │    │   │
│                   │  │  └─────────┘  └─────────┘  └──────┬──────┘  │    │   │
│                   │  └───────────────────────────────────┼─────────┘    │   │
│                   │              MJPEG Stream ◄──────────┤               │   │
│                   └─────────────────────────────────────┼───────────────┘   │
│                                    Telemetry (HTTP)     │                    │
│                                         │               │                    │
│   ┌─────────────────────────────────────▼───────────────┴───────────────┐   │
│   │                        BACKEND (Cloud/On-Prem)                       │   │
│   │                                                                      │   │
│   │  ┌────────────────────────────────────────────────────────────────┐ │   │
│   │  │                    Core Backend (.NET 8)                        │ │   │
│   │  │  ┌──────────┐  ┌─────────────┐  ┌───────────┐  ┌────────────┐ │ │   │
│   │  │  │Telemetry │  │    Risk     │  │  Alert    │  │  SignalR   │ │ │   │
│   │  │  │  Ingest  │─▶│   Engine    │─▶│ Generator │─▶│    Hub     │ │ │   │
│   │  │  └──────────┘  └──────┬──────┘  └───────────┘  └─────┬──────┘ │ │   │
│   │  └───────────────────────┼──────────────────────────────┼────────┘ │   │
│   │                          │                              │          │   │
│   │         ┌────────────────┼────────────────┐             │          │   │
│   │         ▼                ▼                ▼             │          │   │
│   │  ┌────────────┐  ┌─────────────┐  ┌────────────┐       │          │   │
│   │  │TimescaleDB │  │    Redis    │  │ Prometheus │       │          │   │
│   │  │(PostgreSQL)│  │   (Cache)   │  │ (Metrics)  │       │          │   │
│   │  └────────────┘  └─────────────┘  └────────────┘       │          │   │
│   └─────────────────────────────────────────────────────────┼──────────┘   │
│                                                             │              │
│   ┌─────────────────────────────────────────────────────────▼──────────┐   │
│   │                       Dashboard (Next.js)                           │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │   │
│   │  │   Heatmap   │  │  Timeline   │  │   Alerts    │  │   Live    │ │   │
│   │  │    View     │  │   Charts    │  │   Center    │  │  Stream   │ │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Core Design Principles

1. **Privacy by design:** Raw video never leaves the edge device
2. **Edge intelligence:** Computer vision processing runs locally
3. **Proactive risk management:** Predict risk before incidents occur
4. **Multi-tenant ready:** Support multiple organizations, sites, and zones

## Components

### 1. Edge Agent (Python)

Runs on devices with access to RTSP cameras.

**Responsibilities:**

- Connect to RTSP streams with automatic reconnection
- Decode video frames
- Detect persons using YOLOv8
- Extract anonymous features (density, optical flow, entropy)
- Batch and transmit telemetry to Core Backend
- Serve local MJPEG stream for operators

**Key Libraries:**

- OpenCV for video processing
- Ultralytics YOLOv8 for detection
- FastAPI for local HTTP API

### 2. Core Backend (.NET 8)

The central risk engine, deployable on-premises or in the cloud.

**Responsibilities:**

- Receive telemetry via HTTP API
- Calculate risk scores using configurable algorithms
- Manage state and trends with Redis
- Persist events to TimescaleDB
- Broadcast real-time updates via SignalR

**Architecture:**

- Clean Architecture with domain-driven design
- CQRS pattern for read/write separation
- Repository pattern for data access

### 3. Dashboard (Next.js 14)

The operator interface for situational awareness.

**Responsibilities:**

- Visualize risk via heatmaps and timelines
- Display alerts with suggested actions
- Manage zones and video sources
- Show live video streams

## Data Flow

```
1. Ingestion:    Camera (RTSP) ─────▶ Edge Agent
2. Processing:   Edge Agent ─────────▶ Feature Extraction ─────▶ Telemetry JSON
3. Transport:    Edge Agent ─────────▶ HTTP POST ─────▶ Core Backend
4. Analysis:     Core Backend ───────▶ Risk Score ─────▶ Redis + TimescaleDB
5. Presentation: Core Backend ───────▶ SignalR ─────▶ Dashboard
```

## Multi-Tenant Model

```
Tenant (Organization)
└── Site (Physical Location)
    └── Zone (Monitored Area)
        └── Camera (Video Source)
```

## Technology Stack

| Component    | Technology           | Purpose                             |
| ------------ | -------------------- | ----------------------------------- |
| Edge Agent   | Python 3.11+         | Computer vision, feature extraction |
| Core Backend | .NET 8               | API, risk engine, real-time hub     |
| Dashboard    | Next.js 14           | Operator interface                  |
| Database     | TimescaleDB          | Time-series storage                 |
| Cache        | Redis                | State management, trends            |
| Metrics      | Prometheus + Grafana | Observability                       |

## Security Considerations

- No biometric data processing
- Raw video stays on edge devices
- Telemetry contains only anonymized metrics
- HTTPS for all network communication
- Role-based access control (future)
