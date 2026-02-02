'use client';

import { useState, useEffect, useCallback } from 'react';
import { Zone, Source, PolygonPoint, BottleneckPoint } from '@/types';
import { useSignalR } from '@/lib/useSignalR';
import ZoneList from '@/components/ZoneList';
import ZoneForm from '@/components/ZoneForm';
import PolygonDrawer from '@/components/PolygonDrawer';
import ZoneMetricsPanel from '@/components/ZoneMetricsPanel';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export default function ZonesPage() {
    const [zones, setZones] = useState<Zone[]>([]);
    const [sources, setSources] = useState<Source[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [selectedZone, setSelectedZone] = useState<Zone | null>(null);
    const [showForm, setShowForm] = useState(false);
    const [editingZone, setEditingZone] = useState<Zone | null>(null);

    const [drawMode, setDrawMode] = useState<'polygon' | 'bottleneck' | 'view'>('view');
    const [showDetections, setShowDetections] = useState(true);

    // SignalR for real-time updates
    const { connected, currentRisk, zoneRiskMap, subscribeToSite } = useSignalR(true);

    // Subscribe to site on connect
    useEffect(() => {
        if (connected) {
            subscribeToSite('site-01').catch(console.error);
        }
    }, [connected, subscribeToSite]);

    // Get current risk for selected zone
    const getZoneRisk = () => {
        if (!selectedZone) return null;
        return zoneRiskMap.get(selectedZone.zoneId) || currentRisk;
    };

    // Fetch zones
    const fetchZones = useCallback(async () => {
        try {
            const res = await fetch(`${API_URL}/api/zone?tenantId=demo`);
            if (res.ok) {
                const data = await res.json();
                setZones(data);
            }
        } catch (err) {
            console.error('Failed to fetch zones:', err);
            setError('Zone listesi yüklenemedi');
        } finally {
            setLoading(false);
        }
    }, []);

    // Fetch sources for camera selection
    const fetchSources = useCallback(async () => {
        try {
            const res = await fetch(`${API_URL}/api/source`);
            if (res.ok) {
                const data = await res.json();
                setSources(data);
            }
        } catch (err) {
            console.error('Failed to fetch sources:', err);
        }
    }, []);

    useEffect(() => {
        fetchZones();
        fetchSources();
    }, [fetchZones, fetchSources]);

    // Create zone
    const handleCreate = async (zoneData: Partial<Zone>) => {
        try {
            const res = await fetch(`${API_URL}/api/zone`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(zoneData)
            });
            if (res.ok) {
                const newZone = await res.json();
                setZones(prev => [newZone, ...prev]);
                setShowForm(false);
                setSelectedZone(newZone);
                setDrawMode('polygon');
            } else {
                const errText = await res.text();
                setError(errText);
            }
        } catch (err) {
            setError('Zone oluşturulamadı');
        }
    };

    // Update zone
    const handleUpdate = async (zoneData: Partial<Zone>) => {
        if (!editingZone) return;
        try {
            const res = await fetch(`${API_URL}/api/zone/${editingZone.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(zoneData)
            });
            if (res.ok) {
                const updatedZone = await res.json();
                setZones(prev => prev.map(z => z.id === updatedZone.id ? updatedZone : z));
                setShowForm(false);
                setEditingZone(null);
                if (selectedZone?.id === updatedZone.id) {
                    setSelectedZone(updatedZone);
                }
            } else {
                const errText = await res.text();
                setError(errText);
            }
        } catch (err) {
            setError('Zone güncellenemedi');
        }
    };

    // Delete zone
    const handleDelete = async (zone: Zone) => {
        if (!confirm(`"${zone.name}" zone'u silmek istediğinizden emin misiniz?`)) return;
        try {
            const res = await fetch(`${API_URL}/api/zone/${zone.id}`, {
                method: 'DELETE'
            });
            if (res.ok) {
                setZones(prev => prev.filter(z => z.id !== zone.id));
                if (selectedZone?.id === zone.id) {
                    setSelectedZone(null);
                }
            }
        } catch (err) {
            setError('Zone silinemedi');
        }
    };

    // Update polygon
    const handlePolygonChange = async (points: PolygonPoint[]) => {
        if (!selectedZone) return;
        try {
            const res = await fetch(`${API_URL}/api/zone/${selectedZone.id}/polygon`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ polygon: points })
            });
            if (res.ok) {
                const updatedZone = await res.json();
                setZones(prev => prev.map(z => z.id === updatedZone.id ? updatedZone : z));
                setSelectedZone(updatedZone);
            }
        } catch (err) {
            console.error('Failed to update polygon:', err);
        }
    };

    // Update bottlenecks
    const handleBottleneckChange = async (points: BottleneckPoint[]) => {
        if (!selectedZone) return;
        try {
            const res = await fetch(`${API_URL}/api/zone/${selectedZone.id}/bottlenecks`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ bottleneckPoints: points })
            });
            if (res.ok) {
                const updatedZone = await res.json();
                setZones(prev => prev.map(z => z.id === updatedZone.id ? updatedZone : z));
                setSelectedZone(updatedZone);
            }
        } catch (err) {
            console.error('Failed to update bottlenecks:', err);
        }
    };

    // Get video source for selected zone
    const getVideoSrc = () => {
        if (!selectedZone?.cameraId) return undefined;
        const source = sources.find(s => s.id === selectedZone.cameraId);
        if (source) {
            return `${API_URL}/api/source/${source.id}/stream`;
        }
        return undefined;
    };

    return (
        <main>
            <header className="header">
                <div className="logo">SwarmGrid - Zone Yönetimi</div>
                <a href="/" style={{ color: '#94a3b8', textDecoration: 'none' }}>← Dashboard</a>
            </header>

            <div className="container">
                {error && (
                    <div className="card" style={{ background: 'rgba(239, 68, 68, 0.2)', marginBottom: '20px' }}>
                        <p style={{ color: 'var(--danger)', margin: 0 }}>{error}</p>
                        <button
                            onClick={() => setError(null)}
                            style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', marginLeft: '12px' }}
                        >
                            ✕
                        </button>
                    </div>
                )}

                <div className="zones-layout">
                    {/* Left Panel - Zone List */}
                    <div className="zones-sidebar">
                        <div className="card">
                            <div className="card-header">
                                <div className="card-title">Zone Listesi</div>
                                <button
                                    className="btn btn-primary"
                                    onClick={() => { setShowForm(true); setEditingZone(null); }}
                                >
                                    + Yeni Zone
                                </button>
                            </div>

                            {loading ? (
                                <p style={{ color: '#64748b', padding: '20px 0' }}>Yükleniyor...</p>
                            ) : (
                                <ZoneList
                                    zones={zones}
                                    selectedZone={selectedZone}
                                    onSelect={(zone) => { setSelectedZone(zone); setDrawMode('view'); }}
                                    onEdit={(zone) => { setEditingZone(zone); setShowForm(true); }}
                                    onDelete={handleDelete}
                                />
                            )}
                        </div>
                    </div>

                    {/* Right Panel - Polygon Editor */}
                    <div className="zones-main">
                        <div className="card">
                            <div className="card-header">
                                <div className="card-title">
                                    {selectedZone ? `📐 ${selectedZone.name}` : 'Zone Düzenleyici'}
                                </div>
                                {selectedZone && (
                                    <div className="mode-tabs">
                                        <button
                                            className={`mode-tab ${drawMode === 'view' ? 'active' : ''}`}
                                            onClick={() => setDrawMode('view')}
                                        >
                                            👁️ Görüntüle
                                        </button>
                                        <button
                                            className={`mode-tab ${drawMode === 'polygon' ? 'active' : ''}`}
                                            onClick={() => setDrawMode('polygon')}
                                        >
                                            📐 Polygon
                                        </button>
                                        <button
                                            className={`mode-tab ${drawMode === 'bottleneck' ? 'active' : ''}`}
                                            onClick={() => setDrawMode('bottleneck')}
                                        >
                                            📍 Dar Boğaz
                                        </button>
                                        <div className="mode-divider"></div>
                                        <button
                                            className={`mode-tab detection-toggle ${showDetections ? 'active' : ''}`}
                                            onClick={() => setShowDetections(!showDetections)}
                                            title="Tespit noktalarını göster/gizle"
                                        >
                                            {showDetections ? '👁️' : '👁️‍🗨️'} Tespitler
                                        </button>
                                    </div>
                                )}
                            </div>

                            {selectedZone ? (
                                <PolygonDrawer
                                    videoSrc={getVideoSrc()}
                                    mjpegSrc="http://localhost:8000/stream"
                                    polygon={selectedZone.polygon}
                                    bottleneckPoints={selectedZone.bottleneckPoints}
                                    onPolygonChange={handlePolygonChange}
                                    onBottleneckChange={handleBottleneckChange}
                                    mode={drawMode}
                                    width={640}
                                    height={480}
                                    showDetections={showDetections}
                                    personCount={getZoneRisk()?.riskScore
                                        ? Math.round((getZoneRisk()?.riskScore ?? 0) * selectedZone.maxCapacity * 0.5)
                                        : Math.floor(Math.random() * 8) + 1}
                                />
                            ) : (
                                <div className="empty-editor">
                                    <span className="empty-icon">📐</span>
                                    <p>Zone seçin veya yeni zone oluşturun</p>
                                    <p className="hint">Polygon çizerek risk bölgesini tanımlayabilirsiniz</p>
                                </div>
                            )}

                            {selectedZone && (
                                <div className="zone-details">
                                    <div className="detail-row">
                                        <span className="detail-label">Zone ID:</span>
                                        <span className="detail-value">{selectedZone.zoneId}</span>
                                    </div>
                                    <div className="detail-row">
                                        <span className="detail-label">Kapasite:</span>
                                        <span className="detail-value">{selectedZone.maxCapacity} kişi</span>
                                    </div>
                                    <div className="detail-row">
                                        <span className="detail-label">Sarı Eşik:</span>
                                        <span className="detail-value threshold-yellow">{Math.round(selectedZone.yellowThreshold * 100)}%</span>
                                    </div>
                                    <div className="detail-row">
                                        <span className="detail-label">Kırmızı Eşik:</span>
                                        <span className="detail-value threshold-red">{Math.round(selectedZone.redThreshold * 100)}%</span>
                                    </div>
                                    {selectedZone.description && (
                                        <div className="detail-row full">
                                            <span className="detail-label">Açıklama:</span>
                                            <span className="detail-value">{selectedZone.description}</span>
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Real-time Metrics Panel */}
                            {selectedZone && (
                                <ZoneMetricsPanel
                                    zoneId={selectedZone.zoneId}
                                    zoneName={selectedZone.name}
                                    currentRisk={getZoneRisk()}
                                    maxCapacity={selectedZone.maxCapacity}
                                    connected={connected}
                                />
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Form Modal */}
            {showForm && (
                <ZoneForm
                    zone={editingZone}
                    sources={sources}
                    onSubmit={editingZone ? handleUpdate : handleCreate}
                    onCancel={() => { setShowForm(false); setEditingZone(null); }}
                />
            )}

            <style jsx>{`
                .zones-layout {
                    display: grid;
                    grid-template-columns: 400px 1fr;
                    gap: 20px;
                }
                .zones-sidebar {
                    max-height: calc(100vh - 140px);
                    overflow-y: auto;
                }
                .card-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 16px;
                }
                .mode-tabs {
                    display: flex;
                    gap: 4px;
                }
                .mode-tab {
                    padding: 6px 12px;
                    border-radius: 6px;
                    border: none;
                    background: rgba(255, 255, 255, 0.05);
                    color: #94a3b8;
                    cursor: pointer;
                    font-size: 13px;
                    transition: all 0.2s;
                }
                .mode-tab:hover {
                    background: rgba(255, 255, 255, 0.1);
                }
                .mode-tab.active {
                    background: var(--primary);
                    color: #fff;
                }
                .mode-divider {
                    width: 1px;
                    height: 24px;
                    background: var(--border-color);
                    margin: 0 4px;
                }
                .detection-toggle.active {
                    background: rgba(34, 197, 94, 0.2);
                    color: #22c55e;
                }
                .empty-editor {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    min-height: 400px;
                    color: #64748b;
                }
                .empty-icon {
                    font-size: 64px;
                    margin-bottom: 16px;
                }
                .empty-editor p {
                    margin: 4px 0;
                }
                .hint {
                    font-size: 13px;
                    color: #475569;
                }
                .zone-details {
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 12px;
                    margin-top: 16px;
                    padding-top: 16px;
                    border-top: 1px solid var(--border-color);
                }
                .detail-row {
                    display: flex;
                    flex-direction: column;
                    gap: 4px;
                }
                .detail-row.full {
                    grid-column: 1 / -1;
                }
                .detail-label {
                    font-size: 12px;
                    color: #64748b;
                }
                .detail-value {
                    font-weight: 500;
                    color: #fff;
                }
                .threshold-yellow {
                    color: #eab308;
                }
                .threshold-red {
                    color: #ef4444;
                }
                @media (max-width: 1024px) {
                    .zones-layout {
                        grid-template-columns: 1fr;
                    }
                }
            `}</style>
        </main>
    );
}
