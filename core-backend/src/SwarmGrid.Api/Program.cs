using StackExchange.Redis;
using SwarmGrid.Api.Hubs;
using SwarmGrid.Application.Caching;
using SwarmGrid.Application.RiskEngine;
using SwarmGrid.Infrastructure;
using SwarmGrid.Infrastructure.Caching;
using SwarmGrid.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

// Add services
builder.Services.AddControllers();
builder.Services.AddSignalR();

// Add CORS for dashboard
builder.Services.AddCors(options =>
{
    options.AddPolicy("Dashboard", policy =>
    {
        policy.WithOrigins(
                "http://localhost:3000",
                "http://localhost:3001",
                "http://localhost:3002")
              .AllowAnyHeader()
              .AllowAnyMethod()
              .AllowCredentials();
    });
});

// PostgreSQL connection
var postgresConnectionString = builder.Configuration.GetConnectionString("PostgreSQL") 
    ?? "Host=localhost;Database=swarmgrid;Username=swarmgrid;Password=swarmgrid";
builder.Services.AddInfrastructure(postgresConnectionString);
Console.WriteLine($"PostgreSQL configured: {postgresConnectionString.Split(';')[0]}");

// Redis connection
var redisConnectionString = builder.Configuration.GetConnectionString("Redis") ?? "localhost:6379";
try
{
    var redis = ConnectionMultiplexer.Connect(redisConnectionString);
    builder.Services.AddSingleton<IConnectionMultiplexer>(redis);
    builder.Services.AddScoped<IRiskScoreCache, RedisRiskScoreCache>();
    builder.Services.AddScoped<RiskEngineV1>(sp => 
        new RiskEngineV1(sp.GetRequiredService<IRiskScoreCache>()));
    
    Console.WriteLine($"Redis connected: {redisConnectionString}");
}
catch (Exception ex)
{
    // Fallback: Register RiskEngine without Redis
    Console.WriteLine($"Redis connection failed ({redisConnectionString}): {ex.Message}");
    Console.WriteLine("Using in-memory fallback for risk score caching.");
    builder.Services.AddSingleton<RiskEngineV1>();
}

var app = builder.Build();

// Apply pending migrations on startup (optional - for development)
if (app.Environment.IsDevelopment())
{
    using var scope = app.Services.CreateScope();
    var dbContext = scope.ServiceProvider.GetRequiredService<SwarmGridDbContext>();
    try
    {
        dbContext.Database.Migrate();
        Console.WriteLine("Database migrations applied successfully.");
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Database migration warning: {ex.Message}");
        Console.WriteLine("Ensure PostgreSQL is running and try again.");
    }
}

// Configure pipeline
app.UseCors("Dashboard");
app.UseHttpsRedirection();
app.MapControllers();
app.MapHub<RiskHub>("/hubs/risk");

// Health check endpoint
app.MapGet("/health", () => new { status = "healthy", timestamp = DateTime.UtcNow });

app.Run();

