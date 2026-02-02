namespace SwarmGrid.Application.Caching;

/// <summary>
/// Interface for caching risk scores with time-based sliding window.
/// </summary>
public interface IRiskScoreCache
{
    /// <summary>
    /// Add a risk score for a zone with timestamp.
    /// </summary>
    Task AddScoreAsync(string zoneId, double score, DateTime timestamp);
    
    /// <summary>
    /// Get recent scores within the specified time window.
    /// </summary>
    Task<List<(double Score, DateTime Timestamp)>> GetRecentScoresAsync(string zoneId, TimeSpan window);
    
    /// <summary>
    /// Calculate trend factor from recent scores.
    /// Positive = increasing risk, Negative = decreasing risk.
    /// </summary>
    Task<double> CalculateTrendAsync(string zoneId, TimeSpan window);
}
