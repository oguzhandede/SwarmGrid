using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SwarmGrid.Domain.Entities;

namespace SwarmGrid.Infrastructure.Data.Configurations;

/// <summary>
/// EF Core configuration for Telemetry entity.
/// </summary>
public class TelemetryConfiguration : IEntityTypeConfiguration<Telemetry>
{
    public void Configure(EntityTypeBuilder<Telemetry> builder)
    {
        builder.ToTable("telemetries");
        
        builder.HasKey(e => e.Id);
        
        builder.Property(e => e.Id)
            .HasColumnName("id");
            
        builder.Property(e => e.TenantId)
            .HasColumnName("tenant_id")
            .HasMaxLength(100)
            .IsRequired();
            
        builder.Property(e => e.SiteId)
            .HasColumnName("site_id")
            .HasMaxLength(100)
            .IsRequired();
            
        builder.Property(e => e.CameraId)
            .HasColumnName("camera_id")
            .HasMaxLength(100)
            .IsRequired();
            
        builder.Property(e => e.ZoneId)
            .HasColumnName("zone_id")
            .HasMaxLength(100)
            .IsRequired();
            
        builder.Property(e => e.Timestamp)
            .HasColumnName("timestamp");
            
        // Feature columns
        builder.Property(e => e.Density)
            .HasColumnName("density");
            
        builder.Property(e => e.AvgSpeed)
            .HasColumnName("avg_speed");
            
        builder.Property(e => e.SpeedVariance)
            .HasColumnName("speed_variance");
            
        builder.Property(e => e.FlowEntropy)
            .HasColumnName("flow_entropy");
            
        builder.Property(e => e.Alignment)
            .HasColumnName("alignment");
            
        builder.Property(e => e.BottleneckIndex)
            .HasColumnName("bottleneck_index");
            
        builder.Property(e => e.ReceivedAt)
            .HasColumnName("received_at")
            .HasDefaultValueSql("CURRENT_TIMESTAMP");
            
        // Indexes for time-series queries
        builder.HasIndex(e => e.Timestamp)
            .HasDatabaseName("ix_telemetries_timestamp");
            
        builder.HasIndex(e => e.ZoneId)
            .HasDatabaseName("ix_telemetries_zone_id");
            
        builder.HasIndex(e => new { e.ZoneId, e.Timestamp })
            .HasDatabaseName("ix_telemetries_zone_timestamp");
    }
}
