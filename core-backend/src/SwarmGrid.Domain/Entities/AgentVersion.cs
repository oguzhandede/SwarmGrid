namespace SwarmGrid.Domain.Entities;

/// <summary>
/// Agent version for OTA updates.
/// </summary>
public class AgentVersion : BaseEntity
{
    /// <summary>
    /// Semantic version (e.g., "1.2.0").
    /// </summary>
    public required string Version { get; set; }
    
    /// <summary>
    /// Release notes markdown.
    /// </summary>
    public required string ReleaseNotes { get; set; }
    
    /// <summary>
    /// Full package download URL.
    /// </summary>
    public string? DownloadUrl { get; set; }
    
    /// <summary>
    /// Config-only patch (JSON).
    /// </summary>
    public string? ConfigPatchJson { get; set; }
    
    /// <summary>
    /// SHA256 checksum of download package.
    /// </summary>
    public string? Checksum { get; set; }
    
    /// <summary>
    /// Minimum agent version required to update.
    /// </summary>
    public string? MinimumVersion { get; set; }
    
    /// <summary>
    /// Release timestamp.
    /// </summary>
    public DateTime ReleasedAt { get; set; }
    
    /// <summary>
    /// Whether this update is mandatory.
    /// </summary>
    public bool IsRequired { get; set; } = false;
    
    /// <summary>
    /// Whether this version is active/available.
    /// </summary>
    public bool IsActive { get; set; } = true;
    
    /// <summary>
    /// Target tenant ID (null = all tenants).
    /// </summary>
    public string? TargetTenantId { get; set; }
}
