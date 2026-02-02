using SwarmGrid.Domain.Enums;

namespace SwarmGrid.Application.RiskEngine;

/// <summary>
/// DTO for risk event output.
/// </summary>
public record RiskEventDto(
    Guid Id,
    string TenantId,
    string SiteId,
    string CameraId,
    string ZoneId,
    DateTime Timestamp,
    double RiskScore,
    RiskLevel RiskLevel,
    List<string> SuggestedActions,
    bool Acknowledged
);
