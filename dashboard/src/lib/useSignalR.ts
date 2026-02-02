'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import * as signalR from '@microsoft/signalr';
import { RiskEvent } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
const MAX_EVENTS = 50;

export interface UseSignalRResult {
    connected: boolean;
    connecting: boolean;
    currentRisk: RiskEvent | null;
    riskEvents: RiskEvent[];
    zoneRiskMap: Map<string, RiskEvent>;
    error: string | null;
    subscribeToSite: (siteId: string) => Promise<void>;
    subscribeToZone: (zoneId: string) => Promise<void>;
}

export function useSignalR(autoConnect: boolean = true): UseSignalRResult {
    const [connected, setConnected] = useState(false);
    const [connecting, setConnecting] = useState(false);
    const [currentRisk, setCurrentRisk] = useState<RiskEvent | null>(null);
    const [riskEvents, setRiskEvents] = useState<RiskEvent[]>([]);
    const [zoneRiskMap, setZoneRiskMap] = useState<Map<string, RiskEvent>>(new Map());
    const [error, setError] = useState<string | null>(null);
    const connectionRef = useRef<signalR.HubConnection | null>(null);

    const handleRiskUpdate = useCallback((event: RiskEvent) => {
        console.log('Received risk update:', event);
        setCurrentRisk(event);
        setRiskEvents(prev => {
            const updated = [event, ...prev];
            return updated.slice(0, MAX_EVENTS);
        });
        // Update zone risk map for heatmap
        setZoneRiskMap(prev => {
            const updated = new Map(prev);
            updated.set(event.zoneId, event);
            return updated;
        });
    }, []);

    const connect = useCallback(async () => {
        if (connectionRef.current?.state === signalR.HubConnectionState.Connected) {
            return;
        }

        setConnecting(true);
        setError(null);

        try {
            const connection = new signalR.HubConnectionBuilder()
                .withUrl(`${API_URL}/hubs/risk`)
                .withAutomaticReconnect([0, 2000, 5000, 10000, 30000])
                .configureLogging(signalR.LogLevel.Information)
                .build();

            connection.on('RiskUpdate', handleRiskUpdate);

            connection.onclose((err) => {
                console.log('SignalR disconnected', err);
                setConnected(false);
                if (err) {
                    setError('Bağlantı kesildi');
                }
            });

            connection.onreconnecting((err) => {
                console.log('SignalR reconnecting...', err);
                setConnected(false);
                setConnecting(true);
            });

            connection.onreconnected((connectionId) => {
                console.log('SignalR reconnected:', connectionId);
                setConnected(true);
                setConnecting(false);
                setError(null);
            });

            await connection.start();
            connectionRef.current = connection;
            setConnected(true);
            setConnecting(false);
            console.log('SignalR connected successfully');
        } catch (err) {
            console.error('SignalR connection failed:', err);
            setError('Sunucuya bağlanılamadı');
            setConnected(false);
            setConnecting(false);
        }
    }, [handleRiskUpdate]);

    const subscribeToSite = useCallback(async (siteId: string) => {
        if (!connectionRef.current) {
            throw new Error('Not connected');
        }
        await connectionRef.current.invoke('SubscribeToSite', siteId);
        console.log('Subscribed to site:', siteId);
    }, []);

    const subscribeToZone = useCallback(async (zoneId: string) => {
        if (!connectionRef.current) {
            throw new Error('Not connected');
        }
        await connectionRef.current.invoke('SubscribeToZone', zoneId);
        console.log('Subscribed to zone:', zoneId);
    }, []);

    useEffect(() => {
        if (autoConnect) {
            connect();
        }

        return () => {
            if (connectionRef.current) {
                connectionRef.current.stop();
                connectionRef.current = null;
            }
        };
    }, [autoConnect, connect]);

    return {
        connected,
        connecting,
        currentRisk,
        riskEvents,
        zoneRiskMap,
        error,
        subscribeToSite,
        subscribeToZone,
    };
}
