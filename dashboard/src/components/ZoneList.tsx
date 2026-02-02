'use client';

import { Zone } from '@/types';

interface ZoneListProps {
    zones: Zone[];
    selectedZone?: Zone | null;
    onSelect: (zone: Zone) => void;
    onEdit: (zone: Zone) => void;
    onDelete: (zone: Zone) => void;
}

export default function ZoneList({ zones, selectedZone, onSelect, onEdit, onDelete }: ZoneListProps) {
    const getRiskColor = (zone: Zone) => {
        // This would normally come from real-time data
        return 'green';
    };

    const getCapacityColor = (zone: Zone) => {
        // Mock capacity usage
        return 'green';
    };

    return (
        <div className="zone-list">
            {zones.length === 0 ? (
                <div className="empty-state">
                    <span className="empty-icon">🗺️</span>
                    <p>Henüz zone tanımlanmadı</p>
                    <p className="hint">Yeni zone ekleyerek risk bölgelerini tanımlayın</p>
                </div>
            ) : (
                zones.map(zone => (
                    <div
                        key={zone.id}
                        className={`zone-item ${selectedZone?.id === zone.id ? 'selected' : ''}`}
                        onClick={() => onSelect(zone)}
                    >
                        <div className="zone-info">
                            <div className="zone-header">
                                <span className={`status-dot status-${getRiskColor(zone)}`} />
                                <span className="zone-name">{zone.name}</span>
                            </div>
                            <div className="zone-meta">
                                <span className="zone-id">{zone.zoneId}</span>
                                {zone.polygon && zone.polygon.length > 0 && (
                                    <span className="polygon-badge">📐 {zone.polygon.length} nokta</span>
                                )}
                                {zone.bottleneckPoints && zone.bottleneckPoints.length > 0 && (
                                    <span className="bottleneck-badge">📍 {zone.bottleneckPoints.length}</span>
                                )}
                            </div>
                        </div>

                        <div className="zone-thresholds">
                            <div className="threshold-bar">
                                <div
                                    className="threshold-segment green"
                                    style={{ width: `${zone.yellowThreshold * 100}%` }}
                                />
                                <div
                                    className="threshold-segment yellow"
                                    style={{ width: `${(zone.redThreshold - zone.yellowThreshold) * 100}%` }}
                                />
                                <div
                                    className="threshold-segment red"
                                    style={{ width: `${(1 - zone.redThreshold) * 100}%` }}
                                />
                            </div>
                            <div className="threshold-labels">
                                <span>{Math.round(zone.yellowThreshold * 100)}%</span>
                                <span>{Math.round(zone.redThreshold * 100)}%</span>
                            </div>
                        </div>

                        <div className="zone-capacity">
                            <span className="capacity-label">Kapasite</span>
                            <span className="capacity-value">{zone.maxCapacity}</span>
                        </div>

                        <div className="zone-actions">
                            <button
                                className="action-btn edit"
                                onClick={(e) => { e.stopPropagation(); onEdit(zone); }}
                                title="Düzenle"
                            >
                                ✏️
                            </button>
                            <button
                                className="action-btn delete"
                                onClick={(e) => { e.stopPropagation(); onDelete(zone); }}
                                title="Sil"
                            >
                                🗑️
                            </button>
                        </div>
                    </div>
                ))
            )}

            <style jsx>{`
                .zone-list {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }
                .empty-state {
                    text-align: center;
                    padding: 40px 20px;
                    color: #64748b;
                }
                .empty-icon {
                    font-size: 48px;
                    display: block;
                    margin-bottom: 16px;
                }
                .empty-state p {
                    margin: 4px 0;
                }
                .hint {
                    font-size: 13px;
                    color: #475569;
                }
                .zone-item {
                    display: grid;
                    grid-template-columns: 1fr auto auto auto;
                    gap: 16px;
                    align-items: center;
                    padding: 12px 16px;
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid var(--border-color);
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .zone-item:hover {
                    background: rgba(255, 255, 255, 0.06);
                    border-color: var(--primary);
                }
                .zone-item.selected {
                    background: rgba(59, 130, 246, 0.1);
                    border-color: var(--primary);
                }
                .zone-header {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                .status-dot {
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                }
                .status-dot.status-green { background: #22c55e; }
                .status-dot.status-yellow { background: #eab308; }
                .status-dot.status-red { background: #ef4444; }
                .zone-name {
                    font-weight: 500;
                    color: #fff;
                }
                .zone-meta {
                    display: flex;
                    gap: 8px;
                    margin-top: 4px;
                }
                .zone-id {
                    font-size: 12px;
                    color: #64748b;
                    font-family: monospace;
                }
                .polygon-badge, .bottleneck-badge {
                    font-size: 11px;
                    padding: 2px 6px;
                    border-radius: 4px;
                    background: rgba(59, 130, 246, 0.2);
                    color: #60a5fa;
                }
                .bottleneck-badge {
                    background: rgba(239, 68, 68, 0.2);
                    color: #f87171;
                }
                .zone-thresholds {
                    width: 100px;
                }
                .threshold-bar {
                    display: flex;
                    height: 6px;
                    border-radius: 3px;
                    overflow: hidden;
                }
                .threshold-segment {
                    height: 100%;
                }
                .threshold-segment.green { background: #22c55e; }
                .threshold-segment.yellow { background: #eab308; }
                .threshold-segment.red { background: #ef4444; }
                .threshold-labels {
                    display: flex;
                    justify-content: space-between;
                    font-size: 10px;
                    color: #64748b;
                    margin-top: 2px;
                }
                .zone-capacity {
                    text-align: center;
                    min-width: 60px;
                }
                .capacity-label {
                    display: block;
                    font-size: 10px;
                    color: #64748b;
                }
                .capacity-value {
                    font-weight: 600;
                    color: #fff;
                }
                .zone-actions {
                    display: flex;
                    gap: 4px;
                }
                .action-btn {
                    background: none;
                    border: none;
                    padding: 6px;
                    cursor: pointer;
                    border-radius: 4px;
                    transition: background 0.2s;
                }
                .action-btn:hover {
                    background: rgba(255, 255, 255, 0.1);
                }
                .action-btn.delete:hover {
                    background: rgba(239, 68, 68, 0.2);
                }
            `}</style>
        </div>
    );
}
