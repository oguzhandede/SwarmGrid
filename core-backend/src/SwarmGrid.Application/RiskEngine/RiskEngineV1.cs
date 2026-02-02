using System.Collections.Concurrent;
using TelemetryEntity = SwarmGrid.Domain.Entities.Telemetry;
using SwarmGrid.Domain.Entities;
using SwarmGrid.Domain.Enums;
using SwarmGrid.Application.Caching;

namespace SwarmGrid.Application.RiskEngine;

/// <summary>
/// V1 Risk Engine - Rule + Trend based scoring with Redis-backed sliding window.
/// </summary>
public class RiskEngineV1
{
    private readonly IRiskScoreCache? _cache;
    private readonly TimeSpan _windowSize = TimeSpan.FromMinutes(5);
    
    // In-memory fallback for when Redis is not available
    // Uses ConcurrentDictionary for thread safety and bounded size
    private readonly ConcurrentDictionary<string, BoundedQueue<double>> _recentScores = new();
    private const int FallbackWindowSize = 10;
    private const int MaxZonesCached = 100; // Prevent unbounded growth
    
    public RiskEngineV1() { }
    
    public RiskEngineV1(IRiskScoreCache cache)
    {
        _cache = cache;
    }
    
    /// <summary>
    /// Calculate risk score from telemetry data (async version with Redis).
    /// </summary>
    public async Task<RiskEvent> CalculateRiskAsync(TelemetryEntity telemetry, Zone? zone = null)
    {
        // Rule-based scoring
        var rawScore = CalculateRawScore(telemetry);
        
        // Apply trend factor from Redis cache
        double trendFactor = 0;
        if (_cache != null)
        {
            // Store current score in Redis
            await _cache.AddScoreAsync(telemetry.ZoneId, rawScore, DateTime.UtcNow);
            
            // Get trend from Redis
            trendFactor = await _cache.CalculateTrendAsync(telemetry.ZoneId, _windowSize);
        }
        else
        {
            // Fallback to in-memory
            trendFactor = CalculateTrendFactorInMemory(telemetry.ZoneId, rawScore);
        }
        
        var finalScore = Math.Min(1.0, rawScore * (1.0 + trendFactor * 0.3));
        
        // Determine risk level
        var riskLevel = DetermineRiskLevel(finalScore, zone);
        
        // Generate suggested actions
        var actions = GenerateSuggestedActions(telemetry, riskLevel);
        
        return new RiskEvent
        {
            TenantId = telemetry.TenantId,
            SiteId = telemetry.SiteId,
            CameraId = telemetry.CameraId,
            ZoneId = telemetry.ZoneId,
            RiskScore = Math.Round(finalScore, 4),
            RiskLevel = riskLevel,
            SuggestedActions = actions,
            SourceTelemetryId = telemetry.Id
        };
    }
    
    /// <summary>
    /// Sync version for backward compatibility (uses in-memory fallback).
    /// </summary>
    public RiskEvent CalculateRisk(TelemetryEntity telemetry, Zone? zone = null)
    {
        var rawScore = CalculateRawScore(telemetry);
        var trendFactor = CalculateTrendFactorInMemory(telemetry.ZoneId, rawScore);
        var finalScore = Math.Min(1.0, rawScore * (1.0 + trendFactor * 0.3));
        var riskLevel = DetermineRiskLevel(finalScore, zone);
        var actions = GenerateSuggestedActions(telemetry, riskLevel);
        
        return new RiskEvent
        {
            TenantId = telemetry.TenantId,
            SiteId = telemetry.SiteId,
            CameraId = telemetry.CameraId,
            ZoneId = telemetry.ZoneId,
            RiskScore = Math.Round(finalScore, 4),
            RiskLevel = riskLevel,
            SuggestedActions = actions,
            SourceTelemetryId = telemetry.Id
        };
    }
    
    private static double CalculateRawScore(TelemetryEntity telemetry)
    {
        var densityScore = telemetry.Density;
        var entropyScore = telemetry.FlowEntropy;
        var alignmentScore = 1.0 - telemetry.Alignment;
        var bottleneckScore = telemetry.BottleneckIndex;
        
        return densityScore * 0.35 +
               entropyScore * 0.25 +
               alignmentScore * 0.20 +
               bottleneckScore * 0.20;
    }
    
    private static RiskLevel DetermineRiskLevel(double score, Zone? zone)
    {
        var yellowThreshold = zone?.YellowThreshold ?? 0.5;
        var redThreshold = zone?.RedThreshold ?? 0.75;
        
        return score switch
        {
            var s when s >= redThreshold => RiskLevel.Red,
            var s when s >= yellowThreshold => RiskLevel.Yellow,
            _ => RiskLevel.Green
        };
    }
    
    private double CalculateTrendFactorInMemory(string zoneId, double currentScore)
    {
        // Ensure we don't exceed max cached zones (LRU-like cleanup)
        if (_recentScores.Count >= MaxZonesCached && !_recentScores.ContainsKey(zoneId))
        {
            // Remove oldest zone entry when at capacity
            var oldestKey = _recentScores.Keys.FirstOrDefault();
            if (oldestKey != null)
            {
                _recentScores.TryRemove(oldestKey, out _);
            }
        }
        
        var scores = _recentScores.GetOrAdd(zoneId, _ => new BoundedQueue<double>(FallbackWindowSize));
        scores.Enqueue(currentScore);
        
        var scoreList = scores.ToList();
        if (scoreList.Count < 2)
            return 0;
            
        var oldAvg = scoreList.Take(scoreList.Count / 2).Average();
        var newAvg = scoreList.Skip(scoreList.Count / 2).Average();
        
        return newAvg - oldAvg;
    }
    
    private static List<string> GenerateSuggestedActions(TelemetryEntity telemetry, RiskLevel level)
    {
        var actions = new List<string>();
        
        if (level == RiskLevel.Green)
            return actions;
            
        if (telemetry.Density > 0.7)
        {
            actions.Add($"{telemetry.ZoneId} bölgesine güvenlik personeli yönlendir");
            actions.Add("Alternatif çıkışları yönlendirme ekranlarında göster");
        }
        
        if (telemetry.BottleneckIndex > 0.6)
        {
            actions.Add("Dar boğaz noktasında bariyer aç");
            actions.Add("Giriş kapılarında bekleme süresi uygula");
        }
        
        if (telemetry.FlowEntropy > 0.7)
        {
            actions.Add("Yönlendirme anonsları yap");
            actions.Add("LED işaretleri aktif et");
        }
        
        if (level == RiskLevel.Red && actions.Count == 0)
        {
            actions.Add("Acil müdahale ekibini uyar");
            actions.Add("Bölgeyi izole et");
        }
        
        return actions;
    }
}

