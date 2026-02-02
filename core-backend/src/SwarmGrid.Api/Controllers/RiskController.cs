using Microsoft.AspNetCore.Mvc;
using SwarmGrid.Application.Interfaces;
using SwarmGrid.Application.RiskEngine;
using SwarmGrid.Domain.Enums;

namespace SwarmGrid.Api.Controllers;

/// <summary>
/// Risk status and events API.
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class RiskController : ControllerBase
{
    private readonly IRiskEventRepository _riskEventRepository;
    private readonly ILogger<RiskController> _logger;
    
    public RiskController(
        IRiskEventRepository riskEventRepository,
        ILogger<RiskController> logger)
    {
        _riskEventRepository = riskEventRepository;
        _logger = logger;
    }
    
    /// <summary>
    /// Get current risk status for a zone.
    /// </summary>
    [HttpGet("current/{zoneId}")]
    public async Task<ActionResult<RiskEventDto>> GetCurrentRisk(string zoneId)
    {
        // Get the most recent risk event for the zone
        var recentEvents = await _riskEventRepository.GetRecentByZoneAsync(zoneId, 1);
        
        if (recentEvents.Count == 0)
        {
            // Return default green status if no events
            return Ok(new RiskEventDto(
                Guid.NewGuid(),
                "demo",
                "site-01",
                "cam-01",
                zoneId,
                DateTime.UtcNow,
                0.0,
                RiskLevel.Green,
                [],
                false
            ));
        }
        
        var riskEvent = recentEvents[0];
        return Ok(new RiskEventDto(
            riskEvent.Id,
            riskEvent.TenantId,
            riskEvent.SiteId,
            riskEvent.CameraId,
            riskEvent.ZoneId,
            riskEvent.CreatedAt,
            riskEvent.RiskScore,
            riskEvent.RiskLevel,
            riskEvent.SuggestedActions,
            riskEvent.Acknowledged
        ));
    }
    
    /// <summary>
    /// Get recent risk events for a site.
    /// </summary>
    [HttpGet("events/{siteId}")]
    public async Task<ActionResult<List<RiskEventDto>>> GetRecentEvents(
        string siteId,
        [FromQuery] int limit = 50)
    {
        var events = await _riskEventRepository.GetRecentBySiteAsync(siteId, limit);
        
        var dtos = events.Select(e => new RiskEventDto(
            e.Id,
            e.TenantId,
            e.SiteId,
            e.CameraId,
            e.ZoneId,
            e.CreatedAt,
            e.RiskScore,
            e.RiskLevel,
            e.SuggestedActions,
            e.Acknowledged
        )).ToList();
        
        return Ok(dtos);
    }
    
    /// <summary>
    /// Acknowledge a risk event.
    /// </summary>
    [HttpPost("events/{eventId}/acknowledge")]
    public async Task<IActionResult> AcknowledgeEvent(
        Guid eventId,
        [FromBody] AcknowledgeRequest request)
    {
        var acknowledgedEvent = await _riskEventRepository.AcknowledgeAsync(
            eventId, 
            request.UserId, 
            request.Note);
            
        if (acknowledgedEvent == null)
        {
            _logger.LogWarning("Event {EventId} not found for acknowledgment", eventId);
            return NotFound(new { error = "Event not found" });
        }
        
        _logger.LogInformation(
            "Event {EventId} acknowledged by {User}",
            eventId,
            request.UserId);
            
        return Ok(new { 
            acknowledged = true, 
            acknowledgedAt = acknowledgedEvent.AcknowledgedAt,
            acknowledgedBy = acknowledgedEvent.AcknowledgedBy
        });
    }
}

public record AcknowledgeRequest(string UserId, string? Note);
