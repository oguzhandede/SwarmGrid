using Microsoft.EntityFrameworkCore;
using SwarmGrid.Domain.Entities;

namespace SwarmGrid.Infrastructure.Data;

/// <summary>
/// Main DbContext for SwarmGrid application.
/// </summary>
public class SwarmGridDbContext : DbContext
{
    public SwarmGridDbContext(DbContextOptions<SwarmGridDbContext> options) 
        : base(options)
    {
    }
    
    public DbSet<RiskEvent> RiskEvents => Set<RiskEvent>();
    public DbSet<Telemetry> Telemetries => Set<Telemetry>();
    public DbSet<Source> Sources => Set<Source>();
    public DbSet<Zone> Zones => Set<Zone>();
    public DbSet<Device> Devices => Set<Device>();
    public DbSet<AgentVersion> AgentVersions => Set<AgentVersion>();
    
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);
        
        // Apply all configurations from this assembly
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(SwarmGridDbContext).Assembly);
    }
}
