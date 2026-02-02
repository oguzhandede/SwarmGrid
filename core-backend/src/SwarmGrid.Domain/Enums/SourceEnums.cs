namespace SwarmGrid.Domain.Enums;

/// <summary>
/// Type of video/stream source.
/// </summary>
public enum SourceType
{
    Video = 0,
    Camera = 1
}

/// <summary>
/// Status of source processing.
/// </summary>
public enum SourceStatus
{
    Pending = 0,
    Processing = 1,
    Completed = 2,
    Error = 3,
    Connected = 4,
    Disconnected = 5
}
