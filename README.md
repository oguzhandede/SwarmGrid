<p align="center">
  <h1 align="center">🐝 SwarmGrid</h1>
  <p align="center">
    <strong>Privacy-first crowd risk early warning platform</strong>
  </p>
  <p align="center">
    Turn existing CCTV into real-time risk signals — without storing video or tracking individuals
  </p>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://dotnet.microsoft.com/"><img src="https://img.shields.io/badge/.NET-8.0-512BD4" alt=".NET 8"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11+-3776AB" alt="Python 3.11+"></a>
  <a href="https://nextjs.org/"><img src="https://img.shields.io/badge/Next.js-14-000000" alt="Next.js 14"></a>
  <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Docker-Ready-2496ED" alt="Docker Ready"></a>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-documentation">Docs</a> •
  <a href="#-contributing">Contributing</a>
</p>

---

## 📌 Overview

SwarmGrid is an open-source crowd analytics platform that processes video streams on the edge, extracts anonymous movement features, calculates risk scores in a central backend, and delivers real-time alerts to operators.

**Key principle:** Raw video never leaves the edge device. Only anonymized telemetry (density, speed, flow patterns) is transmitted.

## ⚠️ Project Status

> **Alpha** — SwarmGrid is under active development. APIs and data formats may change between releases.

## ✨ Features

- **Privacy by design** — No face recognition, no identity tracking, no raw video storage
- **Edge processing** — Computer vision runs locally; only telemetry is transmitted
- **Real-time risk scoring** — Rolling trends, threshold-based alerts, suggested actions
- **Live dashboard** — Heatmaps, timelines, and risk gauges via SignalR
- **Multi-tenant architecture** — Support for multiple organizations, sites, and zones
- **Observable** — Built-in Prometheus metrics and Grafana dashboards

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐     ┌───────────┐
│ RTSP Camera │────▶│  Edge Agent     │────▶│ Core Backend │────▶│ Dashboard │
│             │     │  (Python + CV)  │     │ (.NET 8 API) │     │ (Next.js) │
└─────────────┘     └─────────────────┘     └──────┬───────┘     └───────────┘
                                                   │
                                    ┌──────────────┼──────────────┐
                                    ▼              ▼              ▼
                              TimescaleDB       Redis       Prometheus
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed data flow.

## 🚀 Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- RTSP camera or video source

### Installation

```bash
# Clone the repository
git clone https://github.com/oguzhandede/SwarmGrid.git
cd SwarmGrid

# Copy environment template
cp .env.example .env

# Configure your RTSP camera URL in .env
# RTSP_URL=rtsp://user:pass@camera-ip:554/stream

# Start all services
docker-compose up -d
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Dashboard | http://localhost:3002 | Main monitoring interface |
| API | http://localhost:5000 | REST API + SignalR hub |
| Edge Stream | http://localhost:8000/stream | Live MJPEG stream |
| Grafana | http://localhost:3001 | Metrics dashboards |
| Prometheus | http://localhost:9090 | Metrics collection |

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/ARCHITECTURE.md) | System design and data flow |
| [Deployment](docs/DEPLOYMENT.md) | Installation and configuration |
| [API Reference](docs/API.md) | REST endpoints and SignalR hub |
| [Edge Agent](edge-agent/README.md) | Camera integration and feature extraction |
| [Core Backend](core-backend/README.md) | Risk engine and persistence |
| [Dashboard](dashboard/README.md) | Web interface |

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Camera settings
RTSP_URL=rtsp://user:pass@camera-ip:554/stream
CAMERA_ID=cam-01
ZONE_ID=zone-01

# Backend connections (defaults work with Docker Compose)
ConnectionStrings__PostgreSQL=Host=postgres;Database=swarmgrid;...
ConnectionStrings__Redis=redis:6379
```

### Edge Agent

Edit `edge-agent/config/settings.yaml` for camera-specific settings like FPS, resolution, and feature extraction parameters.

## 🤝 Contributing

We welcome contributions! Please read:

- [Contributing Guide](CONTRIBUTING.md) — How to submit changes
- [Code of Conduct](CODE_OF_CONDUCT.md) — Community guidelines

### Development Setup

```bash
# Edge Agent (Python)
cd edge-agent
pip install -r requirements.txt
python src/main.py

# Core Backend (.NET)
cd core-backend
dotnet restore
dotnet run --project src/SwarmGrid.Api

# Dashboard (Next.js)
cd dashboard
npm install
npm run dev
```

## 🔒 Security

SwarmGrid is built with privacy as a core principle:

- No face recognition or biometric processing
- Raw video stays on the edge device
- Only anonymized telemetry is transmitted

Found a vulnerability? Please report it privately — see [SECURITY.md](SECURITY.md).

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgements

SwarmGrid is built on the shoulders of giants:

- [OpenCV](https://opencv.org/) — Computer vision
- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) — Object detection
- [SignalR](https://dotnet.microsoft.com/apps/aspnet/signalr) — Real-time communication
- [TimescaleDB](https://www.timescale.com/) — Time-series database
- [Next.js](https://nextjs.org/) — React framework

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/oguzhandede">Oguzhan Dede</a>
</p>
