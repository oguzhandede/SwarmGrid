using System.Text.Json;
using Microsoft.AspNetCore.Mvc;
using SwarmGrid.Application.Interfaces;
using SwarmGrid.Application.Zones;
using SwarmGrid.Domain.Entities;

namespace SwarmGrid.Api.Controllers;

/// <summary>
/// API for managing zones with polygon ROI support.
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class ZoneController : ControllerBase
{
    private readonly IZoneRepository _zoneRepository;
    private readonly ILogger<ZoneController> _logger;
    
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase
    };
    
    public ZoneController(
        IZoneRepository zoneRepository,
        ILogger<ZoneController> logger)
    {
        _zoneRepository = zoneRepository;
        _logger = logger;
    }
    
    /// <summary>
    /// Get all zones for a tenant.
    /// </summary>
    [HttpGet]
    public async Task<ActionResult<IEnumerable<ZoneDto>>> GetAll(
        [FromQuery] string tenantId = "demo",
        [FromQuery] string? siteId = null)
    {
        IEnumerable<Zone> zones;
        
        if (!string.IsNullOrEmpty(siteId))
        {
            zones = await _zoneRepository.GetBySiteAsync(tenantId, siteId);
        }
        else
        {
            zones = await _zoneRepository.GetAllAsync(tenantId);
        }
        
        return Ok(zones.Select(ToDto));
    }
    
    /// <summary>
    /// Get zone by ID.
    /// </summary>
    [HttpGet("{id:guid}")]
    public async Task<ActionResult<ZoneDto>> GetById(Guid id)
    {
        var zone = await _zoneRepository.GetByIdAsync(id);
        if (zone == null)
            return NotFound();
            
        return Ok(ToDto(zone));
    }
    
    /// <summary>
    /// Get zones by camera ID.
    /// </summary>
    [HttpGet("by-camera/{cameraId}")]
    public async Task<ActionResult<IEnumerable<ZoneDto>>> GetByCamera(string cameraId)
    {
        var zones = await _zoneRepository.GetByCameraAsync(cameraId);
        return Ok(zones.Select(ToDto));
    }
    
    /// <summary>
    /// Get zone by zone ID string.
    /// </summary>
    [HttpGet("by-zoneid/{zoneId}")]
    public async Task<ActionResult<ZoneDto>> GetByZoneId(
        string zoneId,
        [FromQuery] string tenantId = "demo",
        [FromQuery] string siteId = "site-01")
    {
        var zone = await _zoneRepository.GetByZoneIdAsync(tenantId, siteId, zoneId);
        if (zone == null)
            return NotFound();
            
        return Ok(ToDto(zone));
    }
    
    /// <summary>
    /// Create a new zone.
    /// </summary>
    [HttpPost]
    public async Task<ActionResult<ZoneDto>> Create([FromBody] CreateZoneDto dto)
    {
        // Check for duplicate
        var existing = await _zoneRepository.GetByZoneIdAsync(dto.TenantId, dto.SiteId, dto.ZoneId);
        if (existing != null)
            return Conflict($"Zone with ID '{dto.ZoneId}' already exists");
        
        var zone = new Zone
        {
            TenantId = dto.TenantId,
            SiteId = dto.SiteId,
            ZoneId = dto.ZoneId,
            Name = dto.Name,
            Description = dto.Description,
            CameraId = dto.CameraId,
            PolygonJson = dto.Polygon != null ? JsonSerializer.Serialize(dto.Polygon, JsonOptions) : null,
            BottleneckPointsJson = dto.BottleneckPoints != null ? JsonSerializer.Serialize(dto.BottleneckPoints, JsonOptions) : null,
            MaxCapacity = dto.MaxCapacity,
            YellowThreshold = dto.YellowThreshold,
            RedThreshold = dto.RedThreshold,
            CameraIds = dto.CameraIds ?? [],
            IsActive = true
        };
        
        await _zoneRepository.AddAsync(zone);
        
        _logger.LogInformation("Created zone: {ZoneId} in site {SiteId}", zone.ZoneId, zone.SiteId);
        
        return CreatedAtAction(nameof(GetById), new { id = zone.Id }, ToDto(zone));
    }
    
    /// <summary>
    /// Update a zone.
    /// </summary>
    [HttpPut("{id:guid}")]
    public async Task<ActionResult<ZoneDto>> Update(Guid id, [FromBody] UpdateZoneDto dto)
    {
        var zone = await _zoneRepository.GetByIdAsync(id);
        if (zone == null)
            return NotFound();
        
        // Update fields if provided
        if (dto.Name != null) zone.Name = dto.Name;
        if (dto.Description != null) zone.Description = dto.Description;
        if (dto.CameraId != null) zone.CameraId = dto.CameraId;
        if (dto.Polygon != null) zone.PolygonJson = JsonSerializer.Serialize(dto.Polygon, JsonOptions);
        if (dto.BottleneckPoints != null) zone.BottleneckPointsJson = JsonSerializer.Serialize(dto.BottleneckPoints, JsonOptions);
        if (dto.MaxCapacity.HasValue) zone.MaxCapacity = dto.MaxCapacity.Value;
        if (dto.YellowThreshold.HasValue) zone.YellowThreshold = dto.YellowThreshold.Value;
        if (dto.RedThreshold.HasValue) zone.RedThreshold = dto.RedThreshold.Value;
        if (dto.CameraIds != null) zone.CameraIds = dto.CameraIds;
        if (dto.IsActive.HasValue) zone.IsActive = dto.IsActive.Value;
        
        await _zoneRepository.UpdateAsync(zone);
        
        _logger.LogInformation("Updated zone: {ZoneId}", zone.ZoneId);
        
        return Ok(ToDto(zone));
    }
    
    /// <summary>
    /// Update polygon only.
    /// </summary>
    [HttpPut("{id:guid}/polygon")]
    public async Task<ActionResult<ZoneDto>> UpdatePolygon(Guid id, [FromBody] UpdatePolygonDto dto)
    {
        var zone = await _zoneRepository.GetByIdAsync(id);
        if (zone == null)
            return NotFound();
        
        zone.PolygonJson = JsonSerializer.Serialize(dto.Polygon, JsonOptions);
        await _zoneRepository.UpdateAsync(zone);
        
        _logger.LogInformation("Updated polygon for zone: {ZoneId}", zone.ZoneId);
        
        return Ok(ToDto(zone));
    }
    
    /// <summary>
    /// Update thresholds only.
    /// </summary>
    [HttpPut("{id:guid}/thresholds")]
    public async Task<ActionResult<ZoneDto>> UpdateThresholds(Guid id, [FromBody] UpdateThresholdsDto dto)
    {
        var zone = await _zoneRepository.GetByIdAsync(id);
        if (zone == null)
            return NotFound();
        
        zone.YellowThreshold = dto.YellowThreshold;
        zone.RedThreshold = dto.RedThreshold;
        if (dto.MaxCapacity.HasValue)
            zone.MaxCapacity = dto.MaxCapacity.Value;
            
        await _zoneRepository.UpdateAsync(zone);
        
        _logger.LogInformation("Updated thresholds for zone: {ZoneId}", zone.ZoneId);
        
        return Ok(ToDto(zone));
    }
    
    /// <summary>
    /// Update bottleneck points only.
    /// </summary>
    [HttpPut("{id:guid}/bottlenecks")]
    public async Task<ActionResult<ZoneDto>> UpdateBottlenecks(Guid id, [FromBody] UpdateBottlenecksDto dto)
    {
        var zone = await _zoneRepository.GetByIdAsync(id);
        if (zone == null)
            return NotFound();
        
        zone.BottleneckPointsJson = JsonSerializer.Serialize(dto.BottleneckPoints, JsonOptions);
        await _zoneRepository.UpdateAsync(zone);
        
        _logger.LogInformation("Updated bottlenecks for zone: {ZoneId}", zone.ZoneId);
        
        return Ok(ToDto(zone));
    }
    
    /// <summary>
    /// Delete a zone.
    /// </summary>
    [HttpDelete("{id:guid}")]
    public async Task<IActionResult> Delete(Guid id)
    {
        var zone = await _zoneRepository.GetByIdAsync(id);
        if (zone == null)
            return NotFound();
        
        await _zoneRepository.DeleteAsync(id);
        
        _logger.LogInformation("Deleted zone: {ZoneId}", zone.ZoneId);
        
        return NoContent();
    }
    
    /// <summary>
    /// Convert entity to DTO.
    /// </summary>
    private static ZoneDto ToDto(Zone zone)
    {
        List<PolygonPointDto>? polygon = null;
        List<BottleneckPointDto>? bottleneckPoints = null;
        
        if (!string.IsNullOrEmpty(zone.PolygonJson))
        {
            try
            {
                polygon = JsonSerializer.Deserialize<List<PolygonPointDto>>(zone.PolygonJson, JsonOptions);
            }
            catch { /* ignore parsing errors */ }
        }
        
        if (!string.IsNullOrEmpty(zone.BottleneckPointsJson))
        {
            try
            {
                bottleneckPoints = JsonSerializer.Deserialize<List<BottleneckPointDto>>(zone.BottleneckPointsJson, JsonOptions);
            }
            catch { /* ignore parsing errors */ }
        }
        
        return new ZoneDto(
            zone.Id,
            zone.TenantId,
            zone.SiteId,
            zone.ZoneId,
            zone.Name,
            zone.Description,
            zone.CameraId,
            polygon,
            bottleneckPoints,
            zone.MaxCapacity,
            zone.YellowThreshold,
            zone.RedThreshold,
            zone.CameraIds,
            zone.IsActive,
            zone.CreatedAt,
            zone.UpdatedAt
        );
    }
}
