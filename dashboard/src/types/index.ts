export enum RiskLevel {
  Green = 0,
  Yellow = 1,
  Red = 2,
}

export interface RiskEvent {
  id: string;
  tenantId: string;
  siteId: string;
  cameraId: string;
  zoneId: string;
  timestamp: string;
  riskScore: number;
  riskLevel: RiskLevel;
  suggestedActions: string[];
  acknowledged: boolean;
}

export interface Telemetry {
  tenantId: string;
  siteId: string;
  cameraId: string;
  zoneId: string;
  timestamp: string;
  density: number;
  avgSpeed: number;
  speedVariance: number;
  flowEntropy: number;
  alignment: number;
  bottleneckIndex: number;
}

export interface Zone {
  id: string;
  tenantId: string;
  siteId: string;
  zoneId: string;
  name: string;
  description?: string;
  cameraId?: string;
  polygon?: PolygonPoint[];
  bottleneckPoints?: BottleneckPoint[];
  maxCapacity: number;
  yellowThreshold: number;
  redThreshold: number;
  cameraIds: string[];
  isActive: boolean;
  createdAt: string;
  updatedAt?: string;
}

export interface PolygonPoint {
  x: number;
  y: number;
}

export interface BottleneckPoint {
  x: number;
  y: number;
  name: string;
}

// Source types for video upload and camera integration
export enum SourceType {
  Video = 0,
  Camera = 1,
}

export enum SourceStatus {
  Pending = 0,
  Processing = 1,
  Completed = 2,
  Error = 3,
  Connected = 4,
  Disconnected = 5,
}

export interface Source {
  id: string;
  tenantId: string;
  siteId: string;
  type: SourceType;
  name: string;
  url: string;
  status: SourceStatus;
  progress: number;
  zoneId: string;
  errorMessage?: string;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
}

export interface SourceProgress {
  sourceId: string;
  status: SourceStatus;
  progress: number;
  message?: string;
}
