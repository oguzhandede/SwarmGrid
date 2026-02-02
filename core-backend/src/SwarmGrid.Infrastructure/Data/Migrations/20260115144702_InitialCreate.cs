using System;
using System.Collections.Generic;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace SwarmGrid.Infrastructure.Data.Migrations
{
    /// <inheritdoc />
    public partial class InitialCreate : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "risk_events",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    tenant_id = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    site_id = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    camera_id = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    zone_id = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    risk_score = table.Column<double>(type: "double precision", nullable: false),
                    risk_level = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    suggested_actions = table.Column<List<string>>(type: "jsonb", nullable: false),
                    acknowledged = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    acknowledged_by = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    acknowledged_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    source_telemetry_id = table.Column<Guid>(type: "uuid", nullable: true),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "CURRENT_TIMESTAMP"),
                    updated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_risk_events", x => x.id);
                });

            migrationBuilder.CreateTable(
                name: "sources",
                columns: table => new
                {
                    id = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    tenant_id = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    site_id = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    type = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    url = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: false),
                    status = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    progress = table.Column<double>(type: "double precision", nullable: false),
                    zone_id = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    error_message = table.Column<string>(type: "character varying(1000)", maxLength: 1000, nullable: true),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "CURRENT_TIMESTAMP"),
                    started_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    completed_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_sources", x => x.id);
                });

            migrationBuilder.CreateTable(
                name: "telemetries",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    tenant_id = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    site_id = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    camera_id = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    zone_id = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    timestamp = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    density = table.Column<double>(type: "double precision", nullable: false),
                    avg_speed = table.Column<double>(type: "double precision", nullable: false),
                    speed_variance = table.Column<double>(type: "double precision", nullable: false),
                    flow_entropy = table.Column<double>(type: "double precision", nullable: false),
                    alignment = table.Column<double>(type: "double precision", nullable: false),
                    bottleneck_index = table.Column<double>(type: "double precision", nullable: false),
                    received_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "CURRENT_TIMESTAMP")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_telemetries", x => x.id);
                });

            migrationBuilder.CreateIndex(
                name: "ix_risk_events_created_at",
                table: "risk_events",
                column: "created_at");

            migrationBuilder.CreateIndex(
                name: "ix_risk_events_site_created",
                table: "risk_events",
                columns: new[] { "site_id", "created_at" });

            migrationBuilder.CreateIndex(
                name: "ix_risk_events_site_id",
                table: "risk_events",
                column: "site_id");

            migrationBuilder.CreateIndex(
                name: "ix_risk_events_zone_id",
                table: "risk_events",
                column: "zone_id");

            migrationBuilder.CreateIndex(
                name: "ix_sources_status",
                table: "sources",
                column: "status");

            migrationBuilder.CreateIndex(
                name: "ix_sources_tenant_id",
                table: "sources",
                column: "tenant_id");

            migrationBuilder.CreateIndex(
                name: "ix_telemetries_timestamp",
                table: "telemetries",
                column: "timestamp");

            migrationBuilder.CreateIndex(
                name: "ix_telemetries_zone_id",
                table: "telemetries",
                column: "zone_id");

            migrationBuilder.CreateIndex(
                name: "ix_telemetries_zone_timestamp",
                table: "telemetries",
                columns: new[] { "zone_id", "timestamp" });
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "risk_events");

            migrationBuilder.DropTable(
                name: "sources");

            migrationBuilder.DropTable(
                name: "telemetries");
        }
    }
}
