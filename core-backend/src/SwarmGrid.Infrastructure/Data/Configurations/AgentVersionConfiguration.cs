using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SwarmGrid.Domain.Entities;

namespace SwarmGrid.Infrastructure.Data.Configurations;

/// <summary>
/// EF Core configuration for AgentVersion entity.
/// </summary>
public class AgentVersionConfiguration : IEntityTypeConfiguration<AgentVersion>
{
    public void Configure(EntityTypeBuilder<AgentVersion> builder)
    {
        builder.ToTable("AgentVersions");
        
        builder.HasKey(v => v.Id);
        
        builder.HasIndex(v => v.Version)
            .IsUnique();
            
        builder.HasIndex(v => v.IsActive);
        
        builder.Property(v => v.Version)
            .IsRequired()
            .HasMaxLength(50);
            
        builder.Property(v => v.ReleaseNotes)
            .IsRequired();
            
        builder.Property(v => v.DownloadUrl)
            .HasMaxLength(500);
            
        builder.Property(v => v.Checksum)
            .HasMaxLength(100);
            
        builder.Property(v => v.MinimumVersion)
            .HasMaxLength(50);
            
        builder.Property(v => v.TargetTenantId)
            .HasMaxLength(100);
    }
}
