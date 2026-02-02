'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { PolygonPoint, BottleneckPoint } from '@/types';

interface DetectedPerson {
    id: number;
    x: number;
    y: number;
    confidence: number;
}

interface PolygonDrawerProps {
    videoSrc?: string;
    imageSrc?: string;
    mjpegSrc?: string;  // Edge Agent MJPEG stream URL
    polygon?: PolygonPoint[];
    bottleneckPoints?: BottleneckPoint[];
    onPolygonChange?: (points: PolygonPoint[]) => void;
    onBottleneckChange?: (points: BottleneckPoint[]) => void;
    mode?: 'polygon' | 'bottleneck' | 'view';
    width?: number;
    height?: number;
    showDetections?: boolean;
    personCount?: number;
}

export default function PolygonDrawer({
    videoSrc,
    imageSrc,
    mjpegSrc,
    polygon = [],
    bottleneckPoints = [],
    onPolygonChange,
    onBottleneckChange,
    mode = 'polygon',
    width = 640,
    height = 480,
    showDetections = false,
    personCount = 0
}: PolygonDrawerProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const videoRef = useRef<HTMLVideoElement>(null);
    const [points, setPoints] = useState<PolygonPoint[]>(polygon || []);
    const [bottlenecks, setBottlenecks] = useState<BottleneckPoint[]>(bottleneckPoints || []);
    const [draggingIndex, setDraggingIndex] = useState<number | null>(null);
    const [isPolygonClosed, setIsPolygonClosed] = useState((polygon || []).length >= 3);
    const [newBottleneckName, setNewBottleneckName] = useState('');
    const [pendingBottleneck, setPendingBottleneck] = useState<{ x: number; y: number } | null>(null);
    const [detectedPersons, setDetectedPersons] = useState<DetectedPerson[]>([]);

    // Sync with props
    useEffect(() => {
        setPoints(polygon || []);
        setIsPolygonClosed((polygon || []).length >= 3);
    }, [polygon]);

    useEffect(() => {
        setBottlenecks(bottleneckPoints || []);
    }, [bottleneckPoints]);

    // Generate and animate detection points based on person count
    useEffect(() => {
        if (!showDetections || personCount <= 0) {
            setDetectedPersons([]);
            return;
        }

        // Function to generate detection positions
        const generatePositions = () => {
            const newPersons: DetectedPerson[] = [];
            const polyBounds = polygon && polygon.length >= 3 ? polygon : null;
            const actualCount = personCount; // Use actual count, no minimum

            for (let i = 0; i < Math.min(actualCount, 30); i++) { // Cap at 30 for performance
                let x: number, y: number;

                if (polyBounds) {
                    // Generate points within polygon bounds with some randomness
                    const centerX = polyBounds.reduce((sum, p) => sum + p.x, 0) / polyBounds.length;
                    const centerY = polyBounds.reduce((sum, p) => sum + p.y, 0) / polyBounds.length;

                    // Calculate spread based on polygon size
                    const spreadX = Math.max(...polyBounds.map(p => Math.abs(p.x - centerX))) * 0.8;
                    const spreadY = Math.max(...polyBounds.map(p => Math.abs(p.y - centerY))) * 0.8;

                    x = centerX + (Math.random() - 0.5) * spreadX * 2;
                    y = centerY + (Math.random() - 0.5) * spreadY * 2;
                } else {
                    // Random positions across the canvas
                    x = 100 + Math.random() * (width - 200);
                    y = 100 + Math.random() * (height - 200);
                }

                newPersons.push({
                    id: i,
                    x: Math.max(20, Math.min(width - 20, x)),
                    y: Math.max(20, Math.min(height - 20, y)),
                    confidence: 0.75 + Math.random() * 0.25
                });
            }

            setDetectedPersons(newPersons);
        };

        // Generate initial positions
        generatePositions();

        // Update positions every 1.5 seconds to simulate movement
        const interval = setInterval(generatePositions, 1500);

        return () => clearInterval(interval);
    }, [showDetections, personCount, polygon, width, height]);

    // Draw canvas
    const draw = useCallback(() => {
        const canvas = canvasRef.current;
        const ctx = canvas?.getContext('2d');
        if (!ctx || !canvas) return;

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw polygon
        if (points.length > 0) {
            ctx.beginPath();
            ctx.moveTo(points[0].x, points[0].y);
            for (let i = 1; i < points.length; i++) {
                ctx.lineTo(points[i].x, points[i].y);
            }
            if (isPolygonClosed && points.length >= 3) {
                ctx.closePath();
                ctx.fillStyle = 'rgba(59, 130, 246, 0.2)';
                ctx.fill();
            }
            ctx.strokeStyle = '#3b82f6';
            ctx.lineWidth = 2;
            ctx.stroke();

            // Draw vertices
            points.forEach((point, index) => {
                ctx.beginPath();
                ctx.arc(point.x, point.y, 6, 0, Math.PI * 2);
                ctx.fillStyle = index === 0 ? '#22c55e' : '#3b82f6';
                ctx.fill();
                ctx.strokeStyle = '#fff';
                ctx.lineWidth = 2;
                ctx.stroke();
            });
        }

        // Draw bottleneck points
        bottlenecks.forEach((bp) => {
            ctx.beginPath();
            ctx.arc(bp.x, bp.y, 8, 0, Math.PI * 2);
            ctx.fillStyle = '#ef4444';
            ctx.fill();
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 2;
            ctx.stroke();

            // Label
            ctx.font = '12px Inter, sans-serif';
            ctx.fillStyle = '#fff';
            ctx.fillText(bp.name, bp.x + 12, bp.y + 4);
        });

        // Draw detected persons
        if (showDetections && detectedPersons.length > 0) {
            detectedPersons.forEach((person) => {
                // Outer glow
                ctx.beginPath();
                ctx.arc(person.x, person.y, 12, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(34, 197, 94, 0.3)';
                ctx.fill();

                // Inner dot
                ctx.beginPath();
                ctx.arc(person.x, person.y, 6, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(34, 197, 94, ${person.confidence})`;
                ctx.fill();
                ctx.strokeStyle = '#fff';
                ctx.lineWidth = 1.5;
                ctx.stroke();
            });

            // Draw count badge
            ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            ctx.fillRect(width - 80, 10, 70, 28);
            ctx.fillStyle = '#22c55e';
            ctx.font = 'bold 14px Inter, sans-serif';
            ctx.fillText(`👤 ${detectedPersons.length}`, width - 70, 30);
        }
    }, [points, bottlenecks, isPolygonClosed, showDetections, detectedPersons, width]);

    useEffect(() => {
        draw();
    }, [draw]);

    // Get mouse position relative to canvas
    const getMousePos = (e: React.MouseEvent<HTMLCanvasElement>): { x: number; y: number } => {
        const canvas = canvasRef.current;
        if (!canvas) return { x: 0, y: 0 };
        const rect = canvas.getBoundingClientRect();
        return {
            x: ((e.clientX - rect.left) / rect.width) * canvas.width,
            y: ((e.clientY - rect.top) / rect.height) * canvas.height
        };
    };

    // Find point near position
    const findNearPoint = (pos: { x: number; y: number }, threshold = 15): number => {
        return points.findIndex(p =>
            Math.sqrt(Math.pow(p.x - pos.x, 2) + Math.pow(p.y - pos.y, 2)) < threshold
        );
    };

    // Handle mouse events
    const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
        if (mode === 'view') return;
        const pos = getMousePos(e);

        if (mode === 'polygon') {
            const nearIndex = findNearPoint(pos);
            if (nearIndex !== -1) {
                // If clicking first point and have enough points, close polygon
                if (nearIndex === 0 && points.length >= 3 && !isPolygonClosed) {
                    setIsPolygonClosed(true);
                    onPolygonChange?.(points);
                } else {
                    setDraggingIndex(nearIndex);
                }
            } else if (!isPolygonClosed) {
                // Add new point
                const newPoints = [...points, pos];
                setPoints(newPoints);
            }
        } else if (mode === 'bottleneck') {
            // In bottleneck mode, clicking adds a bottleneck point
            setPendingBottleneck(pos);
        }
    };

    const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
        if (draggingIndex === null) return;
        const pos = getMousePos(e);
        const newPoints = [...points];
        newPoints[draggingIndex] = pos;
        setPoints(newPoints);
    };

    const handleMouseUp = () => {
        if (draggingIndex !== null) {
            setDraggingIndex(null);
            if (isPolygonClosed) {
                onPolygonChange?.(points);
            }
        }
    };

    // Add bottleneck with name
    const addBottleneck = () => {
        if (!pendingBottleneck || !newBottleneckName.trim()) return;
        const newBottlenecks = [...bottlenecks, { ...pendingBottleneck, name: newBottleneckName.trim() }];
        setBottlenecks(newBottlenecks);
        onBottleneckChange?.(newBottlenecks);
        setPendingBottleneck(null);
        setNewBottleneckName('');
    };

    // Remove bottleneck
    const removeBottleneck = (index: number) => {
        const newBottlenecks = bottlenecks.filter((_, i) => i !== index);
        setBottlenecks(newBottlenecks);
        onBottleneckChange?.(newBottlenecks);
    };

    // Clear polygon
    const clearPolygon = () => {
        setPoints([]);
        setIsPolygonClosed(false);
        onPolygonChange?.([]);
    };

    return (
        <div className="polygon-drawer">
            <div className="canvas-container" style={{ position: 'relative', width, height }}>
                {videoSrc && (
                    <video
                        ref={videoRef}
                        src={videoSrc}
                        style={{
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            width: '100%',
                            height: '100%',
                            objectFit: 'cover'
                        }}
                        autoPlay
                        loop
                        muted
                    />
                )}
                {mjpegSrc && !videoSrc && (
                    <img
                        src={mjpegSrc}
                        alt="Live camera stream"
                        style={{
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            width: '100%',
                            height: '100%',
                            objectFit: 'cover'
                        }}
                    />
                )}
                {imageSrc && !videoSrc && !mjpegSrc && (
                    <img
                        src={imageSrc}
                        alt="Zone background"
                        style={{
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            width: '100%',
                            height: '100%',
                            objectFit: 'cover'
                        }}
                    />
                )}
                {!videoSrc && !imageSrc && !mjpegSrc && (
                    <div style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: '100%',
                        background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#64748b'
                    }}>
                        Kamera görüntüsü bekleniyor...
                    </div>
                )}
                <canvas
                    ref={canvasRef}
                    width={width}
                    height={height}
                    style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: '100%',
                        cursor: mode === 'view' ? 'default' : 'crosshair'
                    }}
                    onMouseDown={handleMouseDown}
                    onMouseMove={handleMouseMove}
                    onMouseUp={handleMouseUp}
                    onMouseLeave={handleMouseUp}
                />
            </div>

            {/* Controls */}
            <div className="drawer-controls" style={{ marginTop: '12px' }}>
                {mode === 'polygon' && (
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <span style={{ color: '#94a3b8', fontSize: '14px' }}>
                            {isPolygonClosed
                                ? `✓ Polygon kaydedildi (${points.length} nokta)`
                                : `${points.length} nokta - İlk noktaya tıklayarak kapatın`}
                        </span>
                        <button className="btn btn-secondary" onClick={clearPolygon} style={{ marginLeft: 'auto' }}>
                            Temizle
                        </button>
                    </div>
                )}

                {mode === 'bottleneck' && (
                    <div>
                        <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
                            <span style={{ color: '#94a3b8', fontSize: '14px' }}>
                                Haritada bir noktaya tıklayarak dar boğaz ekleyin
                            </span>
                        </div>

                        {pendingBottleneck && (
                            <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
                                <input
                                    type="text"
                                    value={newBottleneckName}
                                    onChange={(e) => setNewBottleneckName(e.target.value)}
                                    placeholder="Dar boğaz adı (ör: Çıkış A)"
                                    className="form-input"
                                    style={{ flex: 1 }}
                                    autoFocus
                                />
                                <button className="btn btn-primary" onClick={addBottleneck}>
                                    Ekle
                                </button>
                                <button className="btn btn-secondary" onClick={() => setPendingBottleneck(null)}>
                                    İptal
                                </button>
                            </div>
                        )}

                        {bottlenecks.length > 0 && (
                            <div className="bottleneck-list" style={{ marginTop: '8px' }}>
                                {bottlenecks.map((bp, index) => (
                                    <div key={index} style={{
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        alignItems: 'center',
                                        padding: '4px 8px',
                                        background: 'rgba(239, 68, 68, 0.1)',
                                        borderRadius: '4px',
                                        marginBottom: '4px'
                                    }}>
                                        <span style={{ color: '#ef4444' }}>📍 {bp.name}</span>
                                        <button
                                            onClick={() => removeBottleneck(index)}
                                            style={{
                                                background: 'none',
                                                border: 'none',
                                                color: '#94a3b8',
                                                cursor: 'pointer'
                                            }}
                                        >
                                            ✕
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>

            <style jsx>{`
                .polygon-drawer {
                    background: var(--card-bg);
                    border-radius: 12px;
                    padding: 16px;
                }
                .canvas-container {
                    border-radius: 8px;
                    overflow: hidden;
                    border: 1px solid var(--border-color);
                }
            `}</style>
        </div>
    );
}
