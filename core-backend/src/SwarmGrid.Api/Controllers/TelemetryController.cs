using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.SignalR;
using SwarmGrid.Api.Hubs;
using SwarmGrid.Application.RiskEngine;
using SwarmGrid.Application.Telemetry;
using SwarmGrid.Domain.Entities;
using SwarmGrid.Infrastructure.Data;

namespace SwarmGrid.Api.Controllers;

/// <summary>
/// Telemetry ingestion API for Edge Agents.
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class TelemetryController : ControllerBase
{
    private readonly RiskEngineV1 _riskEngine;
    private readonly IHubContext<RiskHub> _hubContext;
    private readonly SwarmGridDbContext _dbContext;
    private readonly ILogger<TelemetryController> _logger;
    
    public TelemetryController(
        RiskEngineV1 riskEngine,
        IHubContext<RiskHub> hubContext,
        SwarmGridDbContext dbContext,
        ILogger<TelemetryController> logger)
    {
        _riskEngine = riskEngine;
        _hubContext = hubContext;
        _dbContext = dbContext;
        _logger = logger;
    }
    
    /// <summary>
    /// Ingest telemetry data from Edge Agent.
    /// </summary>
    [HttpPost("ingest")]
    public async Task<IActionResult> Ingest([FromBody] List<TelemetryDto> telemetryBatch)
    {
        if (telemetryBatch == null || telemetryBatch.Count == 0)
            return BadRequest("Empty telemetry batch");
        
        try
        {
            var riskEventDtos = new List<RiskEventDto>();
            var telemetriesToPersist = new List<Telemetry>();
            var riskEventsToStore = new List<RiskEvent>();
            
            foreach (var dto in telemetryBatch)
            {
                // Normalize timestamp to UTC for PostgreSQL compatibility
                var timestamp = dto.Timestamp.Kind == DateTimeKind.Unspecified
                    ? DateTime.SpecifyKind(dto.Timestamp, DateTimeKind.Utc)
                    : dto.Timestamp.ToUniversalTime();
                    
                var telemetry = new Telemetry
                {
                    TenantId = dto.TenantId,
                    SiteId = dto.SiteId,
                    CameraId = dto.CameraId,
                    ZoneId = dto.ZoneId,
                    Timestamp = timestamp,
                    Density = dto.Density,
                    AvgSpeed = dto.AvgSpeed,
                    SpeedVariance = dto.SpeedVariance,
                    FlowEntropy = dto.FlowEntropy,
                    Alignment = dto.Alignment,
                    BottleneckIndex = dto.BottleneckIndex
                };
                
                telemetriesToPersist.Add(telemetry);
                
                // Calculate risk (uses Redis for trend analysis)
                var riskEvent = await _riskEngine.CalculateRiskAsync(telemetry);
                riskEventsToStore.Add(riskEvent);
                
                var riskEventDto = new RiskEventDto(
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
                );
                
                riskEventDtos.Add(riskEventDto);
                
                // Log significant events
                if (riskEvent.RiskLevel >= Domain.Enums.RiskLevel.Yellow)
                {
                    _logger.LogWarning(
                        "Risk alert: {Zone} - {Level} ({Score:P0})",
                        riskEvent.ZoneId,
                        riskEvent.RiskLevel,
                        riskEvent.RiskScore);
                }
            }
            
            // Add all entities and save atomically (single transaction)
            await _dbContext.Telemetries.AddRangeAsync(telemetriesToPersist);
            await _dbContext.RiskEvents.AddRangeAsync(riskEventsToStore);
            await _dbContext.SaveChangesAsync();
            
            // Push via SignalR after successful save
            foreach (var riskEventDto in riskEventDtos)
            {
                await _hubContext.SendRiskUpdate(riskEventDto);
            }
            
            _logger.LogInformation(
                "Ingested {Count} telemetry records, generated {RiskCount} risk events",
                telemetryBatch.Count,
                riskEventDtos.Count);
            
            return Ok(new { processed = telemetryBatch.Count, riskEvents = riskEventDtos });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to ingest telemetry batch");
            return StatusCode(500, new { error = "Failed to process telemetry batch", details = ex.Message });
        }
    }
}


