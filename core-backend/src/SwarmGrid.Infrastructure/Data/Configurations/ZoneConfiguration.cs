using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SwarmGrid.Domain.Entities;

namespace SwarmGrid.Infrastructure.Data.Configurations;

/// <summary>
/// EF Core configuration for Zone entity.
/// </summary>
public class ZoneConfiguration : IEntityTypeConfiguration<Zone>
{
    public void Configure(EntityTypeBuilder<Zone> builder)
    {
        builder.ToTable("Zones");
        
        builder.HasKey(z => z.Id);
        
        builder.Property(z => z.TenantId)
            .IsRequired()
            .HasMaxLength(50);
            
        builder.Property(z => z.SiteId)
            .IsRequired()
            .HasMaxLength(50);
            
        builder.Property(z => z.ZoneId)
            .IsRequired()
            .HasMaxLength(50);
            
        builder.Property(z => z.Name)
            .IsRequired()
            .HasMaxLength(200);
            
        builder.Property(z => z.Description)
            .HasMaxLength(1000);
            
        builder.Property(z => z.CameraId)
            .HasMaxLength(50);
            
        builder.Property(z => z.PolygonJson)
            .HasColumnType("jsonb");
            
        builder.Property(z => z.BottleneckPointsJson)
            .HasColumnType("jsonb");
            
        builder.Property(z => z.CameraIds)
            .HasConversion(
                v => string.Join(',', v),
                v => v.Split(',', StringSplitOptions.RemoveEmptyEntries).ToList()
            );
            
        // Indexes
        builder.HasIndex(z => new { z.TenantId, z.SiteId });
        builder.HasIndex(z => new { z.TenantId, z.SiteId, z.ZoneId }).IsUnique();
        builder.HasIndex(z => z.CameraId);
    }
}
