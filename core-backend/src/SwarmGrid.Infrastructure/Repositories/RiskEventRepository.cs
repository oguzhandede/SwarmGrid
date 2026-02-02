using Microsoft.EntityFrameworkCore;
using SwarmGrid.Application.Interfaces;
using SwarmGrid.Domain.Entities;
using SwarmGrid.Infrastructure.Data;

namespace SwarmGrid.Infrastructure.Repositories;

/// <summary>
/// EF Core implementation of IRiskEventRepository.
/// </summary>
public class RiskEventRepository : IRiskEventRepository
{
    private readonly SwarmGridDbContext _context;
    
    public RiskEventRepository(SwarmGridDbContext context)
    {
        _context = context;
    }
    
    public async Task<List<RiskEvent>> GetRecentBySiteAsync(
        string siteId, 
        int limit = 50, 
        CancellationToken cancellationToken = default)
    {
        return await _context.RiskEvents
            .Where(e => e.SiteId == siteId)
            .OrderByDescending(e => e.CreatedAt)
            .Take(limit)
            .ToListAsync(cancellationToken);
    }
    
    public async Task<List<RiskEvent>> GetRecentByZoneAsync(
        string zoneId, 
        int limit = 50, 
        CancellationToken cancellationToken = default)
    {
        return await _context.RiskEvents
            .Where(e => e.ZoneId == zoneId)
            .OrderByDescending(e => e.CreatedAt)
            .Take(limit)
            .ToListAsync(cancellationToken);
    }
    
    public async Task<RiskEvent?> GetByIdAsync(Guid id, CancellationToken cancellationToken = default)
    {
        return await _context.RiskEvents
            .FirstOrDefaultAsync(e => e.Id == id, cancellationToken);
    }
    
    public async Task<RiskEvent> AddAsync(RiskEvent riskEvent, CancellationToken cancellationToken = default)
    {
        _context.RiskEvents.Add(riskEvent);
        await _context.SaveChangesAsync(cancellationToken);
        return riskEvent;
    }
    
    public async Task<RiskEvent?> AcknowledgeAsync(
        Guid eventId, 
        string userId, 
        string? note = null, 
        CancellationToken cancellationToken = default)
    {
        var riskEvent = await _context.RiskEvents
            .FirstOrDefaultAsync(e => e.Id == eventId, cancellationToken);
            
        if (riskEvent == null)
            return null;
            
        riskEvent.Acknowledged = true;
        riskEvent.AcknowledgedBy = userId;
        riskEvent.AcknowledgedAt = DateTime.UtcNow;
        riskEvent.UpdatedAt = DateTime.UtcNow;
        
        // Note is not stored in current entity, but could be added
        // For now we just log it via the caller
        
        await _context.SaveChangesAsync(cancellationToken);
        return riskEvent;
    }
    
    public async Task AddBatchAsync(IEnumerable<RiskEvent> riskEvents, CancellationToken cancellationToken = default)
    {
        await _context.RiskEvents.AddRangeAsync(riskEvents, cancellationToken);
        await _context.SaveChangesAsync(cancellationToken);
    }
}
