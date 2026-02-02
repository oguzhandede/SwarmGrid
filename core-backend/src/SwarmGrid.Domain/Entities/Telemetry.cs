namespace SwarmGrid.Domain.Entities;

/// <summary>
/// Telemetry data from Edge Agent.
/// </summary>
public class Telemetry
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public required string TenantId { get; set; }
    public required string SiteId { get; set; }
    public required string CameraId { get; set; }
    public required string ZoneId { get; set; }
    public DateTime Timestamp { get; set; }
    
    // Features
    public double Density { get; set; }
    public double AvgSpeed { get; set; }
    public double SpeedVariance { get; set; }
    public double FlowEntropy { get; set; }
    public double Alignment { get; set; }
    public double BottleneckIndex { get; set; }
    
    public DateTime ReceivedAt { get; set; } = DateTime.UtcNow;
}
