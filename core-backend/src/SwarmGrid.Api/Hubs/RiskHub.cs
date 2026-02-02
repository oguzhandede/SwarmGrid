using Microsoft.AspNetCore.SignalR;
using SwarmGrid.Application.RiskEngine;

namespace SwarmGrid.Api.Hubs;

/// <summary>
/// SignalR Hub for realtime risk updates.
/// </summary>
public class RiskHub : Hub
{
    private readonly ILogger<RiskHub> _logger;
    
    public RiskHub(ILogger<RiskHub> logger)
    {
        _logger = logger;
    }
    
    public override async Task OnConnectedAsync()
    {
        _logger.LogInformation("Client connected: {ConnectionId}", Context.ConnectionId);
        await base.OnConnectedAsync();
    }
    
    public override async Task OnDisconnectedAsync(Exception? exception)
    {
        _logger.LogInformation("Client disconnected: {ConnectionId}", Context.ConnectionId);
        await base.OnDisconnectedAsync(exception);
    }
    
    /// <summary>
    /// Subscribe to a specific zone's updates.
    /// </summary>
    public async Task SubscribeToZone(string zoneId)
    {
        await Groups.AddToGroupAsync(Context.ConnectionId, $"zone:{zoneId}");
        _logger.LogInformation(
            "Client {ConnectionId} subscribed to zone {ZoneId}",
            Context.ConnectionId,
            zoneId);
    }
    
    /// <summary>
    /// Unsubscribe from a zone.
    /// </summary>
    public async Task UnsubscribeFromZone(string zoneId)
    {
        await Groups.RemoveFromGroupAsync(Context.ConnectionId, $"zone:{zoneId}");
    }
    
    /// <summary>
    /// Subscribe to a site's updates (all zones).
    /// </summary>
    public async Task SubscribeToSite(string siteId)
    {
        await Groups.AddToGroupAsync(Context.ConnectionId, $"site:{siteId}");
        _logger.LogInformation(
            "Client {ConnectionId} subscribed to site {SiteId}",
            Context.ConnectionId,
            siteId);
    }
}

/// <summary>
/// Extension methods for pushing risk events to clients.
/// </summary>
public static class RiskHubExtensions
{
    public static async Task SendRiskUpdate(
        this IHubContext<RiskHub> hubContext,
        RiskEventDto riskEvent)
    {
        // Send to zone subscribers
        await hubContext.Clients
            .Group($"zone:{riskEvent.ZoneId}")
            .SendAsync("RiskUpdate", riskEvent);
            
        // Send to site subscribers
        await hubContext.Clients
            .Group($"site:{riskEvent.SiteId}")
            .SendAsync("RiskUpdate", riskEvent);
    }
}
