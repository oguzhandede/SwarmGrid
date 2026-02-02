using System.Text.Json;
using StackExchange.Redis;
using SwarmGrid.Application.Caching;

namespace SwarmGrid.Infrastructure.Caching;

/// <summary>
/// Redis-based implementation of risk score cache using Sorted Sets.
/// </summary>
public class RedisRiskScoreCache : IRiskScoreCache
{
    private readonly IDatabase _db;
    private readonly TimeSpan _defaultTtl = TimeSpan.FromMinutes(10);
    
    public RedisRiskScoreCache(IConnectionMultiplexer redis)
    {
        _db = redis.GetDatabase();
    }
    
    private static string GetKey(string zoneId) => $"risk:scores:{zoneId}";
    
    public async Task AddScoreAsync(string zoneId, double score, DateTime timestamp)
    {
        var key = GetKey(zoneId);
        var unixMs = new DateTimeOffset(timestamp.ToUniversalTime()).ToUnixTimeMilliseconds();
        
        var entry = new ScoreEntry(score, timestamp.ToUniversalTime());
        var json = JsonSerializer.Serialize(entry);
        
        // Add to sorted set with timestamp as score
        await _db.SortedSetAddAsync(key, json, unixMs);
        
        // Set TTL to auto-expire old data
        await _db.KeyExpireAsync(key, _defaultTtl);
        
        // Clean up entries older than window
        var cutoff = DateTimeOffset.UtcNow.AddMinutes(-10).ToUnixTimeMilliseconds();
        await _db.SortedSetRemoveRangeByScoreAsync(key, double.NegativeInfinity, cutoff);
    }
    
    public async Task<List<(double Score, DateTime Timestamp)>> GetRecentScoresAsync(string zoneId, TimeSpan window)
    {
        var key = GetKey(zoneId);
        var cutoff = DateTimeOffset.UtcNow.Add(-window).ToUnixTimeMilliseconds();
        var now = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
        
        var entries = await _db.SortedSetRangeByScoreAsync(key, cutoff, now);
        var result = new List<(double, DateTime)>();
        
        foreach (var entry in entries)
        {
            try
            {
                var data = JsonSerializer.Deserialize<ScoreEntry>(entry!);
                if (data != null)
                {
                    result.Add((data.Score, data.Timestamp));
                }
            }
            catch
            {
                // Skip malformed entries
            }
        }
        
        return result;
    }
    
    public async Task<double> CalculateTrendAsync(string zoneId, TimeSpan window)
    {
        var scores = await GetRecentScoresAsync(zoneId, window);
        
        if (scores.Count < 2)
            return 0;
        
        // Sort by timestamp
        scores = scores.OrderBy(s => s.Timestamp).ToList();
        
        // Calculate trend: compare first half average to second half average
        var midpoint = scores.Count / 2;
        var oldAvg = scores.Take(midpoint).Average(s => s.Score);
        var newAvg = scores.Skip(midpoint).Average(s => s.Score);
        
        return newAvg - oldAvg;
    }
    
    private record ScoreEntry(double Score, DateTime Timestamp);
}
