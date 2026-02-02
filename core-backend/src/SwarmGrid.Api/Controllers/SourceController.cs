using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.SignalR;
using SwarmGrid.Api.Hubs;
using SwarmGrid.Domain.Entities;
using SwarmGrid.Domain.Enums;

namespace SwarmGrid.Api.Controllers;

/// <summary>
/// API for managing video and camera sources.
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class SourceController : ControllerBase
{
    private static readonly Dictionary<string, Source> _sources = new();
    private readonly IHubContext<RiskHub> _hubContext;
    private readonly ILogger<SourceController> _logger;
    private readonly string _uploadPath;

    public SourceController(
        IHubContext<RiskHub> hubContext,
        ILogger<SourceController> logger,
        IWebHostEnvironment env)
    {
        _hubContext = hubContext;
        _logger = logger;
        _uploadPath = Path.Combine(env.ContentRootPath, "uploads");
        
        // Ensure upload directory exists
        if (!Directory.Exists(_uploadPath))
        {
            Directory.CreateDirectory(_uploadPath);
        }
    }

    /// <summary>
    /// Upload a video file for analysis.
    /// </summary>
    [HttpPost("video")]
    [RequestSizeLimit(500_000_000)] // 500 MB limit
    public async Task<IActionResult> UploadVideo(
        IFormFile file,
        [FromForm] string tenantId,
        [FromForm] string siteId,
        [FromForm] string zoneId,
        [FromForm] string name)
    {
        if (file == null || file.Length == 0)
            return BadRequest("No file uploaded");

        // Validate file extension
        var allowedExtensions = new[] { ".mp4", ".avi", ".mov", ".mkv", ".webm" };
        var extension = Path.GetExtension(file.FileName).ToLowerInvariant();
        
        if (!allowedExtensions.Contains(extension))
            return BadRequest($"Invalid file type. Allowed: {string.Join(", ", allowedExtensions)}");

        try
        {
            // Generate unique filename
            var sourceId = Guid.NewGuid().ToString();
            var fileName = $"{sourceId}{extension}";
            var filePath = Path.Combine(_uploadPath, fileName);

            // Save file
            using (var stream = new FileStream(filePath, FileMode.Create))
            {
                await file.CopyToAsync(stream);
            }

            // Create source record
            var source = new Source
            {
                Id = sourceId,
                TenantId = tenantId,
                SiteId = siteId,
                ZoneId = zoneId,
                Name = string.IsNullOrEmpty(name) ? file.FileName : name,
                Type = SourceType.Video,
                Url = filePath,
                Status = SourceStatus.Pending,
                Progress = 0
            };

            _sources[sourceId] = source;

            _logger.LogInformation("Video uploaded: {Name} ({Size} bytes)", source.Name, file.Length);

            return Ok(ToDto(source));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Video upload failed");
            return StatusCode(500, "Upload failed");
        }
    }

    /// <summary>
    /// Register a camera URL for streaming.
    /// </summary>
    [HttpPost("camera")]
    public IActionResult RegisterCamera([FromBody] CameraConfig config)
    {
        if (string.IsNullOrEmpty(config.RtspUrl))
            return BadRequest("RTSP URL is required");

        // Basic URL validation
        if (!config.RtspUrl.StartsWith("rtsp://") && 
            !config.RtspUrl.StartsWith("http://") &&
            !config.RtspUrl.StartsWith("https://"))
        {
            return BadRequest("Invalid URL format. Must start with rtsp://, http://, or https://");
        }

        var sourceId = Guid.NewGuid().ToString();

        var source = new Source
        {
            Id = sourceId,
            TenantId = config.TenantId,
            SiteId = config.SiteId,
            ZoneId = config.ZoneId,
            Name = config.Name,
            Type = SourceType.Camera,
            Url = config.RtspUrl,
            Status = SourceStatus.Pending,
            Progress = 0
        };

        _sources[sourceId] = source;

        _logger.LogInformation("Camera registered: {Name} ({Url})", source.Name, source.Url);

        return Ok(ToDto(source));
    }

    /// <summary>
    /// Get all sources.
    /// </summary>
    [HttpGet]
    public IActionResult GetSources([FromQuery] string? tenantId = null)
    {
        var sources = _sources.Values
            .Where(s => string.IsNullOrEmpty(tenantId) || s.TenantId == tenantId)
            .OrderByDescending(s => s.CreatedAt)
            .Select(ToDto)
            .ToList();

        return Ok(sources);
    }

    /// <summary>
    /// Get a specific source.
    /// </summary>
    [HttpGet("{id}")]
    public IActionResult GetSource(string id)
    {
        if (!_sources.TryGetValue(id, out var source))
            return NotFound();

        return Ok(ToDto(source));
    }

    /// <summary>
    /// Stream video file for browser playback.
    /// </summary>
    [HttpGet("{id}/stream")]
    public IActionResult StreamVideo(string id)
    {
        if (!_sources.TryGetValue(id, out var source))
            return NotFound("Source not found");

        // Only video files can be streamed
        if (source.Type != SourceType.Video)
            return BadRequest("Only video sources can be streamed");

        if (!System.IO.File.Exists(source.Url))
            return NotFound("Video file not found");

        var extension = Path.GetExtension(source.Url).ToLowerInvariant();
        var contentType = extension switch
        {
            ".mp4" => "video/mp4",
            ".webm" => "video/webm",
            ".avi" => "video/x-msvideo",
            ".mov" => "video/quicktime",
            ".mkv" => "video/x-matroska",
            _ => "application/octet-stream"
        };

        var fileStream = new FileStream(source.Url, FileMode.Open, FileAccess.Read, FileShare.Read);
        
        _logger.LogInformation("Streaming video: {Id} - {Path}", id, source.Url);
        
        return File(fileStream, contentType, enableRangeProcessing: true);
    }

    /// <summary>
    /// Update source properties.
    /// </summary>
    [HttpPatch("{id}")]
    public IActionResult UpdateSource(string id, [FromBody] UpdateSourceDto dto)
    {
        if (!_sources.TryGetValue(id, out var source))
            return NotFound();

        if (!string.IsNullOrEmpty(dto.ZoneId))
            source.ZoneId = dto.ZoneId;
        if (!string.IsNullOrEmpty(dto.Name))
            source.Name = dto.Name;

        _logger.LogInformation("Source updated: {Id} -> ZoneId={ZoneId}", id, source.ZoneId);

        return Ok(ToDto(source));
    }

    /// <summary>
    /// Delete a source.
    /// </summary>
    [HttpDelete("{id}")]
    public IActionResult DeleteSource(string id)
    {
        if (!_sources.TryGetValue(id, out var source))
            return NotFound();

        // Delete file if it's a video
        if (source.Type == SourceType.Video && System.IO.File.Exists(source.Url))
        {
            try
            {
                System.IO.File.Delete(source.Url);
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Failed to delete video file: {Path}", source.Url);
            }
        }

        _sources.Remove(id);
        _logger.LogInformation("Source deleted: {Id}", id);

        return NoContent();
    }

    /// <summary>
    /// Start analysis for a source.
    /// </summary>
    [HttpPost("{id}/start")]
    public async Task<IActionResult> StartAnalysis(string id)
    {
        if (!_sources.TryGetValue(id, out var source))
            return NotFound();

        if (source.Status == SourceStatus.Processing)
            return BadRequest("Analysis already in progress");

        source.Status = SourceStatus.Processing;
        source.StartedAt = DateTime.UtcNow;
        source.Progress = 0;

        _logger.LogInformation("Analysis started for source: {Id}", id);

        // Notify via SignalR
        await _hubContext.Clients.All.SendAsync("SourceProgress", new SourceProgressDto(
            id, SourceStatus.Processing, 0, "Analysis started"
        ));

        // Start background video processing for video sources
        if (source.Type == SourceType.Video && System.IO.File.Exists(source.Url))
        {
            _ = Task.Run(async () =>
            {
                await ProcessVideoInBackground(source.Id, source.Url, source.ZoneId);
            });
        }
        // Start background camera processing for camera sources
        else if (source.Type == SourceType.Camera)
        {
            _ = Task.Run(async () =>
            {
                await ProcessCameraInBackground(source.Id, source.Url, source.ZoneId);
            });
        }

        return Ok(ToDto(source));
    }

    /// <summary>
    /// Process video file in background (simulated processing).
    /// </summary>
    private async Task ProcessVideoInBackground(string sourceId, string videoPath, string zoneId)
    {
        try
        {
            _logger.LogInformation("Starting video processing for {SourceId}", sourceId);
            
            // Get video duration/frame count for progress calculation
            // For now, simulate processing with progress updates
            var random = new Random();
            var baseUrl = "http://localhost:5000";
            
            using var httpClient = new HttpClient();
            
            for (int progress = 0; progress <= 100; progress += 5)
            {
                // Simulate processing time (200-500ms per 5%)
                await Task.Delay(random.Next(200, 500));
                
                // Generate mock telemetry
                var telemetry = new
                {
                    tenantId = "demo",
                    siteId = "site-01",
                    cameraId = "video-" + sourceId.Substring(0, 8),
                    zoneId = zoneId,
                    timestamp = DateTime.UtcNow.ToString("o"),
                    density = 0.2 + random.NextDouble() * 0.6,
                    avgSpeed = 0.3 + random.NextDouble() * 0.4,
                    speedVariance = random.NextDouble() * 0.3,
                    flowEntropy = random.NextDouble() * 0.8,
                    alignment = 0.4 + random.NextDouble() * 0.5,
                    bottleneckIndex = random.NextDouble() * 0.5
                };
                
                // Send telemetry
                try
                {
                    var telemetryContent = new StringContent(
                        System.Text.Json.JsonSerializer.Serialize(new[] { telemetry }),
                        System.Text.Encoding.UTF8,
                        "application/json"
                    );
                    await httpClient.PostAsync($"{baseUrl}/api/telemetry/ingest", telemetryContent);
                }
                catch (Exception ex)
                {
                    _logger.LogWarning(ex, "Telemetry send failed");
                }
                
                // Update progress
                if (_sources.TryGetValue(sourceId, out var source))
                {
                    source.Progress = progress;
                    
                    // Broadcast progress
                    await _hubContext.Clients.All.SendAsync("SourceProgress", new SourceProgressDto(
                        sourceId, SourceStatus.Processing, progress, $"Processing: {progress}%"
                    ));
                }
            }
            
            // Mark as complete
            if (_sources.TryGetValue(sourceId, out var completedSource))
            {
                completedSource.Status = SourceStatus.Completed;
                completedSource.Progress = 100;
                completedSource.CompletedAt = DateTime.UtcNow;
                
                await _hubContext.Clients.All.SendAsync("SourceProgress", new SourceProgressDto(
                    sourceId, SourceStatus.Completed, 100, "Processing complete"
                ));
            }
            
            _logger.LogInformation("Video processing complete for {SourceId}", sourceId);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Video processing failed for {SourceId}", sourceId);
            
            if (_sources.TryGetValue(sourceId, out var errorSource))
            {
                errorSource.Status = SourceStatus.Error;
                errorSource.ErrorMessage = ex.Message;
                
                await _hubContext.Clients.All.SendAsync("SourceProgress", new SourceProgressDto(
                    sourceId, SourceStatus.Error, 0, ex.Message
                ));
            }
        }
    }

    /// <summary>
    /// Process camera stream in background - runs continuously until stopped.
    /// </summary>
    private async Task ProcessCameraInBackground(string sourceId, string cameraUrl, string zoneId)
    {
        try
        {
            _logger.LogInformation("Starting camera stream for {SourceId}: {Url}", sourceId, cameraUrl);
            
            // Mark as connected
            if (_sources.TryGetValue(sourceId, out var connectedSource))
            {
                connectedSource.Status = SourceStatus.Connected;
                await _hubContext.Clients.All.SendAsync("SourceProgress", new SourceProgressDto(
                    sourceId, SourceStatus.Connected, 0, "Camera connected"
                ));
            }
            
            // Continuous streaming - Edge Agent handles actual processing
            // This loop keeps the status as Connected until user stops
            while (true)
            {
                // Check if source still exists and is connected
                if (!_sources.TryGetValue(sourceId, out var source) || 
                    source.Status == SourceStatus.Pending)
                {
                    _logger.LogInformation("Camera stream stopped by user for {SourceId}", sourceId);
                    break;
                }
                
                // Wait before checking again (reduced from 2s to 5s to minimize CPU usage)
                await Task.Delay(5000);
            }
            
            _logger.LogInformation("Camera stream ended for {SourceId}", sourceId);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Camera stream failed for {SourceId}", sourceId);
            
            if (_sources.TryGetValue(sourceId, out var errorSource))
            {
                errorSource.Status = SourceStatus.Error;
                errorSource.ErrorMessage = ex.Message;
                
                await _hubContext.Clients.All.SendAsync("SourceProgress", new SourceProgressDto(
                    sourceId, SourceStatus.Error, 0, ex.Message
                ));
            }
        }
    }

    ///<summary>
    /// Stop analysis for a source.
    /// </summary>
    [HttpPost("{id}/stop")]
    public async Task<IActionResult> StopAnalysis(string id)
    {
        if (!_sources.TryGetValue(id, out var source))
            return NotFound();

        source.Status = SourceStatus.Pending;
        source.Progress = 0;

        _logger.LogInformation("Analysis stopped for source: {Id}", id);

        await _hubContext.Clients.All.SendAsync("SourceProgress", new SourceProgressDto(
            id, SourceStatus.Pending, 0, "Analysis stopped"
        ));

        return Ok(ToDto(source));
    }

    /// <summary>
    /// Update source progress (called by Edge Agent).
    /// </summary>
    [HttpPost("{id}/progress")]
    public async Task<IActionResult> UpdateProgress(string id, [FromBody] SourceProgressDto progress)
    {
        if (!_sources.TryGetValue(id, out var source))
            return NotFound();

        source.Status = progress.Status;
        source.Progress = progress.Progress;

        if (progress.Status == SourceStatus.Completed)
        {
            source.CompletedAt = DateTime.UtcNow;
        }
        else if (progress.Status == SourceStatus.Error)
        {
            source.ErrorMessage = progress.Message;
        }

        // Broadcast progress to dashboard
        await _hubContext.Clients.All.SendAsync("SourceProgress", progress);

        return Ok();
    }

    private static SourceDto ToDto(Source source) => new(
        source.Id,
        source.TenantId,
        source.SiteId,
        source.Type,
        source.Name,
        source.Url,
        source.Status,
        source.Progress,
        source.ZoneId,
        source.ErrorMessage,
        source.CreatedAt,
        source.StartedAt,
        source.CompletedAt
    );
}

// DTO for updating source
public record UpdateSourceDto(
    string? ZoneId = null,
    string? Name = null
);
