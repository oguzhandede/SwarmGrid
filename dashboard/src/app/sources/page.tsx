'use client';

import { useState, useEffect, useCallback } from 'react';
import { Source, SourceType, SourceStatus } from '@/types';
import LiveVideoPlayer from '@/components/LiveVideoPlayer';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
const EDGE_AGENT_URL = process.env.NEXT_PUBLIC_EDGE_AGENT_URL || 'http://localhost:8000';

export default function SourcesPage() {
    const [sources, setSources] = useState<Source[]>([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedSource, setSelectedSource] = useState<Source | null>(null);

    // Form states
    const [videoFile, setVideoFile] = useState<File | null>(null);
    const [cameraUrl, setCameraUrl] = useState('');
    const [zoneName, setZoneName] = useState('');
    const [zoneId, setZoneId] = useState('');

    // Fetch sources
    const fetchSources = useCallback(async () => {
        try {
            const res = await fetch(`${API_URL}/api/source`);
            if (res.ok) {
                const data = await res.json();
                setSources(data);
            }
        } catch (err) {
            console.error('Failed to fetch sources:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchSources();
    }, [fetchSources]);

    // Upload video
    const handleVideoUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!videoFile) return;

        setUploading(true);
        setError(null);

        const formData = new FormData();
        formData.append('file', videoFile);
        formData.append('tenantId', 'demo');
        formData.append('siteId', 'site-01');
        formData.append('zoneId', zoneId || 'default-zone');
        formData.append('name', zoneName || videoFile.name);

        try {
            const res = await fetch(`${API_URL}/api/source/video`, {
                method: 'POST',
                body: formData,
            });

            if (res.ok) {
                const newSource = await res.json();
                setSources(prev => [newSource, ...prev]);
                setVideoFile(null);
                setZoneName('');
                setZoneId('');
            } else {
                const errText = await res.text();
                setError(errText);
            }
        } catch (err) {
            setError('Upload failed');
        } finally {
            setUploading(false);
        }
    };

    // Register camera
    const handleCameraRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!cameraUrl) return;

        setError(null);

        try {
            const res = await fetch(`${API_URL}/api/source/camera`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    tenantId: 'demo',
                    siteId: 'site-01',
                    zoneId: zoneId || 'default-zone',
                    name: zoneName || 'Camera',
                    rtspUrl: cameraUrl,
                }),
            });

            if (res.ok) {
                const newSource = await res.json();
                setSources(prev => [newSource, ...prev]);
                setCameraUrl('');
                setZoneName('');
                setZoneId('');
            } else {
                const errText = await res.text();
                setError(errText);
            }
        } catch (err) {
            setError('Registration failed');
        }
    };

    // Start analysis
    const handleStartAnalysis = async (sourceId: string) => {
        try {
            const res = await fetch(`${API_URL}/api/source/${sourceId}/start`, {
                method: 'POST',
            });
            if (res.ok) {
                fetchSources();
            }
        } catch (err) {
            console.error('Failed to start analysis:', err);
        }
    };

    // Delete source
    const handleDelete = async (sourceId: string) => {
        try {
            const res = await fetch(`${API_URL}/api/source/${sourceId}`, {
                method: 'DELETE',
            });
            if (res.ok) {
                setSources(prev => prev.filter(s => s.id !== sourceId));
            }
        } catch (err) {
            console.error('Failed to delete source:', err);
        }
    };

    const getStatusText = (status: SourceStatus) => {
        switch (status) {
            case SourceStatus.Pending: return 'Bekliyor';
            case SourceStatus.Processing: return 'İşleniyor';
            case SourceStatus.Completed: return 'Tamamlandı';
            case SourceStatus.Error: return 'Hata';
            case SourceStatus.Connected: return 'Bağlı';
            case SourceStatus.Disconnected: return 'Bağlantı Kesildi';
            default: return 'Bilinmiyor';
        }
    };

    const getStatusColor = (status: SourceStatus) => {
        switch (status) {
            case SourceStatus.Processing:
            case SourceStatus.Connected: return 'green';
            case SourceStatus.Pending: return 'yellow';
            case SourceStatus.Error:
            case SourceStatus.Disconnected: return 'red';
            default: return 'gray';
        }
    };

    return (
        <main>
            <header className="header">
                <div className="logo">SwarmGrid - Kaynak Yönetimi</div>
                <a href="/" style={{ color: '#94a3b8', textDecoration: 'none' }}>← Dashboard</a>
            </header>

            <div className="container">
                {error && (
                    <div className="card" style={{ background: 'rgba(239, 68, 68, 0.2)', marginBottom: '20px' }}>
                        <p style={{ color: 'var(--danger)' }}>{error}</p>
                    </div>
                )}

                <div className="grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
                    {/* Left Column - Forms */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        {/* Video Upload Form */}
                        <div className="card">
                            <div className="card-title">📹 Video Yükle</div>
                            <form onSubmit={handleVideoUpload}>
                                <div className="form-group">
                                    <label>Video Dosyası</label>
                                    <input
                                        type="file"
                                        accept="video/*"
                                        onChange={(e) => setVideoFile(e.target.files?.[0] || null)}
                                        className="form-input"
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Kaynak Adı</label>
                                    <input
                                        type="text"
                                        value={zoneName}
                                        onChange={(e) => setZoneName(e.target.value)}
                                        placeholder="örn: AVM Girişi"
                                        className="form-input"
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Zone ID</label>
                                    <input
                                        type="text"
                                        value={zoneId}
                                        onChange={(e) => setZoneId(e.target.value)}
                                        placeholder="örn: entrance"
                                        className="form-input"
                                    />
                                </div>
                                <button
                                    type="submit"
                                    className="btn btn-primary"
                                    disabled={!videoFile || uploading}
                                    style={{ width: '100%', marginTop: '12px' }}
                                >
                                    {uploading ? 'Yükleniyor...' : 'Yükle ve Analiz Başlat'}
                                </button>
                            </form>
                        </div>

                        {/* Camera URL Form */}
                        <div className="card">
                            <div className="card-title">📷 Kamera Bağla</div>
                            <form onSubmit={handleCameraRegister}>
                                <div className="form-group">
                                    <label>RTSP / HTTP URL</label>
                                    <input
                                        type="text"
                                        value={cameraUrl}
                                        onChange={(e) => setCameraUrl(e.target.value)}
                                        placeholder="rtsp://user:pass@ip:port/stream"
                                        className="form-input"
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Kaynak Adı</label>
                                    <input
                                        type="text"
                                        value={zoneName}
                                        onChange={(e) => setZoneName(e.target.value)}
                                        placeholder="örn: Otopark Kamerası"
                                        className="form-input"
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Zone ID</label>
                                    <input
                                        type="text"
                                        value={zoneId}
                                        onChange={(e) => setZoneId(e.target.value)}
                                        placeholder="örn: parking-a"
                                        className="form-input"
                                    />
                                </div>
                                <button
                                    type="submit"
                                    className="btn btn-primary"
                                    disabled={!cameraUrl}
                                    style={{ width: '100%', marginTop: '12px' }}
                                >
                                    Kamerayı Kaydet
                                </button>
                            </form>
                        </div>
                    </div>

                    {/* Right Column - Video Player */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        <LiveVideoPlayer source={selectedSource} edgeAgentUrl={EDGE_AGENT_URL} />

                        {/* Source List */}
                        <div className="card">
                            <div className="card-title">Aktif Kaynaklar</div>
                            {loading ? (
                                <p style={{ color: '#64748b' }}>Yükleniyor...</p>
                            ) : sources.length === 0 ? (
                                <p style={{ color: '#64748b' }}>Henüz kaynak eklenmedi.</p>
                            ) : (
                                <div className="source-list">
                                    {sources.map((source) => (
                                        <div
                                            key={source.id}
                                            className={`source-item ${selectedSource?.id === source.id ? 'selected' : ''}`}
                                            onClick={() => setSelectedSource(source)}
                                            style={{ cursor: 'pointer' }}
                                        >
                                            <div className="source-info">
                                                <span className="source-icon">
                                                    {source.type === SourceType.Video ? '📹' : '📷'}
                                                </span>
                                                <div>
                                                    <div className="source-name">{source.name}</div>
                                                    <div className="source-zone">{source.zoneId}</div>
                                                </div>
                                            </div>
                                            <div className="source-status">
                                                <span className={`status-indicator status-${getStatusColor(source.status)}`} />
                                                {getStatusText(source.status)}
                                                {source.status === SourceStatus.Processing && (
                                                    <span className="source-progress"> ({source.progress.toFixed(0)}%)</span>
                                                )}
                                            </div>
                                            <div className="source-actions">
                                                {source.status === SourceStatus.Pending && (
                                                    <button
                                                        className="btn btn-primary"
                                                        onClick={(e) => { e.stopPropagation(); handleStartAnalysis(source.id); }}
                                                    >
                                                        Başlat
                                                    </button>
                                                )}
                                                <button
                                                    className="btn btn-danger"
                                                    onClick={(e) => { e.stopPropagation(); handleDelete(source.id); }}
                                                >
                                                    Sil
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
}

