'use client';

import { useMemo, useState } from 'react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine,
} from 'recharts';
import { RiskEvent, RiskLevel } from '@/types';

interface RiskTimelineProps {
    riskEvents: RiskEvent[];
    maxDataPoints?: number;
}

interface ChartDataPoint {
    time: string;
    timestamp: number;
    score: number;
    zoneId: string;
    level: RiskLevel;
}

export default function RiskTimeline({ riskEvents, maxDataPoints = 30 }: RiskTimelineProps) {
    const [selectedZone, setSelectedZone] = useState<string>('all');

    // Get unique zones
    const zones = useMemo(() => {
        const uniqueZones = new Set(riskEvents.map(e => e.zoneId));
        return ['all', ...Array.from(uniqueZones)];
    }, [riskEvents]);

    // Transform events to chart data
    const chartData = useMemo(() => {
        let filtered = riskEvents;
        if (selectedZone !== 'all') {
            filtered = riskEvents.filter(e => e.zoneId === selectedZone);
        }

        const data: ChartDataPoint[] = filtered
            .slice(0, maxDataPoints)
            .reverse()
            .map(event => ({
                time: new Date(event.timestamp).toLocaleTimeString('tr-TR', {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                }),
                timestamp: new Date(event.timestamp).getTime(),
                score: Math.round(event.riskScore * 100),
                zoneId: event.zoneId,
                level: event.riskLevel,
            }));

        return data;
    }, [riskEvents, selectedZone, maxDataPoints]);

    // Custom tooltip
    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload as ChartDataPoint;
            const levelText = data.level === RiskLevel.Red ? 'Kritik' :
                data.level === RiskLevel.Yellow ? 'Dikkat' : 'Normal';
            const levelColor = data.level === RiskLevel.Red ? 'var(--danger)' :
                data.level === RiskLevel.Yellow ? 'var(--warning)' : 'var(--success)';

            return (
                <div className="chart-tooltip">
                    <div className="tooltip-time">{data.time}</div>
                    <div className="tooltip-score" style={{ color: levelColor }}>
                        {data.score}% - {levelText}
                    </div>
                    <div className="tooltip-zone">{data.zoneId}</div>
                </div>
            );
        }
        return null;
    };

    // Gradient definition for area fill
    const getGradientOffset = () => {
        if (chartData.length === 0) return { yellow: 0.5, red: 0.25 };
        const max = Math.max(...chartData.map(d => d.score));
        const min = Math.min(...chartData.map(d => d.score));

        if (max <= 0) return { yellow: 0, red: 0 };

        const yellowOffset = max > 50 ? 1 - (50 / max) : 1;
        const redOffset = max > 75 ? 1 - (75 / max) : 1;

        return { yellow: yellowOffset, red: redOffset };
    };

    const gradientOffset = getGradientOffset();

    return (
        <div className="timeline-container">
            <div className="timeline-header">
                <h3>Risk Trend Grafiği</h3>
                <select
                    value={selectedZone}
                    onChange={(e) => setSelectedZone(e.target.value)}
                    className="zone-selector"
                >
                    {zones.map(zone => (
                        <option key={zone} value={zone}>
                            {zone === 'all' ? 'Tüm Zoneler' : zone}
                        </option>
                    ))}
                </select>
            </div>

            <div className="chart-wrapper">
                {chartData.length === 0 ? (
                    <div className="chart-empty">
                        Henüz veri yok. Telemetri bekleniyor...
                    </div>
                ) : (
                    <ResponsiveContainer width="100%" height={250}>
                        <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                            <defs>
                                <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="var(--danger)" stopOpacity={0.8} />
                                    <stop offset={`${gradientOffset.red * 100}%`} stopColor="var(--danger)" stopOpacity={0.6} />
                                    <stop offset={`${gradientOffset.yellow * 100}%`} stopColor="var(--warning)" stopOpacity={0.4} />
                                    <stop offset="100%" stopColor="var(--success)" stopOpacity={0.2} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                            <XAxis
                                dataKey="time"
                                tick={{ fill: '#94a3b8', fontSize: 11 }}
                                axisLine={{ stroke: 'rgba(255,255,255,0.2)' }}
                            />
                            <YAxis
                                domain={[0, 100]}
                                tick={{ fill: '#94a3b8', fontSize: 11 }}
                                axisLine={{ stroke: 'rgba(255,255,255,0.2)' }}
                                tickFormatter={(value) => `${value}%`}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            <ReferenceLine
                                y={75}
                                stroke="var(--danger)"
                                strokeDasharray="5 5"
                                strokeWidth={1}
                                label={{ value: 'Kritik', fill: 'var(--danger)', fontSize: 10, position: 'right' }}
                            />
                            <ReferenceLine
                                y={50}
                                stroke="var(--warning)"
                                strokeDasharray="5 5"
                                strokeWidth={1}
                                label={{ value: 'Dikkat', fill: 'var(--warning)', fontSize: 10, position: 'right' }}
                            />
                            <Area
                                type="monotone"
                                dataKey="score"
                                stroke="var(--primary)"
                                strokeWidth={2}
                                fill="url(#riskGradient)"
                                animationDuration={500}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                )}
            </div>
        </div>
    );
}
