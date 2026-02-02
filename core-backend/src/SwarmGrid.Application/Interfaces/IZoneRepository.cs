namespace SwarmGrid.Application.Interfaces;

using SwarmGrid.Domain.Entities;

/// <summary>
/// Repository interface for Zone operations.
/// </summary>
public interface IZoneRepository
{
    /// <summary>
    /// Get all zones for a tenant.
    /// </summary>
    Task<IEnumerable<Zone>> GetAllAsync(string tenantId);
    
    /// <summary>
    /// Get all zones for a site.
    /// </summary>
    Task<IEnumerable<Zone>> GetBySiteAsync(string tenantId, string siteId);
    
    /// <summary>
    /// Get all zones for a camera.
    /// </summary>
    Task<IEnumerable<Zone>> GetByCameraAsync(string cameraId);
    
    /// <summary>
    /// Get zone by ID.
    /// </summary>
    Task<Zone?> GetByIdAsync(Guid id);
    
    /// <summary>
    /// Get zone by ZoneId string.
    /// </summary>
    Task<Zone?> GetByZoneIdAsync(string tenantId, string siteId, string zoneId);
    
    /// <summary>
    /// Add a new zone.
    /// </summary>
    Task<Zone> AddAsync(Zone zone);
    
    /// <summary>
    /// Update an existing zone.
    /// </summary>
    Task UpdateAsync(Zone zone);
    
    /// <summary>
    /// Delete a zone.
    /// </summary>
    Task DeleteAsync(Guid id);
}
