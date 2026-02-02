using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using SwarmGrid.Application.Interfaces;
using SwarmGrid.Infrastructure.Data;
using SwarmGrid.Infrastructure.Repositories;

namespace SwarmGrid.Infrastructure;

/// <summary>
/// Infrastructure service registration extension.
/// </summary>
public static class DependencyInjection
{
    /// <summary>
    /// Add infrastructure services including DbContext and repositories.
    /// </summary>
    public static IServiceCollection AddInfrastructure(
        this IServiceCollection services, 
        string connectionString)
    {
        // Register DbContext with PostgreSQL
        services.AddDbContext<SwarmGridDbContext>(options =>
            options.UseNpgsql(connectionString, npgsqlOptions =>
            {
                npgsqlOptions.EnableRetryOnFailure(
                    maxRetryCount: 3,
                    maxRetryDelay: TimeSpan.FromSeconds(5),
                    errorCodesToAdd: null);
            }));
        
        // Register repositories
        services.AddScoped<IRiskEventRepository, RiskEventRepository>();
        services.AddScoped<ITelemetryRepository, TelemetryRepository>();
        services.AddScoped<IZoneRepository, ZoneRepository>();
        
        return services;
    }
}
