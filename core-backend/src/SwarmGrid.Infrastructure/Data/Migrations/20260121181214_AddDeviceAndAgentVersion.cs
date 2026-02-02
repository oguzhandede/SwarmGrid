using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace SwarmGrid.Infrastructure.Data.Migrations
{
    /// <inheritdoc />
    public partial class AddDeviceAndAgentVersion : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "AgentVersions",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    Version = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    ReleaseNotes = table.Column<string>(type: "text", nullable: false),
                    DownloadUrl = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    ConfigPatchJson = table.Column<string>(type: "text", nullable: true),
                    Checksum = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    MinimumVersion = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    ReleasedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    IsRequired = table.Column<bool>(type: "boolean", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    TargetTenantId = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_AgentVersions", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Devices",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    DeviceId = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    DeviceSecretHash = table.Column<string>(type: "character varying(256)", maxLength: 256, nullable: false),
                    TenantId = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    SiteId = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    CameraId = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    Name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: true),
                    AgentVersion = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    IpAddress = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    LastHeartbeat = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    Status = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    MetadataJson = table.Column<string>(type: "text", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Devices", x => x.Id);
                });

            migrationBuilder.CreateIndex(
                name: "IX_AgentVersions_IsActive",
                table: "AgentVersions",
                column: "IsActive");

            migrationBuilder.CreateIndex(
                name: "IX_AgentVersions_Version",
                table: "AgentVersions",
                column: "Version",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Devices_CameraId",
                table: "Devices",
                column: "CameraId");

            migrationBuilder.CreateIndex(
                name: "IX_Devices_DeviceId",
                table: "Devices",
                column: "DeviceId",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Devices_TenantId_SiteId",
                table: "Devices",
                columns: new[] { "TenantId", "SiteId" });
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "AgentVersions");

            migrationBuilder.DropTable(
                name: "Devices");
        }
    }
}
