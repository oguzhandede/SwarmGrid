# SwarmGrid Edge Agent

The Edge Agent is the computer vision component of SwarmGrid. It connects to RTSP camera streams, extracts anonymized crowd features, and publishes telemetry to the Core Backend.

**Key principle:** Raw video never leaves this device. Only anonymized metrics are transmitted.

## Features

- ✅ RTSP stream ingestion with automatic reconnection
- ✅ Real-time person detection (YOLOv8)
- ✅ Feature extraction: density, speed, flow entropy, alignment, bottleneck index
- ✅ Telemetry batching with retry logic
- ✅ HTTP API for health checks and MJPEG streaming

## Requirements

- Python 3.11+
- RTSP camera or video source
- (Optional) CUDA-capable GPU for faster inference

## Quick Start

### Using Docker (Recommended)

```bash
# From repository root
docker-compose up -d edge-agent
```

### Local Development

```bash
cd edge-agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run the agent
python src/main.py
```

## Configuration

### Configuration File

Edit `config/settings.yaml`:

```yaml
rtsp_url: "rtsp://user:pass@camera-ip:554/stream"
backend_url: "http://localhost:5000"
tenant_id: "demo"
site_id: "site-01"
camera_id: "cam-01"
zone_id: "zone-01"
fps: 10
frame_width: 640
frame_height: 480

telemetry:
  send_interval_seconds: 1
  batch_size: 10

api:
  port: 8000
```

### Environment Variables

Environment variables override config file values:

| Variable      | Description              | Default                 |
| ------------- | ------------------------ | ----------------------- |
| `RTSP_URL`    | Camera stream URL        | -                       |
| `BACKEND_URL` | Core Backend API URL     | `http://localhost:5000` |
| `CAMERA_ID`   | Unique camera identifier | `cam-01`                |
| `ZONE_ID`     | Zone identifier          | `zone-01`               |
| `LOG_LEVEL`   | Logging level            | `INFO`                  |

## API Endpoints

| Endpoint           | Method | Description        |
| ------------------ | ------ | ------------------ |
| `/health`          | GET    | Health check       |
| `/stream`          | GET    | MJPEG video stream |
| `/stream/snapshot` | GET    | Single JPEG frame  |

Default port: `8000`

## Telemetry Format

The agent sends batched telemetry to the backend:

```json
[
  {
    "tenantId": "demo",
    "siteId": "site-01",
    "cameraId": "cam-01",
    "zoneId": "zone-01",
    "timestamp": "2024-01-30T12:00:00Z",
    "density": 0.45,
    "avgSpeed": 0.12,
    "speedVariance": 0.03,
    "flowEntropy": 0.8,
    "alignment": 0.6,
    "bottleneckIndex": 0.2
  }
]
```

## Testing

```bash
pytest tests/
```

## Troubleshooting

### Camera Connection Issues

1. Verify RTSP URL in VLC: `vlc rtsp://user:pass@camera-ip:554/stream`
2. Check network connectivity to camera
3. Review logs: `docker-compose logs -f edge-agent`

### High CPU Usage

- Reduce `fps` in settings
- Lower `frame_width` and `frame_height`
- Consider GPU acceleration with CUDA
