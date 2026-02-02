using System.Security.Cryptography;
using System.Text;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SwarmGrid.Domain.Entities;
using SwarmGrid.Infrastructure.Data;

namespace SwarmGrid.Api.Controllers;

/// <summary>
/// Device provisioning and management API.
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class DeviceController : ControllerBase
{
    private readonly SwarmGridDbContext _context;
    private readonly ILogger<DeviceController> _logger;
    
    public DeviceController(
        SwarmGridDbContext context,
        ILogger<DeviceController> logger)
    {
        _context = context;
        _logger = logger;
    }
    
    /// <summary>
    /// Register a new edge device.
    /// </summary>
    [HttpPost("register")]
    public async Task<ActionResult<DeviceRegistrationResponse>> Register(
        [FromBody] DeviceRegistrationRequest request)
    {
        // Check if device already exists
        var existingDevice = await _context.Devices
            .FirstOrDefaultAsync(d => d.DeviceId == request.DeviceId);
            
        if (existingDevice != null)
        {
            // Device already registered, validate secret
            if (VerifySecret(request.DeviceSecret, existingDevice.DeviceSecretHash))
            {
                _logger.LogInformation("Device {DeviceId} re-authenticated", request.DeviceId);
                return Ok(new DeviceRegistrationResponse(
                    existingDevice.DeviceId,
                    existingDevice.Status.ToString(),
                    "Device already registered",
                    existingDevice.IsActive
                ));
            }
            else
            {
                _logger.LogWarning("Device {DeviceId} registration failed: invalid secret", request.DeviceId);
                return Unauthorized(new { error = "Invalid device secret" });
            }
        }
        
        // Generate secret hash
        var secretHash = HashSecret(request.DeviceSecret);
        
        // Create new device
        var device = new Device
        {
            DeviceId = request.DeviceId,
            DeviceSecretHash = secretHash,
            TenantId = request.TenantId,
            SiteId = request.SiteId,
            CameraId = request.CameraId,
            Name = request.Name ?? $"Edge Agent {request.DeviceId[..8]}",
            AgentVersion = request.AgentVersion,
            IpAddress = GetClientIpAddress(),
            Status = DeviceStatus.Active, // Auto-approve for MVP
            IsActive = true
        };
        
        _context.Devices.Add(device);
        await _context.SaveChangesAsync();
        
        _logger.LogInformation(
            "New device registered: {DeviceId} for tenant {TenantId}, site {SiteId}",
            device.DeviceId, device.TenantId, device.SiteId);
            
        return CreatedAtAction(nameof(GetDevice), 
            new { deviceId = device.DeviceId },
            new DeviceRegistrationResponse(
                device.DeviceId,
                device.Status.ToString(),
                "Device registered successfully",
                device.IsActive
            ));
    }
    
    /// <summary>
    /// Validate device token.
    /// </summary>
    [HttpPost("validate")]
    public async Task<ActionResult<DeviceValidationResponse>> Validate(
        [FromBody] DeviceValidationRequest request)
    {
        var device = await _context.Devices
            .FirstOrDefaultAsync(d => d.DeviceId == request.DeviceId);
            
        if (device == null)
        {
            return NotFound(new { error = "Device not found" });
        }
        
        if (!VerifySecret(request.DeviceSecret, device.DeviceSecretHash))
        {
            _logger.LogWarning("Device {DeviceId} validation failed: invalid secret", request.DeviceId);
            return Unauthorized(new { error = "Invalid device secret" });
        }
        
        if (!device.IsActive || device.Status != DeviceStatus.Active)
        {
            return StatusCode(403, new { error = "Device not active", status = device.Status.ToString() });
        }
        
        return Ok(new DeviceValidationResponse(
            device.DeviceId,
            device.TenantId,
            device.SiteId,
            device.CameraId,
            true
        ));
    }
    
    /// <summary>
    /// Heartbeat from edge device.
    /// </summary>
    [HttpPost("heartbeat")]
    public async Task<ActionResult<HeartbeatResponse>> Heartbeat(
        [FromBody] HeartbeatRequest request)
    {
        var device = await _context.Devices
            .FirstOrDefaultAsync(d => d.DeviceId == request.DeviceId);
            
        if (device == null)
        {
            return NotFound(new { error = "Device not found" });
        }
        
        // Validate secret
        if (!VerifySecret(request.DeviceSecret, device.DeviceSecretHash))
        {
            return Unauthorized(new { error = "Invalid device secret" });
        }
        
        // Update heartbeat info
        device.LastHeartbeat = DateTime.UtcNow;
        device.IpAddress = GetClientIpAddress();
        
        if (!string.IsNullOrEmpty(request.AgentVersion))
        {
            device.AgentVersion = request.AgentVersion;
        }
        
        await _context.SaveChangesAsync();
        
        // Check for pending updates
        var updateAvailable = await CheckForUpdates(device.AgentVersion ?? "0.0.0", device.TenantId);
        
        return Ok(new HeartbeatResponse(
            DateTime.UtcNow,
            device.Status.ToString(),
            updateAvailable
        ));
    }
    
    /// <summary>
    /// Get device information.
    /// </summary>
    [HttpGet("{deviceId}")]
    public async Task<ActionResult<DeviceDto>> GetDevice(string deviceId)
    {
        var device = await _context.Devices
            .FirstOrDefaultAsync(d => d.DeviceId == deviceId);
            
        if (device == null)
        {
            return NotFound();
        }
        
        return Ok(new DeviceDto(
            device.Id,
            device.DeviceId,
            device.TenantId,
            device.SiteId,
            device.CameraId,
            device.Name,
            device.AgentVersion,
            device.IpAddress,
            device.LastHeartbeat,
            device.Status.ToString(),
            device.IsActive,
            device.CreatedAt
        ));
    }
    
    /// <summary>
    /// List all devices for a tenant.
    /// </summary>
    [HttpGet]
    public async Task<ActionResult<IEnumerable<DeviceDto>>> ListDevices(
        [FromQuery] string tenantId = "demo",
        [FromQuery] string? siteId = null)
    {
        var query = _context.Devices.Where(d => d.TenantId == tenantId);
        
        if (!string.IsNullOrEmpty(siteId))
        {
            query = query.Where(d => d.SiteId == siteId);
        }
        
        var devices = await query
            .OrderByDescending(d => d.LastHeartbeat)
            .ToListAsync();
            
        return Ok(devices.Select(d => new DeviceDto(
            d.Id,
            d.DeviceId,
            d.TenantId,
            d.SiteId,
            d.CameraId,
            d.Name,
            d.AgentVersion,
            d.IpAddress,
            d.LastHeartbeat,
            d.Status.ToString(),
            d.IsActive,
            d.CreatedAt
        )));
    }
    
    /// <summary>
    /// Revoke/deactivate a device.
    /// </summary>
    [HttpPost("{deviceId}/revoke")]
    public async Task<IActionResult> RevokeDevice(string deviceId)
    {
        var device = await _context.Devices
            .FirstOrDefaultAsync(d => d.DeviceId == deviceId);
            
        if (device == null)
        {
            return NotFound();
        }
        
        device.Status = DeviceStatus.Revoked;
        device.IsActive = false;
        await _context.SaveChangesAsync();
        
        _logger.LogInformation("Device {DeviceId} revoked", deviceId);
        
        return Ok(new { message = "Device revoked" });
    }
    
    #region Helper Methods
    
    private static string HashSecret(string secret)
    {
        using var sha256 = SHA256.Create();
        var bytes = sha256.ComputeHash(Encoding.UTF8.GetBytes(secret));
        return Convert.ToBase64String(bytes);
    }
    
    private static bool VerifySecret(string secret, string hash)
    {
        return HashSecret(secret) == hash;
    }
    
    private string? GetClientIpAddress()
    {
        return HttpContext.Connection.RemoteIpAddress?.ToString();
    }
    
    private async Task<bool> CheckForUpdates(string currentVersion, string tenantId)
    {
        var latestVersion = await _context.AgentVersions
            .Where(v => v.IsActive)
            .Where(v => v.TargetTenantId == null || v.TargetTenantId == tenantId)
            .OrderByDescending(v => v.ReleasedAt)
            .FirstOrDefaultAsync();
            
        if (latestVersion == null)
        {
            return false;
        }
        
        return CompareVersions(latestVersion.Version, currentVersion) > 0;
    }
    
    private static int CompareVersions(string v1, string v2)
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
    
    #endregion
}

#region DTOs

public record DeviceRegistrationRequest(
    string DeviceId,
    string DeviceSecret,
    string TenantId,
    string SiteId,
    string? CameraId,
    string? Name,
    string? AgentVersion
);

public record DeviceRegistrationResponse(
    string DeviceId,
    string Status,
    string Message,
    bool IsActive
);

public record DeviceValidationRequest(
    string DeviceId,
    string DeviceSecret
);

public record DeviceValidationResponse(
    string DeviceId,
    string TenantId,
    string SiteId,
    string? CameraId,
    bool IsValid
);

public record HeartbeatRequest(
    string DeviceId,
    string DeviceSecret,
    string? AgentVersion
);

public record HeartbeatResponse(
    DateTime ServerTime,
    string Status,
    bool UpdateAvailable
);

public record DeviceDto(
    Guid Id,
    string DeviceId,
    string TenantId,
    string SiteId,
    string? CameraId,
    string? Name,
    string? AgentVersion,
    string? IpAddress,
    DateTime? LastHeartbeat,
    string Status,
    bool IsActive,
    DateTime CreatedAt
);

#endregion
