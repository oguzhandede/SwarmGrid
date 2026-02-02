namespace SwarmGrid.Domain.Entities;

/// <summary>
/// Zone definition within a site.
/// </summary>
public class Zone : BaseEntity
{
    public required string TenantId { get; set; }
    public required string SiteId { get; set; }
    public required string ZoneId { get; set; }
    public required string Name { get; set; }
    
    /// <summary>
    /// Zone description
    /// </summary>
    public string? Description { get; set; }
    
    /// <summary>
    /// Primary camera ID for polygon drawing
    /// </summary>
    public string? CameraId { get; set; }
    
    /// <summary>
    /// Polygon points (JSON serialized array of {x, y})
    /// </summary>
    public string? PolygonJson { get; set; }
    
    /// <summary>
    /// Bottleneck points (JSON serialized array of {x, y, name})
    /// </summary>
    public string? BottleneckPointsJson { get; set; }
    
    /// <summary>
    /// Maximum capacity for this zone
    /// </summary>
    public int MaxCapacity { get; set; }
    
    /// <summary>
    /// Yellow (warning) risk threshold (0-1)
    /// </summary>
    public double YellowThreshold { get; set; } = 0.5;
    
    /// <summary>
    /// Red (critical) risk threshold (0-1)
    /// </summary>
    public double RedThreshold { get; set; } = 0.75;
    
    /// <summary>
    /// Associated camera IDs (for multi-camera zones)
    /// </summary>
    public List<string> CameraIds { get; set; } = [];
    
    /// <summary>
    /// Whether this zone is active
    /// </summary>
    public bool IsActive { get; set; } = true;
}
