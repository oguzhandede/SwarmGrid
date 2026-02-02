namespace SwarmGrid.Application.Zones;

using System.Text.Json.Serialization;

/// <summary>
/// Polygon point DTO.
/// </summary>
public record PolygonPointDto(
    [property: JsonPropertyName("x")] double X,
    [property: JsonPropertyName("y")] double Y
);

/// <summary>
/// Bottleneck point DTO with name.
/// </summary>
public record BottleneckPointDto(
    [property: JsonPropertyName("x")] double X,
    [property: JsonPropertyName("y")] double Y,
    [property: JsonPropertyName("name")] string Name
);

/// <summary>
/// Zone response DTO.
/// </summary>
public record ZoneDto(
    Guid Id,
    string TenantId,
    string SiteId,
    string ZoneId,
    string Name,
    string? Description,
    string? CameraId,
    List<PolygonPointDto>? Polygon,
    List<BottleneckPointDto>? BottleneckPoints,
    int MaxCapacity,
    double YellowThreshold,
    double RedThreshold,
    List<string> CameraIds,
    bool IsActive,
    DateTime CreatedAt,
    DateTime? UpdatedAt
);

/// <summary>
/// Create zone request DTO.
/// </summary>
public record CreateZoneDto(
    string TenantId,
    string SiteId,
    string ZoneId,
    string Name,
    string? Description = null,
    string? CameraId = null,
    List<PolygonPointDto>? Polygon = null,
    List<BottleneckPointDto>? BottleneckPoints = null,
    int MaxCapacity = 100,
    double YellowThreshold = 0.5,
    double RedThreshold = 0.75,
    List<string>? CameraIds = null
);

/// <summary>
/// Update zone request DTO.
/// </summary>
public record UpdateZoneDto(
    string? Name = null,
    string? Description = null,
    string? CameraId = null,
    List<PolygonPointDto>? Polygon = null,
    List<BottleneckPointDto>? BottleneckPoints = null,
    int? MaxCapacity = null,
    double? YellowThreshold = null,
    double? RedThreshold = null,
    List<string>? CameraIds = null,
    bool? IsActive = null
);

/// <summary>
/// Update polygon only request DTO.
/// </summary>
public record UpdatePolygonDto(
    List<PolygonPointDto> Polygon
);

/// <summary>
/// Update thresholds only request DTO.
/// </summary>
public record UpdateThresholdsDto(
    double YellowThreshold,
    double RedThreshold,
    int? MaxCapacity = null
);

/// <summary>
/// Update bottleneck points only request DTO.
/// </summary>
public record UpdateBottlenecksDto(
    List<BottleneckPointDto> BottleneckPoints
);
