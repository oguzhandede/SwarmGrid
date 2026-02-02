using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SwarmGrid.Domain.Entities;

namespace SwarmGrid.Infrastructure.Data.Configurations;

/// <summary>
/// EF Core configuration for Source entity.
/// </summary>
public class SourceConfiguration : IEntityTypeConfiguration<Source>
{
    public void Configure(EntityTypeBuilder<Source> builder)
    {
        builder.ToTable("sources");
        
        builder.HasKey(e => e.Id);
        
        builder.Property(e => e.Id)
            .HasColumnName("id")
            .HasMaxLength(100);
            
        builder.Property(e => e.TenantId)
            .HasColumnName("tenant_id")
            .HasMaxLength(100);
            
        builder.Property(e => e.SiteId)
            .HasColumnName("site_id")
            .HasMaxLength(100);
            
        builder.Property(e => e.Type)
            .HasColumnName("type")
            .HasConversion<string>()
            .HasMaxLength(20);
            
        builder.Property(e => e.Name)
            .HasColumnName("name")
            .HasMaxLength(200);
            
        builder.Property(e => e.Url)
            .HasColumnName("url")
            .HasMaxLength(500);
            
        builder.Property(e => e.Status)
            .HasColumnName("status")
            .HasConversion<string>()
            .HasMaxLength(20);
            
        builder.Property(e => e.Progress)
            .HasColumnName("progress");
            
        builder.Property(e => e.ZoneId)
            .HasColumnName("zone_id")
            .HasMaxLength(100);
            
        builder.Property(e => e.ErrorMessage)
            .HasColumnName("error_message")
            .HasMaxLength(1000);
            
        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .HasDefaultValueSql("CURRENT_TIMESTAMP");
            
        builder.Property(e => e.StartedAt)
            .HasColumnName("started_at");
            
        builder.Property(e => e.CompletedAt)
            .HasColumnName("completed_at");
            
        // Indexes
        builder.HasIndex(e => e.TenantId)
            .HasDatabaseName("ix_sources_tenant_id");
            
        builder.HasIndex(e => e.Status)
            .HasDatabaseName("ix_sources_status");
    }
}
