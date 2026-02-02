using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace SwarmGrid.Infrastructure.Data.Migrations
{
    /// <inheritdoc />
    public partial class AddZonesTable : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "Zones",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    SiteId = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    ZoneId = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    Name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    Description = table.Column<string>(type: "character varying(1000)", maxLength: 1000, nullable: true),
                    CameraId = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    PolygonJson = table.Column<string>(type: "jsonb", nullable: true),
                    BottleneckPointsJson = table.Column<string>(type: "jsonb", nullable: true),
                    MaxCapacity = table.Column<int>(type: "integer", nullable: false),
                    YellowThreshold = table.Column<double>(type: "double precision", nullable: false),
                    RedThreshold = table.Column<double>(type: "double precision", nullable: false),
                    CameraIds = table.Column<string>(type: "text", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Zones", x => x.Id);
                });

            migrationBuilder.CreateIndex(
                name: "IX_Zones_CameraId",
                table: "Zones",
                column: "CameraId");

            migrationBuilder.CreateIndex(
                name: "IX_Zones_TenantId_SiteId",
                table: "Zones",
                columns: new[] { "TenantId", "SiteId" });

            migrationBuilder.CreateIndex(
                name: "IX_Zones_TenantId_SiteId_ZoneId",
                table: "Zones",
                columns: new[] { "TenantId", "SiteId", "ZoneId" },
                unique: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "Zones");
        }
    }
}
