import * as signalR from '@microsoft/signalr';
import { RiskEvent } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

let connection: signalR.HubConnection | null = null;

export async function connectToRiskHub(
  onRiskUpdate: (event: RiskEvent) => void,
  onConnected?: () => void,
  onDisconnected?: () => void
): Promise<signalR.HubConnection> {
  if (connection) {
    return connection;
  }

  connection = new signalR.HubConnectionBuilder()
    .withUrl(`${API_URL}/hubs/risk`)
    .withAutomaticReconnect()
    .configureLogging(signalR.LogLevel.Information)
    .build();

  connection.on('RiskUpdate', (event: RiskEvent) => {
    onRiskUpdate(event);
  });

  connection.onclose(() => {
    console.log('SignalR connection closed');
    onDisconnected?.();
  });

  connection.onreconnected(() => {
    console.log('SignalR reconnected');
    onConnected?.();
  });

  try {
    await connection.start();
    console.log('SignalR connected');
    onConnected?.();
  } catch (err) {
    console.error('SignalR connection error:', err);
    onDisconnected?.();
    throw err;
  }

  return connection;
}

export async function subscribeToZone(zoneId: string): Promise<void> {
  if (!connection) {
    throw new Error('Not connected to SignalR');
  }
  await connection.invoke('SubscribeToZone', zoneId);
}

export async function subscribeToSite(siteId: string): Promise<void> {
  if (!connection) {
    throw new Error('Not connected to SignalR');
  }
  await connection.invoke('SubscribeToSite', siteId);
}

export async function disconnect(): Promise<void> {
  if (connection) {
    await connection.stop();
    connection = null;
  }
}
