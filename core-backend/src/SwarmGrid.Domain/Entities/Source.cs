using SwarmGrid.Domain.Enums;

namespace SwarmGrid.Domain.Entities;

/// <summary>
/// Represents a video or camera source for analysis.
/// </summary>
public class Source
{
    public string Id { get; set; } = Guid.NewGuid().ToString();
    public string TenantId { get; set; } = string.Empty;
    public string SiteId { get; set; } = string.Empty;
    public SourceType Type { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Url { get; set; } = string.Empty;  // File path or RTSP URL
    public SourceStatus Status { get; set; } = SourceStatus.Pending;
    public double Progress { get; set; }  // 0-100 for video files
    public string ZoneId { get; set; } = string.Empty;
    public string? ErrorMessage { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime? StartedAt { get; set; }
    public DateTime? CompletedAt { get; set; }
}
