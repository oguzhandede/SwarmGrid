'use client';

import { useState, useEffect } from 'react';
import { RiskEvent, RiskLevel } from '@/types';

interface ZoneMetricsPanelProps {
    zoneId: string;
    zoneName: string;
    currentRisk: RiskEvent | null;
    maxCapacity: number;
    connected: boolean;
    demoMode?: boolean;
}

export default function ZoneMetricsPanel({
    zoneId,
    zoneName,
    currentRisk,
    maxCapacity,
    connected,
    demoMode = true // Enable demo mode by default
}: ZoneMetricsPanelProps) {
    // Demo state - simulates real-time updates
    const [demoData, setDemoData] = useState({
        density: 0.62,
        riskLevel: RiskLevel.Yellow,
        timestamp: new Date()
    });

    // Simulate real-time updates in demo mode
    useEffect(() => {
        if (!demoMode || currentRisk) return;

        const interval = setInterval(() => {
            setDemoData(prev => {
                // Simulate fluctuating density between 0.4 and 0.85
                const newDensity = Math.max(0.4, Math.min(0.85,
                    prev.density + (Math.random() - 0.5) * 0.15
                ));

                // Determine risk level based on density
                let newRiskLevel = RiskLevel.Green;
                if (newDensity >= 0.75) newRiskLevel = RiskLevel.Red;
                else if (newDensity >= 0.50) newRiskLevel = RiskLevel.Yellow;

                return {
                    density: newDensity,
                    riskLevel: newRiskLevel,
                    timestamp: new Date()
                };
            });
        }, 2000); // Update every 2 seconds

        return () => clearInterval(interval);
    }, [demoMode, currentRisk]);

    // Use real data if available, otherwise use demo data
    const density = currentRisk?.riskScore ?? (demoMode ? demoData.density : 0);
    const riskLevel = currentRisk?.riskLevel ?? (demoMode ? demoData.riskLevel : RiskLevel.Green);
    const timestamp = currentRisk?.timestamp ? new Date(currentRisk.timestamp) : (demoMode ? demoData.timestamp : null);

    // Calculate estimated person count from density
    const estimatedPersonCount = Math.round(density * maxCapacity * 1.2);

    const getRiskLevelText = (level: RiskLevel) => {
        switch (level) {
            case RiskLevel.Red: return 'Kritik';
            case RiskLevel.Yellow: return 'Dikkat';
            default: return 'Normal';
        }
    };

    const getRiskLevelColor = (level: RiskLevel) => {
        switch (level) {
            case RiskLevel.Red: return '#ef4444';
            case RiskLevel.Yellow: return '#eab308';
            default: return '#22c55e';
        }
    };

    const getStatusIcon = () => {
        if (!connected) return '⚫';
        switch (riskLevel) {
            case RiskLevel.Red: return '🔴';
            case RiskLevel.Yellow: return '🟡';
            default: return '🟢';
        }
    };

    return (
        <div className="metrics-panel">
            <div className="metrics-header">
                <span className="metrics-title">📊 Canlı Metrikler</span>
                <span className={`connection-status ${connected ? 'connected' : 'disconnected'}`}>
                    {connected ? '● Bağlı' : '○ Bağlantı yok'}
                </span>
            </div>

            <div className="metrics-grid">
                {/* Risk Status */}
                <div className="metric-card risk-card" style={{ borderColor: getRiskLevelColor(riskLevel) }}>
                    <div className="metric-icon">{getStatusIcon()}</div>
                    <div className="metric-content">
                        <div className="metric-label">Risk Durumu</div>
                        <div className="metric-value" style={{ color: getRiskLevelColor(riskLevel) }}>
                            {getRiskLevelText(riskLevel)}
                        </div>
                    </div>
                </div>

                {/* Density */}
                <div className="metric-card">
                    <div className="metric-icon">👥</div>
                    <div className="metric-content">
                        <div className="metric-label">Yoğunluk</div>
                        <div className="metric-value">
                            {(density * 100).toFixed(0)}%
                        </div>
                        <div className="density-bar">
                            <div
                                className="density-fill"
                                style={{
                                    width: `${density * 100}%`,
                                    background: getRiskLevelColor(riskLevel)
                                }}
                            />
                        </div>
                    </div>
                </div>

                {/* Estimated Person Count */}
                <div className="metric-card">
                    <div className="metric-icon">🧑‍🤝‍🧑</div>
                    <div className="metric-content">
                        <div className="metric-label">Tahmini Kişi</div>
                        <div className="metric-value">
                            {estimatedPersonCount} <span className="metric-unit">/ {maxCapacity}</span>
                        </div>
                    </div>
                </div>

                {/* Last Update */}
                <div className="metric-card">
                    <div className="metric-icon">🕐</div>
                    <div className="metric-content">
                        <div className="metric-label">Son Güncelleme</div>
                        <div className="metric-value time">
                            {timestamp
                                ? timestamp.toLocaleTimeString('tr-TR')
                                : '--:--:--'
                            }
                        </div>
                    </div>
                </div>
            </div>

            {/* Suggested Actions */}
            {currentRisk && currentRisk.suggestedActions.length > 0 && (
                <div className="suggested-actions">
                    <div className="actions-header">⚡ Önerilen Aksiyonlar</div>
                    <ul className="actions-list">
                        {currentRisk.suggestedActions.map((action, index) => (
                            <li key={index}>{action}</li>
                        ))}
                    </ul>
                </div>
            )}

            <style jsx>{`
                .metrics-panel {
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid var(--border-color);
                    border-radius: 12px;
                    padding: 16px;
                    margin-top: 16px;
                }
                .metrics-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 16px;
                }
                .metrics-title {
                    font-weight: 600;
                    color: #fff;
                }
                .connection-status {
                    font-size: 12px;
                    padding: 4px 8px;
                    border-radius: 12px;
                }
                .connection-status.connected {
                    color: #22c55e;
                    background: rgba(34, 197, 94, 0.1);
                }
                .connection-status.disconnected {
                    color: #64748b;
                    background: rgba(100, 116, 139, 0.1);
                }
                .metrics-grid {
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 12px;
                }
                .metric-card {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding: 12px;
                    background: rgba(255, 255, 255, 0.02);
                    border: 1px solid var(--border-color);
                    border-radius: 8px;
                }
                .metric-card.risk-card {
                    border-width: 2px;
                }
                .metric-icon {
                    font-size: 24px;
                }
                .metric-content {
                    flex: 1;
                }
                .metric-label {
                    font-size: 11px;
                    color: #64748b;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                .metric-value {
                    font-size: 20px;
                    font-weight: 600;
                    color: #fff;
                }
                .metric-value.time {
                    font-family: monospace;
                    font-size: 16px;
                }
                .metric-unit {
                    font-size: 12px;
                    color: #64748b;
                    font-weight: 400;
                }
                .density-bar {
                    height: 4px;
                    background: var(--border-color);
                    border-radius: 2px;
                    margin-top: 6px;
                    overflow: hidden;
                }
                .density-fill {
                    height: 100%;
                    border-radius: 2px;
                    transition: width 0.3s ease;
                }
                .suggested-actions {
                    margin-top: 16px;
                    padding-top: 16px;
                    border-top: 1px solid var(--border-color);
                }
                .actions-header {
                    color: #eab308;
                    font-weight: 500;
                    margin-bottom: 8px;
                }
                .actions-list {
                    margin: 0;
                    padding-left: 20px;
                }
                .actions-list li {
                    color: #94a3b8;
                    font-size: 13px;
                    margin-bottom: 4px;
                }
                @media (max-width: 1200px) {
                    .metrics-grid {
                        grid-template-columns: repeat(2, 1fr);
                    }
                }
            `}</style>
        </div>
    );
}
