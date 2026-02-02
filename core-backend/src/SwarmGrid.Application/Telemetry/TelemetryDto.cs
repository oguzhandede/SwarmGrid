namespace SwarmGrid.Application.Telemetry;

/// <summary>
/// DTO for incoming telemetry from Edge Agent.
/// </summary>
public record TelemetryDto(
    string TenantId,
    string SiteId,
    string CameraId,
    string ZoneId,
    DateTime Timestamp,
    double Density,
    double AvgSpeed,
    double SpeedVariance,
    double FlowEntropy,
    double Alignment,
    double BottleneckIndex
);
