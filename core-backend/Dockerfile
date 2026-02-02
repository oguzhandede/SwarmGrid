FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base
WORKDIR /app
EXPOSE 5000

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copy project files
COPY src/SwarmGrid.Domain/SwarmGrid.Domain.csproj SwarmGrid.Domain/
COPY src/SwarmGrid.Application/SwarmGrid.Application.csproj SwarmGrid.Application/
COPY src/SwarmGrid.Infrastructure/SwarmGrid.Infrastructure.csproj SwarmGrid.Infrastructure/
COPY src/SwarmGrid.Api/SwarmGrid.Api.csproj SwarmGrid.Api/

# Restore
RUN dotnet restore SwarmGrid.Api/SwarmGrid.Api.csproj

# Copy source
COPY src/ .

# Build
RUN dotnet build SwarmGrid.Api/SwarmGrid.Api.csproj -c Release -o /app/build

FROM build AS publish
RUN dotnet publish SwarmGrid.Api/SwarmGrid.Api.csproj -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENV ASPNETCORE_URLS=http://+:5000
ENTRYPOINT ["dotnet", "SwarmGrid.Api.dll"]
