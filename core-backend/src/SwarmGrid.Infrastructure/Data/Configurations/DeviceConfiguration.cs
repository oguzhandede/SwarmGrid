using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SwarmGrid.Domain.Entities;

namespace SwarmGrid.Infrastructure.Data.Configurations;

/// <summary>
/// EF Core configuration for Device entity.
/// </summary>
public class DeviceConfiguration : IEntityTypeConfiguration<Device>
{
    public void Configure(EntityTypeBuilder<Device> builder)
    {
        builder.ToTable("Devices");
        
        builder.HasKey(d => d.Id);
        
        builder.HasIndex(d => d.DeviceId)
            .IsUnique();
            
        builder.HasIndex(d => new { d.TenantId, d.SiteId });
        
        builder.HasIndex(d => d.CameraId);
        
        builder.Property(d => d.DeviceId)
            .IsRequired()
            .HasMaxLength(100);
            
        builder.Property(d => d.DeviceSecretHash)
            .IsRequired()
            .HasMaxLength(256);
            
        builder.Property(d => d.TenantId)
            .IsRequired()
            .HasMaxLength(100);
            
        builder.Property(d => d.SiteId)
            .IsRequired()
            .HasMaxLength(100);
            
        builder.Property(d => d.CameraId)
            .HasMaxLength(100);
            
        builder.Property(d => d.Name)
            .HasMaxLength(200);
            
        builder.Property(d => d.AgentVersion)
            .HasMaxLength(50);
            
        builder.Property(d => d.IpAddress)
            .HasMaxLength(50);
            
        builder.Property(d => d.Status)
            .HasConversion<string>()
            .HasMaxLength(20);
    }
}
