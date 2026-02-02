using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SwarmGrid.Domain.Entities;
using System.Text.Json;

namespace SwarmGrid.Infrastructure.Data.Configurations;

/// <summary>
/// EF Core configuration for RiskEvent entity.
/// </summary>
public class RiskEventConfiguration : IEntityTypeConfiguration<RiskEvent>
{
    public void Configure(EntityTypeBuilder<RiskEvent> builder)
    {
        builder.ToTable("risk_events");
        
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
            
        builder.Property(e => e.RiskScore)
            .HasColumnName("risk_score");
            
        builder.Property(e => e.RiskLevel)
            .HasColumnName("risk_level")
            .HasConversion<string>()
            .HasMaxLength(20);
            
        // Store SuggestedActions as JSON with explicit converter
        builder.Property(e => e.SuggestedActions)
            .HasColumnName("suggested_actions")
            .HasColumnType("jsonb")
            .HasConversion(
                v => JsonSerializer.Serialize(v, (JsonSerializerOptions?)null),
                v => JsonSerializer.Deserialize<List<string>>(v, (JsonSerializerOptions?)null) ?? new List<string>()
            );
            
        builder.Property(e => e.Acknowledged)
            .HasColumnName("acknowledged")
            .HasDefaultValue(false);
            
        builder.Property(e => e.AcknowledgedBy)
            .HasColumnName("acknowledged_by")
            .HasMaxLength(100);
            
        builder.Property(e => e.AcknowledgedAt)
            .HasColumnName("acknowledged_at");
            
        builder.Property(e => e.SourceTelemetryId)
            .HasColumnName("source_telemetry_id");
            
        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .HasDefaultValueSql("CURRENT_TIMESTAMP");
            
        builder.Property(e => e.UpdatedAt)
            .HasColumnName("updated_at");
            
        // Indexes for common queries
        builder.HasIndex(e => e.SiteId)
            .HasDatabaseName("ix_risk_events_site_id");
            
        builder.HasIndex(e => e.ZoneId)
            .HasDatabaseName("ix_risk_events_zone_id");
            
        builder.HasIndex(e => e.CreatedAt)
            .HasDatabaseName("ix_risk_events_created_at");
            
        builder.HasIndex(e => new { e.SiteId, e.CreatedAt })
            .HasDatabaseName("ix_risk_events_site_created");
    }
}
