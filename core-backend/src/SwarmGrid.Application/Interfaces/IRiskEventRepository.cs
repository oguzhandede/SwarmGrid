using SwarmGrid.Domain.Entities;

namespace SwarmGrid.Application.Interfaces;

/// <summary>
/// Repository interface for RiskEvent operations.
/// </summary>
public interface IRiskEventRepository
{
    /// <summary>
    /// Get recent risk events for a site.
    /// </summary>
    Task<List<RiskEvent>> GetRecentBySiteAsync(string siteId, int limit = 50, CancellationToken cancellationToken = default);
    
    /// <summary>
    /// Get recent risk events for a zone.
    /// </summary>
    Task<List<RiskEvent>> GetRecentByZoneAsync(string zoneId, int limit = 50, CancellationToken cancellationToken = default);
    
    /// <summary>
    /// Get a risk event by ID.
    /// </summary>
    Task<RiskEvent?> GetByIdAsync(Guid id, CancellationToken cancellationToken = default);
    
    /// <summary>
    /// Add a new risk event.
    /// </summary>
    Task<RiskEvent> AddAsync(RiskEvent riskEvent, CancellationToken cancellationToken = default);
    
    /// <summary>
    /// Acknowledge a risk event.
    /// </summary>
    Task<RiskEvent?> AcknowledgeAsync(Guid eventId, string userId, string? note = null, CancellationToken cancellationToken = default);
    
    /// <summary>
    /// Add multiple risk events in batch.
    /// </summary>
    Task AddBatchAsync(IEnumerable<RiskEvent> riskEvents, CancellationToken cancellationToken = default);
}
