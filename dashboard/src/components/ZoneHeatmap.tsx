'use client';

import { RiskEvent, RiskLevel } from '@/types';

// Demo AVM zone layout
const DEMO_ZONES = [
    { id: 'entrance', name: 'Ana Giriş', row: 0, col: 0, colSpan: 1 },
    { id: 'corridor', name: 'Ana Koridor', row: 0, col: 1, colSpan: 1 },
    { id: 'shops', name: 'Mağazalar', row: 0, col: 2, colSpan: 1 },
    { id: 'foodcourt-exit', name: 'Food Court Çıkış', row: 0, col: 3, colSpan: 1 },
    { id: 'parking-a', name: 'Otopark A', row: 1, col: 0, colSpan: 2 },
    { id: 'parking-b', name: 'Otopark B', row: 1, col: 2, colSpan: 2 },
];

interface ZoneHeatmapProps {
    zoneRiskMap: Map<string, RiskEvent>;
    onZoneClick?: (zoneId: string) => void;
}

export default function ZoneHeatmap({ zoneRiskMap, onZoneClick }: ZoneHeatmapProps) {
    const getRiskColor = (zoneId: string): string => {
        const event = zoneRiskMap.get(zoneId);
        if (!event) return 'var(--heatmap-inactive)';

        const score = event.riskScore;
        // Gradient from green (0) -> yellow (0.5) -> red (1)
        if (score < 0.5) {
            // Green to Yellow
            const ratio = score / 0.5;
            return `rgba(${Math.round(34 + 211 * ratio)}, ${Math.round(197 - 42 * ratio)}, ${Math.round(94 - 83 * ratio)}, 0.8)`;
        } else {
            // Yellow to Red
            const ratio = (score - 0.5) / 0.5;
            return `rgba(${Math.round(245 - 6 * ratio)}, ${Math.round(155 - 87 * ratio)}, ${Math.round(11 - 11 * ratio)}, 0.9)`;
        }
    };

    const getRiskInfo = (zoneId: string) => {
        const event = zoneRiskMap.get(zoneId);
        if (!event) return { score: null, level: null, time: null };
        return {
            score: (event.riskScore * 100).toFixed(0),
            level: event.riskLevel,
            time: new Date(event.timestamp).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })
        };
    };

    const getLevelText = (level: RiskLevel | null) => {
        if (level === null) return 'Veri yok';
        switch (level) {
            case RiskLevel.Red: return 'Kritik';
            case RiskLevel.Yellow: return 'Dikkat';
            default: return 'Normal';
        }
    };

    return (
        <div className="heatmap-container">
            <div className="heatmap-header">
                <h3>Zone Risk Haritası</h3>
                <span className="heatmap-subtitle">AVM Kat Planı</span>
            </div>
            <div className="heatmap-grid">
                {DEMO_ZONES.map((zone) => {
                    const info = getRiskInfo(zone.id);
                    const isActive = info.score !== null;

                    return (
                        <div
                            key={zone.id}
                            className={`heatmap-zone ${isActive ? 'active' : 'inactive'}`}
                            style={{
                                gridColumn: `span ${zone.colSpan}`,
                                backgroundColor: getRiskColor(zone.id),
                            }}
                            onClick={() => onZoneClick?.(zone.id)}
                        >
                            <div className="zone-name">{zone.name}</div>
                            <div className="zone-id">{zone.id}</div>
                            {isActive ? (
                                <>
                                    <div className="zone-score">{info.score}%</div>
                                    <div className="zone-level">{getLevelText(info.level)}</div>
                                    <div className="zone-time">{info.time}</div>
                                </>
                            ) : (
                                <div className="zone-inactive">Bekleniyor...</div>
                            )}
                        </div>
                    );
                })}
            </div>
            <div className="heatmap-legend">
                <span className="legend-item">
                    <span className="legend-color" style={{ background: 'var(--success)' }}></span>
                    Normal
                </span>
                <span className="legend-item">
                    <span className="legend-color" style={{ background: 'var(--warning)' }}></span>
                    Dikkat
                </span>
                <span className="legend-item">
                    <span className="legend-color" style={{ background: 'var(--danger)' }}></span>
                    Kritik
                </span>
            </div>
        </div>
    );
}
