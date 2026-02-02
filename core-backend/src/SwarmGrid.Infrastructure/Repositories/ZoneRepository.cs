using Microsoft.EntityFrameworkCore;
using SwarmGrid.Application.Interfaces;
using SwarmGrid.Domain.Entities;
using SwarmGrid.Infrastructure.Data;

namespace SwarmGrid.Infrastructure.Repositories;

/// <summary>
/// Zone repository implementation.
/// </summary>
public class ZoneRepository : IZoneRepository
{
    private readonly SwarmGridDbContext _context;
    
    public ZoneRepository(SwarmGridDbContext context)
    {
        _context = context;
    }
    
    public async Task<IEnumerable<Zone>> GetAllAsync(string tenantId)
    {
        return await _context.Zones
            .Where(z => z.TenantId == tenantId)
            .OrderBy(z => z.SiteId)
            .ThenBy(z => z.Name)
            .ToListAsync();
    }
    
    public async Task<IEnumerable<Zone>> GetBySiteAsync(string tenantId, string siteId)
    {
        return await _context.Zones
            .Where(z => z.TenantId == tenantId && z.SiteId == siteId)
            .OrderBy(z => z.Name)
            .ToListAsync();
    }
    
    public async Task<IEnumerable<Zone>> GetByCameraAsync(string cameraId)
    {
        return await _context.Zones
            .Where(z => z.CameraId == cameraId || z.CameraIds.Contains(cameraId))
            .OrderBy(z => z.Name)
            .ToListAsync();
    }
    
    public async Task<Zone?> GetByIdAsync(Guid id)
    {
        return await _context.Zones.FindAsync(id);
    }
    
    public async Task<Zone?> GetByZoneIdAsync(string tenantId, string siteId, string zoneId)
    {
        return await _context.Zones
            .FirstOrDefaultAsync(z => 
                z.TenantId == tenantId && 
                z.SiteId == siteId && 
                z.ZoneId == zoneId);
    }
    
    public async Task<Zone> AddAsync(Zone zone)
    {
        zone.CreatedAt = DateTime.UtcNow;
        _context.Zones.Add(zone);
        await _context.SaveChangesAsync();
        return zone;
    }
    
    public async Task UpdateAsync(Zone zone)
    {
        zone.UpdatedAt = DateTime.UtcNow;
        _context.Zones.Update(zone);
        await _context.SaveChangesAsync();
    }
    
    public async Task DeleteAsync(Guid id)
    {
        var zone = await _context.Zones.FindAsync(id);
        if (zone != null)
        {
            _context.Zones.Remove(zone);
            await _context.SaveChangesAsync();
        }
    }
}
