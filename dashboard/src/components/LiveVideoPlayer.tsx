'use client';

import { useState, useEffect } from 'react';
import { Source, SourceType, SourceStatus } from '@/types';

interface LiveVideoPlayerProps {
    source: Source | null;
    apiUrl?: string;
    edgeAgentUrl?: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
const EDGE_AGENT_URL = process.env.NEXT_PUBLIC_EDGE_AGENT_URL || 'http://localhost:8000';

export default function LiveVideoPlayer({
    source,
    apiUrl = API_URL,
    edgeAgentUrl = EDGE_AGENT_URL
}: LiveVideoPlayerProps) {
    const [error, setError] = useState<string | null>(null);
    const [streamKey, setStreamKey] = useState(0);

    // Determine stream URL based on source type
    const getStreamUrl = () => {
        if (!source) return null;

        if (source.type === SourceType.Video) {
            // Video files are served from backend
            return `${apiUrl}/api/source/${source.id}/stream`;
        } else {
            // Camera streams from Edge Agent MJPEG
            return `${edgeAgentUrl}/stream`;
        }
    };

    const streamUrl = getStreamUrl();

    // Check if source can be played
    const isVideoSource = source?.type === SourceType.Video;
    const isCameraSource = source?.type === SourceType.Camera;

    const isActive = source && (
        source.status === SourceStatus.Processing ||
        source.status === SourceStatus.Connected ||
        source.status === SourceStatus.Completed
    );

    useEffect(() => {
        setError(null);
        // Force refresh stream when source changes
        setStreamKey(prev => prev + 1);
    }, [source]);

    const handleError = () => {
        if (isCameraSource) {
            setError('Edge Agent bağlantısı başarısız. Agent çalışıyor mu?');
        } else {
            setError('Video yüklenemedi');
        }
    };

    const getStatusText = (status: SourceStatus) => {
        switch (status) {
            case SourceStatus.Processing: return 'İşleniyor';
            case SourceStatus.Connected: return 'Bağlı';
            case SourceStatus.Completed: return 'Tamamlandı';
            case SourceStatus.Pending: return 'Bekliyor';
            case SourceStatus.Error: return 'Hata';
            default: return 'Bilinmiyor';
        }
    };

    return (
        <div className="video-player-container">
            <div className="video-player-header">
                <h3>{isCameraSource ? '📷 Canlı Kamera' : '📹 Video Oynatıcı'}</h3>
                {source && (
                    <span className="video-source-name">{source.name}</span>
                )}
            </div>

            <div className="video-frame">
                {!source ? (
                    <div className="video-placeholder">
                        <span className="placeholder-icon">📷</span>
                        <p>Kaynak seçilmedi</p>
                        <p className="placeholder-hint">Listeden bir kaynak seçin</p>
                    </div>
                ) : !isActive ? (
                    <div className="video-placeholder">
                        <span className="placeholder-icon">⏸️</span>
                        <p>{isCameraSource ? 'Kamera beklemede' : 'Video beklemede'}</p>
                        <p className="placeholder-hint">"Başlat" butonuna tıklayın</p>
                    </div>
                ) : error ? (
                    <div className="video-placeholder error">
                        <span className="placeholder-icon">⚠️</span>
                        <p>{error}</p>
                        <p className="placeholder-hint">
                            {isCameraSource ? 'Edge Agent: python main.py' : 'Dosya erişilebilir mi?'}
                        </p>
                    </div>
                ) : isCameraSource ? (
                    // MJPEG stream for cameras
                    <img
                        key={`cam-${streamKey}`}
                        src={streamUrl || ''}
                        alt="Live Camera Stream"
                        className="video-stream"
                        onError={handleError}
                    />
                ) : (
                    // HTML5 video for video files
                    <video
                        key={`vid-${source.id}-${streamKey}`}
                        src={streamUrl || ''}
                        controls
                        autoPlay
                        muted
                        className="video-stream"
                        onError={handleError}
                    />
                )}
            </div>

            {source && (
                <div className="video-info-bar">
                    <div className="info-item">
                        <span className="info-label">Zone:</span>
                        <span className="info-value">{source.zoneId}</span>
                    </div>
                    <div className="info-item">
                        <span className="info-label">Status:</span>
                        <span className="info-value">
                            {getStatusText(source.status)}
                        </span>
                    </div>
                    <div className="info-item">
                        <span className="info-label">Type:</span>
                        <span className="info-value">
                            {source.type === SourceType.Video ? '📹 Video' : '📷 Kamera'}
                        </span>
                    </div>
                </div>
            )}
        </div>
    );
}
