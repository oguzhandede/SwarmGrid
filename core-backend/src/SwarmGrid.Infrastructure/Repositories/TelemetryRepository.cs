using Microsoft.EntityFrameworkCore;
using SwarmGrid.Application.Interfaces;
using SwarmGrid.Domain.Entities;
using SwarmGrid.Infrastructure.Data;

namespace SwarmGrid.Infrastructure.Repositories;

/// <summary>
/// EF Core implementation of ITelemetryRepository.
/// </summary>
public class TelemetryRepository : ITelemetryRepository
{
    private readonly SwarmGridDbContext _context;
    
    public TelemetryRepository(SwarmGridDbContext context)
    {
        _context = context;
    }
    
    public async Task<Telemetry> AddAsync(Telemetry telemetry, CancellationToken cancellationToken = default)
    {
        _context.Telemetries.Add(telemetry);
        await _context.SaveChangesAsync(cancellationToken);
        return telemetry;
    }
    
    public async Task<int> AddBatchAsync(
        IEnumerable<Telemetry> telemetries, 
        CancellationToken cancellationToken = default)
    {
        _context.Telemetries.AddRange(telemetries);
        return await _context.SaveChangesAsync(cancellationToken);
    }
    
    public async Task<List<Telemetry>> GetRecentByZoneAsync(
        string zoneId, 
        int limit = 100, 
        CancellationToken cancellationToken = default)
    {
        return await _context.Telemetries
            .Where(t => t.ZoneId == zoneId)
            .OrderByDescending(t => t.Timestamp)
            .Take(limit)
            .ToListAsync(cancellationToken);
    }
    
    public async Task<List<Telemetry>> GetByTimeRangeAsync(
        string zoneId, 
        DateTime startTime, 
        DateTime endTime, 
        CancellationToken cancellationToken = default)
    {
        return await _context.Telemetries
            .Where(t => t.ZoneId == zoneId && t.Timestamp >= startTime && t.Timestamp <= endTime)
            .OrderBy(t => t.Timestamp)
            .ToListAsync(cancellationToken);
    }
}
