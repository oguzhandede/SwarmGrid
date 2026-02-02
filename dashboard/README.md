# SwarmGrid Dashboard

Real-time monitoring interface for SwarmGrid. Built with Next.js 14, it provides operators with live visualization of crowd density, risk levels, and alerts.

## Features

- ✅ Real-time zone heatmaps
- ✅ Live risk gauge and trend charts
- ✅ Alert center with acknowledgment
- ✅ Live MJPEG video stream overlay
- ✅ Zone configuration and management
- ✅ Responsive design for all devices

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **UI:** React 18, Tailwind CSS
- **Language:** TypeScript
- **Charts:** Recharts
- **Real-time:** SignalR

## Requirements

- Node.js 20+
- npm, yarn, or pnpm

## Quick Start

### Using Docker (Recommended)

```bash
# From repository root
docker-compose up -d dashboard
```

### Local Development

```bash
cd dashboard

# Install dependencies
npm install

# Start development server
npm run dev
```

Open http://localhost:3000 in your browser.

## Configuration

Create a `.env.local` file:

```env
# Core Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:5000

# Edge Agent stream URL
NEXT_PUBLIC_EDGE_AGENT_URL=http://localhost:8000

# Default site to display
NEXT_PUBLIC_DEFAULT_SITE_ID=site-01
```

## Project Structure

```
src/
├── app/           # Next.js App Router pages
│   ├── zones/     # Zone management
│   └── sources/   # Source configuration
├── components/    # Reusable React components
│   ├── ZoneHeatmap.tsx
│   ├── RiskTimeline.tsx
│   └── ...
├── lib/           # API and SignalR utilities
└── types/         # TypeScript type definitions
```

## Build for Production

```bash
npm run build
npm start
```

## Development

### Linting

```bash
npm run lint
```

### Type Checking

```bash
npm run type-check
```
