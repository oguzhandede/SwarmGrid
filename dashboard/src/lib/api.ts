import { RiskEvent, Zone } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

export async function getCurrentRisk(zoneId: string): Promise<RiskEvent> {
  return fetchApi<RiskEvent>(`/api/risk/current/${zoneId}`);
}

export async function getRecentEvents(siteId: string, limit = 50): Promise<RiskEvent[]> {
  return fetchApi<RiskEvent[]>(`/api/risk/events/${siteId}?limit=${limit}`);
}

export async function acknowledgeEvent(eventId: string, userId: string, note?: string): Promise<void> {
  await fetchApi(`/api/risk/events/${eventId}/acknowledge`, {
    method: 'POST',
    body: JSON.stringify({ userId, note }),
  });
}

export async function getZones(siteId: string): Promise<Zone[]> {
  return fetchApi<Zone[]>(`/api/zones?siteId=${siteId}`);
}

export async function healthCheck(): Promise<{ status: string; timestamp: string }> {
  return fetchApi('/health');
}
