'use client';

import { useEffect } from 'react';
import { RiskLevel } from '@/types';
import { useSignalR } from '@/lib/useSignalR';
import ZoneHeatmap from '@/components/ZoneHeatmap';
import RiskTimeline from '@/components/RiskTimeline';

// Configuration from environment variables
const DEFAULT_SITE_ID = process.env.NEXT_PUBLIC_DEFAULT_SITE_ID || 'site-01';

export default function Home() {
    const {
        connected,
        connecting,
        currentRisk,
        riskEvents,
        zoneRiskMap,
        error,
        subscribeToSite
    } = useSignalR(true);

    // Subscribe to configured site on connect
    useEffect(() => {
        if (connected) {
            subscribeToSite(DEFAULT_SITE_ID).catch(console.error);
        }
    }, [connected, subscribeToSite]);

    const getRiskColor = (level: RiskLevel) => {
        switch (level) {
            case RiskLevel.Red: return 'red';
            case RiskLevel.Yellow: return 'yellow';
            default: return 'green';
        }
    };

    const getConnectionStatus = () => {
        if (connecting) return { text: 'Bağlanıyor...', color: 'yellow' };
        if (error) return { text: error, color: 'red' };
        if (connected) return { text: 'Bağlı', color: 'green' };
        return { text: 'Bağlantı kesik', color: 'red' };
    };

    const status = getConnectionStatus();

    return (
        <main>
            <header className="header">
                <div className="logo">SwarmGrid</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <a href="/zones" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '14px' }}>
                        📐 Zone Yönetimi
                    </a>
                    <a href="/sources" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '14px' }}>
                        📹 Kaynak Yönetimi
                    </a>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span className={`status-indicator status-${status.color}`} />
                        <span>{status.text}</span>
                    </div>
                </div>
            </header>

            <div className="container">
                <div className="grid">
                    {/* Current Risk Card */}
                    <div className="card">
                        <div className="card-title">Güncel Risk Skoru</div>
                        <div className={`card-value risk-${currentRisk ? getRiskColor(currentRisk.riskLevel) : 'green'}`}>
                            {currentRisk ? `${(currentRisk.riskScore * 100).toFixed(1)}%` : '-'}
                        </div>
                        {currentRisk && (
                            <div style={{ marginTop: '12px', color: '#94a3b8' }}>
                                <span className={`status-indicator status-${getRiskColor(currentRisk.riskLevel)}`} />
                                {currentRisk.riskLevel === RiskLevel.Green && 'Normal'}
                                {currentRisk.riskLevel === RiskLevel.Yellow && 'Dikkat'}
                                {currentRisk.riskLevel === RiskLevel.Red && 'Kritik'}
                            </div>
                        )}
                    </div>

                    {/* Zone Info Card */}
                    <div className="card">
                        <div className="card-title">Aktif Zone</div>
                        <div className="card-value" style={{ fontSize: '24px' }}>
                            {currentRisk?.zoneId || '-'}
                        </div>
                        <div style={{ marginTop: '12px', color: '#94a3b8' }}>
                            Site: {currentRisk?.siteId || '-'}
                        </div>
                    </div>

                    {/* Connection Status Card */}
                    <div className="card">
                        <div className="card-title">Bağlantı Durumu</div>
                        <div className="card-value" style={{ fontSize: '24px' }}>
                            <span className={`status-indicator status-${status.color}`} />
                            {connecting ? 'Bağlanıyor' : connected ? 'Aktif' : 'Pasif'}
                        </div>
                        <div style={{ marginTop: '12px', color: '#94a3b8' }}>
                            Alınan event: {riskEvents.length}
                        </div>
                    </div>
                </div>

                {/* Zone Heatmap */}
                <div style={{ marginTop: '20px' }}>
                    <ZoneHeatmap
                        zoneRiskMap={zoneRiskMap}
                        onZoneClick={(zoneId) => console.log('Zone clicked:', zoneId)}
                    />
                </div>

                {/* Risk Timeline Chart */}
                <div style={{ marginTop: '20px' }}>
                    <RiskTimeline riskEvents={riskEvents} />
                </div>

                {/* Alerts Section */}
                <div className="card" style={{ marginTop: '20px' }}>
                    <div className="card-title">Son Alarmlar</div>
                    {riskEvents.length === 0 ? (
                        <p style={{ color: '#64748b', padding: '20px 0' }}>
                            {connected ? 'Henüz alarm yok. Telemetri verisi bekleniyor...' : 'Sunucuya bağlanılıyor...'}
                        </p>
                    ) : (
                        <ul className="alert-list">
                            {riskEvents.map((event) => (
                                <li key={event.id} className={`alert-item ${getRiskColor(event.riskLevel)}`}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                        <strong>{event.zoneId}</strong>
                                        <span>{new Date(event.timestamp).toLocaleTimeString('tr-TR')}</span>
                                    </div>
                                    <div style={{ marginTop: '4px', fontSize: '14px', color: '#94a3b8' }}>
                                        Risk: {(event.riskScore * 100).toFixed(1)}%
                                    </div>
                                    {event.suggestedActions.length > 0 && (
                                        <ul style={{ marginTop: '8px', paddingLeft: '16px' }}>
                                            {event.suggestedActions.map((action, i) => (
                                                <li key={i} style={{ fontSize: '13px', color: '#cbd5e1' }}>{action}</li>
                                            ))}
                                        </ul>
                                    )}
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </div>
        </main>
    );
}

