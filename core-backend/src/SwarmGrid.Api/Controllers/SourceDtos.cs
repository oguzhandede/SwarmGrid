using SwarmGrid.Domain.Enums;

namespace SwarmGrid.Api.Controllers;

/// <summary>
/// DTO for video upload configuration.
/// </summary>
public record VideoUploadConfig(
    string TenantId,
    string SiteId,
    string ZoneId,
    string Name
);

/// <summary>
/// DTO for camera registration.
/// </summary>
public record CameraConfig(
    string TenantId,
    string SiteId,
    string ZoneId,
    string Name,
    string RtspUrl
);

/// <summary>
/// DTO for source response.
/// </summary>
public record SourceDto(
    string Id,
    string TenantId,
    string SiteId,
    SourceType Type,
    string Name,
    string Url,
    SourceStatus Status,
    double Progress,
    string ZoneId,
    string? ErrorMessage,
    DateTime CreatedAt,
    DateTime? StartedAt,
    DateTime? CompletedAt
);

/// <summary>
/// DTO for analysis progress update (via SignalR).
/// </summary>
public record SourceProgressDto(
    string SourceId,
    SourceStatus Status,
    double Progress,
    string? Message
);
