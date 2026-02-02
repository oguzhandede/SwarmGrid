using TelemetryEntity = SwarmGrid.Domain.Entities.Telemetry;

namespace SwarmGrid.Application.Interfaces;

/// <summary>
/// Repository interface for Telemetry operations.
/// </summary>
public interface ITelemetryRepository
{
    /// <summary>
    /// Add a single telemetry record.
    /// </summary>
    Task<TelemetryEntity> AddAsync(TelemetryEntity telemetry, CancellationToken cancellationToken = default);
    
    /// <summary>
    /// Add multiple telemetry records in batch.
    /// </summary>
    Task<int> AddBatchAsync(IEnumerable<TelemetryEntity> telemetries, CancellationToken cancellationToken = default);
    
    /// <summary>
    /// Get recent telemetries for a zone.
    /// </summary>
    Task<List<TelemetryEntity>> GetRecentByZoneAsync(string zoneId, int limit = 100, CancellationToken cancellationToken = default);
    
    /// <summary>
    /// Get telemetries in a time range for a zone.
    /// </summary>
    Task<List<TelemetryEntity>> GetByTimeRangeAsync(string zoneId, DateTime startTime, DateTime endTime, CancellationToken cancellationToken = default);
}
