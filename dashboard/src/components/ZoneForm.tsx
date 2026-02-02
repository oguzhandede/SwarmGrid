'use client';

import { useState, useEffect } from 'react';
import { Zone, Source } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

interface ZoneFormProps {
    zone?: Zone | null;
    sources?: Source[];
    onSubmit: (zone: Partial<Zone>) => void;
    onCancel: () => void;
}

export default function ZoneForm({ zone, sources = [], onSubmit, onCancel }: ZoneFormProps) {
    const [formData, setFormData] = useState({
        zoneId: '',
        name: '',
        description: '',
        cameraId: '',
        maxCapacity: 100,
        yellowThreshold: 0.5,
        redThreshold: 0.75
    });

    useEffect(() => {
        if (zone) {
            setFormData({
                zoneId: zone.zoneId,
                name: zone.name,
                description: zone.description || '',
                cameraId: zone.cameraId || '',
                maxCapacity: zone.maxCapacity,
                yellowThreshold: zone.yellowThreshold,
                redThreshold: zone.redThreshold
            });
        }
    }, [zone]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit({
            ...formData,
            tenantId: 'demo',
            siteId: 'site-01'
        });
    };

    return (
        <div className="zone-form-overlay">
            <div className="zone-form-modal">
                <div className="modal-header">
                    <h2>{zone ? 'Zone Düzenle' : 'Yeni Zone Oluştur'}</h2>
                    <button onClick={onCancel} className="close-btn">✕</button>
                </div>

                <form onSubmit={handleSubmit}>
                    <div className="form-grid">
                        <div className="form-group">
                            <label>Zone ID</label>
                            <input
                                type="text"
                                value={formData.zoneId}
                                onChange={(e) => setFormData({ ...formData, zoneId: e.target.value })}
                                placeholder="örn: entrance-main"
                                className="form-input"
                                required
                                disabled={!!zone}
                            />
                        </div>

                        <div className="form-group">
                            <label>Zone Adı</label>
                            <input
                                type="text"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                placeholder="örn: Ana Giriş"
                                className="form-input"
                                required
                            />
                        </div>

                        <div className="form-group full-width">
                            <label>Açıklama</label>
                            <textarea
                                value={formData.description}
                                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                placeholder="Zone hakkında detaylar..."
                                className="form-input"
                                rows={2}
                            />
                        </div>

                        <div className="form-group">
                            <label>İlişkili Kamera</label>
                            <select
                                value={formData.cameraId}
                                onChange={(e) => setFormData({ ...formData, cameraId: e.target.value })}
                                className="form-input"
                            >
                                <option value="">Kamera seçin</option>
                                {sources.map(source => (
                                    <option key={source.id} value={source.id}>
                                        {source.name}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="form-group">
                            <label>Maksimum Kapasite</label>
                            <input
                                type="number"
                                value={formData.maxCapacity}
                                onChange={(e) => setFormData({ ...formData, maxCapacity: parseInt(e.target.value) || 0 })}
                                min={1}
                                className="form-input"
                            />
                        </div>

                        <div className="form-group">
                            <label>Sarı Uyarı Eşiği ({Math.round(formData.yellowThreshold * 100)}%)</label>
                            <input
                                type="range"
                                value={formData.yellowThreshold}
                                onChange={(e) => setFormData({ ...formData, yellowThreshold: parseFloat(e.target.value) })}
                                min={0}
                                max={1}
                                step={0.05}
                                className="form-range"
                            />
                            <div className="threshold-preview yellow" style={{ width: `${formData.yellowThreshold * 100}%` }} />
                        </div>

                        <div className="form-group">
                            <label>Kırmızı Alarm Eşiği ({Math.round(formData.redThreshold * 100)}%)</label>
                            <input
                                type="range"
                                value={formData.redThreshold}
                                onChange={(e) => setFormData({ ...formData, redThreshold: parseFloat(e.target.value) })}
                                min={0}
                                max={1}
                                step={0.05}
                                className="form-range"
                            />
                            <div className="threshold-preview red" style={{ width: `${formData.redThreshold * 100}%` }} />
                        </div>
                    </div>

                    <div className="form-actions">
                        <button type="button" onClick={onCancel} className="btn btn-secondary">
                            İptal
                        </button>
                        <button type="submit" className="btn btn-primary">
                            {zone ? 'Güncelle' : 'Oluştur'}
                        </button>
                    </div>
                </form>
            </div>

            <style jsx>{`
                .zone-form-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.7);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                }
                .zone-form-modal {
                    background: var(--card-bg);
                    border-radius: 16px;
                    width: 100%;
                    max-width: 600px;
                    max-height: 90vh;
                    overflow-y: auto;
                    border: 1px solid var(--border-color);
                }
                .modal-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 20px 24px;
                    border-bottom: 1px solid var(--border-color);
                }
                .modal-header h2 {
                    margin: 0;
                    font-size: 18px;
                    color: #fff;
                }
                .close-btn {
                    background: none;
                    border: none;
                    color: #94a3b8;
                    font-size: 20px;
                    cursor: pointer;
                }
                .close-btn:hover {
                    color: #fff;
                }
                form {
                    padding: 24px;
                }
                .form-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 16px;
                }
                .form-group {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }
                .form-group.full-width {
                    grid-column: 1 / -1;
                }
                .form-group label {
                    color: #94a3b8;
                    font-size: 14px;
                }
                .form-range {
                    width: 100%;
                    height: 6px;
                    border-radius: 3px;
                    background: var(--border-color);
                    appearance: none;
                    cursor: pointer;
                }
                .form-range::-webkit-slider-thumb {
                    appearance: none;
                    width: 18px;
                    height: 18px;
                    border-radius: 50%;
                    background: var(--primary);
                    cursor: pointer;
                }
                .threshold-preview {
                    height: 4px;
                    border-radius: 2px;
                    margin-top: 4px;
                }
                .threshold-preview.yellow {
                    background: linear-gradient(90deg, #22c55e, #eab308);
                }
                .threshold-preview.red {
                    background: linear-gradient(90deg, #eab308, #ef4444);
                }
                .form-actions {
                    display: flex;
                    justify-content: flex-end;
                    gap: 12px;
                    margin-top: 24px;
                    padding-top: 20px;
                    border-top: 1px solid var(--border-color);
                }
            `}</style>
        </div>
    );
}
