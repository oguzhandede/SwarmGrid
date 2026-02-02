using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SwarmGrid.Domain.Entities;
using SwarmGrid.Infrastructure.Data;

namespace SwarmGrid.Api.Controllers;

/// <summary>
/// OTA update management API.
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class UpdateController : ControllerBase
{
    private readonly SwarmGridDbContext _context;
    private readonly ILogger<UpdateController> _logger;
    
    public UpdateController(
        SwarmGridDbContext context,
        ILogger<UpdateController> logger)
    {
        _context = context;
        _logger = logger;
    }
    
    /// <summary>
    /// Check for available updates.
    /// </summary>
    [HttpGet("check")]
    public async Task<ActionResult<UpdateCheckResponse>> CheckUpdate(
        [FromQuery] string currentVersion,
        [FromQuery] string? tenantId = null)
    {
        var query = _context.AgentVersions
            .Where(v => v.IsActive);
            
        // Filter by tenant if specified
        if (!string.IsNullOrEmpty(tenantId))
        {
            query = query.Where(v => v.TargetTenantId == null || v.TargetTenantId == tenantId);
        }
        else
        {
            query = query.Where(v => v.TargetTenantId == null);
        }
        
        var latestVersion = await query
            .OrderByDescending(v => v.ReleasedAt)
            .FirstOrDefaultAsync();
            
        if (latestVersion == null)
        {
            return Ok(new UpdateCheckResponse(
                currentVersion,
                null,
                false,
                false,
                null,
                null
            ));
        }
        
        var comparison = CompareVersions(latestVersion.Version, currentVersion);
        var updateAvailable = comparison > 0;
        
        // Check minimum version requirement
        var canUpdate = true;
        if (!string.IsNullOrEmpty(latestVersion.MinimumVersion))
        {
            canUpdate = CompareVersions(currentVersion, latestVersion.MinimumVersion) >= 0;
        }
        
        return Ok(new UpdateCheckResponse(
            currentVersion,
            updateAvailable ? latestVersion.Version : null,
            updateAvailable,
            latestVersion.IsRequired && updateAvailable,
            updateAvailable ? latestVersion.ReleaseNotes : null,
            updateAvailable && canUpdate ? new UpdateInfo(
                latestVersion.Version,
                latestVersion.DownloadUrl,
                latestVersion.ConfigPatchJson,
                latestVersion.Checksum,
                latestVersion.IsRequired
            ) : null
        ));
    }
    
    /// <summary>
    /// Get specific version details.
    /// </summary>
    [HttpGet("version/{version}")]
    public async Task<ActionResult<AgentVersionDto>> GetVersion(string version)
    {
        var agentVersion = await _context.AgentVersions
            .FirstOrDefaultAsync(v => v.Version == version);
            
        if (agentVersion == null)
        {
            return NotFound();
        }
        
        return Ok(new AgentVersionDto(
            agentVersion.Id,
            agentVersion.Version,
            agentVersion.ReleaseNotes,
            agentVersion.DownloadUrl,
            agentVersion.ConfigPatchJson,
            agentVersion.Checksum,
            agentVersion.MinimumVersion,
            agentVersion.ReleasedAt,
            agentVersion.IsRequired,
            agentVersion.IsActive
        ));
    }
    
    /// <summary>
    /// List all versions.
    /// </summary>
    [HttpGet("versions")]
    public async Task<ActionResult<IEnumerable<AgentVersionDto>>> ListVersions(
        [FromQuery] bool activeOnly = true)
    {
        var query = _context.AgentVersions.AsQueryable();
        
        if (activeOnly)
        {
            query = query.Where(v => v.IsActive);
        }
        
        var versions = await query
            .OrderByDescending(v => v.ReleasedAt)
            .Take(20)
            .ToListAsync();
            
        return Ok(versions.Select(v => new AgentVersionDto(
            v.Id,
            v.Version,
            v.ReleaseNotes,
            v.DownloadUrl,
            v.ConfigPatchJson,
            v.Checksum,
            v.MinimumVersion,
            v.ReleasedAt,
            v.IsRequired,
            v.IsActive
        )));
    }
    
    /// <summary>
    /// Create a new version (admin).
    /// </summary>
    [HttpPost("versions")]
    public async Task<ActionResult<AgentVersionDto>> CreateVersion(
        [FromBody] CreateVersionRequest request)
    {
        // Check for duplicate version
        var existing = await _context.AgentVersions
            .FirstOrDefaultAsync(v => v.Version == request.Version);
            
        if (existing != null)
        {
            return Conflict($"Version {request.Version} already exists");
        }
        
        var version = new AgentVersion
        {
            Version = request.Version,
            ReleaseNotes = request.ReleaseNotes,
            DownloadUrl = request.DownloadUrl,
            ConfigPatchJson = request.ConfigPatchJson,
            Checksum = request.Checksum,
            MinimumVersion = request.MinimumVersion,
            ReleasedAt = DateTime.UtcNow,
            IsRequired = request.IsRequired,
            IsActive = request.IsActive,
            TargetTenantId = request.TargetTenantId
        };
        
        _context.AgentVersions.Add(version);
        await _context.SaveChangesAsync();
        
        _logger.LogInformation("Created agent version {Version}", version.Version);
        
        return CreatedAtAction(nameof(GetVersion),
            new { version = version.Version },
            new AgentVersionDto(
                version.Id,
                version.Version,
                version.ReleaseNotes,
                version.DownloadUrl,
                version.ConfigPatchJson,
                version.Checksum,
                version.MinimumVersion,
                version.ReleasedAt,
                version.IsRequired,
                version.IsActive
            ));
    }
    
    /// <summary>
    /// Report update result from edge agent.
    /// </summary>
    [HttpPost("report")]
    public async Task<IActionResult> ReportUpdate([FromBody] UpdateReportRequest request)
    {
        _logger.LogInformation(
            "Update report from device {DeviceId}: {FromVersion} -> {ToVersion}, Success: {Success}",
            request.DeviceId,
            request.FromVersion,
            request.ToVersion,
            request.Success);
            
        // Update device version if successful
        if (request.Success)
        {
            var device = await _context.Devices
                .FirstOrDefaultAsync(d => d.DeviceId == request.DeviceId);
                
            if (device != null)
            {
                device.AgentVersion = request.ToVersion;
                await _context.SaveChangesAsync();
            }
        }
        
        return Ok(new { received = true });
    }
    
    #region Helper Methods
    
    private static int CompareVersions(string v1, string v2)
    {
        try
        {
            var parts1 = v1.Split('.').Select(int.Parse).ToArray();
            var parts2 = v2.Split('.').Select(int.Parse).ToArray();
            
            for (int i = 0; i < Math.Max(parts1.Length, parts2.Length); i++)
            {
                var p1 = i < parts1.Length ? parts1[i] : 0;
                var p2 = i < parts2.Length ? parts2[i] : 0;
                
                if (p1 > p2) return 1;
                if (p1 < p2) return -1;
            }
            
            return 0;
        }
        catch
        {
            return string.Compare(v1, v2, StringComparison.Ordinal);
        }
    }
    
    #endregion
}

#region DTOs

public record UpdateCheckResponse(
    string CurrentVersion,
    string? LatestVersion,
    bool UpdateAvailable,
    bool IsRequired,
    string? ReleaseNotes,
    UpdateInfo? Update
);

public record UpdateInfo(
    string Version,
    string? DownloadUrl,
    string? ConfigPatch,
    string? Checksum,
    bool IsRequired
);

public record AgentVersionDto(
    Guid Id,
    string Version,
    string ReleaseNotes,
    string? DownloadUrl,
    string? ConfigPatchJson,
    string? Checksum,
    string? MinimumVersion,
    DateTime ReleasedAt,
    bool IsRequired,
    bool IsActive
);

public record CreateVersionRequest(
    string Version,
    string ReleaseNotes,
    string? DownloadUrl,
    string? ConfigPatchJson,
    string? Checksum,
    string? MinimumVersion,
    bool IsRequired = false,
    bool IsActive = true,
    string? TargetTenantId = null
);

public record UpdateReportRequest(
    string DeviceId,
    string FromVersion,
    string ToVersion,
    bool Success,
    string? ErrorMessage
);

#endregion
